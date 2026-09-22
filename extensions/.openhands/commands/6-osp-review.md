---
description: "OSP Phase 6: Synthesize verified findings into a single venue-formatted review"
reads: [".brain/session.json", ".brain/raw/00_review_guidelines.md", ".brain/raw/01_structured_summary.md", ".brain/raw/02_retrieved_literature.md", ".brain/raw/03_domain_narrative.md", ".brain/raw/04_missing_baselines.md", ".brain/raw/05_qa_*.md"]
writes: [".brain/review/final_review.md", ".brain/session.json"]
---

# /6-osp-review — Final Review Generation

Synthesizes the structured summary, retrieved literature, domain narrative, missing baselines, and verified Q&A pairs into a single consolidated review formatted to the venue's guidelines.

## Activation

Invoke the `osp-reviewer-agent` skill.

## Inputs — none of these is a gate

This is the phase most exposed to a skip, and the one that must never refuse: a review the user can read
beats no review at all. Take whatever artifacts exist.

- `summary`, `literature`, `historian`, `baseline_scout`, `qa` — any of them may be absent or `skipped`.
- `05_qa_<slug>.md`, one per criterion, holding however many pairs `qa_pairs_per_criterion` asked for.
  Some criteria may have none.

**Every gap goes in `## What this review did not have`** (see the reviewer skill), and the Confidence
section must reflect it. A thin review that says it is thin is honest work. A thin review that reads like
a complete one is the failure this section exists to prevent.

**Record any skip before you start.** The orchestrator is not in the loop when the user runs this
command directly, so it falls to you: for every earlier phase still `pending`, set
`phases.<name>.status = "skipped"` and `phases.<name>.skip_reason` to their reason, or
`"user ran /6-osp-review first"`. A phase left `pending` reads as "not reached yet", and the final review
cannot tell the difference.


## Opening block (print before step 1)

Render the **opening block** exactly as `.openhands/defaults/phase_block_template.md` defines it — that
file holds the rail, the rules and the widths, and it is the only place they are written down.
This is phase **7 of 7** (`review`); read the rail's state from `session.json`. Values:

      DOING    synthesise everything into one review
      READS    every .brain/raw/ artifact that exists
      WRITES   .brain/review/final_review.md
      COST     ~2 min, no external calls

## Steps

1. Read all artifacts listed in the frontmatter.
2. Activate the `osp-reviewer-agent` skill.
3. The skill follows the structure dictated by `00_review_guidelines.md`. If using the generic fallback, the structure is: Summary / Strengths / Weaknesses / Detailed comments per criterion / Questions for authors / **What this review did not have** / Decision recommendation / Confidence. That gap section is appended whatever the venue format — see the skill.
4. The skill performs **no new retrieval** — it is decoupled from investigation, synthesis only.
5. Write `.brain/review/final_review.md`.
6. Update `session.json`:
   - `phases.review.status = "completed"`
   - `phases.review.completed_at = <now>`
   - `phases.review.notes = "Final review written; decision: <recommendation>"`
   - `resume_from = "completed"`

## Closing block (print when the phase ends)

Render the **closing block** from `.openhands/defaults/phase_block_template.md`. **Build the rail from
`session.json`** — `●` only where `status == "completed"`, `○` for `pending` *and* `skipped`. A
phase the user skipped must not show as done.
Drop `BLOCKED` and `NOTE` when there is nothing to put on them. Values:

      DONE     decision: <from the reviewer's scale>
               .brain/review/final_review.md
      NOTE     <what the review did not have, or omit this line>
      YOURS    a draft. Cut what you disagree with, check the
               citations. Your name is on it, not ours.
      NEXT     re-run any phase, then /6-osp-review again


## Re-run behavior

Re-running overwrites `final_review.md`. Useful when the user wants to regenerate the review after revising an earlier phase (e.g., re-running `/5-osp-qa` for a single criterion). Warn before overwriting.

## Pitfalls

- Do not introduce new findings. Every claim in the review must trace to a prior artifact.
- Do not invent citations. Every cited paper must be in `02_retrieved_literature.md`.
- Match the venue's tone and structure exactly. ICLR ≠ NeurIPS ≠ workshop.
