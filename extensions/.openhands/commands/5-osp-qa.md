---
description: "OSP Phase 5: Multi-Aspect Q&A — configurable pairs per criterion (default 2)"
reads: [".brain/session.json", ".brain/raw/00_review_guidelines.md", ".brain/raw/01_structured_summary.md", ".brain/raw/03_domain_narrative.md", ".brain/raw/04_missing_baselines.md"]
writes: [".brain/raw/05_qa_<criterion_slug>.md (per criterion)", ".brain/session.json"]
---
> **Tool capability:** This tool does NOT support subagents. Use the self-reflection fallback: strict turn markers (`=== Query Agent === ... === END === === Answer Generator === ...`) within the main context window. This is a documented weaker substitute — see KNOWN_LIMITATIONS.md.


# /5-osp-qa — Multi-Aspect Q&A Engine

For each criterion in `session.json.qa_criteria[]`, generate N probing Q&A pairs (N = `qa_pairs_per_criterion`, default 2). The Query Agent runs in the main thread; the Answer Generator runs as a subagent on tools that support it.

## Activation

Invoke the `osp-query-agent` skill (main thread). The Query Agent will spawn `osp-answer-generator-agent` per question.

## Prerequisites

- `phases.summary.status`, `phases.literature.status`, `phases.historian.status`, `phases.baseline_scout.status` all `"completed"`.
- `qa_criteria[]` is non-empty in `session.json`.

## Step 0 — Resource check and pair count (run BEFORE any Q&A work)

1. Read `session.json`. Count `qa_criteria[]` items (call it C).
2. Read `qa_pairs_per_criterion` from `session.json` (default 2 if absent).
3. Print the resource estimate:

   ```
   ⚠️  Q&A Engine — resource estimate
      Criteria:  C
      Pairs/criterion: N  (currently set in session.json)
      Total subagent calls: C × N = <total>
      Estimated time: ~<total × 45s> at typical API latency

      Pair count guide:
        2  — quick scan, catches the most obvious issues         (default)
        5  — thorough coverage, good for most reviews
        10 — exhaustive, suitable for high-stakes decisions
   ```

4. Ask the user: "How many Q&A pairs per criterion? Press Enter for [N] or type a number (2–10):"
5. If the user enters a number, update `session.json.qa_pairs_per_criterion` to that value and use it.
   If the user presses Enter, use the existing value.

## Mode selection

- **Subagent mode (default):** Claude Code, Cursor, Gemini CLI, GitHub Copilot CLI, Antigravity. The Query Agent delegates each question to the Answer Generator as a subagent with a fresh, minimal context bundle.
- **Self-reflection mode:** Mistral Vibe and OpenHands use strict turn markers (`=== Query Agent === ... === END === === Answer Generator === ...`) within the main context window.

## Steps

1. Read all input artifacts listed in the frontmatter.
2. Activate the `osp-query-agent` skill.
3. For each criterion in `qa_criteria[]`:
   - Open or initialize `.brain/raw/05_qa_<criterion_slug>.md` from `defaults/qa_pair_template.md`.
   - Generate exactly `qa_pairs_per_criterion` Q&A pairs:
     - For each, the Query Agent formulates a probing question grounded in the structured summary, narrative, and missing baselines.
     - The Query Agent delegates to the Answer Generator (subagent or self-reflection per mode).
     - The Answer Generator returns `(answer, citations, discrepancy_flag)`.
     - The pair is appended to the file.
   - Update `phases.qa.criteria_progress[<slug>] = "completed"`.
4. After all criteria are done:
   - `phases.qa.status = "completed"`
   - `phases.qa.notes = "<C> criteria × <N> pairs each; <M> discrepancies flagged"`
   - `resume_from = "review"`

## User-facing report (print after all criteria complete)

```
── Q&A Engine complete ──────────────────────────────────────
Ran <N> pairs across <C> criteria — <M> discrepancies flagged.
↳ .brain/raw/05_qa_<slug>.md  (one file per criterion)
Next: /6-osp-review
─────────────────────────────────────────────────────────────
```

## Re-run behavior

Re-running overwrites `05_qa_<slug>.md` per criterion. To re-run only one criterion, pass its slug as an argument; the rest are skipped.

## Pitfalls

- The Answer Generator must NOT see prior questions in subagent mode. Each invocation is stateless.
- The Query Agent must NOT answer its own questions.
- Do not generate fewer pairs than `qa_pairs_per_criterion`. The count must match exactly.
