---
description: >
  The technical blueprint. What this project IS and how it actually works — the domain it models, the
  rules it enforces, and the machinery underneath. A reader must be able to UNDERSTAND the system from
  this file, not merely find out where to look: it is not an orientation page, an index or a map. The
  stack and the folder tree are the cheapest facts in any repository and an agent re-derives both in one
  command; the value here is everything a command cannot produce. It describes the CURRENT state, so it
  changes in place and is never split.
  NOT here: rationale or rejected options (BRAINSTORM.md), product rules (MANIFESTO.md), visual design
  (DESIGN.md), or a deep file tree — a written tree is stale within a week.
authority: blueprint
writes: agent, when explicitly refactoring
status: active
covers: the system as it is today
last_updated: "2026-09-11"
---

# 🏗️ ARCHITECTURE — How this project is built

**Contents**

| § | |
|---|---|
| [1](#1-what-this-is-in-one-page) | What this is, in one page |
| [2](#2-tech-stack) | Tech stack |
| [3](#3-repo-layout) | Repo layout |
| [4](#4-the-seven-step-protocol) | The seven-step protocol |
| [5](#5-the-session-and-how-it-moves) | The session, and how it moves |
| [6](#6-the-artifact-contract) | The artifact contract |
| [7](#7-one-source-fourteen-tools) | One source, fourteen tools |
| [8](#8-what-the-system-refuses-to-do) | What the system refuses to do |
| [9](#9-the-search-layer) | The search layer |
| [10](#10-the-terminal-is-the-interface) | The terminal is the interface |
| [11](#11-what-it-depends-on) | What it depends on |
| [12](#12-words-that-mean-something-specific-here) | Words that mean something specific here |

---

## 1. What this is, in one page

**There is no runtime.** Nothing in this repository executes the review. The reviewing agent is whatever
AI tool the user already runs — Claude Code, Cursor, Gemini CLI, and eleven others. What this repository
ships is the *protocol that agent follows*: a set of prompt files copied into the user's project, plus a
small search server the agent can call, plus the installers that put both in place.

That single fact explains nearly every design decision below. There is no process to hold state, so state
is a JSON file on disk. There is no scheduler to guarantee a step runs three times, so "three times" is
enforced by requiring three files to exist. There is no way to set a temperature or a sampler, so every
parameter the paper specifies is either structural or gone.

```
paper.pdf ─► [0] onboard ─► [1] summarise ─► [2] retrieve ×3 ─► [3] narrate history ─┐
                                                                                      ▼
   final_review.md ◄── [6] synthesise ◄── [5] interrogate ×criteria ◄── [4] audit baselines
```

**The few facts that explain most of the design:**

| | |
|---|---|
| **The library is prompts, not code** | 1,337 lines of canonical prompt markdown against 1,612 lines of Python and 1,344 of shell — and the Python is all sync tooling and search, none of it review logic. §3 |
| **One source, fourteen adapters, generated** | Editing a per-tool directory is pointless; it is wiped on the next sync. §7 |
| **Paper hyperparameters are enforced by file structure** | `k=3` retrieval rounds means three files must exist on disk, because a model will otherwise claim it did three rounds. §4 |
| **The agent's memory is a JSON file** | `session.json` is the only thing connecting one slash command to the next. §5 |
| **The orchestrator never does review work** | It reads state and names the next command. Every write is done by the persona skill that owns the step. §5 |
| **The search server is deliberately stupid** | It fetches. It never decides what to fetch. §9 |

---

## 2. Tech stack

| Layer | Choice | Note |
|---|---|---|
| **Protocol** | Markdown with YAML-ish frontmatter | The actual product. Parsed by the host AI tool, and by a deliberately simple home-grown parser in `sync_adapters.py` — keep frontmatter flat, no nesting or anchors. |
| **Sync + tooling** | Python 3.10+, stdlib only | `sync_adapters.py`, `merge_mcp_config.py`, `test_parity.py`. No third-party dependency in the dev toolchain. |
| **Installers** | Bash, `set -e` | 14 per-tool scripts plus a menu at `install.sh`. Must survive `curl … \| bash`. |
| **Search server** | Python + FastMCP (`mcp>=1.2.0`) over stdio | Runs as a subprocess of the host tool. |
| **Search providers** | `arxiv`, `semanticscholar`, `scholarly` + BeautifulSoup | Pinned in `mcp-server/requirements.txt`. Google Scholar is HTML scraping and is best-effort. |
| **Runtime isolation** | A venv per user project at `.open-scholar-peer/mcp/` | Not published to PyPI; the installer builds it in place. |

*Measured: `cat extensions/_shared/{commands/*.md,skills/*/SKILL.md,rules/*.md,defaults/*.md} | wc -l` → 1337; `cat scripts/*.py mcp-server/*.py mcp-server/providers/*.py | wc -l` → 1612; `cat install.sh scripts/*.sh | wc -l` → 1344.*

---

## 3. Repo layout

| Path | Owns |
|---|---|
| `extensions/_shared/` | **The canonical protocol.** 8 commands, 8 skills, 1 rules file, 3 templates, 1 manifest — 21 files. The only place a human edits protocol content. |
| `extensions/.{tool}/` | 14 generated adapter directories, 282 files. Never edited by hand. |
| `mcp-server/` | The search server and its three providers. Source of truth; the copy in a user's project is the runtime. |
| `scripts/` | Sync, parity check, MCP-config merge, `.brain/` and venv scaffolding, 14 installers, smoke tests. |
| `docs/` | Human-facing: build phases, I/O contracts, brain layout, limitations, troubleshooting, and the source paper. |
| `.brain-template/` | The `session.json` skeleton copied into every user project. |
| `kia-context/` | This harness. |

*Measured: `find extensions/_shared -type f | wc -l` → 21; `find extensions -path extensions/_shared -prune -o -type f -print | wc -l` → 282; `ls scripts/install_*.sh | wc -l` → 14.*

Not in the repository, created in the *user's* project by the installer: `.brain/` (review state, gitignored)
and `.open-scholar-peer/mcp/` (the server plus its venv, gitignored).

---

## 4. The seven-step protocol

This is the domain. Each step is one slash command, activating exactly one persona skill, reading a
declared set of files and writing exactly one artifact. Personas are never blended.

| Step | Command | Persona | Produces |
|---|---|---|---|
| 0 | `/0-osp-onboarding` | orchestrator | `00_review_guidelines.md`, the criteria list, empty per-criterion Q&A files |
| 1 | `/1-osp-summary` | Summary Agent | `01_structured_summary.md` — claims, method, evidence |
| 2 | `/2-osp-literature` | Literature Review Agent | `02a`, `02b`, `02c` round files, then consolidated `02_retrieved_literature.md` |
| 3 | `/3-osp-historian` | Historian Agent | `03_domain_narrative.md` — the sub-field as a sequence of eras |
| 4 | `/4-osp-baseline-scout` | Baseline Scout | `04_missing_baselines.md` — severity-rated omissions |
| 5 | `/5-osp-qa` | Query Agent + Answer Generator | `05_qa_<criterion>.md`, one file per criterion |
| 6 | `/6-osp-review` | Reviewer Agent | `review/final_review.md` |
| — | `/open-scholar-peer` | orchestrator | nothing — reads state, names the next command |

**Why the split is not cosmetic.** Steps 1 and 2 run in opposite directions: step 1 is *internal
compression* and is forbidden from introducing outside context; step 2 is *external retrieval* and is
forbidden from synthesising. Step 3 turns a list of papers into a trajectory, which is the only thing that
makes "incremental or paradigm shift?" answerable. Step 4 is adversarial by construction — it searches for
what is absent, independently of the authors' framing. Step 6 does **no retrieval at all**; decoupling
investigation from reporting is what lets the same evidence be rendered for a different venue by changing
only the guidelines.

### Three hyperparameters, three fates

The paper specifies temperature 0.7, `k=3` retrieval rounds, and `N_QA=10` Q&A pairs
(`docs/paper/SUMMARY.md`). Host tools expose none of these to a slash command, so:

| Paper says | Here | How |
|---|---|---|
| temperature 0.7 | **gone** | Not reachable from a prompt file. Unreproducible, and documented as such. |
| `k = 3` rounds | **structural** | Three separate round files must exist. The Literature skill calls this non-negotiable precisely because a model will otherwise assert it ran three rounds without doing so. |
| `N_QA = 10` | **user-chosen, default 2** | Persisted as `session.json.qa_pairs_per_criterion`; the template renders `### Q1`…`### QN` from it. Ten pairs across every criterion was judged too expensive as a default. |

### Q&A: two agents, or one agent pretending

Step 5 is the only step that runs two personas. The Query Agent holds the main thread and must never
answer its own questions; each question goes to a fresh, stateless Answer Generator that cannot see the
other questions. That isolation is the point — it is what stops the verification being coloured by the
reasoning that produced the question.

12 of 14 tools support real subagents; Antigravity is one of them but tries-then-falls-back, because
whether a persona skill is reachable through its `invoke_subagent` is unconfirmed (D17). The other two —
Mistral Vibe and OpenHands — always use **self-reflection**: both personas in one context window, separated by hard turn markers
(`=== Query Agent === … === Answer Generator === …`). This is a weaker substitute and is published as one
(`docs/KNOWN_LIMITATIONS.md` §1). The banner that tells a tool which mode it is in is injected at sync
time by `sync_adapters.py::adapt_qa_body_for_tool()` — the single semantic transform in the whole pipeline.

*Measured: `python3 -c "…; sum(1 for t in TOOLS.values() if t.supports_subagent)"` → 12 of 14. It read
11 until 2026-09-11, when Antigravity moved into the subagent group — see `logs/BRAINSTORM.md` D16.*

---

## 5. The session, and how it moves

`.brain/session.json` is the entire memory of a review. Slash commands share nothing else.

```
.brain/
├── session.json          venue · paper · criteria · phase states · resume_from
├── input/                paper.pdf (as supplied) + paper.md (canonical readable form)
├── raw/                  00_… 01_… 02a/b/c_… 02_… 03_… 04_… 05_qa_<slug>_… 
└── review/final_review.md
```

**The phase machine.** Seven phase blocks, each moving `pending → in_progress → completed`, plus
`resume_from` naming the next one. Two phases carry extra state: `literature.rounds_completed` counts
0→3, and `qa.criteria_progress` is a map of criterion slug → status, so a single criterion can be redone
without redoing the rest.

**Who is allowed to move it.** The persona skill that executes a step writes its own phase block and
advances `resume_from`. The orchestrator explicitly does **not** — `osp-orchestrator/SKILL.md` puts it as
*"You verify, you don't write."* This matters: the orchestrator is also the thing that runs when a user
types `/open-scholar-peer`, and a dispatcher that mutated state would corrupt a session just by being
asked where it was.

**Criteria are venue-driven, not fixed.** Step 0 scrapes the venue's real review form and writes one
`qa_criteria[]` entry per criterion it finds. A venue with seven criteria produces seven; a venue with
three produces three. Everything downstream loops over that list, so the shape of the final review is set
by the venue rather than by this repository.

**Re-running is allowed and lossy.** A completed step re-run overwrites its own artifact after one
warning. It does **not** invalidate anything downstream — re-running step 1 leaves the step 5 files
reflecting a summary that no longer exists. Cascading invalidation is a known gap
(`docs/KNOWN_LIMITATIONS.md` §8), not a solved problem.

> **Code contradicts template.** Commands read `phases.literature.rounds_completed`
> (`extensions/_shared/commands/2-osp-literature.md`), but `.brain-template/session.json` does not declare
> the field. It works — the command defaults a missing value to 0 — but the schema is incomplete.

---

## 6. The artifact contract

Every artifact, without exception, has three top-level sections:

| Section | Answers | Why it exists |
|---|---|---|
| `## Method` | What the agent actually did — queries run, tools used, what it filtered out | Auditability. A report, never a transcript. |
| `## Output` | The artifact itself | This is what the next persona reads. |
| `## Provenance` | Sources, URLs, confidence flags, tools that were unavailable | Verifiability by a human, and honest gaps. |

`Provenance` is where the system is required to admit failure: a skill that could not reach a search
provider must list it under "tools unavailable" rather than return a quietly thinner corpus.

Each command declares `reads:` and `writes:` in its frontmatter, and the agent is instructed to load
**only** what `reads:` names — never the whole `.brain/`. That is the mechanism behind "context-aware" in
the paper's title: bounded context per persona, enforced by a declared contract rather than by hope. The
full table is `docs/ARTIFACT_CONTRACTS.md`.

---

## 7. One source, fourteen tools

Fourteen AI tools disagree about nearly everything: what a command file is called, where it lives, whether
it is Markdown or TOML, where always-on instructions go, and how MCP servers are registered. Maintaining
fourteen copies of an eight-step protocol by hand guarantees drift.

```
extensions/_shared/  ──►  sync_adapters.py  ──►  extensions/.{claude,cursor,…}/  ──►  install_*.sh  ──►  user project
   21 files                 capability matrix          282 files, 14 dirs              copy + wire MCP
```

`sync_adapters.py` holds a `ToolCaps` row per tool: subagent support, Q&A mode, command directory,
command extension, skill directory, rules directory, and any extra always-on file. Sync **wipes** each
target directory and regenerates it, so stale files cannot survive a rename.

The transforms are:

| Transform | Why it exists |
|---|---|
| Markdown → TOML | Gemini CLI commands are TOML with the body in a `prompt = """…"""` field. |
| Rules → `GEMINI.md` / `AGENTS.md` / `QWEN.md` / `guidelines.md` | Each tool has its own always-on instruction filename, some at the tool root rather than in a rules directory. |
| Rules → `.mdc` with `alwaysApply: true` | Cursor's format. |
| Q&A banner injection | The only content-level branch, and the only one with three outcomes: `subagent`, `prefer-subagent` (try, then degrade), `self-reflection`. |

Three guards keep this honest: `sync_adapters.py --check` regenerates into a temp tree and byte-compares
(exit 1 on drift), `test_parity.py` asserts every tool has every canonical asset, and `test_install.sh`
smoke-tests all 14 installers in temp directories. All three pass as of 2026-09-11.

**Installers** copy the adapter (after `clean_adapter.sh` removes OSP-managed files from a previous
version), scaffold `.brain/`, build the MCP venv via `init_mcp.sh`, and then either merge the server into
the tool's JSON config with `merge_mcp_config.py` or print a paste-ready snippet for tools whose config is
TOML, global, or otherwise not safely machine-editable. Tools sharing the project-root `AGENTS.md` surface
merge through `merge_agents_md.sh` using `<!-- OSP-BEGIN/OSP-END -->` markers — never a bespoke merge.

---

## 8. What the system refuses to do

Refusals are as much a part of the specification as actions. These are enforced in prompt text, which
means they are strong conventions rather than hard gates — worth knowing when reasoning about failure.

| Refusal | Where |
|---|---|
| **Advance without a readable paper.** If `.brain/input/paper.md` is absent and only a PDF exists, convert it or stop. Explicitly: do not assume the host tool will cope. | `commands/1-osp-summary.md` — "Hard input guard" |
| **Advance out of order.** A step whose prerequisite phase is not `completed` refuses and names the command to run first. | every numbered command; `osp-orchestrator` |
| **Auto-advance at all.** Phase boundaries exist so the user can read the artifact. | `commands/open-scholar-peer.md` |
| **Invent an era.** The Historian may not create an era with fewer than two supporting papers in the corpus. | `osp-historian-agent` |
| **Blame the authors for the future.** The Scout may not flag a baseline published after the paper's cutoff. | `osp-baseline-scout-agent` |
| **Answer its own question.** The Query Agent delegates or uses turn markers; never both roles in one voice. | `osp-query-agent` |
| **Carry context between questions.** The Answer Generator is stateless per question in subagent mode. | `osp-answer-generator-agent` |
| **Introduce findings at the end.** The Reviewer synthesises only; a missing critique means re-running an earlier step. | `osp-reviewer-agent` |
| **Cite anything not retrieved.** Every reference traces to `02_retrieved_literature.md`. | `osp-reviewer-agent`, `osp-answer-generator-agent` |
| **Soften a severity rating to be polite.** | `osp-baseline-scout-agent` |

---

## 9. The search layer

15 MCP tools over three providers, exposed by `mcp-server/osp_mcp.py`.

| Provider | Tools | Key | Character |
|---|---|---|---|
| arXiv | 2 | none | Pre-prints. Field-prefixed queries (`ti:`, `au:`, `abs:`) and category codes. Via the official `arxiv` package. |
| Semantic Scholar | 10 | optional | Citation graph — references, citations, batch lookup, authors, recommendations, snippet search. Anonymous limits are aggressive. |
| Google Scholar | 3 | none | Breadth: theses, workshop papers, blogs. HTML scraping, best-effort, not load-bearing. |

*Measured: `grep -c '^@mcp.tool()' mcp-server/osp_mcp.py` → 15.*

Every tool is atomic and stateless. The server decides nothing: which queries to run, which results to
keep, and when the corpus is sufficient are all the agent's judgement. This is a standing constraint from
`genesis/IDEA.md` §3.3, not an accident of scope.

Two operational details worth knowing. Every provider call goes through `_run()`, which pushes the
synchronous call into a thread with `asyncio.wait_for` and a timeout (`OSP_CALL_TIMEOUT`, default 90s) —
one hung HTTP call cannot wedge the server. And every tool returns a consistent error envelope
(`[{"error": …}]` for searches, `{"error": …}` for single records) rather than raising, so a failing
provider degrades that one call instead of the step.

The Literature Agent is instructed to fire **all** providers in the same dispatch batch with per-index
query formulations, not sequentially — a paper ranked low in one index is often top of another.

---

## 10. The terminal is the interface

There is no GUI, so the terminal block *is* the product surface, and its shape is specified in
`extensions/_shared/rules/osp-rules.md` as an always-on rule rather than left to the model.

Every phase opens with an orientation block — what this phase does, what it reads, what it writes, and a
rough effort estimate — and closes with a report of **what was found**, not merely which command comes
next. The rule is explicit that this runs *every* time, including re-runs: the user is learning the
system as they go.

Artifact paths are printed twice: once in the host tool's native clickable form (`@.brain/…` for Claude,
Cursor, Gemini and others; `#file:` for Copilot CLI; a plain path where there is no shorthand) and once as
a `↳ .brain/…` line, so the path is usable regardless of tool.

Resource warnings precede anything expensive. Step 5 prints the full multiplication — criteria × pairs =
subagent calls, with an estimated wall-clock — *before* asking how many pairs to run.

---

## 11. What it depends on

**On the user's machine:** `git`, `bash`, `python3` 3.10+ with `venv` (checked explicitly, because Debian
and Ubuntu ship `python3` without `ensurepip`), and one of the 14 supported AI tools.

**External services:** arXiv, Semantic Scholar (optional key via `.env`), Google Scholar (scraped).
Optionally `markitdown-mcp` via `uvx` for PDF → Markdown conversion — the one dependency that can block
step 0 outright.

**What this repository exposes:** the 8 slash commands, the 8 persona skills, 15 MCP tools, and the
`.brain/` artifact layout. The artifact layout is the real public contract — users read those files, and
renaming one breaks a workflow no test will catch.

---

## 12. Words that mean something specific here

| Term | Here it means |
|---|---|
| **Parametric vacuum** | The paper's name for the core failure: judging a submission against frozen training data with no live picture of the field. Everything about steps 2–4 exists to fill it. |
| **Brain** | `.brain/` — the per-project review state directory. Not a model, not memory in the LLM sense. A pattern inherited from the earlier `reviewer-os` project. |
| **Adapter** | A generated per-tool directory under `extensions/`. Always generated, never authored. |
| **Round** | One of the three literature retrieval passes, each with a distinct anchoring strategy. Re-running the command runs the *next* round, not all three. |
| **Criterion** | One dimension of the venue's own review form, discovered at onboarding. The count is venue-driven. |
| **Persona** | A skill file that gives the host agent one role for one step. Personas are never blended. |
| **Self-reflection** | The degraded Q&A mode for tools without subagents. Always a substitute, never an equivalent. |
| **Discrepancy** | A verified conflict between a paper's claim and retrieved evidence, tagged `[DISCREPANCY]`. Discrepancies are what the final review's weaknesses are built from. |
| **`.agents/` vs `.agent/`** | Two different products, both now subagent-capable. `extensions/.agent/` is Antigravity (desktop); `extensions/.agents/` is Antigravity CLI. The desktop installer writes to *both* `./.agents/` and `./.agent/` in the user's project, because Antigravity's own docs moved workspace customizations to `.agents/` while keeping `.agent/` working. A repo-root `/.agents/` in this repository is unrelated local tooling and is gitignored. |
