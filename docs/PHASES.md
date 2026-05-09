# Open ScholarPeer (OSP) — v2 Implementation Phases

This plan supersedes the v1 phases (which are obsolete — v1 collapsed 7 paper-specified agent roles into 3 commands, losing scientific fidelity). v2 maps 1:1 to the paper's agent topology, adds dynamic venue scaffolding, and uses a self-contained MCP install.

Use this file as an execution checklist. Mark items `[ ]` → `[x]` in order. Phases are sequential; each depends on the previous.

---

## Naming Conventions (locked)

- **Project shortname:** `osp` (Open ScholarPeer). Note: "ScholarPeer" alone refers to the upstream paper/Google authors; we use "Open ScholarPeer" / `osp` for our implementation.
- **Slash commands:** `/N-osp-{step}` for numbered workflow steps (e.g. `/0-osp-onboarding`, `/1-osp-summary`). Plus one stateless dispatcher: `/open-scholar-peer` (reads `session.json`, tells user which numbered command to run next).
- **Skills:** `osp-{persona}` — no number prefix since order is irrelevant for skills (e.g. `osp-summary-agent`, `osp-query-agent`, `osp-orchestrator`).
- **Brain root:** `.brain/` at project root.
- **MCP install root:** `.open-scholar-peer/mcp/` at project root (self-contained venv + server).

---

## Execution Tracker

- [x] Phase 0 — Cleanup of v1 artifacts
- [x] Phase 1 — Foundation (brain schema, shared layout, artifact contracts)
- [x] Phase 2 — Canonical `_shared/` content (skills + commands + defaults)
- [x] Phase 3 — Sync script (`_shared/` → per-tool adapters)
- [x] Phase 4 — Consolidated MCP server (arxiv + semantic_scholar + google_scholar)
- [x] Phase 5 — Installer scripts (`.open-scholar-peer/mcp/` setup + per-tool MCP wiring)
- [x] Phase 6 — Cross-tool validation, docs, release readiness *(E2E live-tool test deferred to manual run)*

---

## Phase 0 — Cleanup

### Goal (Phase 0)

Wipe v1 implementation cleanly so v2 starts from a known empty state.

### Deliverables (Phase 0)

- [ ] Delete `extensions/_shared/commands/{1-knowledge-acquisition,2-qa-engine,3-review-generation}.md`
- [ ] Delete `extensions/_shared/skills/scholar-peer/SKILL.md`
- [ ] Delete `extensions/_shared/rules/` (if any v1 rules)
- [ ] Delete all per-tool adapter content under `extensions/.{claude,cursor,gemini,agent,github}/` — regenerated in Phase 3
- [ ] Delete `mcp-server/scholar_mcp.py` (rewritten in Phase 4)
- [ ] Delete or archive any v1 helper scripts in repo root (`update_workflow.py`, `update_json_phases.py`, `rename_phases.py`)

### Exit Criteria (Phase 0)

- [ ] `extensions/` contains only empty directory shells under `_shared/` and per-tool roots
- [ ] `mcp-server/` is empty (or contains only `.gitkeep`)
- [ ] Repo builds cleanly with no broken references

---

## Phase 1 — Foundation

### Goal (Phase 1)

Lock down the shared schemas and contracts that all later phases depend on.

### Deliverables (Phase 1)

- [ ] **`session.json` schema v2** — extend `.brain-template/session.json`:
  - `venue: { name, year, source_url, criteria_source: "web"|"user"|"generic" }`
  - `paper: { title, path, parsed_path, type }`
  - `qa_criteria: [{ slug, label, definition }]` (populated at onboarding)
  - `phases: { onboarding, summary, literature, historian, baseline_scout, qa, review }` each with `{ status, started_at, completed_at, notes }`
  - `mcp: { semantic_scholar_api_key_present: bool }`
  - `resume_from: <phase_slug>`
