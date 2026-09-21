---
description: >
  The execution log, part two. Milestones from M14, their deliverables, the acceptance criteria each
  one is judged against, and the report written when each is done. Same job as part one: the file an
  agent opens to find out what to build next, and writes to when the build moves. Append-only and
  chronological.
  NOT here: the loop, the circuit breakers and the milestone table — those are stated once, in part
  one. Nor why a choice was made (BRAINSTORM.md), nor any rule that outlives the milestone
  (MANIFESTO.md / ARCHITECTURE.md).
authority: state
writes: agent, every session
status: active
covers: "Extensions phase, 2026-09-21 onward — M14 onward"
last_updated: "2026-09-21"
---

# 📈 PROGRESS, part two — What we are building

> **← Previous:** [`PROGRESS.md`](PROGRESS.md) — M1–M13, closed. Everything before 2026-09-21.
> **Next →** none yet. When this file is split, the pointer goes here and in the new part.

**How to work through this file is written in part one, not here.** [The loop](PROGRESS.md#the-loop),
[the circuit breakers](PROGRESS.md#circuit-breakers), [the releases](PROGRESS.md#releases) and
[the milestone table](PROGRESS.md#milestones) are stated once, there. This part holds only the
milestones themselves.

**Where part one ended.** M11–M13 built the search layer: 22 MCP tools over six open databases, full
text from arXiv and Europe PMC, and an installer that lets the user choose which databases get
installed. That last change is what made M14 necessary — the prompts were still naming tools that
might not be there.

**Contents**

| § | |
|---|---|
| [M14](#-milestone-m14-tell-the-agent-how-to-choose-a-source-not-which-ones-exist) | Source judgement, not a tool list (done) |
| [M15](#-milestone-m15-no-step-is-a-gate-issue-13) | No step is a gate (done) |
| [M16](#-milestone-m16-one-phase-block-and-you-can-see-where-you-are-issue-25) | One phase block (done) |
| [Independent review](#-independent-review-of-m14m16--2026-09-21-antigravity-gemini-38-flash-high) | All three, reviewed cold |

---

## 🏁 Milestone M14: Tell the agent how to choose a source, not which ones exist

**Target.** The retrieval prompts name five search tools by name. Since M13 the user chooses which
databases are installed, so a named tool may simply not be there — and naming it is a promise we can no
longer keep. Worse, the lists carry no judgement: nothing says Google Scholar fails often, that Europe
PMC is noise on a CS paper, or that native web search is not optional. Replace the lists with a short
capability guide and let the agent decide. Decisions: `BRAINSTORM.md` D26.

**Blast radius, measured 2026-09-21:** `grep -rln "search_arxiv|search_semantic_scholar|search_google_scholar"`
over `extensions/_shared/` → **5 files**, all canonical. The 14 adapter directories regenerate from them.

### Deliverables

- [x] **P1 — one capability block, written once.** Replace the hardcoded tool lists in `skills/osp-literature-review-agent/SKILL.md` (the authoritative one), `skills/osp-baseline-scout-agent/SKILL.md`, `skills/osp-answer-generator-agent/SKILL.md`, `defaults/qa_pair_template.md` and `commands/2-osp-literature.md`. Describe each source by **what it is for**, not by tool name, and say plainly that the set is per-project.
- [x] **P2 — the judgement the owner specified**, in this order of priority. Native **web search is always available and never optional** — every round. **arXiv is the strongest single source** for CS, physics and maths, and the only one that also returns full text. **Semantic Scholar is generous** and is the citation graph. *(Corrected on delivery: generous **with a key**. Keyless it shares one pool with every anonymous caller worldwide and throttles unpredictably — `README.md` rate table, measured 2026-09-21. The prompt says so.)* **Google Scholar is the least reliable — it is often blocked, and that is normal**; its failure must never be read as "no papers exist". **Europe PMC only when the paper touches medicine, biology, public health or psychology.** **OpenAlex when retraction status or field-normalised impact matters**, and it may be rate-limited without a key.
- [x] **P3 — promise nothing.** The agent must *discover* what it has rather than assume. No sentence may imply a given tool is present. The phrasing to beat: "use the ones you can see" is already there but sits under a list that reads like a guarantee.
- [x] **P4 — say it briefly.** The owner asked for a high-level overview, not a manual. Target ~10 lines in the Literature skill and one or two sentences everywhere else. A long block is a block the agent skims.
- [x] **P5 — keep the domain rule that already exists.** `search_zenodo` is not a literature tool and must stay out of the rounds; the Baseline Scout keeps it, and the retraction check.
- [x] **P6 — re-sync.** `python3 scripts/sync_adapters.py`, then `--check` and `test_parity.py`.

### Acceptance criteria

1. No canonical file states or implies that a particular search tool is installed.
2. The Literature skill's source guidance is ≤ 12 lines and covers all six capabilities.
3. Every claim in it is one the providers actually honour — cross-check against `mcp-server/README.md`.
4. An agent reading only these prompts would not call Europe PMC on a pure CS paper, and would not record a Google Scholar block as "no papers found".
5. `sync_adapters.py --check` and `test_parity.py` pass.

**Depends on:** M13.

### Report — 2026-09-21

**Shipped in `06f4290`.** The prompts no longer name a search tool they cannot guarantee. Each source is
described by what it is **for**; the agent lists what it actually has and chooses on the paper's topic.

| | Recorded in the plan | Measured on delivery |
|---|---|---|
| canonical files carrying a tool inventory | 5 | **8** |
| lines of source guidance in the Literature skill | target ~10 | **9** (six capabilities) |
| net change across the canonical files | — | **−60 lines** |
| generated adapter files rewritten | — | **110** |

**Why the blast radius was wrong.** It was measured with a grep over three tool names
(`search_arxiv|search_semantic_scholar|search_google_scholar`). That misses
`commands/4-osp-baseline-scout.md` (which wrote `osp-mcp.search_*`), `skills/osp-query-agent/SKILL.md`
(`osp-mcp.*`) and `defaults/round_strategy_template.md` (only Europe PMC and Zenodo by name). Two further
sites had **no tool name to grep for at all** and were found by reading: a resource notice naming four
databases in prose, and the literature skill's orientation block printing
`Tools: arxiv + semantic_scholar + google_scholar`.

**A tool name is now legal only inside a conditional.** *"If you have an arXiv search, it takes
`date_from` / `date_to` / `categories`"* keeps the M11 filter knowledge without re-promising the tool.
An inventory bullet is the defect; a conditional clause is not.

### Review round — 2026-09-21

One subagent, lens: *read these prompts as the agent, on a CS paper, with only arXiv and Semantic Scholar
installed.* **14 findings, all fixed.** Two were HIGH and both sat in the Baseline Scout:

1. **The Scout's output template still hardcoded Zenodo** — `- **Code / data release:** <what Zenodo
   returned ... or "nothing found on Zenodo">`, unconditional, inside a mandatory block. An agent without
   Zenodo had two options: leave a required field blank, or write "nothing found" for a search it never
   ran. **That is the error-vs-empty bug M11 spent a milestone removing, rebuilt inside a template.** The
   retraction check on the very next line already had the escape (`— or "not run"`); the code-release
   check did not. The asymmetry was the whole defect.
2. **The Scout's pointer to the authority was dangling.** The rewrite left *"its `## Sources` section is
   the rule"* with no path, in a persona activated on its own whose `reads:` contract names only three
   `.brain/` artifacts. Neither the field rule nor the error-vs-empty rule was reachable from inside the
   Scout — the old inline list, for all its faults, at least carried them.

Three more worth recording:

- **"Semantic Scholar is generous" contradicted our own rate table**, measured the same day. The
  deliverable P2 predates that table; it is corrected above and in the prompt.
- **The rewrite kept Europe PMC's prohibition and dropped its obligation.** The old bullet said *"add it
  to every round when the paper is in those fields; arXiv barely covers them."* Only the "not on a CS
  paper" half survived, so a biomedical paper got **weaker** guidance than before.
- **I introduced one myself**: `(markitdown is installed with OSP)` — a flat assertion that a tool is
  present, which is the exact defect class this milestone exists to remove, and contradicted twice
  elsewhere in the same prompt set.

Also found outside the measured radius: `docs/ARTIFACT_CONTRACTS.md:55` still carried the old inventory
verbatim. It is referenced by `rules/osp-rules.md`, which ships to every user project — and `docs/` is
never copied there, so that reference is dead at runtime regardless. Fixed the text; the dead pointer is
noted against M15.

**Acceptance:** 1 ✅ (no tool name survives outside a conditional) · 2 ✅ (9 lines, six capabilities) ·
3 ✅ after the Semantic Scholar and OpenAlex corrections · 4 ✅ (reviewer confirmed it would not call a
biomedical database on a CS paper, and is stopped three separate ways from reading a block as empty) ·
5 ✅.

**Late second round — 2026-09-21.** The first M14 reviewer reported after the milestone had shipped,
having read an intermediate tree. Five of its findings were already fixed; **four were not, and were
real.** The sharpest is a loss I had not noticed: the old text said *"In **every round** you MUST
dispatch **all available retrieval tools** simultaneously"*, and my rewrite replaced it with *"Choose by
the paper's topic, not by the list"* — which licenses narrowing to a single source. The only surviving
counterweight, *"Relying on only one source biases the corpus"*, sat 32 lines below the bullets it
qualified. **A breadth floor was traded for judgement and nothing was left holding the floor.** It is
now in the lead paragraph, where it binds.

Also from that round: the open bibliographic index was described only as a retraction lookup, hiding
that it is a general all-field search carrying exactly the year filters round 3 needs — so an agent
would never call it during a round; the Answer Generator had no field rule and no pointer to
`## Sources` while the Baseline Scout had been given one; the error-vs-empty rule lived only in the
Literature Agent although the Scout and the Answer Generator both search; and the retraction template's
`"not run"` conflated *I chose not to* with *I could not*.

**Owed and unrelated, settled the same day:** the live OpenAlex round-trip finally ran — 6 checks green,
including a known retracted DOI flagged `isRetracted=True` and a nonsense DOI raising rather than
returning an empty record. **Semantic Scholar still rate-limits this machine (HTTP 429)**, so its data
path remains unproved; the error path works. See O18.

---

## 🏁 Milestone M15: No step is a gate (issue #13)

**Target.** The protocol forces three literature rounds and blocks a phase whose prerequisites are
unmet. Three rounds is the paper's recommendation, not a law, and it costs real money in tokens. The
owner's position: *"user should be free to skip any step and we should compromise. It is not
user-friendly to block the user."* After this milestone every phase can be skipped, every skip is
recorded, and the final review says what it was missing. Decisions: `BRAINSTORM.md` D27.

**Measured 2026-09-21:** **9** prerequisite or refusal lines across **6** of the 8 commands, plus the
round gate at `commands/2-osp-literature.md:53` which sets `completed` only at `rounds_completed == 3`.
*(Re-measured on delivery: **17**. See the Report.)*

### Deliverables

- [x] **K1 — a `skipped` state.** `.brain-template/session.json` phases currently carry `{status, started_at, completed_at, notes}` with `status` one of pending/in_progress/completed. Add `skipped`, and a `skip_reason`. `scripts/init_brain.sh` must match.
- [x] **K2 — rounds become a recommendation.** After each literature round, report and offer: run another, or move on. Stop setting `completed` only at 3; a phase left at 1 or 2 rounds is `completed` with `rounds_completed` recorded. The suggestion stays visible — **say what skipping costs once, and do not nag**.
- [x] **K3 — prerequisites warn, they do not refuse.** Convert all 9 gate lines. A missing input becomes a stated degradation — *"no baseline scout was run, so missing-baseline findings are absent from this review"* — not a stop.
- [x] **K4 — the artifact records the choice.** Every skip appears in the phase's Provenance and in `session.json`, so a reader of the final review can tell a thin corpus from a thorough one. This is MANIFESTO rule 8 applied to the user's own decisions.
- [x] **K5 — `6-osp-review` degrades honestly.** It cites Q&A pairs directly, so it is the phase most exposed to a skip. It must produce a review that names its own gaps rather than refusing to run.
- [x] **K6 — the orchestrator stops implying a fixed path.** `commands/open-scholar-peer.md` and `skills/osp-orchestrator` present seven steps in order; they should present a recommended order the user may leave.
- [x] **K7 — resolves O2.** The stale "10 pairs each" prerequisite in `6-osp-review` is one of the 9 gates and goes with them.

### Acceptance criteria

1. Every one of the 8 commands runs to completion with all prior phases `skipped`.
2. A literature phase stopped after round 1 is `completed`, with `rounds_completed: 1` and a skip note.
3. `6-osp-review` produces a review with zero Q&A pairs, and says so in its own text.
4. No command refuses to run because of a missing upstream artifact.
5. `session.json` after a skipped phase is valid against the template's shape.
6. O2 is closed; O6 (cascading invalidation) is explicitly **not** solved here and stays open.

**Depends on:** M14, because the skip wording and the source wording touch the same files.

### Report — 2026-09-21

**No phase refuses to run any more.** Every `## Prerequisites` heading is gone; each is now
`## Inputs — none of these is a gate`, stating what is *lost* rather than what is forbidden. Three
literature rounds became a recommendation: the phase completes at whatever count the user stops at.

| | Planned | Measured on delivery |
|---|---|---|
| gate / refusal lines | 9, in 6 of 8 commands | **17** — 14 in `commands/`, **3 in `skills/`** |
| `## Prerequisites` headings left | — | **0** |
| phase status values | 3 (`pending`, `in_progress`, `completed`) | **4** — `skipped` added |
| canonical files changed | — | 20 (208 with the generated adapters) |

**Why the count was wrong.** It was taken by reading the `## Prerequisites` sections. Five more
refusals sat elsewhere in the same commands, and **the master gate was in a skill** —
`osp-orchestrator/SKILL.md:20`, *"If any are missing, refuse to advance"* — in a file the measurement
never opened.

**One stop survives, deliberately.** With no readable paper there is nothing to review. It is now
labelled as the only one, in both places it appears, and each points at the other.

**Not the paper's fault.** ScholarPeer recommends three rounds; OSP was enforcing them. A recommendation
enforced as a law is a bug in the implementation, not a disagreement with the method — which is why
`MANIFESTO.md` rule 2 was amended rather than excepted. See D29.

### Review round — 2026-09-21

One subagent, lens: *adversarial skipper — skip everything you are allowed to, and find where the system
still blocks you or, worse, lets you through while producing something that looks complete.*
**15 findings, 5 HIGH, all fixed.** The milestone was not sound when it was handed over:

1. **The skip chain was broken at hop one.** `"skipped"` was declared in the schema and collected by the
   reviewer skill, but **nothing ever wrote it.** I found this myself while the review ran and fixed it
   in `rules/osp-rules.md`; the reviewer then found the deeper half — the orchestrator is the only thing
   told to record a skip, and **it is not in the loop** when the user simply types the next command.
   Skipping the Baseline Scout left `status: "pending"`, indistinguishable from "not reached yet". Every
   downstream command now records upstream skips itself.
2. **The orchestrator was told both to write and never to write `session.json`** — rule 5 says *"You
   verify, you don't write"*, 43 lines above the instruction to record a skip. Whichever the model
   picked, the skip was lost half the time.
3. **The Q&A template did worse than lose a skip — it asserted the opposite.** A static line,
   *"Context bundle loaded: structured summary, domain narrative, missing baselines, review guidelines"*,
   in a file the Query Agent is told to follow *exactly*. A user who skipped three phases still got an
   artifact claiming all four were read.
4. **The literature skill still set `completed` only when all four files existed**, flatly contradicting
   the command beside it. A one-round stop never completed the phase.
5. **Gap detection was file-presence only.** A one-round corpus and a three-round corpus produce the same
   filename, so a thin review came out reading like a thorough one with no disclosure and no reduction in
   Confidence. The reviewer now reads `session.json`, not the directory listing.
6. **`## What this review did not have` was being silently dropped on every venue-specific review** — the
   enumerated structure omitted it, and venue forms have no slot for it. That is the common case, so the
   entire M15 safety net was off by default. It is now appended whatever the venue format.

Also fixed from the review: a fictional `--force-binary` escape hatch inside the one guard that blocks;
`markitdown.convert` (the real name is `convert_to_markdown`) in that same guard, so the blocking path
could fire on a tool-name typo; *"Must run before any other numbered step"* still on `/0-osp-onboarding`;
an unconditional blocking wait on the venue question; a status snapshot with two glyphs for three
meanings; and the `init_brain.sh` fallback having drifted from the template.

**Closes O1** (the duplicated write step — a real bad edit in three files, not cosmetic), **O2** (the
stale "10 pairs each") and **O3** (`rounds_completed` never declared). **O6** stays open and is explicitly
not solved here.

**Acceptance:** 1 ✅ · 2 ✅ · 3 ✅ · 4 ✅ · 5 ✅ (verified mechanically — every `phases.*` field the prompts
write is declared, and the two initialisers are identical in shape) · 6 ✅.


---

## 🏁 Milestone M16: One phase block, and you can see where you are (issue #25)

**Target.** Every phase ends with a hand-written block of text. The owner's objection: *"it is not very
easily readable... I prefer least amount of text and prefer visuals."* Replace all seven with one
design — **variation C**, chosen from five candidates on 2026-09-21: a progress rail welded into the top
rule, then left-hand labels with an aligned value column. Decisions: `BRAINSTORM.md` D28.

**Measured 2026-09-21:** **7** of the 8 commands carry a closing block; each was written separately and
they have drifted.

### Deliverables

- [x] **R1 — the chosen design, specified once.** The top rule carries the rail and the phase name: `── ●──●──◐──○──○──○──○ ── LITERATURE round 2 of 3 ────`. Below it, left-hand labels — `DONE`, `BLOCKED`, `NEXT` — with values in an aligned column. A closing rule. Nothing else.
- [x] **R2 — the rail states progress, including unfinished work.** `●` done, `◐` in progress or deliberately left short, `○` not started. The half-filled marker is how M15's "you may move on" becomes visible without a sentence.
- [x] **R3 — `BLOCKED` is its own label.** A provider that failed gets its own line, never buried in prose. Reporting a block as "no results" is the failure M11 existed to remove and it must not return through the reporting layer.
- [x] **R4 — `NEXT` offers, it does not command.** Where M15 allows a choice, both routes appear: the recommended one first, the alternative under it.
- [x] **R5 — one definition, seven users.** Put the template in `defaults/` and have each command reference it, the way `round_strategy_template.md` already works. Seven hand-maintained copies is how the current blocks drifted.
- [x] **R6 — it must read unrendered.** Not every one of the 14 tools renders markdown, so the block is plain text with box-drawing characters and must be legible raw. Give an ASCII fallback for the rail, as `install.sh` does for its glyphs.
- [x] **R7 — least text.** The owner's actual requirement. Each block should be shorter than the one it replaces; count the lines before and after.

### Acceptance criteria

1. All 7 closing blocks come from one definition; changing it changes all of them.
2. Each new block is no longer than the block it replaced. Show the line counts.
3. The rail shows the correct position for each of the seven phases, and `◐` appears for a phase left deliberately short.
4. A blocked provider appears under its own `BLOCKED` label.
5. The block is legible as raw text, with no markdown rendering.
6. `sync_adapters.py --check` and `test_parity.py` pass.

**Depends on:** M15 — the rail renders M15's states, so the behaviour has to exist before the display can be honest about it.

### Report — 2026-09-21

**Seven drifted blocks became one definition.** `defaults/phase_block_template.md` holds the rail, the
rules, the widths, the labels and the ASCII fallback. Every command supplies values only.

| | Before | After |
|---|---|---|
| files carrying a rendered rail | 7 hand-written blocks | **1** |
| opening blocks (mandated by `rules/osp-rules.md` all along) | **1 of 7** | 7 of 7 |
| closing-block lines, total | 40 | 42 — **40** typical, with `BLOCKED`/`NOTE` absent |
| rule width | 57–61, inconsistent | **60**, every one |
| anything checking the shape | nothing | `test_parity.py::check_phase_blocks` |

**The first attempt failed this milestone's own main goal.** Each command carried a rendered copy of its
block *as well as* a reference to the template — **11 files with a rail in them**. Changing the design
tomorrow meant 11 hand edits, and they would drift again exactly as the originals had. Measured it,
then restructured. R5 now holds literally: one file.

### Review round — 2026-09-21

One subagent, lens: *raw-text renderer — judge it as bytes on a screen, count display columns not bytes.*
It read the pre-restructure tree and independently reached the same verdict on R5 ("seventeen copies…
the milestone bought a convention, not a mechanism"), which the restructure had already answered.
**Nine further defects, all fixed.** The two worst were in `rules/osp-rules.md` — the file loaded on
**every** invocation, and the one file this milestone had never thought to open:

1. **It carried a second, competing definition of the block.** 58-column rules, no rail,
   `Reads:`/`Writes:`/`Effort:` instead of `READS`/`WRITES`/`COST`, and a line 80 columns wide — over
   the cap the new template sets. An always-on rule beats a command file, so the old format would have
   won.
2. **It mandated the `↳` glyph**, which now appears in zero blocks.

The rest:

- **`/4-osp-baseline-scout` runs 6–10 live searches and had no `BLOCKED` label**, and none of the
  error-vs-empty prose. A provider that 429s would print *"`<N>` missing baselines"* — a partial search
  reported as a finding. **That is the M11 bug, one phase over.** Same gap, weaker, in onboarding's
  venue lookup.
- **The closing blocks said "rail advanced by one" without saying to read `session.json`**, so a skipped
  phase would have rendered as done. Silent degradation, which M15 exists to forbid.
- **The dispatcher printed seven anonymous circles** and kept its key in prose the user never sees.
- The printed decision menu omitted `Weak Reject`, which the reviewer skill can return.
- **Content overhung the rules by up to 9 columns**, so the block was not bounded in raw text at all.
  Every value now fits inside 60. `(recommended)` is dropped where only one route exists — the layout
  already says it.
- The ASCII fallback named no trigger and covered only the rail glyphs, not the `—` and `·` that also
  appear inside blocks.

**The mechanism, which is the part that lasts.** `test_parity.py` gains `check_phase_blocks()`: it fails
if any file but the template renders a rail, if a rule is not exactly 60 display columns, if the rail is
not seven markers, if a line passes 72, or if the value column moves. **Verified by injecting both
faults and watching it fail.** Nothing checked these blocks before — which is how seven of them drifted.

**Acceptance:** 1 ✅ (one definition, enforced) · 2 ✅ (40 → 40 typical; six of seven equal or shorter,
literature +1 for a `BLOCKED` label the old block could not express) · 3 ✅ (all 14 rail positions
verified mechanically) · 4 ✅ · 5 ✅ · 6 ✅.


---

---

## 🔍 Independent review of M14–M16 — 2026-09-21: Antigravity, Gemini 3.8 Flash (High)

One run, all three milestones plus the README, no knowledge of how any of it was built. It needed
`--dangerously-skip-permissions` to run shell commands at all — headless mode auto-denies them and
exits 0 with a 303-byte notice, which is the silent-failure mode the skill warns about. HEAD and the
working tree were recorded before the run and confirmed byte-identical after.

**11 findings, 4 HIGH, all fixed in `a4f2c91`.**

**The one that mattered most, and that two internal review rounds missed.**
`/0-osp-onboarding` **pre-scaffolds** `.brain/raw/05_qa_<slug>.md` for every criterion. So the reviewer
skill's completeness test — *"No such file? write 'No Q&A was run for this criterion'"* — can never
fire. Its other test read `phases.qa.criteria_progress` for entries *"that is not `completed`"*, but an
unrun criterion has **no key there at all**, not a key set to `pending`. Both tests therefore pass on a
Q&A run covering 1 of 5 criteria, and `## What this review did not have` comes out empty. **The precise
failure M15 exists to prevent — a thin review that reads as complete — reached the end of M16 alive,
because both of its detectors were looking at the wrong thing.** Completeness now comes from
`criteria_progress` keyed by `qa_criteria[]`, and the skill says outright that a file's existence
proves nothing.

**The other three HIGH were all self-inflicted by the M15 review round.** Fixing that round's
"nothing writes `skipped`" finding, I gave the orchestrator an exception to write `session.json`. That
contradicts `open-scholar-peer.md`'s own frontmatter (`writes: []`) and the line *"does not modify
`session.json`"*, duplicates the pre-flight every command already runs, and produces a **false**
`skip_reason` — `"user ran /6-osp-review first"` for a phase abandoned three steps earlier. Separately,
the Baseline Scout's output template offered hits / `"nothing found"` / `"not checked"` and **no slot
for a provider failure**, so a 429 became a claim that the authors released no code; and the Answer
Generator had no error-vs-empty contract at all, so a rate-limited verification search could confirm a
novelty claim.

**Where the docs had drifted behind the code:** `AGENTS.md` still called `k=3` fixed and carried a stale
copy of the retired orientation block; `ARCHITECTURE.md` still carried the O3 callout claiming
`rounds_completed` was undeclared, and described the retired `↳` glyph in §10; the README's *"What is
installed on your machine?"* never named `.mcp.json`, `AGENTS.md` or `QWEN.md` at the project root, so
its uninstall line was incomplete — and that section is the one telling users their embargoed paper will
not be committed.

**Checked and found clean:** every rate limit in the README's database table, against provider code and
published documentation.

**The lesson, again.** Two internal rounds found 29 defects between them and still left four HIGH ones,
three of which *the second round's own fixes introduced*. A reviewer that has not read the previous
review is worth more than one that has.

---

> **← Previous:** [`PROGRESS.md`](PROGRESS.md) — M1–M13.
> **Next →** none yet.
