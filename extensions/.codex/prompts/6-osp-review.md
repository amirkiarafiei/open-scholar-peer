---
description: "OSP Phase 6: Synthesize verified findings into a single venue-formatted review"
reads: [".brain/session.json", ".brain/raw/00_review_guidelines.md", ".brain/raw/01_structured_summary.md", ".brain/raw/02_retrieved_literature.md", ".brain/raw/03_domain_narrative.md", ".brain/raw/04_missing_baselines.md", ".brain/raw/05_qa_*.md"]
writes: [".brain/review/final_review.md", ".brain/session.json"]
---

# /6-osp-review — Final Review Generation

Synthesizes the structured summary, retrieved literature, domain narrative, missing baselines, and verified Q&A pairs into a single consolidated review formatted to the venue's guidelines.

## Activation

Invoke the `osp-reviewer-agent` skill.

## Prerequisites

- All earlier phases completed: `summary`, `literature`, `historian`, `baseline_scout`, `qa`.
- All `05_qa_<slug>.md` files exist with 10 pairs each.

## Steps

1. Read all artifacts listed in the frontmatter.
2. Activate the `osp-reviewer-agent` skill.
3. The skill follows the structure dictated by `00_review_guidelines.md`. If using the generic fallback, the structure is: Summary / Strengths / Weaknesses / Detailed comments per criterion / Questions for authors / Decision recommendation / Confidence.
4. The skill performs **no new retrieval** — it is decoupled from investigation, synthesis only.
5. Write `.brain/review/final_review.md`.
6. Write `.brain/review/final_review.md`.
7. Update `session.json`:
   - `phases.review.status = "completed"`
   - `phases.review.notes = "Final review written; decision: <recommendation>"`
   - `resume_from = "completed"`

## User-facing report (print after completion)

```
── Review complete ───────────────────────────────────────
Decision: <Reject | Major revision | Minor revision | Accept>
↳ .brain/review/final_review.md
To revise any phase, re-invoke its slash command.
──────────────────────────────────────────────────────────
```

## Re-run behavior

Re-running overwrites `final_review.md`. Useful when the user wants to regenerate the review after revising an earlier phase (e.g., re-running `/5-osp-qa` for a single criterion). Warn before overwriting.

## Pitfalls

- Do not introduce new findings. Every claim in the review must trace to a prior artifact.
- Do not invent citations. Every cited paper must be in `02_retrieved_literature.md`.
- Match the venue's tone and structure exactly. ICLR ≠ NeurIPS ≠ workshop.
