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
last_updated: "2026-09-22"
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

## 🔧 Follow-up — 2026-09-21: four tools were never wired, and one snippet broke configs

Not a milestone. Found while explaining an earlier review finding to the owner, who recognised it
immediately as something no installer should ask of a user.

**What was wrong.** Four of the fourteen tools — Codex CLI, Mistral Vibe, OpenCode, OpenHands — ended
their install by writing a snippet and asking the user to paste it. For two of them the installer
*printed a working command and did not run it*. `KNOWN_LIMITATIONS.md` stated the consequence plainly:
*"nothing is wired up until you paste the snippet; the review will run but every literature search will
fail."*

**And the Vibe snippet was worse than a manual step.** It omitted `transport`, a pydantic discriminator.
Pasting it does not break one entry — it invalidates the user's entire Vibe config. Shipped since
`6942464`.

**Measured against the real binaries** (Vibe 2.25.5, OpenHands CLI 1.16.0, OpenCode 1.17.19, plus Codex
upstream source), every one is automatable. See D31 for what each supports and why the TOML objection
was wrong.

| Tool | Now | Scope |
|---|---|---|
| OpenCode | `.opencode/opencode.json` | project |
| Mistral Vibe | `.vibe/config.toml` | project |
| Codex CLI | `codex mcp add` | global |
| OpenHands CLI | `~/.openhands/mcp.json` | global |

**New:** `scripts/merge_mcp_toml.py`, which parses before writing, rewrites only the blocks OSP owns,
re-reads from disk afterwards and restores the original if the result is invalid — the same contract
`merge_mcp_config.py` honours for JSON. 13 hostile cases covered, including a file it correctly
declines. It needs no TOML parser at all when there is no existing config, which matters: the system
Python here is 3.10, and `tomllib` arrived in 3.11.

`merge_mcp_config.py` gained `--style opencode` for OpenCode's `{type, command: [argv]}` entry shape,
and its stale-entry recogniser now handles an argv list as well as a command string — it had been
working by accident, through `str(list)`.

**Proof it works, not just that files appear.** `test_install.sh` now asserts the real config files
rather than the snippets, and OpenCode was pointed at an installed binary: it loaded the config and
reported `markitdown` **connected**.

**The install box problem dissolved.** An earlier review found the closing box hid the required wiring
step. With nothing left to wire, no per-tool installer passes a manual action any more, so there is
nothing for the box to hide.

**One genuine exception, recorded rather than worked around:** the OpenHands *web UI* keeps MCP settings
in a database behind an authenticated API. No file reaches it, and neither would an agent asked to
configure itself. Those users still get the snippet; the CLI needs nothing.
---

## 🔬 Four-lens review of the whole system — 2026-09-21

Not a milestone. The owner asked for two lenses, each run twice and independently: **does this implement
the paper's protocol**, and **is it clear to a researcher reviewing their first paper**. Two subagents
and two Antigravity runs (Gemini 3.8 Flash, high). Roughly 25 findings; the ones that changed the
product are below. Shipped in `4a4546d`.

### Fidelity — what the paper requires and we did not do

**No cutoff date existed anywhere.** The paper enforces one in four agent prompts (`cutoff` appears 18
times) and markets temporal validity as its advantage over a rival that *"cited papers published months
or years after the review cutoff date"*. We had none, and round 3 searched "the last 12 months" from
**today** — so reviewing a 2025 submission would fault its authors for missing 2026 work. Not a stricter
review, a wrong one. `session.json` now carries `paper.cutoff_date`, onboarding asks for it with a
default, and every round is bounded by it. Verified against the PDF before acting.

**Retrieval was unfalsifiable.** Both literature tables held Title/Authors/Year/Venue and no identifier,
so a paper the agent retrieved and one it remembered were byte-identical on disk — which made MANIFESTO
rules 3 and 4 unverifiable *in principle*. One ID column now, one identifier per row, `no id` when there
is none so the gap is visible.

**Verification could be asserted.** `Result: consistent` was legal with zero searches behind it. The
cross-check line must now name an identifier or say `not verified: <reason>`.

**The Historian shipped one of the paper's three required sections.** Open problems and a stated
significance standard were missing, and four downstream prompts expect them. Both restored, and the Q&A
engine points at them — otherwise significance is judged against the model's taste.

Reviewers also confirmed OSP is **stronger than the paper** in three places: the error-vs-empty
discipline, reading full text rather than abstracts, and the retraction and code-release checks.

### Friction — what a first-time reviewer hits

- **A dead end.** Every recovery path said run `scripts/init_brain.sh`; the `curl | bash` install clones
  to a temp dir and deletes it, so that file is never in the user's project. Three places fixed.
- **Nothing said the review is a draft.** MANIFESTO rule 9 — *"it drafts; the reviewer signs"* — had
  never reached the user, who was handed an accept/reject verdict and a confidence score. Now a `YOURS`
  label in the closing block, defined once in the template, plus a line in the README.
- `uvx markitdown-mcp` is a **server, not a smoke test**: typed in a terminal it waits silently and looks
  hung. Four places now say `--help`.
- **`/5-osp-qa` overwrote every Q&A file without asking** — the most expensive artifact in the system.
- `/2-osp-literature`'s "Re-run behavior" contradicted its own step 1.
- README Option 2 installed into the clone rather than the paper's folder; TROUBLESHOOTING's workflow
  section called two normal outcomes bugs and is rewritten.

### Left alone deliberately

The `N_QA` misreading — see D32. The owner judged the current default fine.


---

## 🏁 Milestone M17: Seven more tools, and three of them do not fit the mould

