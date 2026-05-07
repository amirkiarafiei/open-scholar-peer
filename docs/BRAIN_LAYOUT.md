# `.brain/` Layout — Open ScholarPeer v2

The `.brain/` directory at the project root is the persistent state store for an OSP review session. It is gitignored — it may contain confidential paper content and is never committed.

## Tree

```
.brain/
├── session.json                       Single source of truth for run state
├── input/                             User drops paper here (any format)
│   ├── paper.pdf                      (or .docx, .tex, etc.)
│   └── paper.md                       (parsed via markitdown MCP, optional)
├── raw/                               All intermediate phase artifacts
│   ├── 00_review_guidelines.md        Venue criteria scraped or pasted at onboarding
│   ├── 01_structured_summary.md       Summary Agent output (claims, method, evidence)
│   ├── 02a_literature_round1.md       Sub-domain anchor search
│   ├── 02b_literature_round2.md       Method anchor search
│   ├── 02c_literature_round3.md       Temporal/expansion search
│   ├── 02_retrieved_literature.md     Consolidated corpus from rounds a/b/c
│   ├── 03_domain_narrative.md         Historian Agent output (chronological narrative)
│   ├── 04_missing_baselines.md        Baseline Scout Agent output (adversarial findings)
│   ├── 05_qa_<criterion_slug>.md      One file per active criterion (10 Q&A pairs each)
│   └── transcripts/                   Optional per-step audit logs
└── review/
    └── final_review.md                Consolidated Reviewer Agent output
```

## Naming rules

- Numeric prefixes (`00`, `01`, `02a`, …) reflect execution order. Files within a phase that branch are suffixed with letters (`02a`, `02b`, `02c`).
- Criterion slugs use kebab-case derived from the venue's review form (e.g. `novelty`, `technical-soundness`, `clarity`, `significance`, `reproducibility`). The slug list is authoritative in `session.json.qa_criteria[].slug`.
- One artifact per file. Never append unrelated content to an existing artifact.

## Lifecycle

1. **`/0-osp-onboarding`** scaffolds `00_review_guidelines.md`, populates `session.json.qa_criteria`, pre-creates empty `05_qa_<slug>.md` files (with the criterion definition as a header), and ensures `input/` contains a paper.
2. Each subsequent step **reads** the artifacts named in its contract (see `ARTIFACT_CONTRACTS.md`), invokes its persona skill, and **writes** exactly one artifact.
3. Each step updates the matching `phases.<name>` block in `session.json` on completion.
4. Re-running a completed step **overwrites** the artifact with a warning (per v2 design).

## What is *not* in `.brain/`

- Tool-specific configs (`.mcp.json`, `.claude/`, `.cursor/`, etc.) — those live at project root.
- The MCP server itself — that lives in `.scholar-peer/mcp/` (also gitignored).
- Any human-edited templates — those live in `extensions/_shared/defaults/` (committed to repo).
