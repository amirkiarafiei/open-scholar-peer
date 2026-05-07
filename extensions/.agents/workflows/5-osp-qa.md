---
description: "OSP Phase 5: Multi-Aspect Q&A — 10 probing pairs per criterion"
reads: [".brain/session.json", ".brain/raw/00_review_guidelines.md", ".brain/raw/01_structured_summary.md", ".brain/raw/03_domain_narrative.md", ".brain/raw/04_missing_baselines.md"]
writes: [".brain/raw/05_qa_<criterion_slug>.md (per criterion)", ".brain/session.json"]
---
> **Tool capability:** This tool does NOT support subagents. Use the self-reflection fallback: strict turn markers (`=== Query Agent === ... === END === === Answer Generator === ...`) within the main context window. This is a documented weaker substitute — see KNOWN_LIMITATIONS.md.


# /5-osp-qa — Multi-Aspect Q&A Engine

For each criterion in `session.json.qa_criteria[]`, generate exactly 10 probing Q&A pairs. The Query Agent runs in the main thread; the Answer Generator runs as a subagent (or self-reflects on Antigravity).

## Activation

Invoke the `osp-query-agent` skill (main thread). The Query Agent will spawn `osp-answer-generator-agent` per question.

## Prerequisites

- `phases.summary.status`, `phases.literature.status`, `phases.historian.status`, `phases.baseline_scout.status` all `"completed"`.
- `qa_criteria[]` is non-empty in `session.json`.
- Empty pre-scaffolded `05_qa_<slug>.md` files exist (from onboarding).

## Mode selection

- **Subagent mode (default):** Claude Code, Cursor, Gemini CLI, GitHub Copilot CLI. The Query Agent delegates each question to the Answer Generator as a subagent with a fresh, minimal context bundle.
- **Self-reflection mode (Antigravity only):** The Query Agent uses strict turn markers (`=== Query Agent === ... === END === === Answer Generator === ...`) within the main context window. Documented as a known weaker substitute — see `KNOWN_LIMITATIONS.md`.

The mode is determined by the host tool. Sync script encodes this per tool.

## Steps

1. Read all input artifacts listed in the frontmatter.
2. Activate the `osp-query-agent` skill.
3. For each criterion in `qa_criteria[]`:
   - Open `.brain/raw/05_qa_<criterion_slug>.md` (pre-scaffolded by onboarding).
   - Generate exactly 10 Q&A pairs:
     - For each, the Query Agent formulates a probing question grounded in the structured summary, narrative, and missing baselines.
     - The Query Agent delegates to the Answer Generator (subagent or self-reflection per mode).
     - The Answer Generator returns `(answer, citations, discrepancy_flag)`.
     - The pair is appended to the file.
   - The file template (`defaults/qa_pair_template.md`) enforces 10 pairs structurally. The agent must not advance to the next criterion until 10 pairs are present.
   - Update `phases.qa.criteria_progress[<slug>] = "completed"`.
4. After all criteria are done:
   - `phases.qa.status = "completed"`
   - `phases.qa.notes = "<N> criteria × 10 pairs each; <M> discrepancies flagged"`
   - `resume_from = "review"`
5. Tell the user: "Q&A complete. Next: `/6-osp-review`."

## Re-run behavior

Re-running overwrites `05_qa_<slug>.md` per criterion. The user may also re-run for a single criterion only — pass the slug as an argument; the rest are skipped.

## Pitfalls

- The Answer Generator must NOT see prior questions when in subagent mode. Each invocation is stateless. Pass only the current question, the criterion definition, and the minimal context bundle.
- The Query Agent must NOT answer its own questions. Always delegate (subagent) or use turn markers (self-reflection).
- The 10-pair count is structural — enforced by the file template, not a hyperparameter.
