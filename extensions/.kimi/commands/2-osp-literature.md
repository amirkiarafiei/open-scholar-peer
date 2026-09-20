---
description: "OSP Phase 2: External retrieval — one round per invocation (sub-domain, method, temporal)"
reads: [".brain/session.json", ".brain/raw/01_structured_summary.md"]
writes: [".brain/raw/02a_literature_round1.md", ".brain/raw/02b_literature_round2.md", ".brain/raw/02c_literature_round3.md", ".brain/raw/02_retrieved_literature.md", ".brain/session.json"]
---

# /2-osp-literature — Literature Review & Expansion

Runs ONE round of external retrieval per invocation. Three rounds are recommended; the user decides how
many to run. After each round it reports what it found and offers both routes: another round, or move on.

## Activation

Invoke the `osp-literature-review-agent` skill.

## Inputs — none of these is a gate

- `phases.summary.status == "completed"` and `01_structured_summary.md` exists. Without it, read
  `.brain/input/paper.md` and derive the query terms yourself; say in Provenance that you did.
- Rounds run in order (1 → 2 → 3) because each strategy builds on the last. **How many you run is the
  user's choice** — one round is a valid, thinner corpus, not an error.

## Resource notice

⚠️ Each invocation makes ~8-12 API calls across whichever databases this project
installed, plus native web search. Expect 1-3 minutes per round.

## Round definitions

| # | Anchor | Goal |
|---|--------|------|
| 1 | `sub-domain-anchor` | Search using the paper's stated sub-domain and primary keywords |
| 2 | `method-anchor` | Search using the method's name and key technical terms |
| 3 | `temporal-expansion` | Filter to last 12 months; include arXiv pre-prints, concurrent submissions |

## Steps

1. Read `.brain/session.json`.
   - Determine `next_round = phases.literature.rounds_completed + 1` (default 0 → next = 1).
   - If `next_round > 3`, all three recommended rounds are done: consolidate if that has not happened
     yet, and point at `/3-osp-historian`.
   - If any earlier round file is missing, resume from that round instead.

2. Read `.brain/raw/01_structured_summary.md`.

3. Run the **next pending round only**:
   - Activate the `osp-literature-review-agent` skill for that round.
   - The skill lists the retrieval tools this project installed, picks the ones that suit the paper's
     field (its `## Sources` section is the rule), and dispatches them together with **different
     query formulations**.
   - Write the round file (`02a`, `02b`, or `02c`) using the template at `defaults/round_strategy_template.md`.

4. Update `session.json`:
   - Increment `phases.literature.rounds_completed`.
   - Set `phases.literature.status = "in_progress"`.
   - **Then offer the choice, and act on the answer.** Another round, or move on. Whenever the user
     moves on — after 1, 2 or 3 rounds — set `phases.literature.status = "completed"`,
     `phases.literature.notes = "<N> of 3 rounds; <M> unique papers retained"`,
     `resume_from = "historian"`, and write the consolidated `02_retrieved_literature.md`
     (deduplicated table of everything retained so far). Stopping at 1 or 2 rounds is a completed
     phase with a smaller corpus, **not** an incomplete one.
   - If they stopped early, set `phases.literature.skip_reason` to their reason, or
     `"user moved on after round <N>"` if they gave none.

5. Print a progress banner and brief findings summary:
   ```
   ── Literature Review ────────────────────────────────────
   Round N/3 complete  (anchor: <anchor-name>)
   Papers retained this round: <n>
   Top finds: <2-3 bullet highlights>
   ↳ .brain/raw/02N_literature_round<N>.md
   ─────────────────────────────────────────────────────────
   ```
   - If `rounds_completed < 3`, give both routes, recommended first: `/2-osp-literature` for round
     N+1, or `/3-osp-historian` to move on with what is already retained. Say once what the thinner
     corpus costs — a round-2 stop means the method-anchor search never ran, so concurrent work using
     the same technique may be missing. Do not repeat it on the next invocation.
   - If `rounds_completed == 3`: "Next: /3-osp-historian"

## Re-run behavior

Calling `/2-osp-literature` when a round is already complete will re-run that same round.
Warn once before overwriting its file, then proceed.
