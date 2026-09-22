# Artifact Contracts — Open ScholarPeer v2

Every workflow step has a strict I/O contract. The agent **must** load only the artifacts in `reads:` (not the whole `.brain/`) and **must** write the single artifact in `writes:`. This is how context-awareness is enforced without dumping the full transcript into every persona.

**A `reads:` entry is an input, not a gate.** The user may skip any phase, so any listed artifact may be
absent. A missing input is a **degradation, never a refusal**: run the step on what is there, name the gap
in the artifact's `## Provenance`, and carry it through to the final review. The one thing no step can work
around is a missing readable paper — with no `paper.md` there is nothing to review at all.

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

Each round dispatches the retrieval tools this project actually installed — the set is chosen at install time and differs per project — with **different query formulations** per round. Which sources suit which paper is decided in the `## Sources` section of `osp-literature-review-agent`, the single authority. Queries used are listed in each round's `## Provenance`.

Three rounds are recommended, not required. After the last round the user chooses to run, the agent writes `02_retrieved_literature.md` consolidating retained papers (deduplicated), with one entry per paper: title, authors, year, venue, abstract, source(s) it appeared in, and records how many rounds were actually run.

## Q&A contract for `/5-osp-qa`

For every criterion in `session.json.qa_criteria[]`, the step produces `.brain/raw/05_qa_<slug>.md` with **exactly N Q&A pairs**, where N is `session.json.qa_pairs_per_criterion` (user-configurable at `/5-osp-qa` start; default 2). The file template (from `defaults/qa_pair_template.md`) is:

```markdown
# Q&A — <criterion label>

## Method
<`Mode: subagent` or `Mode: self-reflection` — which was actually used, what context bundle was passed, etc.>

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

**Subagent vs self-reflection.** Where subagents are available, Q&A runs as: main thread holds Query Agent persona, spawns Answer Generator Agent as subagent for each question, receives back `(answer, citations, discrepancy)`. Where they are not — the banner at the top of `/5-osp-qa` says which applies on your tool — the agent self-reflects with strict turn markers:

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

## What `session.json` holds

The file every phase reads first. Three parts worth naming, because nothing
else documents them:

| Key | What it is |
|---|---|
| `phases.<name>.status` | one of `pending`, `in_progress`, `completed`, `skipped`. A skip is a user's choice and is recorded, never inferred |
| `phases.<name>.skip_reason` | why, in the user's terms, so the final review can say what it did not have |
| `phases.literature.rounds_completed` | how many retrieval rounds actually ran. Three is a recommendation, not a requirement |
| `qa_criteria[]` | one entry per venue criterion, with `slug`, `label` and `definition` |
| `mcp.semantic_scholar_api_key_present` | whether a key was found, so a thin Semantic Scholar result can be explained |
| `mcp.interface` | how this project reaches the search tools: `mcp`, `cli` or `none` |

### `mcp.interface`

Written by `/0-osp-onboarding` and followed by every later phase, so the
decision is made once rather than guessed per phase.

- `mcp` — the search tools answer as tool calls. The normal case.
- `cli` — no MCP client, or MCP is not answering, and the shell can reach the
  network. `osp_cli.py` is used instead. Second class but complete.
- `none` — the search layer cannot be reached at all: it is not installed, or
  this host blocks outbound network from the shell. **The protocol still runs**,
  on the agent's own knowledge and whatever web search the host provides, and
  every artifact must say the corpus had no database behind it.

Two rules that are easy to get wrong:

**Missing is not `none`.** A project set up before this field existed has no
value, and `init_brain.sh` never touches an existing `.brain/`. An absent field
means "nobody has checked yet" — decide it and write it, do not assume the
worst.

**It goes stale.** A server that dies mid-session leaves `mcp` recorded. If a
search fails while the field says `mcp`, re-probe once and rewrite it before
reporting a gap. A server nobody can reach looks exactly like a database with
nothing in it, and that confusion is the one thing this layer exists to prevent.

## Update protocol for `session.json`

After writing its artifact, every step updates the matching `phases.<name>` block:
- `status: "completed"`
- `completed_at: <ISO 8601 UTC>`
- `notes: <one-line summary of what was produced>`

And updates `resume_from` to the next pending phase.