- [ ] **`.brain/` directory contract** documented in `docs/BRAIN_LAYOUT.md`:
  ```
  .brain/
  ├── session.json
  ├── input/                          (paper goes here; agent helps user place it)
  ├── raw/
  │   ├── 00_review_guidelines.md
  │   ├── 01_structured_summary.md
  │   ├── 02a_literature_round1.md
  │   ├── 02b_literature_round2.md
  │   ├── 02c_literature_round3.md
  │   ├── 02_retrieved_literature.md  (consolidated from rounds)
  │   ├── 03_domain_narrative.md
  │   ├── 04_missing_baselines.md
  │   ├── 05_qa_<criterion_slug>.md   (one per active criterion)
  │   └── transcripts/                (optional — per-step audit logs)
  └── review/
      └── final_review.md
  ```
- [ ] **Artifact contract** for each step documented in `docs/ARTIFACT_CONTRACTS.md`:
  - Each artifact has three required sections: `## Method` (what was done, queries run, tools used), `## Output` (the actual content), `## Provenance` (sources, citations).
  - Each step lists its `reads:` (prior artifacts it loads as context) and `writes:` (artifact it produces).
- [ ] **Generic guidelines fallback** — `extensions/_shared/defaults/generic_review_guidelines.md` with criteria: novelty, technical_soundness, clarity, significance, reproducibility.
- [ ] **`_shared/` directory layout manifest** — `extensions/_shared/MANIFEST.md` listing every canonical file the sync script must produce per tool.

### Tests (Phase 1)

- [ ] `session.json` v2 validates against a JSON schema check
- [ ] Brain layout doc references match deliverable file list

### Exit Criteria (Phase 1)

- [ ] All schemas, contracts, and layouts are written and reviewed
- [ ] No code yet — only specs and templates

---

## Phase 2 — Canonical `_shared/` Content

### Goal (Phase 2)

Author all skills and commands once, in `_shared/`, as the single source of truth.

### Deliverables (Phase 2)

#### Skills (8 total) — `extensions/_shared/skills/{name}/SKILL.md`

- [ ] `osp-orchestrator` — top-level skill, triggered by review-related phrases. Owns the dispatcher behavior.
- [ ] `osp-summary-agent` — Internal Compression. Extracts claims / method / evidence into structured summary Ŝ.
- [ ] `osp-literature-review-agent` — External Context. Knows the 3-round strategy (sub-domain anchor → method anchor → temporal/expansion). Uses ALL tools per round (osp-mcp + native web search). Forces one file per round.
- [ ] `osp-historian-agent` — Compresses retrieved literature into chronological domain narrative.
- [ ] `osp-baseline-scout-agent` — Adversarial auditor. Identifies missing baselines & datasets.
- [ ] `osp-query-agent` — Probing question generator. Loops through criteria; demands N Q&A pairs per criterion where N = `session.json.qa_pairs_per_criterion` (user-configurable at `/5-osp-qa` start, default 2; enforced via file template).
- [ ] `osp-answer-generator-agent` — Verifier/responder. Subagent-only by default; falls back to self-reflection mode if platform lacks subagents (Antigravity). Self-reflection mode uses strict turn-marker format: `=== Query Agent === ... === END === === Answer Generator === ...`.
- [ ] `osp-reviewer-agent` — Synthesizes final consolidated review using venue guidelines + structured summary + Q&A pairs.

#### Commands (8 total) — `extensions/_shared/commands/{name}.md`

