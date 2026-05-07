---
description: "OSP Phase 3: Compress retrieved literature into a chronological domain narrative"
reads: [".brain/session.json", ".brain/raw/01_structured_summary.md", ".brain/raw/02_retrieved_literature.md"]
writes: [".brain/raw/03_domain_narrative.md", ".brain/session.json"]
---

# /3-osp-historian — Sub-Domain Historian

Compresses the retrieved literature into a chronological narrative that mimics a senior researcher's mental model of the sub-domain.

## Activation

Invoke the `osp-historian-agent` skill.

## Prerequisites

- `phases.literature.status == "completed"` and `02_retrieved_literature.md` exists.

## Steps

1. Read `.brain/session.json`, `.brain/raw/01_structured_summary.md`, `.brain/raw/02_retrieved_literature.md`.
2. Activate the `osp-historian-agent` skill.
3. The skill builds a chronological narrative grouped by inflection points (eras), each characterized by its dominant approach and what triggered the transition out.
4. The skill places the paper under review in the narrative — same era it claims, or a different one — and identifies its closest precedents.
5. Write `.brain/raw/03_domain_narrative.md`.
6. Update `session.json`:
   - `phases.historian.status = "completed"`
   - `phases.historian.notes = "<N> eras identified; paper placed in era <N>"`
   - `resume_from = "baseline_scout"`
7. Tell the user: "Domain narrative written. Next: `/4-osp-baseline-scout`."

## Re-run behavior

Re-running overwrites `03_domain_narrative.md`. Warn before doing so.
