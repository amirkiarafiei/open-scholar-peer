# Artifact Contracts — Open ScholarPeer v2

Every workflow step has a strict I/O contract. The agent **must** load only the artifacts in `reads:` (not the whole `.brain/`) and **must** write the single artifact in `writes:`. This is how context-awareness is enforced without dumping the full transcript into every persona.

## Universal artifact structure

Every `.brain/raw/*.md` file (and `review/final_review.md`) has three required top-level sections:

```markdown
# <Artifact title>

## Method
<What the agent did. Tools used, queries run, filtering criteria, decisions made.
 Report-style — not raw transcripts. 5–15 lines.>

## Output
<The actual content of the artifact — the structured summary, the narrative,
 the Q&A pairs, etc.>

## Provenance
<List of sources cited, papers found, URLs, confidence flags.
 Anything a reviewer would need to verify the work.>
```

**Why three sections.** *Method* gives auditability ("what did the agent actually do?"). *Output* is the consumable artifact for downstream personas. *Provenance* makes the work verifiable by humans.

## Per-step contracts

| Step | Command | Skill | Reads | Writes |
|---|---|---|---|---|
| 0 | `/0-osp-onboarding` | `osp-orchestrator` | `session.json` | `00_review_guidelines.md`, scaffolds empty `05_qa_<slug>.md`, updates `session.json` |
| 1 | `/1-osp-summary` | `osp-summary-agent` | `session.json`, `.brain/input/paper.{pdf,md}` | `01_structured_summary.md` |
| 2 | `/2-osp-literature` | `osp-literature-review-agent` | `session.json`, `01_structured_summary.md` | `02a_literature_round1.md`, `02b_literature_round2.md`, `02c_literature_round3.md`, then consolidated `02_retrieved_literature.md` |
| 3 | `/3-osp-historian` | `osp-historian-agent` | `session.json`, `01_structured_summary.md`, `02_retrieved_literature.md` | `03_domain_narrative.md` |
| 4 | `/4-osp-baseline-scout` | `osp-baseline-scout-agent` | `session.json`, `01_structured_summary.md`, `02_retrieved_literature.md` | `04_missing_baselines.md` |
| 5 | `/5-osp-qa` | `osp-query-agent` (main) + `osp-answer-generator-agent` (subagent) | `session.json`, `01_structured_summary.md`, `03_domain_narrative.md`, `04_missing_baselines.md`, `00_review_guidelines.md` | `05_qa_<criterion_slug>.md` (one per active criterion) |
| 6 | `/6-osp-review` | `osp-reviewer-agent` | `session.json`, `00_review_guidelines.md`, `01_structured_summary.md`, `02_retrieved_literature.md`, `03_domain_narrative.md`, `04_missing_baselines.md`, all `05_qa_*.md` | `review/final_review.md` |
| — | `/open-scholar-peer` | `osp-orchestrator` | `session.json` | (none — dispatcher only) |

## Round-strategy contract for `/2-osp-literature`

The literature step writes **three separate files** to make the 3-round expansion auditable. Each round file has a mandatory `Strategy:` field at the top of its `## Method` section:

| File | Strategy | Description |
|---|---|---|
| `02a_literature_round1.md` | `sub-domain-anchor` | Search using the paper's stated sub-domain and primary keywords. Goal: locate the established prior art. |
| `02b_literature_round2.md` | `method-anchor` | Search using the proposed method's name and technical terms. Goal: find prior work using similar techniques. |
| `02c_literature_round3.md` | `temporal-expansion` | Search filtered to last 12 months + concurrent work + arXiv pre-prints + workshop papers. Goal: catch what static knowledge cutoffs miss. |

Each round must use **all available retrieval tools** (osp-mcp arxiv/semantic_scholar/google_scholar + native Web Search) with **different query formulations** per round. Queries used are listed in each round's `## Provenance`.

After all three rounds, the agent writes `02_retrieved_literature.md` consolidating retained papers (deduplicated), with one entry per paper: title, authors, year, venue, abstract, source(s) it appeared in.

## Q&A contract for `/5-osp-qa`

For every criterion in `session.json.qa_criteria[]`, the step produces `.brain/raw/05_qa_<slug>.md` with **exactly N Q&A pairs**, where N is `session.json.qa_pairs_per_criterion` (user-configurable at `/5-osp-qa` start; default 2). The file template (from `defaults/qa_pair_template.md`) is:

```markdown
# Q&A — <criterion label>

## Method
<which subagent (or self-reflection mode) was used, what context bundle was passed, etc.>

## Output
### Q1
<probing question>
### A1
<answer with verification against domain narrative; flags discrepancy if any>

### Q2
...

### Q10
...

## Provenance
<sources cited per answer>
```

**Subagent vs self-reflection.** On Claude Code / Cursor / Gemini CLI / GitHub Copilot CLI, Q&A runs as: main thread holds Query Agent persona, spawns Answer Generator Agent as subagent for each question, receives back `(answer, citations, discrepancy)`. On Antigravity (no subagents), the agent self-reflects with strict turn markers:

```
=== Query Agent (probing) ===
<question>
=== END Query Agent ===
=== Answer Generator (verifying) ===
<answer with citations and discrepancy flag>
=== END Answer Generator ===
```

The turn markers force the LLM to make the role boundary explicit in its own attention window. This is a known weaker substitute for true context isolation — see `KNOWN_LIMITATIONS.md`.

## Re-run semantics

Re-invoking a step whose phase is `completed` overwrites the artifact and resets the phase status to `in_progress` → `completed`. The agent **must** print a one-line warning to the user before overwriting.

## Update protocol for `session.json`

After writing its artifact, every step updates the matching `phases.<name>` block:
- `status: "completed"`
- `completed_at: <ISO 8601 UTC>`
- `notes: <one-line summary of what was produced>`

And updates `resume_from` to the next pending phase.
