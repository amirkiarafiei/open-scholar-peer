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
last_updated: "2026-09-23"
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
| [7](#7-one-source-twenty-one-tools) | One source, twenty-one tools |
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
| **The library is prompts, not code** | 1,996 lines of canonical prompt markdown against 7,048 lines of Python and 3,317 of shell — and none of that code is review logic; it is sync tooling, search and installers. §3 |
| **One source, twenty-one adapters, generated** | Editing a per-tool directory is pointless; it is wiped on the next sync. §7 |
| **Paper hyperparameters are enforced by file structure** | Each retrieval round the user runs must leave its own file on disk, because a model will otherwise claim rounds it did not run. `k=3` is the recommendation; the count is the user's. §4 |
| **The agent's memory is a JSON file** | `session.json` is the only thing connecting one slash command to the next. §5 |
| **The orchestrator never does review work** | It reads state and names the next command. Every write is done by the persona skill that owns the step. §5 |
| **The search server is deliberately stupid** | It fetches. It never decides what to fetch. §9 |

---

## 2. Tech stack

| Layer | Choice | Note |
|---|---|---|
| **Protocol** | Markdown with YAML-ish frontmatter | The actual product. Parsed by the host AI tool, and by a deliberately simple home-grown parser in `sync_adapters.py` — keep frontmatter flat, no nesting or anchors. |
| **Sync + tooling** | Python 3.10+, stdlib only | `sync_adapters.py`, `merge_mcp_config.py`, `test_parity.py`. No third-party dependency in the dev toolchain. |
| **Installers** | Bash, `set -e` | 21 per-tool scripts plus a menu at `install.sh`. Must survive `curl … \| bash`. |
| **Search server** | Python + FastMCP (`mcp>=1.2.0,<2.0`) over stdio | Runs as a subprocess of the host tool. **The ceiling is load-bearing:** mcp 2.x deletes `mcp.server.fastmcp` and renames `FastMCP` to `MCPServer`, so an unbounded pin left the server unable to import at all. O15. |
| **Search providers** | `arxiv`, `semanticscholar`, `scholarly` + BeautifulSoup; Europe PMC, Zenodo and OpenAlex over plain `requests` | Pinned, with upper bounds, in `mcp-server/requirements.txt`. Google Scholar is HTML scraping and is best-effort. |
| **Runtime isolation** | A venv per user project at `.open-scholar-peer/mcp/` | Not published to PyPI; the installer builds it in place. |

*Re-measured 2026-09-20: `cat extensions/_shared/{commands/*.md,skills/*/SKILL.md,rules/*.md,defaults/*.md} | wc -l` → **1342**; `cat scripts/*.py mcp-server/*.py mcp-server/providers/*.py | wc -l` → **5,851**; `cat install.sh scripts/*.sh | wc -l` → **1922**. The shell figure grew most: M9 took `install.sh` from 88 lines to a 607-line TUI and added `scripts/_post_install.sh`.*

---

## 3. Repo layout

| Path | Owns |
|---|---|
| `extensions/_shared/` | **The canonical protocol.** 8 commands, 8 skills, 2 rules files, 4 templates, 1 manifest — 23 files. The only place a human edits protocol content. |
| `extensions/.{tool}/` | 21 generated adapter directories, 467 files. Never edited by hand. |
| `mcp-server/` | The search server and its six providers. Source of truth; the copy in a user's project is the runtime. |
| `scripts/` | Sync, parity check, MCP-config merge, `.brain/` and venv scaffolding, 21 installers, smoke tests. |
| `docs/` | Human-facing: build phases, I/O contracts, brain layout, limitations, troubleshooting, and the source paper. |
| `.brain-template/` | The `session.json` skeleton copied into every user project. |
| `kia-context/` | This harness. |

*Measured 2026-09-21: `find extensions/_shared -type f | wc -l` → 23; `find extensions -path extensions/_shared -prune -o -type f -print | wc -l` → 467; `ls scripts/install_*.sh | wc -l` → 21.*

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
| `k = 3` rounds | **structural, per round run** | One file per round actually run, written before the next begins — non-negotiable, because a model will otherwise assert rounds it did not run. **How many rounds is the user's choice** (D29, M15): the phase completes at 1, 2 or 3 with `rounds_completed` recorded. |
| `N_QA = 10` | **user-chosen, default 2** | Persisted as `session.json.qa_pairs_per_criterion`; the template renders `### Q1`…`### QN` from it. Ten pairs across every criterion was judged too expensive as a default. |

### Q&A: two agents, or one agent pretending

Step 5 is the only step that runs two personas. The Query Agent holds the main thread and must never
answer its own questions; each question goes to a fresh, stateless Answer Generator that cannot see the
other questions. That isolation is the point — it is what stops the verification being coloured by the
reasoning that produced the question.

17 of 21 tools support real subagents, in three groups. **14 delegate outright.** **3 try and degrade** —
Antigravity, Hermes and OpenClaw each document a subagent framework with its own context window, but none
documents that a persona *skill* is reachable through it, so the banner tells them to attempt delegation
and fall back rather than stop (D17, D36). **4 always self-reflect** — Mistral Vibe, OpenHands, Pi and
Cline — running both personas in one context window separated by hard turn markers
(`=== Query Agent === … === Answer Generator === …`). This is a weaker substitute and is published as one
(`docs/KNOWN_LIMITATIONS.md` §1). The banner that tells a tool which mode it is in is injected at sync
time by `sync_adapters.py::adapt_qa_body_for_tool()` — the single semantic transform in the whole pipeline.

Three of the delegating tools needed the persona written twice. Oh My Pi, Grok Build and Kilo Code
dispatch to a named *agent definition* and cannot target a skill, so `sync_adapters.py` also emits each
persona as a flat file under the tool's `agent_dir`. Without it they would have fallen back to
self-reflection while being fully capable of the real thing (D36).

*Measured 2026-09-21: `sum(1 for t in TOOLS.values() if t.supports_subagent)` → 17 of 21; qa_mode splits
14 subagent / 3 prefer-subagent / 4 self-reflection. It read 12 of 14 until this wave — see D16, D36.*

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

> **Template and initialisers agree.** `phases.literature.rounds_completed` is declared in
> `.brain-template/session.json` and in the `scripts/init_brain.sh` fallback, alongside `skip_reason` and
> the four permitted `status` values. Closed as O3 on 2026-09-21 (M15).

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

## 7. One source, twenty-one tools

Twenty-one AI tools disagree about nearly everything: what a command file is called, where it lives,
whether it is Markdown or TOML, whether a slash command is a file at all or only a skill, where always-on
instructions go, how subagents are addressed, and how MCP servers are registered — or whether the tool
has MCP at all. Maintaining twenty-one copies of an eight-step protocol by hand guarantees drift.

```
extensions/_shared/  ──►  sync_adapters.py  ──►  extensions/.{claude,cursor,…}/  ──►  install_*.sh  ──►  user project
   23 files                 capability matrix          467 files, 21 dirs              copy + wire MCP
```

`sync_adapters.py` holds a `ToolCaps` row per tool: subagent support, Q&A mode, command directory,
command extension, skill directory, rules directory, any extra always-on file, and three fields added
by the 2026-09 wave — `commands_as_skills`, `agent_dir`, `search_mode` and `install_dir`. Sync **wipes** each target
directory and regenerates it, so stale files cannot survive a rename.

The transforms are:

| Transform | Why it exists |
|---|---|
| Markdown → TOML | Gemini CLI commands are TOML with the body in a `prompt = """…"""` field. |
| Rules → `GEMINI.md` / `AGENTS.md` / `QWEN.md` / `guidelines.md` | Each tool has its own always-on instruction filename, some at the tool root rather than in a rules directory. |
| Rules → `.mdc` with `alwaysApply: true` | Cursor's format. |
| Q&A banner injection | A content-level branch with three outcomes: `subagent`, `prefer-subagent` (try, then degrade), `self-reflection`. |
| Commands → skill directories | Hermes and OpenClaw have no file-based slash commands at all — every skill is one. Cline retired its command mechanism in favour of skills. On those three the 8 commands ship as `<skill_dir>/<name>/SKILL.md`. |
| Skills → flat agent definitions | Oh My Pi, Grok Build and Kilo Code delegate to a named agent file and cannot dispatch a skill, so each persona is emitted a second time under `agent_dir`. |
| Rules + CLI addendum | A tool with no MCP client at all (Pi) gains a short block in its always-on file saying the interface is always `cli`. Every other tool gets the fallback through the always-on rules instead. The `defaults/...` pointer inside the addendum is resolved **after** it is joined on — resolving first rewrote only the base file and shipped the pointer dead. |
| `defaults/x.md` → `.<tool>/defaults/x.md` | Nothing is ever installed at `<project>/defaults/`; the adapter lands in `.claude/`, `.codex/`, `.agents/`. The canonical files keep the short form so they stay tool-agnostic, and each adapter gets a path that resolves. `install_dir` names it, and is **not** derivable from `root` — `--check` clones tools with a temporary root. |

Three guards keep this honest: `sync_adapters.py --check` regenerates into a temp tree and byte-compares
(exit 1 on drift), `test_parity.py` asserts every tool has every canonical asset, and `test_install.sh`
smoke-tests all 21 installers in temp directories, and `test_parity.py` additionally asserts that its
own hand-written tool list still matches the capability matrix. All pass as of 2026-09-21.

**Installers** copy the adapter (after `clean_adapter.sh` removes OSP-managed files from a previous
version), scaffold `.brain/`, build the MCP venv via `init_mcp.sh`, and then either merge the server into
the tool's config — `merge_mcp_config.py` for JSON, `merge_mcp_toml.py` for Mistral Vibe's TOML, and
`codex mcp add` for Codex, which edits its own TOML through `toml_edit` and so keeps the user's comments.
**Every supported tool is wired automatically; none asks the user to paste anything.** The one exception
is not a tool but a surface: the OpenHands *web UI* keeps MCP settings in its database, so a snippet is
left for those users. A paste-ready snippet is also written as the fall-back whenever a merge declines —
which happens only when the user's existing config cannot be parsed, and their file is then left untouched. Tools sharing the project-root `AGENTS.md` surface
merge through `merge_agents_md.sh` using `<!-- OSP-BEGIN/OSP-END -->` markers — never a bespoke merge.

---

## 8. What the system refuses to do

Refusals are as much a part of the specification as actions. These are enforced in prompt text, which
means they are strong conventions rather than hard gates — worth knowing when reasoning about failure.

| Refusal | Where |
|---|---|
| **Advance without a readable paper.** If `.brain/input/paper.md` is absent and only a PDF exists, convert it or stop. Do not assume the host tool will cope. **Since M15 this is the only refusal left in the system** — with no paper there is nothing to review. | `commands/0-osp-onboarding.md`, `commands/1-osp-summary.md` |
| ~~**Advance out of order.**~~ **Removed in M15 (D29).** No step is a gate: a phase with missing inputs states what it is therefore missing, records the skip in `session.json` and its Provenance, and runs. The final review names its own gaps under `## What this review did not have`. | `rules/osp-rules.md` §Brain protocol 4–5 |
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

22 tools over six databases, defined in `mcp-server/core.py` — but only the databases this project
enabled are served.

**Three files, and the split is the point.** `providers/` does the network work and knows nothing
above it. `core.py` holds the 22 tool functions, the error envelope, the gating and the timeout, and
imports no transport. `osp_mcp.py` (66 lines) serves them over MCP; `osp_cli.py` serves the same
function objects over argv. Neither front end names a tool, so neither can drift from the other, and
**the CLI does not import `mcp`** — a fallback that fails with the thing it is a fallback for is not
a fallback (M18, D34).

| Database | Tools | Key | Character |
|---|---|---|---|
| arXiv | 3 | none | Pre-prints. Field-prefixed queries (`ti:`, `au:`, `abs:`). Category and date filtering happen inside the query, so arXiv does them. Also serves **full text**, from the LaTeX source. |
| Semantic Scholar | 11 | optional | Citation graph — references, citations, batch lookup, authors, recommendations, title matching, snippet search. Anonymous access is one pool shared globally and is throttled hard. |
| Google Scholar | 3 | none | Breadth: theses, workshop papers, blogs. HTML scraping, best-effort, not load-bearing. |
| Europe PMC | 2 | none | Biomedical and life sciences. Serves **full text** as XML over a plain request — the cheapest full-text path in the system. |
| Zenodo | 1 | none | Not a paper search. Code, datasets and software releases: *did the authors release their code?* |
| OpenAlex | 2 | optional | ~327 million works. Carries `is_retracted`, which nothing else here can see, and field-normalised citation impact. |

*Measured 2026-09-22: `grep -c '^@tool_for(' mcp-server/core.py` → 22. The tools moved out of the
server file in M18; `osp_mcp.py` names none of them.*

**Which tools exist is a per-project decision.** The installer asks, and writes the answer to `.env` as
`OSP_SOURCES`; `osp_mcp.py` reads it once at start-up and registers only those. An unset value means all
six, so installs predating this are unaffected. This is not cosmetic: D21 rejected "always on" precisely
because a longer tool list costs the agent on every request, and a three-database project carries 17
tools rather than 22. An unknown name warns and is ignored; a value naming nothing valid falls back to
all six rather than leaving the agent with no tools at all.

Every tool is atomic and stateless. The server decides nothing: which queries to run, which results to
keep, and when the corpus is sufficient are all the agent's judgement. This is a standing constraint set
at t=0 — the design explicitly forbade a tool like `fetch_literature` — not an accident of scope. See
`logs/BRAINSTORM.md` D3. Two caches exist and neither breaks that rule, because both change *when* an
answer arrives and never *what* it is: one HTTP client per provider, and an eight-entry cache of parsed
arXiv text so paging through a paper does not re-download it, and one
download per paper however many callers ask at once (D25, O17).

**Both caches are per process, and that is a real limit on the CLI surface.** One MCP server is one
process, so they work. Every `osp_cli.py call` is a new process, so they do not. Two of the three
mechanisms were restored across processes by a lock file carrying arXiv's timestamp — the
one-at-a-time rule and the three-second gap, which were not degraded in CLI mode but **absent**: a
fresh process read `_last_raw_request = 0.0`, computed a gap of ~1.79 billion seconds, and never
slept. The parsed-text cache was not, so paging through one paper still re-downloads it once per
window (**O26**). The `batch` subcommand removes the whole problem for the common case by running a
round in one process (D39).

Three operational details worth knowing.

Every provider call goes through `_run()`, which pushes the synchronous call into a thread with
`asyncio.wait_for` and a timeout (`OSP_CALL_TIMEOUT`, default 90 s, overridable per call through a
`ContextVar`). Because `asyncio.to_thread` cannot cancel a running thread, that timeout alone is not
enough — a provider that hangs keeps working after the caller has given up, and `asyncio.run()` then
*joins* it on the way out. Measured: a 1 s deadline against a 6 s call raised at 1.00 s and the
process did not return until 6.01 s. The CLI therefore writes its result inside the event loop and
leaves through `os._exit` after an explicit flush, so the answer is never held hostage to the thing
that already timed out. So each one also bounds itself from the inside: arXiv waits at most 15 s for
the single connection its terms allow, pins the package to three attempts and caps a download at 35 s,
for a worst case of 66 s on search and 78 s on a full-text read; Google Scholar's whole retry budget is
63 s; Europe PMC's is 60 s. Each is pinned by a test, because the point is to stay
under the 90 s ceiling.

Every tool returns a consistent error envelope — `[{"error": …, "reason": …}]` for searches,
`{"error": …, "reason": …}` for single records — rather than raising. **`reason` is what makes a
failure actionable**: `blocked`, `rate_limited`, `busy`, `timeout`, `not_found` or `bad_request`. An
empty list means one thing only, which is that the search ran and matched nothing. That distinction is
load-bearing; the layer spent months reporting a Google Scholar block as a successful zero-hit search.

Full text is read in windows and never written to disk (D20). A window ends at a paragraph break rather
than a character count, so a number cannot be cut in half, and `next_offset` chains the calls.

### What the audit found, and what is left

An audit on 2026-09-19 measured this layer against the live APIs and found three claims here to be
aspirations rather than facts. **All three were fixed in M11** and the measurements are in
`logs/PROGRESS.md`:

| The claim | Then | Now |
|---|---|---|
| arXiv supports category and date filtering | a category filter returned 3 of 25 in the requested category; a 12-month window returned 1 paper | filtering happens inside the query: 25 of 25, and a full page |
| a failing provider degrades one call, not the step | a Google Scholar block returned `[]`, identical to a genuine zero-hit search | a block raises and carries `reason: blocked` |
| one hung HTTP call cannot wedge the server | the Semantic Scholar client retried a 429 for ~375 s, long past the 90 s timeout, while the orphaned thread kept hitting the API | the package's retry is off; the same call now fails in 1.3 s naming the cause |

Consequently the old warning that **an API key made OSP slower** no longer holds: that was the
auto-pagination, which issued 100–200 requests where one was asked for. One search is now one request.
The documented Semantic Scholar limits are unchanged — 1 request per second with a key, against 1000 RPS
shared by every unauthenticated caller on earth — and in practice the shared pool is the worse deal.

The Literature Agent is instructed to fire **all** providers in the same dispatch batch with per-index
query formulations, not sequentially — a paper ranked low in one index is often top of another.

### The same tools, without MCP

`mcp-server/osp_cli.py` exposes the identical 22 tools over argv and JSON. It began as Pi's only
path — MCP and web access are both stated non-features there, so without it the protocol would have
run with nothing to retrieve (D34) — and M18 made it **the documented fallback for all 21 tools**.

**MCP stays the default everywhere. The CLI is second class**, and which one a project uses is
decided once, by a mechanical rule, and recorded in `session.json` as `mcp.interface`:

| | Check | Outcome |
|---|---|---|
| 1 | `osp_cli.py` is not on disk | `none` — the search layer was never installed |
| 2 | an OSP tool answers | `mcp` |
| 3 | otherwise, and the shell can reach the network | `cli` |
| 4 | otherwise | `none` — reported plainly, never as an empty corpus |

The fourth row exists because three tools block outbound network from the shell by default — Codex
CLI, Antigravity IDE on macOS/Linux, and Kiro Web at its baseline tier (O25). All three have working
MCP, so the fallback is missing only where it is not needed; they also have **no fallback at all** if
their MCP breaks. The rule deliberately does *not* ask the agent to inspect its own tool list: hosts
disagree about what a crashed server looks like, a tool list can be a start-up snapshot, and
`OSP_SOURCES` gating makes per-tool reasoning actively wrong. **One `.env` governs both surfaces**,
so the CLI never has a database MCP lacks — a missing tool is never a reason to change interface.

The value goes stale, so a failed search under `mcp` re-probes once and rewrites the field. A server
that died mid-session looks exactly like a database with nothing in it, and telling those two apart
is what this whole layer is for.

**Neither surface owns a schema.** FastMCP derives one from the tool's signature through pydantic;
the CLI derives the same one through `inspect.signature`. A human edits one decorated function and
both follow. `scripts/test_schema_parity.py` pins the derivation rules — names, required sets, types
and defaults field by field, then the whole document byte for byte — plus a frozen census of the
seven annotation forms the 22 tools use, so an eighth cannot arrive unnoticed.

Three properties of the CLI that MCP does not need, all added in M18 and all measured:

- **A hard wall-clock bound.** See the timeout note above.
- **An output cap.** A 50-result search wrote 103,399 bytes (~24,500 tokens); a host truncating that
  mid-document leaves an agent holding a fragment it reports as complete. The cut happens in the CLI
  instead, where it can be described. Every cut is declared under `osp_truncated`, in one of three
  shapes: a **list** gains a last element and the records above it are whole; a **record** has its
  heaviest fields shrunk and the marker merged in, naming each field and the unit; a **full-text
  window** is re-cut with `returned_chars`, `truncated` and `next_offset` corrected, so paging still
  chains exactly. The marker is deliberately *not* the error envelope shape — a truncated search is
  not a failed one. **Two things exceed the cap on purpose:** an error envelope is never dropped, so
  a failure whose message alone is oversized still arrives with its `reason`; and below a floor there
  is no room for both the record and an honest account of what was cut, so the account wins.
- **`batch`.** One process for a whole round, which restores the rate limit, the caches and the
  de-duplication and pays one start-up instead of eighteen (D39). **Each item gets the budget a
  single call gets**, not a share of it — dividing it made the recommended path return less the more
  you asked for, which is the opposite of what `batch` is for (D47).

Its exit codes carry the distinction this layer exists to protect — **0** the call ran (an empty list
means nothing matched), **1** it failed and the envelope names a `reason`, **2** the call itself was
malformed — but the shipped guidance tells the agent to **branch on `reason`, never on the exit
code**. Measured, the codes are genuinely ambiguous: a database switched off by `OSP_SOURCES` and a
misspelled tool both exit 2 and need opposite responses.

`init_mcp.sh` ships it with every install, exports `OSP_SEARCH_CLI`, and **proves it runs** by
calling `osp_cli.py list` before reporting success — one check in the file all 21 installers source.

## 10. The terminal is the interface

There is no GUI, so the terminal block *is* the product surface, and its shape is specified in
`extensions/_shared/rules/osp-rules.md` as an always-on rule rather than left to the model.

Every phase opens and closes with a block whose format is defined **once**, in
`extensions/_shared/defaults/phase_block_template.md`: a 60-column rule carrying the phase label alone and
centred, then the progress rail on its own `PROGRESS` line directly under it, then
left-hand labels — `DOING` / `READS` / `WRITES` / `COST` opening, `DONE` / `BLOCKED` / `NOTE` / `NEXT`
closing — with values in a column at 12. No other file may render a rail; `scripts/test_parity.py`
fails if one does. The block runs *every* time, including re-runs: the user is learning the system as
they go, and the closing one reports **what was found**, not merely which command comes next.

Artifact paths are printed on a continuation line under `DONE`, in the value column, paired with the
host tool's native clickable form where it has one (`@.brain/…` for Claude, Cursor, Gemini and others;
`#file:` for Copilot CLI; a plain path where there is no shorthand).

Resource warnings precede anything expensive. Step 5 prints the full multiplication — criteria × pairs =
subagent calls, with an estimated wall-clock — *before* asking how many pairs to run.

---

## 11. What it depends on

**On the user's machine:** `git`, `bash`, `python3` 3.10+ with `venv` (checked explicitly, because Debian
and Ubuntu ship `python3` without `ensurepip`), and one of the 21 supported AI tools.

**External services:** arXiv, Semantic Scholar (optional key), Google Scholar (scraped), Europe PMC,
Zenodo, and OpenAlex (optional key). Keys live in `.env`; none is required.
Optionally `markitdown-mcp` via `uvx` for PDF → Markdown conversion — the one dependency that can block
step 0 outright.

**What this repository exposes:** the 8 slash commands, the 8 persona skills, up to 22 MCP tools, and the
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
