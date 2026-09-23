---
description: "OSP Phase 3: Compress retrieved literature into a chronological domain narrative"
reads: [".brain/session.json", ".brain/raw/01_structured_summary.md", ".brain/raw/02_retrieved_literature.md"]
writes: [".brain/raw/03_domain_narrative.md", ".brain/session.json"]
---

# /3-osp-historian — Sub-Domain Historian

Compresses the retrieved literature into a chronological narrative that mimics a senior researcher's mental model of the sub-domain.

## Activation

Invoke the `osp-historian-agent` skill.

## Inputs — none of these is a gate

- `phases.literature.status == "completed"` and `02_retrieved_literature.md` exists. Without it you have
  no retrieved corpus, so the narrative rests on your own knowledge alone — which has a cutoff and will
  miss recent work. Build it anyway, mark the phase's own limits in Provenance, and say plainly in the
  narrative that no literature was retrieved. Recommend `/2-osp-literature` once.

**Record any skip before you start.** The orchestrator is not in the loop when the user runs this
command directly, so it falls to you: for every earlier phase still `pending`, set
`phases.<name>.status = "skipped"` and `phases.<name>.skip_reason` to their reason, or
`"user ran /3-osp-historian first"`. A phase left `pending` reads as "not reached yet", and the final review
cannot tell the difference.


## Opening block (print before step 1)

Render the **opening block** exactly as `.pi/defaults/phase_block_template.md` defines it — that
file holds the rail, the rules and the widths, and it is the only place they are written down.
This is phase **4 of 7** (`historian`); read the rail's state from `session.json`. Values:

      DOING    build the sub-field's chronological narrative
      READS    .brain/raw/01_structured_summary.md
               .brain/raw/02_retrieved_literature.md
      WRITES   .brain/raw/03_domain_narrative.md
      COST     ~2 min, no external calls

## Steps

1. Read `.brain/session.json`, `.brain/raw/01_structured_summary.md`, `.brain/raw/02_retrieved_literature.md`.
2. Activate the `osp-historian-agent` skill.
3. The skill builds a chronological narrative grouped by inflection points (eras), each characterized by its dominant approach and what triggered the transition out.
4. The skill places the paper under review in the narrative — same era it claims, or a different one — and identifies its closest precedents.
5. Write `.brain/raw/03_domain_narrative.md`.
6. Update `session.json`:
   - `phases.historian.status = "completed"`
   - `phases.historian.completed_at = <now>`
   - `phases.historian.notes = "<N> eras identified; paper placed in era <N>"`
   - `resume_from = "baseline_scout"`

## Closing block (print when the phase ends)

Render the **closing block** from `.pi/defaults/phase_block_template.md`. **Build the rail from
`session.json`** — `●` only where `status == "completed"`, `○` for `pending` *and* `skipped`. A
phase the user skipped must not show as done.
Drop `BLOCKED` and `NOTE` when there is nothing to put on them. Values:

      DONE     <N> eras mapped, paper placed in era <E>
               closest precedents: <2-3, comma separated>
               .brain/raw/03_domain_narrative.md
      NEXT     /4-osp-baseline-scout   audit the baselines


## Re-run behavior

Re-running overwrites `03_domain_narrative.md`. Warn before doing so.