- [ ] `open-scholar-peer` — **stateless dispatcher**. Reads `session.json`, prints current state, tells user which `/N-osp-*` command to run next. Always-available regardless of phase.
- [ ] `0-osp-onboarding` — Stage 0. Asks venue → web-searches official guidelines → falls back (ask user → generic). Locates paper (asks user, helps find it). Optionally invokes markitdown MCP to convert PDF → MD. Scaffolds criteria-specific empty `05_qa_<slug>.md` files. Saves everything to `session.json`.
- [ ] `1-osp-summary` — Invokes `osp-summary-agent`. Reads paper from `.brain/input/`. Writes `01_structured_summary.md`.
- [ ] `2-osp-literature` — Invokes `osp-literature-review-agent`. Runs 3 strategy-distinct rounds. Writes `02a/02b/02c_literature_round*.md` then consolidates to `02_retrieved_literature.md`.
- [ ] `3-osp-historian` — Invokes `osp-historian-agent`. Reads `02_retrieved_literature.md`. Writes `03_domain_narrative.md`.
- [ ] `4-osp-baseline-scout` — Invokes `osp-baseline-scout-agent`. Reads summary + literature. Writes `04_missing_baselines.md`.
- [ ] `5-osp-qa` — Invokes `osp-query-agent` (main thread). Loops over `qa_criteria[]`. For each: spawns `osp-answer-generator-agent` as subagent (or self-reflects on Antigravity / Vibe / OpenHands). Forces N Q&A pairs via `### Q1...### QN` template, where N = `session.json.qa_pairs_per_criterion`. Writes `05_qa_<slug>.md` per criterion.
- [ ] `6-osp-review` — Invokes `osp-reviewer-agent`. Reads everything. Writes consolidated `review/final_review.md`.

#### Rules (always-on)

- [ ] `extensions/_shared/rules/osp-rules.md` — Brain protocol summary: read session.json first, load relevant prior artifacts, update session.json after each phase, use `osp-` skill names, prefer subagent over self-reflection where supported.

#### Defaults

- [ ] `extensions/_shared/defaults/generic_review_guidelines.md`
- [ ] `extensions/_shared/defaults/qa_pair_template.md` (dynamic `### Q1/A1 ... ### QN/AN` skeleton, where N is rendered from `session.json.qa_pairs_per_criterion`)
- [ ] `extensions/_shared/defaults/round_strategy_template.md` (one per round)

### Tests (Phase 2)

- [ ] Every skill has frontmatter (name, description) and a clear trigger
- [ ] Every command declares its `reads:` and `writes:` in a header block
- [ ] All 8 numbered commands have a unique number prefix (no collisions)
- [ ] No skill or command references a tool/path that doesn't exist
- [ ] Rules file is < 50 lines (always-on context cost matters)

### Exit Criteria (Phase 2)

- [ ] All canonical content authored and self-consistent
- [ ] Cross-references between commands and skills are valid

---

## Phase 3 — Sync Script

### Goal (Phase 3)

Build the Python sync script that generates per-tool adapters from `_shared/`. Manual trigger; small project.

### Deliverables (Phase 3)

