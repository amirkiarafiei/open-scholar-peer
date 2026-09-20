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

## User-facing report (print after completion)

```
── Domain Narrative complete ─────────────────────────────
Mapped <N> historical eras; placed paper in era <E>.
Closest precedents: <2-3 bullet items>
↳ .brain/raw/03_domain_narrative.md
Next: /4-osp-baseline-scout
──────────────────────────────────────────────────────────
```

## Re-run behavior

Re-running overwrites `03_domain_narrative.md`. Warn before doing so.
