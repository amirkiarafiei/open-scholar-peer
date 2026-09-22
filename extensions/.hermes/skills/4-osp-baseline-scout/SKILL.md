---
name: 4-osp-baseline-scout
description: "OSP Phase 4: Identify missing baselines and datasets the authors failed to compare against"
---

# /4-osp-baseline-scout — Adversarial Baseline Audit

Acts as an adversarial auditor identifying baselines and datasets the authors should have compared against but didn't.

## Activation

Invoke the `osp-baseline-scout-agent` skill.

## Inputs — none of these is a gate

- `phases.literature.status == "completed"`. Without a retrieved corpus the Scout searches from scratch,
  which it is built to do anyway — it just costs more calls and may miss what an earlier round already
  found. Run it, and say in Provenance that there was no corpus to start from.
- `historian` is helpful and never required; the Scout works from the structured summary.
- No structured summary either? Read `.brain/input/paper.md` directly for the task and the baselines
  claimed, and record that you did.

**Record any skip before you start.** The orchestrator is not in the loop when the user runs this
command directly, so it falls to you: for every earlier phase still `pending`, set
`phases.<name>.status = "skipped"` and `phases.<name>.skip_reason` to their reason, or
`"user ran /4-osp-baseline-scout first"`. A phase left `pending` reads as "not reached yet", and the final review
cannot tell the difference.


## Resource notice

⚠️ Makes ~6-10 API calls to search for SOTA methods and benchmarks. Expect 1-2
minutes, or longer when it reads a paper in full — one full-text read can take
up to ~75 seconds on its own.

## Opening block (print before step 1)

Render the **opening block** exactly as `.hermes/defaults/phase_block_template.md` defines it — that
file holds the rail, the rules and the widths, and it is the only place they are written down.
This is phase **5 of 7** (`baseline_scout`); read the rail's state from `session.json`. Values:

      DOING    find baselines and datasets the authors left out
      READS    .brain/raw/01_structured_summary.md
               .brain/raw/02_retrieved_literature.md
      WRITES   .brain/raw/04_missing_baselines.md
      COST     ~2 min, ~6-10 searches

## Steps

1. Read `.brain/session.json`, `.brain/raw/01_structured_summary.md`, `.brain/raw/02_retrieved_literature.md`.
2. Activate the `osp-baseline-scout-agent` skill.
3. The skill identifies the paper's task and the baselines actually used (from the structured summary's Evidence section).
4. The skill independently searches for state-of-the-art methods on the same task and benchmarks,
   using whichever retrieval tools this project installed plus native web search — including, where
   they are present, a full-text reader, a retraction check, and a code-and-data repository search.
   Targeted queries include leaderboards, benchmark suites, and recent SOTA claims.
5. The skill produces a table of missing baselines and missing datasets with severity ratings (high/medium/low).
6. Where a reported number decides the finding, the skill opens the source and
   checks it, rather than trusting the abstract.
7. Write `.brain/raw/04_missing_baselines.md`.
8. Update `session.json`:
   - `phases.baseline_scout.status = "completed"`
   - `phases.baseline_scout.completed_at = <now>`
   - `phases.baseline_scout.notes = "<N> missing baselines (<X> high); <M> missing datasets"`
   - `resume_from = "qa"`

## Closing block (print when the phase ends)

Render the **closing block** from `.hermes/defaults/phase_block_template.md`. **Build the rail from
`session.json`** — `●` only where `status == "completed"`, `○` for `pending` *and* `skipped`. A
phase the user skipped must not show as done.
This phase runs live searches, so **one `BLOCKED` line per provider that failed** — an error is not
an empty result, and a source that never ran must never be reported as a baseline that is not
missing. Drop `BLOCKED` and `NOTE` when there is nothing to put on them. Values:

      DONE     <N> missing baselines (<X> high), <M> datasets
               .brain/raw/04_missing_baselines.md
      BLOCKED  <source> — <reason>, nothing was searched
      NEXT     /5-osp-qa   interrogate the paper


## Re-run behavior

Re-running overwrites `04_missing_baselines.md`. Warn before doing so.