- [ ] `scripts/sync_adapters.py` with per-tool transformers:
  - **Claude Code** → `extensions/.claude/{commands,skills,rules}/` — markdown with YAML frontmatter; skills as `skills/<name>/SKILL.md`.
  - **Cursor** → `extensions/.cursor/{commands,skills,rules}/` — `.mdc` for rules, `.md` for commands/skills.
  - **Gemini CLI** → `extensions/.gemini/{commands,skills,agents}/` — `.toml` for commands (transformed from MD frontmatter), `.md` for skills, subagent files.
  - **Antigravity** → `extensions/.agent/{workflows,skills,rules}/` — markdown; also dual-write to `extensions/.agents/` for backward compat. **Tag Q&A workflow as `mode: self-reflection`** since Antigravity lacks subagents.
  - **GitHub Copilot CLI** → `extensions/.github/` + `AGENTS.md` (+ Copilot CLI's prompts/skills layout per https://docs.github.com/en/copilot/how-tos/copilot-cli/cli-best-practices).
- [ ] Sync script runs idempotently (re-running doesn't change unrelated files)
- [ ] Sync script wipes target tool dirs before regenerating (no stale files)
- [ ] Per-tool subagent capability matrix encoded in script (Claude/Cursor/Gemini/Copilot CLI = subagent; Antigravity = self-reflection)

### Tests (Phase 3)

- [ ] Run script → verify all 13 tool directories populated
- [ ] Parity test: for every command in `_shared/commands/`, all 13 tools have an equivalent file
- [ ] Re-run script → no diff in output (idempotent)
- [ ] Antigravity Q&A file contains self-reflection turn-marker template; other tools' Q&A files contain subagent-delegation instructions

### Exit Criteria (Phase 3)

- [ ] One source edit + one sync command regenerates all 13 tool adapters correctly

---

## Phase 4 — Consolidated MCP Server

### Goal (Phase 4)

Build one MCP server (`osp_mcp`) exposing arxiv + semantic_scholar + google_scholar tools with proper docstrings and error handling.

### Deliverables (Phase 4)

- [ ] `mcp-server/osp_mcp.py` — single FastMCP server combining:
  - **arXiv tools** (rewrite from current thin version): `search_arxiv`, `get_arxiv_paper_details` — full docstrings, typed returns.
  - **Semantic Scholar tools** (port from `~/.gemini/antigravity/mcp-servers/semantic-scholar-server/`): `search_semantic_scholar`, `get_paper_details`, `get_author_details`, `get_citations_and_references`. Reads `SEMANTIC_SCHOLAR_API_KEY` env var, falls back to anonymous limits.
  - **Google Scholar tools** (port from `~/.gemini/antigravity/mcp-servers/google-scholar-server/`): `search_google_scholar`, `advanced_google_scholar_search`, `get_author_info`.
- [ ] `mcp-server/requirements.txt` — fastmcp, semanticscholar, scholarly, etc.
- [ ] `mcp-server/README.md` — how to run standalone, env vars, API key setup, extension points (community can add more providers).
- [ ] All tools have rich docstrings (3+ sentences, parameter descriptions, return shape) so agents understand when to call them.
- [ ] Consistent error envelope across all tools (`{"error": "..."}`).

### Tests (Phase 4)

- [ ] Server starts cleanly with `python osp_mcp.py`
- [ ] Each tool returns valid response on a real query (manual smoke test)
- [ ] Server runs without `SEMANTIC_SCHOLAR_API_KEY` set (anonymous mode works)

### Exit Criteria (Phase 4)

- [ ] Single MCP server with 9–10 well-documented tools across 3 providers
- [ ] Future contributors can add a new provider by adding a section + tool decorators

---

## Phase 5 — Installer Scripts

### Goal (Phase 5)

Each install script is a one-liner UX: `bash install.sh` → pick tool → everything wired up. Self-contained `.open-scholar-peer/mcp/` per project.

### Deliverables (Phase 5)

- [ ] **`scripts/init_mcp.sh`** — shared helper invoked by all installers:
  1. Create `<project>/.open-scholar-peer/mcp/`
  2. Copy `mcp-server/osp_mcp.py` + `requirements.txt` into it
  3. `python3 -m venv .open-scholar-peer/mcp/.venv`
  4. `.open-scholar-peer/mcp/.venv/bin/pip install -r requirements.txt`
  5. Add `.open-scholar-peer/` to `.gitignore`
- [ ] **`scripts/init_brain.sh`** — updated for v2 schema (already exists; needs schema bump)
- [ ] **Per-tool MCP config writers** (one logical block per installer):
  - `install_claude.sh` → write/merge `<project>/.mcp.json` with two entries: `osp` (points to `.open-scholar-peer/mcp/.venv/bin/python` + `osp_mcp.py`) and `markitdown` (uvx or pipx command).
  - `install_cursor.sh` → write `<project>/.cursor/mcp.json` with same two entries.
  - `install_gemini.sh` → write `<project>/.gemini/mcp.json` (or extension manifest) with same two entries.
  - `install_antigravity.sh` → emit instructions for the user to add entries to `~/.gemini/antigravity/mcp_config.json` (global config — can't be done programmatically for this tool); copy a ready-to-paste snippet to clipboard or file.
  - `install_copilot.sh` → write the equivalent for Copilot CLI.
- [ ] **Per-tool adapter file copy** — each installer copies its `extensions/.{tool}/` content into the user's project root.
- [ ] **`install.sh`** — top-level dispatcher (mostly works; update tool labels: "GitHub Copilot CLI" not just "GitHub Copilot").
- [ ] **MarkItDown MCP** — register the official Microsoft `markitdown-mcp` package alongside `osp_mcp` in every tool's MCP config. Document the install command (`pipx install markitdown-mcp` or equivalent).

### Tests (Phase 5)

- [ ] Fresh install on empty directory → `.brain/`, `.open-scholar-peer/`, tool config, adapter files all created
- [ ] Re-running installer is idempotent (no breakage, no duplicate config entries)
- [ ] `.open-scholar-peer/mcp/.venv/bin/python osp_mcp.py` runs successfully
- [ ] Existing user config files (e.g., pre-existing `.mcp.json`) are merged, not overwritten
- [ ] Linux + macOS shells both succeed

### Exit Criteria (Phase 5)

- [ ] One-liner install works for every supported tool
- [ ] Self-contained `.open-scholar-peer/mcp/` survives repo deletion
- [ ] User can verify install by invoking `/open-scholar-peer` and seeing the dispatcher respond

---

## Phase 6 — Cross-Tool Validation, Docs, Release

### Goal (Phase 6)

Confirm parity across tools, document limitations, and ship.

### Deliverables (Phase 6)

- [ ] **E2E test per tool** — fresh install + run `/0-osp-onboarding` + `/1-osp-summary` on a sample paper; verify artifacts exist and have correct sections. *(Deferred — requires interactive AI tool sessions; covered by `scripts/test_install.sh` for structural validation.)*
- [x] **Parity test** — `scripts/test_parity.py` confirms every command and skill exists in every tool's adapter directory.
- [x] **Install smoke test** — `scripts/test_install.sh` runs each installer in a temp dir and verifies expected file structure.
- [x] **README.md rewrite** — quickstart, architecture diagram, command reference (`/open-scholar-peer` + 7 numbered commands), tool support matrix.
- [x] **`docs/KNOWN_LIMITATIONS.md`** — covers Antigravity self-reflection, Semantic Scholar rate limits, PDF parsing, MCP global config friction, single-paper sessions, Google Scholar best-effort, hyperparameter rigidity, downstream invalidation.
- [x] **`docs/TROUBLESHOOTING.md`** — common issues by symptom (install / MCP server / workflow / sync).
- [x] **`docs/CONTRIBUTING.md`** — golden rule, four contribution paths (commands, skills, MCP providers, sync transformers), code style, PR checklist.
- [x] **AGENTS.md update** — rewritten for v2 file layout, naming conventions, build cycle.

### Tests (Phase 6)

- [x] Parity script passes (no missing commands/skills per tool)
- [x] All 13 tools structural smoke test passes via `scripts/test_install.sh`
- [ ] *(Manual)* README quickstart, when followed verbatim, produces a working install on a real machine

### Exit Criteria (Phase 6)

- [x] v2 is structurally releasable
- [x] All known limitations documented; no surprises for users
- [x] *(Manual milestone)* full end-to-end run on a real paper completed successfully — ready to tag v1

---

## Phase 6+ — Polish & Refinement (Latest)

### Recent Work

Ongoing refinements for UX and robustness:

#### MCP Server & Tool Improvements

- [x] **Timeout wrapper** — all async tool calls wrapped with `asyncio.wait_for(timeout=30)` to prevent hangs (Semantic Scholar, arXiv)
- [x] **Expanded Semantic Scholar** — from 4 → 10 tools: `get_paper_references`, `get_paper_citations`, `get_papers_batch`, `search_authors`, `get_author_papers`, `get_paper_recommendations`, `search_snippets` (in addition to `search_semantic_scholar` and `get_paper_details`)
- [x] **ArXiv via package** — switched from raw HTTP to `arxiv` Python package for better rate limiting and reliability
- [x] **Dotenv loading** — MCP server loads `.env` at startup for API key injection
- [x] **Sidecar tracking** — OSP-managed MCP entries tracked in `.scholar-peer/osp-managed-entries.json` to prevent Gemini JSON validation breakage

#### Command & Skill Enhancements

- [x] **User orientation rule** — every phase invocation prints opening context block: what this phase does, reads, writes, effort estimate
- [x] **Informative output** — closing reports describe findings/counts/highlights, not just "run X next"
- [x] **Venue confirmation forcing** — `/0-osp-onboarding` Step 3 always asks user, even if paper shows venue; uses tool's native ask mechanism
- [x] **Native file referencing rule** — osp-rules.md documents per-tool format: `@file` for Claude/Cursor/Gemini, `#file:` for Copilot CLI, plain path for Antigravity
- [x] **Simultaneous literature retrieval** — literature review agent fires all search tools in parallel dispatch (not sequential), with per-tool query formulations

#### Installer & Docs Polish

- [x] **Spinner animations** — `init_mcp.sh` uses braille spinner with `kill -0` polling for venv/pip operations; non-blocking in CI
- [x] **Numbered "Next:" format** — all installers end with `Next: (1) ... (2) run /open-scholar-peer`
- [x] **Removed "Drop your paper" instruction** — user relies on `/open-scholar-peer` orchestrator for paper path discovery
- [x] **Directory rename** — `.scholar-peer/` → `.open-scholar-peer/mcp/` throughout (init_mcp.sh, merge_mcp_config.py, docs, gitignore)
- [x] **Tool name shortening** — "Google Antigravity IDE" → "Antigravity", "GitHub Copilot CLI" → "Copilot CLI" (install.sh menu, installer headers, README table, docs)
- [x] **`.env` for API keys** — installers create `.env` at project root with example placeholder; documented in README
- [x] **Dynamic Q&A pairs** — default 2 pairs per criterion (user-configurable at `/5-osp-qa` start); templates use `{{qa_pairs_per_criterion}}`

#### Documentation Updates

- [x] **README** — updated architecture, API keys section, configurable Q&A mention, tool support matrix with short names
- [x] **TROUBLESHOOTING** — "paper not found" now directs to `/open-scholar-peer` instead of manual copy
- [x] **All docs** — updated directory references, tool names, Q&A pair counts

### Exit Criteria (Phase 6+)

- [x] MCP server is robust (timeouts, expanded tooling, env-loaded keys)
- [x] All agents are informative (orientation blocks, findings-based reports)
- [x] Literature review uses all tools simultaneously
- [x] Installers are polished (spinners, numbered ending, no "drop paper" instruction)
- [x] Docs are current and user-friendly
- [x] *(Manual milestone)* live E2E test on a real paper verified — all 7 phases produce a coherent review

---

## Out of Scope (deferred)

- [ ] **Multi-paper sessions** — `.brain/sessions/<paper_slug>/` with active-session pointer. Currently v1 = one paper per `.brain/`.
- [ ] **`src/backend`** — DeepAgents JS / LangGraph standalone runtime.
- [ ] **`src/frontend`** — Customized Deep Agents UI with stepper UX.
- [ ] **Publishing `osp-mcp` to PyPI** — currently v1 = self-contained venv per project; future = `pipx install osp-mcp`.
- [ ] **CI for sync drift** — currently manual; future = pre-commit hook or GH Actions check that fails if `_shared/` is newer than any adapter.
- [ ] **Parallelization within Phase 1** — Summary, LitReview, Historian, BaselineScout could run in parallel but currently sequential for simplicity and methodology fidelity.