**Target.** Add Pi, Oh My Pi, Grok Build, Hermes, Cline, Kilo Code and OpenClaw. The owner's
constraint on the research: *"We should never infer but get verified info about layout and what the
agents support."* One subagent per vendor, each required to cite a URL per fact and to write
`NOT DOCUMENTED` rather than fill a gap from another tool's conventions.

**Measured before starting.** Adding a tool touched **13** places: the capability matrix, a *second*
hand-written registry in `test_parity.py`, two `case` arms in `clean_adapter.sh`, a new installer, the
smoke test, four index-aligned arrays in `install.sh`, and the count "14" in README, AGENTS.md, four
`docs/` files and three `kia-context/` files.

### What the research changed

Three of the seven did not fit the existing shape, so the design grew rather than the entries:

| Tool | What broke the mould | Answer |
|---|---|---|
| **Pi** | No MCP client and no web access — both stated non-features. Built-ins are `read`, `bash`, `edit`, `write`, `grep`, `find`, `ls` | `mcp-server/osp_cli.py`, the same 22 tools over argv (D34) |
| **Hermes**, **OpenClaw**, **Cline** | No file-based slash commands — a skill *is* a command | `commands_as_skills` in the matrix (D35) |
| **Oh My Pi**, **Grok Build**, **Kilo Code** | Real subagents, but delegation resolves an agent file and cannot dispatch a skill | `agent_dir`: each persona emitted twice (D36) |

Four findings contradicted what a reasonable person would have assumed, and each would have shipped a
broken install:

- **Kilo Code's `.kilocode/` is legacy**, EOL 2026-07-31. Current is `.kilo/`, and its CLI is a fork of
  OpenCode — so its MCP block is OpenCode's shape and needed no new writer. Worse, **`.kilo/rules/` is
  not auto-loaded** unless listed in an `instructions` key, so the obvious place for a rules file is a
  silent no-op. Rules ship via `AGENTS.md`, which cannot be switched off.
- **Cline has no project-local MCP config at all.** Its global file moved out of VS Code extension
  storage to `~/.cline/data/settings/cline_mcp_settings.json`, shared by the CLI and the extension. The
  published docs name two other paths; the reviewer checked the resolver at HEAD and found **nothing
  reads either**. Deepwiki asserted a third, also wrong.
- **Hermes loads exactly one project context file, first match wins** — `.hermes.md` beats `AGENTS.md`.
  Writing the Hermes-native file would have silently suppressed the user's own `AGENTS.md`.
- **OpenClaw refuses to boot on an unknown config key**, taking the user's chat channels and cron with
  it. So nothing writes `~/.openclaw/openclaw.json`; MCP goes in through `openclaw mcp add`.

**Three tools gate on trust, and a `.gitignore` line can hide OSP entirely.** Pi ignores everything
under `.pi/` until the folder is trusted, and `/trust` does not reload the running session; Hermes
needs `hermes skills trust`; Grok Build loads project rules only for a trusted folder. Grok Build and
Oh My Pi both skip gitignored files during discovery. All of it is stated in the installer's closing
block and in `TROUBLESHOOTING.md`, because a file we write that the tool never reads is the failure
mode this project already paid for once.

### Deliverables

