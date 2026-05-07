---
description: "OSP Phase 0: Venue lookup, paper detection, criteria scaffolding"
reads: [".brain/session.json"]
writes: [".brain/raw/00_review_guidelines.md", ".brain/raw/05_qa_<slug>.md (per criterion)", ".brain/session.json"]
---

# /0-osp-onboarding — Stage 0: Onboarding

Prepares the review environment. Must run before any other numbered step.

## Activation

Invoke the `osp-orchestrator` skill (no domain persona needed for this step).

## Steps

### 1. Read session state

- Read `.brain/session.json`. If missing, run `scripts/init_brain.sh` first or initialize a default per the v2 schema.
- If `phases.onboarding.status == "completed"` and `qa_criteria` is non-empty, ask the user whether to re-run (which would overwrite `00_review_guidelines.md` and any pre-scaffolded `05_qa_*.md` files). If they decline, exit.

### 2. Locate the paper and ensure a readable text version

- Check `.brain/input/` for a paper file. Common extensions: `.pdf`, `.md`, `.tex`, `.docx`.
- If empty, ask the user where the paper is. Help them collaboratively — accept any path, then copy the file into `.brain/input/`.
- **Always produce `.brain/input/paper.md`** (the canonical readable form):
  - If the original is `.md`, ensure it's named `paper.md` (rename if necessary).
  - If the original is `.pdf` / `.docx` / `.tex`, attempt conversion with the `markitdown` MCP tool (`markitdown.convert`). Save output to `.brain/input/paper.md`.
  - If `markitdown` is unavailable, **do not silently advance**. Tell the user explicitly that downstream phases require `paper.md` and offer two options: (a) install markitdown (`uvx markitdown-mcp`), or (b) provide a manual markdown conversion. Pause until one is in place.
- Save `paper.path` (original) and `paper.parsed_path` (the canonical `.brain/input/paper.md`) into `session.json`.

### 3. Identify the venue

- Ask the user: "Which venue or journal are you reviewing for? (e.g. ICLR 2026, NeurIPS 2025, Nature Machine Intelligence, arXiv-only)".
- Save `venue.name` and `venue.year` to `session.json`.

### 4. Retrieve venue review guidelines (fallback chain)

Try in order, stop at the first that succeeds:

1. **Web search** for the venue's official review form / reviewer instructions / scoring rubric. Use queries like `"<venue> <year> reviewer guidelines"`, `"<venue> review form"`, `"<venue> reviewer checklist"`.
2. **Ask the user** to paste guidelines if web search came up empty or returned irrelevant content.
3. **Generic fallback:** copy `extensions/_shared/defaults/generic_review_guidelines.md` (or its synced equivalent in your tool's `defaults/` directory) into `.brain/raw/00_review_guidelines.md`.

Set `venue.criteria_source` in `session.json` to `"web"`, `"user"`, or `"generic"` accordingly. Set `venue.source_url` if web-sourced.

### 5. Write `00_review_guidelines.md`

Write the retrieved/provided/generic guidelines to `.brain/raw/00_review_guidelines.md` using the universal artifact structure (Method / Output / Provenance):

- **Method:** how the guidelines were sourced (web search query, user paste, generic fallback).
- **Output:** the actual guidelines content. Include the venue's scoring rubric, the required review sections, and the criteria the venue uses.
- **Provenance:** source URL or "user-provided" or "generic fallback".

### 6. Extract criteria and populate `qa_criteria[]`

Parse the guidelines to extract the evaluation criteria. Each criterion becomes an entry in `session.json.qa_criteria`:

```json
{
  "slug": "novelty",
  "label": "Novelty & Originality",
  "definition": "<one-paragraph definition from the guidelines>"
}
```

If the venue uses 7 criteria, you produce 7 entries. If 3, you produce 3. The number is venue-driven, not fixed.

### 7. Pre-scaffold empty Q&A files

For each criterion in `qa_criteria[]`, create `.brain/raw/05_qa_<slug>.md` from the template at `defaults/qa_pair_template.md` (or the synced equivalent). Pre-fill:
- The criterion label and definition in the header
- Empty `### Q1` … `### Q10` placeholders

This is a **structural nudge**: when the Query Agent runs in Phase 5, the empty file is already on disk, signaling that 10 pairs are required.

### 8. Update `session.json`

- `phases.onboarding.status = "completed"`
- `phases.onboarding.completed_at = <now ISO 8601 UTC>`
- `phases.onboarding.notes = "Venue: <name>; criteria: <N>; paper: <path>; guidelines source: <web|user|generic>"`
- `resume_from = "summary"`

### 9. Tell the user the next step

"Onboarding complete. Run `/1-osp-summary` to begin Internal Compression."
