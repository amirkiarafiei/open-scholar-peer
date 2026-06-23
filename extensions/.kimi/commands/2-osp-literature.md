---
description: "OSP Phase 2: External retrieval — one round per invocation (sub-domain, method, temporal)"
reads: [".brain/session/session.json", ".brain/session/raw/01_structured_summary.md"]
writes: [".brain/session/raw/02a_literature_round1.md", ".brain/session/raw/02b_literature_round2.md", ".brain/session/raw/02c_literature_round3.md", ".brain/session/raw/02_retrieved_literature.md", ".brain/session/session.json"]
---

# /2-osp-literature — Literature Review & Expansion

Runs ONE round of external retrieval per invocation. Invoke up to 3 times to complete all rounds.
After each round it shows a progress banner and asks whether to continue.

## Activation

Invoke the `osp-literature-review-agent` skill.

## Prerequisites

- `phases.summary.status == "completed"` and `01_structured_summary.md` exists.
- Rounds must be run in order (1 → 2 → 3).

## Resource notice

⚠️ Each invocation makes ~8-12 API calls across 3 databases (arXiv, Semantic Scholar, Google Scholar), called **one at a time**. Wall-clock time per round depends on provider latency — a slow or rate-limited provider blocks until `OSP_CALL_TIMEOUT` expires (default 180 s). Tune this in your `.env` to match your tolerance: `OSP_CALL_TIMEOUT=30` means any hung provider bails in 30 s. This is a config setting, not a workaround.

## Round definitions

| # | Anchor | Goal |
|---|--------|------|
| 1 | `sub-domain-anchor` | Search using the paper's stated sub-domain and primary keywords |
| 2 | `method-anchor` | Search using the method's name and key technical terms |
| 3 | `temporal-expansion` | Filter to last 12 months; include arXiv pre-prints, concurrent submissions |

## Steps

1. Read `.brain/session/session.json`.
   - Determine `next_round = phases.literature.rounds_completed + 1` (default 0 → next = 1).
   - If `next_round > 3`, print: "All 3 rounds complete. Next: `/3-osp-historian`." and stop.
   - If any earlier round file is missing, resume from that round instead.

2. Read `.brain/session/raw/01_structured_summary.md`.

3. Run the **next pending round only**:
   - Activate the `osp-literature-review-agent` skill for that round.
   - The skill searches each provider **separately, in order**: `search-arxiv` → `search-semantic-scholar` → `search-google-scholar`, then native web search. Prefer individual calls over `search-all` to ensure partial results and early progress reporting if one provider hangs, though `search-all` remains available if a unified lookup is preferred.
   - Write the round file (`02a`, `02b`, or `02c`) using the template at `defaults/round_strategy_template.md`.

4. Update `session.json`:
   - Increment `phases.literature.rounds_completed`.
   - If `rounds_completed == 1`: set `phases.literature.status = "in_progress"`.
   - If `rounds_completed == 3`: set `phases.literature.status = "completed"`,
     `phases.literature.notes = "3 rounds; <N> unique papers retained"`, `resume_from = "historian"`.
     Write the consolidated `.brain/session/raw/02_retrieved_literature.md` (deduplicated table of all retained papers).

5. Print a progress banner and brief findings summary:
   ```
   ── Literature Review ────────────────────────────────
   Round N/3 complete  (anchor: <anchor-name>)
   Papers retained this round: <n>
   Top finds: <2-3 bullet highlights>

   Sources this round:
     arxiv             ✅  <n> papers
     semantic_scholar  ✅/⚠️  <n> papers (or: timed out)
     google_scholar    ✅/⚠️  <n> papers (or: rate-limited)
     web search        ✅/—  (native tool or unavailable)

    ↳ .brain/session/raw/02N_literature_round<N>.md
   ──────────────────────────────────────────────
   ```
   - If `rounds_completed < 3`: "Run `/2-osp-literature` again to continue to round N+1."
   - If `rounds_completed == 3`: "Next: /3-osp-historian"

## Re-run behavior

Calling `/2-osp-literature` when a round is already complete will re-run that same round.
Warn once before overwriting its file, then proceed.