- [x] **T1 — verified research, one subagent per vendor.** Seven briefs, each demanding a source URL
  per fact. Two names were ambiguous and were disambiguated with evidence rather than guessed: "Pi"
  resolves to `earendil-works/pi` (not Inflection's chatbot), and "Oh My Pi" to `can1357/oh-my-pi`, a
  **hard fork** of Pi — *"the on-disk layout is entirely omp's own"* — not the similarly named Pi
  extension bundle `@ayulab/oh-my-pi`.
- [x] **T2 — capability matrix extended**, three new fields whose defaults leave the first 14
  byte-identical: `commands_as_skills`, `agent_dir`, `search_mode`.
- [x] **T3 — seven adapters generated.** 23 canonical files to **467** files across **21** directories.
- [x] **T4 — seven installers**, each wiring MCP by the vendor's own supported route. **20 of 21 tools
  auto-configure MCP; the 21st has none to configure.** No paste-a-snippet step remains anywhere.
- [x] **T5 — `osp_cli.py`**, the no-MCP search surface. Verified live against arXiv in both argv and
  stdin form, and on all five malformed-input paths.
- [x] **T6 — `clean_adapter.sh` rewritten.** It now removes the command-as-skill directories too, and
  **errors on an unknown tool instead of guessing** a rules path.
- [x] **T7 — the two tool registries can no longer drift.** `test_parity.py` keeps its hand-written
  list — deriving it from the code under test would make the path check tautological — but now asserts
  the two agree by name. Verified by deleting a tool from one: exit 1.
- [x] **T8 — `merge_mcp_toml.py` gained Grok Build's table style** and, found while reading it, a fix
  for **unescaped TOML strings**: a Windows path's backslashes were interpolated raw.
- [x] **T9 — first regression suite for the TOML merger**, `test_merge_toml.py`, 39 checks. It reports
  honestly that Group B ran against a stub, because no TOML reader exists on Python 3.10.
- [x] **T10 — documentation.** README table, `KNOWN_LIMITATIONS.md` §1 rewritten and **§9/§10 added**,
  `TROUBLESHOOTING.md` gained the trust-gate and gitignore tables, plus AGENTS.md and CONTRIBUTING.md.

### Report

**Every number re-measured 2026-09-21:** 23 canonical files · 467 generated · 21 adapter directories ·
21 installers · 17 of 21 tools with real subagents (14 delegate, 3 try-and-degrade, 4 self-reflect) ·
20 of 21 wired for MCP · 22 search tools, unchanged.

**Tests:** `sync_adapters.py --check` clean · `test_parity.py` 21 tools · `test_install.sh` 21 of 21 ·
`test_providers_unit.py` 251 checks · `test_merge_toml.py` 39 checks. The last two were each
fault-injected to prove they can fail.

**The smoke test earned its keep.** It caught `osp_cli.py` missing from Pi's install — the stub for
`init_mcp.sh` had not been updated to mirror the real script's output. The fix went to the stub, not
the expectation: a stub that under-reports what a script produces lets a tool pass here and fail for a
user.

**An unplanned finding, now D37.** Three prompt files still named which tools support subagents, and
those lists were wrong the moment Pi and Cline arrived — one would have told a Pi user that subagents
were available. Replaced with the principle and a pointer to the generated banner. **Zero tool
*inventories* now remain in `extensions/_shared/`**; three named mentions survive, each inside a
conditional clause, which is what M14 permits. Tool 22 will require no prompt edit.

The first version of this paragraph said *zero tool names*, which was false — see D37. Both reviewers
caught it independently.

---

## 🔍 Review of M17 — 2026-09-21: one subagent, one Antigravity (Gemini 3.8 Flash, high)

Two reviewers, same scope, run independently. **16 defects, all fixed.** The overlap is the useful
part: both found the exit-code defect without seeing each other's work, which is the third time this
project has seen a fresh reviewer beat an informed one.

### The two that would have reached every user

**The empty-vs-error rule was broken again, through the new surface.** `osp_cli.py` decided its exit
code with `isinstance(result, dict)`. But a *search* tool declares `list[dict]` and returns failure as
`[_err(...)]` — measured: **14 of the 22 tools**, and they are precisely the ones an agent calls most.
So a blocked Google Scholar or a rate-limited Semantic Scholar exited **0**, the code that means *the
search ran and matched nothing*. The prose OSP ships in Pi's `AGENTS.md` tells the agent to branch on
exactly that. M11 spent a milestone separating those two facts; a new calling convention put them back
together in one `isinstance`. Fixed with `_is_error()`, which recognises both shapes.

**`clean_adapter.sh` destroyed `.omp/RULES.md`.** Oh My Pi is the only tool whose rules file lives
*inside* the adapter directory, so the cleanup `rm -f` — harmless everywhere else, where the merge
target is at the project root — deleted the user's own file moments before `merge_agents_md.sh` would
have merged into it. First install, no backup. The arm is now deliberately empty, with the reason
written where the next person will read it.

### The rest

| | Defect | Where it led |
|---|---|---|
| HIGH | `hermes mcp add` is interactive; hung 3m18s, and returns 0 when cancelled | D38 — read the config back, never trust the exit code |
| HIGH | Python 3.10 has no `tomllib`, so a **re-install** of Grok Build or Vibe could not update its own config | the merger hands over to a TOML-capable interpreter |
| MED | `[[ mcp_servers ]]` with inner spaces was not matched, so a re-install appended a **second** `osp`; Vibe takes the first, so a dead path won permanently | regex instead of an exact string compare |
| MED | `merge_mcp_toml.py` stripped **any** block named `osp`, including one the user wrote | ownership check; refuses rather than clobbers |
| MED | `openclaw mcp add` refuses an existing name and has no `--force` | remove-then-add, `--no-probe`, verified by read-back |
| MED | sub-tables (`[mcp_servers.osp.env]`) orphaned when the parent was stripped | swallowed with the parent |
| MED | `clean_adapter.sh` glob `*-osp-*` would delete a user's `team-osp-eval` | narrowed to `[0-9]-osp-*` |
| MED | `$CLINE_DIR` ignored — a green tick on a file Cline never reads | honoured |
| MED | argparse errors printed plain text, breaking the JSON-only contract | every path emits the envelope |
| LOW | `_run` reported as "a database you switched off"; TTY hang on empty stdin; single-quoted TOML names; comments above the next table deleted; CRLF rewritten as LF; a `%d` log format crashing on a wrong-typed argument | each fixed |

### What the round says about our own claims

Three of the sixteen were **false statements in our own prose**, not code. The worst was D37's *"zero
tool names remain"*, which I wrote after grepping six names out of twenty-one and missing both
`Antigravity` and `MANIFEST.md` — the latter still carried two per-tool tables covering 6 of 21, one
cell reading "TBD" since Phase 5. A reviewer also corrected *"no TOML parser exists on this box"*:
`/usr/bin/python3.11` was there the whole time, and the test suite had been reporting stub coverage
for no reason. It now re-execs under a real parser and says `B(real parser)`.

**Rule 7 applies to the command behind a number, not only to the number.** A measured claim is only as
good as the grep, and both of these passed a grep that was too narrow to fail.

### Verification after the round

23 canonical files · 467 generated · 21 adapter directories · 21 installers. `sync --check` clean ·
`test_parity.py` 21 tools · `test_merge_toml.py` **54** checks against a real parser ·
`test_providers_unit.py` 251 · `test_install.sh` **21 of 21**. The TOML suite and the parity registry
check were each fault-injected to prove they can fail.

**Stated, not hidden:** `test_install.sh` cannot exercise a vendor CLI, because the CLI is not
installed in CI. Both HIGH installer defects lived in exactly that gap and were found by a reviewer
running on a machine that had the tool. The limitation is now written at the top of the test.

---

## 🔧 Fix — 2026-09-21: the pointer to the phase-block template resolved nowhere

Found while planning M18, fixed immediately because it was live. **O23, closed by D40.**

`extensions/_shared/` carries 29 references of the form `` `defaults/phase_block_template.md` ``.
Nothing is ever installed at `<project>/defaults/` — every installer copies the adapter into
`.claude/`, `.codex/`, `.agents/`. **Measured: dead on all 21 tools**, not the 13 an outside reviewer
counted, because the path fails from the project root wherever that tool keeps its rules. The file it
points at is the only definition of the phase block, so an agent that followed the pointer found
nothing and had to invent the format.

**Fix.** `_shared/` keeps the short form and stays tool-agnostic; `sync_adapters.py` rewrites it per
tool from a new explicit `install_dir`. Measured after: **0** bare references in generated output,
**262** files carrying a path that resolves, 29 still short in canonical — which is correct.

**The bug inside the fix is the part worth remembering.** The first version derived the prefix from
`tool.root.name`. `--check` clones each tool with a temporary root, so it generated `claude/defaults/…`
against the real run's `.claude/defaults/…`, and **20 of 21 tools drifted**. Only OpenClaw passed,
because it alone had an explicit value. The drift check caught it; I did not. `install_dir` is now
stated on all 21 and raises rather than guessing.

**Guarded.** `test_parity.py` fails on any bare `defaults/…` reference in generated output, verified by
injecting one.

---

## 🏁 Milestone M18: The CLI becomes a tested second-class fallback

**Status: delivered 2026-09-22.** Planned 2026-09-21 and revised twice after two independent reviews —
one architecture lens, one agent-and-fresh-machine lens. Six HIGH findings between them; the shape
survived and almost everything inside it changed. The Report is at the end of this section.

**Target.** `osp_cli.py` exists today for one tool: Pi has no MCP client, so it was built as Pi's only
path (D34). This milestone makes it the documented fallback for **all 21 tools**, on a layering that
does not depend on the thing it replaces. MCP stays default everywhere. The CLI is second class.
It also closes **issue #16**.

### The invariant this milestone exists to protect

M11 spent a milestone establishing one rule: **an empty result and a provider failure must never look
alike.** The CLI surface has now broken it three separate ways, each found by measurement:

| | Route back into the failure | Status |
|---|---|---|
| 1 | The exit code ignored list-wrapped envelopes; 14 of 22 tools return `[_err(...)]` | found and fixed 2026-09-21 |
| 2 | **Output too large.** 50 results is 104,939 B (~26k tokens). The host truncates mid-document; the agent salvages a short corpus and never knows | open — C12 |
| 3 | **Import fails above `main()`.** Measured: `mcp`, `arxiv`, or the wrong interpreter each give **exit 1 with zero bytes of stdout**, while the contract says exit 1 means "read `reason`" | open — C2 |

So M18 states the invariant once and derives tests from it, rather than patching each hole:

> **No execution path may leave the agent unable to tell "the provider failed" from "there are no
> papers".** That includes an empty stdout, a truncated document, and any exit code whose documented
> meaning is not what the process actually did.

A reviewer's description of the worst moment, which C12 and criterion 12 exist to prevent — and which
the first draft's criteria would **not** have caught:

> The agent runs `search_arxiv max_results=50`, the host truncates 105 KB mid-JSON, it salvages twelve
> papers and writes Provenance saying nothing was missing — exit 0, no `reason`, and a review built on
> a quarter of the corpus.

Criterion 7 measures what the CLI *wrote*, not what the agent *received*, so it passes throughout.

### Why the current shape is wrong

`osp_cli.py` imports `osp_mcp.py` for the tool registry, the functions and the error mapping. That
avoided a second registry — the right goal, the wrong seam. Measured 2026-09-21, five runs:

- **71–72% of the import is the `mcp` package** — 273–277 ms of 379–386 ms, for a library the CLI
  never uses.
- **The CLI dies when `mcp` is broken.** Simulated: `ImportError`, no JSON, no envelope.

```
   today                                   M18
   ─────                                   ───
   providers/                              providers/
       ↑                                       ↑
   osp_mcp.py  ── tools, errors, gating,    core.py  ── tools, errors, gating, timeout
       ↑          timeout, AND the             ↑    ↑
   osp_cli.py     FastMCP server          osp_mcp  osp_cli   ── two thin adapters
```

**Measured seam:** `osp_mcp.py` is 952 lines, 22 tool functions, and exactly **four** MCP-specific
lines — 28, 90, 158, 952. The extraction is mechanical. `providers/` is already MCP-free.

### Three failure modes that belong to the CLI alone

All measured. All invisible in MCP mode. All must be fixed here.

**The timeout does not bound the process.** `asyncio.wait_for` cancels the wait; it does not stop the
worker thread, and `asyncio.run()` joins it at shutdown. A 1 s timeout against a 6 s call **returned at
6.0 s**. Correction to the first draft: the realistic worst case is ~78 s (the inner provider budgets),
not "never returns" — but it is unbounded by the setting that claims to bound it.

**Per-process state voids the rate-limit guard and the cache.** `providers/arxiv.py` keeps *four*
pieces of module-level state, not one: `_CLIENT_LOCK`, `_last_raw_request`, `_TEXT_CACHE` and
`_INFLIGHT`. One MCP server is one process, so one set governs everything. Each CLI call is a new
process. Measured: `_last_raw_request` starts at `0.0`, so a fresh process computes a gap of
**1,790,018,205 s** against `_MIN_GAP = 3.0` and **never sleeps**. The three-second gap arXiv's terms
ask for is not degraded in CLI mode — it is absent. And `ARCHITECTURE.md` §9 records the cache as a
*solved* problem: *"an eight-entry cache of parsed arXiv text so paging through a paper does not
re-download it, and one download per paper however many callers ask at once (D25, O17)."* A 300k-char
paper is six windows: one download in MCP mode, **six downloads and six LaTeX parses** in CLI mode.
M18 promotes this path from one tool to twenty-one, so it multiplies the regression by twenty-one.

**Output size is unbounded.** See the invariant table above.

### Deliverables

- [x] **C0 — a golden file before anything moves.** Capture `list --json` and every tool's `schema`
  now; assert byte-identity after C1. Nothing currently tests the 22 wrappers, and C1 is the riskiest
  step in the milestone. Doubles as the C3 fixture.
- [x] **C1 — extract `mcp-server/core.py`.** Move the 22 tool functions, `_err`, `_enabled_sources`,
  the gating and `_run`. The registry is **decorator-built**, so adding tool 23 stays one edit.
  `load_dotenv()` moves to core. `logging.basicConfig()` **does not** — it configures the *root*
  logger, and each front end must own its own logging (see C6). `osp_mcp.py` keeps only the FastMCP
  import, the server object, a registration loop, and `mcp.run()`.
- [x] **C2 — no import may kill the CLI silently.** The CLI must not import `mcp`; and `import core`
  must sit **inside** the guard that already wraps `main()`, so any `ImportError` yields
  `{"error": ..., "reason": "failed"}` on stdout with exit 1. Test by blocking `mcp`, `arxiv`,
  `requests`, `bs4` and `semanticscholar` in turn — not `mcp` alone. A wrong working directory cannot
  be fixed in Python (the shell never starts it, exit 127), so the guide must give an absolute path.
- [x] **C3 — one source of truth, two derivers, pinned.** The tool function's signature is the single
  source. FastMCP reads it through pydantic; the CLI reads it through `inspect.signature`. **Neither
  owns a schema**, and this is deliberately *not* the "two artifacts a human edits" drift this project
  keeps paying for — a human edits one decorated function and both surfaces follow. Saying otherwise
  would invite a future reader to hand-write 22 schemas and create the second source that does not
  exist. Verified: alternatives are closed — `FastMCP.tool()`, `add_tool()` and `Tool.from_function()`
  accept no schema argument, and importing `func_metadata` alone costs ~0.35 s.
  The parity test therefore pins the *derivation rules*: compare argument names, required sets,
  **types and defaults**, and fail loudly on any annotation both readers have not been shown to handle
  alike. Names and required sets already match 22/22 today, so comparing only those would be a test
  that cannot fail.
- [x] **C4 — a hard wall-clock bound.** After the deadline the CLI emits the `timeout` envelope,
  **flushes stdout explicitly** — a hard exit skips Python's buffers, so the envelope would be lost
  exactly when it matters — and exits without waiting for a stuck worker. Reuse `_err`'s existing
  `reason: "timeout"`; do not mint a second spelling. Add `--timeout`; it needs a real path to
  `_run`, which today reads a module global at 23 call sites — use a `ContextVar` defaulting to
  `OSP_CALL_TIMEOUT`.
- [x] **C5 — a cross-process guard for the calls that are not batched.** Scoped down by D39: `batch`
  runs a round in one process, so the in-process lock, the three-second gap and the text cache all
  work there without help. What remains is the agent that issues single calls. The lock file carries
  the last-request timestamp so the gap survives a fresh process; use `fcntl.flock` so the kernel
  releases it if a process dies; keep the existing 15 s `_LOCK_WAIT` / `ArxivBusy` contract rather
  than blocking. The on-disk parsed-text cache is **deferred to O26**, and until it exists
  `KNOWN_LIMITATIONS.md` must say plainly that CLI paging re-downloads per window.
- [x] **C6 — output discipline, correctly diagnosed.** The first draft blamed input schemas for the
  37,463 B `list --json`. Measured: schemas are 7,118 B; **descriptions are 20,698 B**. Dropping
  schemas alone reaches 30,345 B against a 5 KB target. So: `list --json` carries name, first docstring
  line and required only — measured **3,702 B** — and `schema <tool>` carries the full schema and the
  full description. Quiet stderr at the **root** logger, because two of the three lines on a call come
  from the `arxiv` package, not from OSP; add `--verbose`. Document stdin-with-a-heredoc as the
  preferred form, because shell quoting breaks on a title containing an apostrophe. Reconfigure
  stdin and stdout to UTF-8: under an ASCII locale a non-ASCII query fails with "surrogates not
  allowed" and is reported as `bad_request`, which blames the agent for the environment's fault.
- [x] **C7 — the start-up probe, issue #16.** Record `search_interface` inside the existing `mcp` block
  of `session.json` as `interface`. Touches `.brain-template/session.json`, the fallback heredoc in
  `init_brain.sh`, and `ARTIFACT_CONTRACTS.md`. Two rules the first draft missed: **absent is not
  `none`** — `init_brain.sh` skips an existing `.brain/`, so upgraders have no field and must be
  probed, not defaulted; and the value **does** go stale — a server that dies at phase 3 leaves `mcp`
  recorded. On the first failed search of a phase, re-probe once and rewrite the field.
- [x] **C8 — instructions where they are cheap *and* reachable.** Move `search_via_cli.md` to
  `defaults/`. **Caution, measured:** on 13 of 21 tools the rules merge into the project-root
  `AGENTS.md` while defaults land in `.<tool>/defaults/`, so a bare `defaults/…` pointer resolves to
  nothing. The pointer must carry the tool's real path, or the text must be inlined for those tools.
  **The same defect already ships** for `phase_block_template.md` — raised as **O23**.
- [x] **C9 — the CLI is tested independently.** `scripts/test_cli.py`, driven through `bash` as an
  agent drives it. Must cover: every subcommand; `schema` for all 22 tools; malformed JSON; a query
  containing an apostrophe and a double quote; non-ASCII input; a gated-off source; the timeout bound;
  exit codes asserted **together with `reason`**, not alone; JSON on stdout for every invocation;
  stdout and stderr separate; each blocked import; stdin as an open pipe with no data; and — the case
  whose absence made criterion 11 toothless — **a result larger than the cap**, asserting that what
  reaches the caller is valid JSON that declares its own truncation.
- [x] **C10 — prove it on a new machine, reusing what exists.** `install_pi.sh:53` already runs
  `osp_cli.py list` after a real install and reports the result. Extend that check to all 21
  installers rather than inventing a new test. `test_install.sh` stubs `init_mcp.sh`, so the stub must
  also create `core.py`, and it writes no `.env`, so `OSP_SOURCES` is untested there.
- [x] **C11 — documentation.** `ARCHITECTURE.md` §9; `KNOWN_LIMITATIONS.md` §9 rewritten from "Pi only"
  to "the fallback for everyone"; `TROUBLESHOOTING.md` gains the stall and rate-limit symptoms;
  `CONTRIBUTING.md` gains "add a tool to both surfaces"; README one line. Also
  `osp-literature-review-agent/SKILL.md` and `2-osp-literature.md`, which the first draft missed.
- [x] **C12 — bound the size of a result.** The CLI caps its own stdout (`--max-bytes`, default
  ~24 KB). When it truncates it emits a *valid* envelope saying so: returned count, total count, and
  how to page. Measured need: `search_arxiv max_results=50` is 104,939 B and `read_arxiv_paper`
  defaults to 44,708 B, while `max_chars` is documented to 200,000. Consider a lower default
  `max_chars` on the CLI surface.
- [x] **C13 — make the surface choice mechanical, and prove the shell can reach the network.** A reviewer's conclusion, accepted: **an agent
  cannot reliably answer "are the OSP tools in my tool list?"** Hosts differ on a crashed server, a
  tool list can be a start-up snapshot, and partial `OSP_SOURCES` gating makes per-tool reasoning
  actively wrong. The rule becomes three ordered checks: `osp_cli.py` absent → `none`; any OSP tool
  callable → `mcp`; otherwise → `cli`. And state the fact that removes most of the confusion: **one
  `.env` governs both surfaces, so the CLI never has a source MCP lacks — a missing tool is never a
  reason to change surface.** And add a fourth outcome: measured 2026-09-21, three tools block
  outbound network from the shell by default, so `cli` must be confirmed by one cheap reachability
  check before it is recorded. A shell that cannot reach the network is `none`, reported plainly —
  never an empty corpus. Use this probe, verified 2026-09-21 against a reachable host (572 ms), an
  unroutable one (5,091 ms, bounded by its own timeout) and a proxy-style block:

  ```bash
  python3 -c "import urllib.request as u;u.urlopen('https://api.openalex.org/works?per-page=1',timeout=5).read(1);print('NET_OK')" 2>/dev/null || echo NET_BLOCKED
  ```

  Each choice in it prevents a false negative: the timeout is internal because coreutils `timeout` is
  absent on macOS; Python rather than `curl` because a missing `curl` also looks like a block; a real
  HTTPS fetch rather than a TCP connect because a proxy accepts the connect then refuses. Probe a host
  OSP actually calls — Antigravity allowlists per domain, so one approved host proves nothing about
  the others.
- [x] **C14 — something must run the tests.** There is **no CI at all** — no workflows, no Makefile
  (`AGENTS.md:132` says so). After M18 there would be five manual suites, and every "the test fails if
  they diverge" in this plan would be words. Add a CI job running sync-check, parity, providers, TOML
  and CLI suites.
- [x] **C16 — a `batch` call, so a round runs in one process.** D39, resolving O24. Takes a JSON array
  of calls and returns an array of results in the same order. The process boundary is the only real
  difference between CLI mode and MCP mode, and batch removes it for the common path: the arXiv lock,
  the three-second gap, the eight-entry text cache and the in-flight de-duplication all start working
  again with no new machinery, and one start-up is paid instead of eighteen. Design constraints, which
  are what answer the owner's concern about timeouts: a deadline **per item**, never one for the
  batch; one envelope per item so a failure is attributed to its own call; a single failure never
  aborts the rest; a bounded batch size; and C12's output cap applied per item **and** to the whole
  response. The literature skill keeps saying "dispatch them together" — that sentence stays true on
  both surfaces, which is why no prompt changes.

- [x] **C15 — fix the guide's exit-code contract.** `search_via_cli.md` is wrong in both directions,
  measured: a gated-off source exits **2** while the file says 2 means "fix and retry" — a switched-off
  database is not fixable, and three lines later the same file says to record it as a corpus gap; and a
  bad argument *value* exits **1** while the file says malformed is 2. The instruction becomes
  **branch on `reason`, never on the exit code**, with the exit code as a coarse hint only.

### Order

**Planned C0 → C1 → C2 → C3. Executed C0 → C1 → C3 → C2, because the planned order is impossible:**
C2 removes the CLI's `mcp` import, but the CLI read its whole surface — tool list, descriptions *and*
schemas — off FastMCP's pydantic objects, so it could not stop importing `mcp` until C3 gave it a
schema of its own. C6 also moved up to sit beside C2: until it landed, `list --json` still carried
schemas and was still exposed to an unknown annotation. (D41.)

Nothing else is safe until the layering holds, no import can kill the process
silently, and the two derivers are pinned. Then C4, C5, C6, C12 in any order. Then C7, C8, C13, C15 —
prompt and contract work. Then C9, C10, C14, which judge all of it. C11 last.

### Acceptance criteria

Each measured, not reasoned. Revised where review showed a criterion would pass while the property was
false.

| | Criterion |
|---|---|
| 1 | `osp_cli.py list` succeeds with **each** of `mcp`, `arxiv`, `requests`, `bs4`, `semanticscholar` blocked in turn — or, where the dependency is genuinely needed, prints an envelope and exits 1 with non-empty stdout |
| 2 | Start cost: `call` at least **70%** below today's 445 ms; `list` at least **90%** below. Measured tiers: bare python 12 ms, eager core 129 ms, one lazy provider 78–107 ms. **This is a regression guard, not a benefit** — 0.3 s of import sits against 2–6 s of provider latency. The reason to drop `mcp` is that the fallback must not fail with the primary; the speed is a side effect and must not be quoted as the point |
| 3 | Argument **names, required sets, types and defaults** match between the two derivers for all 22 tools, and an unknown annotation fails the test |
| 4 | `--timeout 2` against a cold `read_arxiv_paper` exits within **3.0 s**, measured — not "within the deadline", because `OSP_CALL_TIMEOUT` 90 s exceeds every inner budget and would never fire |
| 5 | Two concurrent CLI arXiv calls never hold the connection at once, **and** consecutive calls are ≥3 s apart, **and** six `read_arxiv_paper` windows on one id cause one download |
| 6 | `list --json` under **5 KB** by default; `schema <tool>` still complete |
| 7a | `call` and `schema` put exactly one JSON document on stdout and nothing else |
| 7b | `call … 2>&1` still parses as JSON |
| 8 | A query containing an apostrophe and a double quote works through the documented form |
| 9 | `session.json` carries the interface after onboarding, including for a project whose `.brain/` predates M18 |
| 10 | A fresh sandbox install with a real venv runs `osp_cli.py list`, on all 21 installers |
| 11 | `test_cli.py` fails when a fault is injected into each of its own guarantees |
| 12 | A 50-result search returns valid JSON under the cap and says it truncated |
| 13 | Exit codes are asserted together with `reason`; no test passes on the code alone |
| 14 | CI runs every suite on push |
| 15 | A `batch` of one round's calls costs **one** process start, and consecutive arXiv calls inside it are ≥3 s apart |
| 16 | One failing item in a batch returns its own envelope and does not stop the others |

### Decisions taken into this milestone

- **MCP stays default on all 21 tools.** The CLI is second class, chosen by C13's mechanical rule.
- **`mcp-server/` keeps its name.** Renaming breaks the user-visible `.open-scholar-peer/mcp/` path in
  every existing install, and `mcp` as a directory name collides with the Python package.
- **`batch` is in, as C16** (D39). It was deferred in the first draft; the review showed the
  sequential-skill alternative does not avoid the cross-process work and costs over a minute of
  overhead per literature phase. Batch removes the process boundary, which is the actual difference
  between the two surfaces.

### Open questions raised by the review

- **O24 — closed by D39.** `batch` (C16). The skill's "dispatch them together" instruction is left
  exactly as it is.
- **O26 — CLI paging through one paper still re-downloads it.** What batch does not cover: six
  `read_arxiv_paper` windows issued one at a time are six processes and six downloads. Deferred from
  C5; must be stated in `KNOWN_LIMITATIONS.md` until it is fixed.
- **O25 — probed and answered.** Three tools block outbound network from the shell by default:
  **Codex CLI** (`network_access = false`, confirmed in code), **Antigravity IDE** on macOS/Linux
  (sandbox on, per-domain allowlist — all five providers would need approving individually), and
  **Kiro Web** at its baseline tier. Everything else allows it, including **Pi, which has no sandbox
  at all** — so the fallback works exactly where it is the only path. All three blocked tools have
  working MCP, so the fallback is missing only where it is not needed; but it also means those three
  have **no fallback at all** if their MCP breaks. Consequences for this milestone: C13's probe must
  include a cheap reachability check so "my shell has no network" is reported rather than silently
  becoming an empty corpus, and C11 must name these three tools.
- **The live-product question it raised is answered: no shipping bug.** MCP subprocesses are **not**
  sandboxed on Codex — `mcp_servers` entries spawn through `LocalStdioServerLauncher` with a plain
  `tokio::process::Command`, while shell calls go through `codex_sandboxing::spawn_process`. The
  sandbox attaches at the exec path, not at MCP spawn. Read from code, **not stated in any vendor
  document**, so it is on the pre-release smoke-test list. For Antigravity IDE the same question is
  `NOT DOCUMENTED`; test rather than assume.
- **O23 — a `defaults/…` pointer is already dead on 13 of 21 tools.** Pre-existing, not introduced
  here: `phase_block_template.md` is referenced by a bare relative path from rules that merge into the
  project-root `AGENTS.md`. C8 must not repeat it, and the existing case needs fixing.
- **Bash approvals.** On hosts that prompt per command, CLI mode costs 8–12 approvals per literature
  round. CLI-mode guidance should tell the agent to group calls into one shell invocation.

### Report — 2026-09-22

Delivered in six commits on `feat/richer-search`, each verified before the next began.

**The layering.** `osp_mcp.py` went from **952 lines to 66** and holds only the four MCP-specific
lines it always had. `core.py` (1,163 lines) holds the 22 tool functions, moved **verbatim**, plus
the error envelope, the gating and the timeout. `osp_cli.py` imports `core` and **never `mcp`**
(measured: 0 occurrences).

**What made the move checkable.** Nothing tested the 22 wrappers, so C0 captured **220 files** first
— `list`, `list --json`, every tool's `schema`, six error paths and the `mcp.list_tools()` dump,
across three `OSP_SOURCES` settings (22 / 17 / 3 tools), each with stdout, stderr *and* exit code.
After C1: byte-identical. After C3+C2: byte-identical. After C6: **3 files changed, and they were
exactly the three `list --json` captures C6 targets.** The `list_tools()` dump matching matters
independently: it proves MCP clients were handed the same surface throughout.

**Two silent regressions the golden caught that a coarser check would not.** `_is_gated_off` compared
`fn.__module__` against the importing module's name, so after the move it would have returned False
for every tool and turned *"this database is switched off — edit OSP_SOURCES"* into *"no tool named
X"*. Both exit 2. And `sync_adapters.py` resolved `defaults/…` pointers *before* appending the CLI
addendum, so any pointer inside it shipped dead — proven by reverting the fix and watching parity
report `[pi] bare defaults/... reference resolves to nothing`.

**Against the acceptance criteria** — every figure measured on 2026-09-22, none carried forward:

| | Criterion | Result |
|---|---|---|
| 1 | each of 5 dependencies blocked in turn | **passes outright** — `list` works with `mcp`, `arxiv`, `requests`, `bs4`, `semanticscholar` *and* `dotenv` blocked; no envelope needed. A `call` against the broken one returns an envelope naming it an install problem |
| 2 | start cost | `call` **104 ms = 76.6% below** (≥70%); `list` **38 ms = 91.5% below** (≥90%). Both required lazy providers *and* moving `asyncio` out of the import path |
| 3 | derivers agree on names, required, types, defaults | **22/22 byte-identical**, descriptions too; 218 checks; an 8th annotation form fails the frozen census |
| 4 | `--timeout 2` on a cold `read_arxiv_paper` | **2,123 ms**, under 3.0 s. An 8 s stuck worker with a 1 s deadline exits at **1,076 ms** (was 6,010 ms) |
| 5 | arXiv guard | consecutive calls in **separate processes 3.01 s apart** (was: never slept, gap computed as ~1.79 billion seconds); two concurrent processes **never overlap**. Six-windows-one-download holds in MCP and in `batch`; **O26** for single calls |
| 6 | `list --json` under 5 KB | **3,703 B**, from 37,463. Schemas were only 23% of it — descriptions were 70% |
| 7 | stdout purity | one JSON document per invocation; `2>&1` parses; stderr empty by default |
| 8 | apostrophe and double quote | passes through argv (properly quoted) and through stdin |
| 9 | `session.json` carries the interface | field added to template and to the installer heredoc; absent ≠ `none` |
| 10 | fresh install runs `osp_cli.py list` | **verified with a real venv**: "Search layer answers — 22 tools, verified by running it", on `install_claude.sh` — a tool that never had a check. One edit in `init_mcp.sh` serves all 21 |
| 11 | the suite fails when faulted | **9 of 9 faults caught**, tree restored byte-identical |
| 12 | a 50-result search | **103,399 → 22,108 B**, valid JSON, declares "11 of 50" |
| 13 | exit codes asserted with `reason` | no test in `test_cli.py` asserts an exit code alone |
| 14 | CI runs every suite | `.github/workflows/ci.yml` calls `scripts/test_all.sh`; full local run **103 s** |
| 15 | a batch is one process start | **1,229 ms against 2,622 ms** for the same three calls separately; the 3 s arXiv gap held *inside* the batch |
| 16 | one failing item keeps the rest | verified with a malformed call beside three good ones |

**Suites:** 259 provider checks (was 251), 218 schema-parity (new), 114 CLI (new), 9 fault injections
(new), 54 TOML, 21-tool parity, 21 installer smoke tests, sync-check. All green. `test_install.sh`
stopped copying `.venv` and `.git` per tool — about 5 GB a run — and went from minutes to **20 s**.

**Defects found by the new tests, in the code those tests were written for:** `batch` turned a falsy
wrong type (`"arguments": []`) into `{}` through `or {}`, so the type check never saw it and the call
failed later as a *missing* argument rather than a bad one; the inner timeout message did not say
nothing had been searched, and the inner timeout is the one that normally fires; and `batch` reported
a wrong argument *name* as a generic `failed` where `call` reported `bad_request` with the schema
command — the same mistake, two different answers.

**And two gaps in the new tests themselves**, found by the fault injector on its first run: the batch
fault flipped `return_exceptions`, which proves nothing because `run_one` catches everything itself;
and the unicode test set `LC_ALL=C`, which on this interpreter still yields a UTF-8 stdout because
PEP 538 coerces the C locale — `PYTHONCOERCECLOCALE=0` and `PYTHONUTF8=0` are needed to get the
environment a user on a bare container actually has. Without them that check passed either way.

**Not in the plan, done anyway:** stopped shipping this machine's `__pycache__` into users' projects,
and fixed a broken table row in `README.md` where the `.open-scholar-peer/mcp/` entry was missing a
cell. The contributor guide's example was wrong before this milestone — it showed `@mcp.tool()` and a
bare `asyncio.to_thread`, contradicting the step two lines below it — and now matches the code.

**Issue #16** was already closed by the owner (*"Done in `feat/richer-search`"*), so C7/C13 fulfil a
promise already made in public rather than closing an open issue. **PR #18**, still open from an
outside contributor, covers the same ground and is superseded on three counted grounds: it names
three specific tools (breaks M14/D26), it **halts** on a missing tool (breaks M15), and it asks the
agent to inspect its own tool list, which C13 concludes cannot be done reliably.

### Out of scope

- Renaming `mcp-server/`.
- The on-disk parsed-text cache — O26.
- **Any change to the records the 22 tools return.** Deliberately narrowed from the first draft's "no
  behaviour change", which was true and misleading: the returned records are identical, but cost,
  caching and rate-limit posture change materially in CLI mode, and that is the whole point of C5 and
  C12.

---

> **← Previous:** [`PROGRESS.md`](PROGRESS.md) — M1–M13.
> **Next →** none yet.
