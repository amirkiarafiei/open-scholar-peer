---
description: >
  The map of the context harness. Says what every folder and file is, what era it covers, and which one
  to open for a given question. Holds no rules of its own — it points at the files that do. Update it
  whenever a context file is added, renamed, moved, split or closed.
  NOT here: any rule, any decision, any technical detail. If something is decided here, it is in the
  wrong file.
authority: map
writes: agent, when files move
status: active
covers: the whole harness
last_updated: "2026-09-11"
harness: kiacontext v0.2
---

# 🗺️ INDEX — What each file is, and when to open it

This file is a **map, not an authority**. Nothing is decided here. If this file and the file it describes
disagree, the described file wins and this one is the bug.

**Reading it takes a minute. Read it before opening anything else.**

**Contents**

| § | |
|---|---|
| [1](#1-the-project-in-five-lines) | The project in five lines |
| [2](#2-phases) | Phases |
| [3](#3-kia-context--the-harness) | `kia-context/` — the harness |
| [4](#4-docs--human-facing-artifacts) | `docs/` — human-facing artifacts |
| [5](#5-which-file-answers-which-question) | Which file answers which question |
| [6](#6-the-numbering-and-why-it-never-restarts) | The numbering, and why it never restarts |
| [7](#7-what-references-what) | What references what |

---

## 1. The project in five lines

**Open ScholarPeer** is an open-source implementation of Google's published *ScholarPeer* peer-review
protocol — a paper-to-code project. It installs into the directory holding a paper and lets a researcher
run all seven review steps inside the AI coding tool they already pay for, across 14 supported tools.
There is no runtime: the product is prompt files, a small academic-search server, and the installers that
put both in place. **The one thing that must stay true:** it runs on the user's own tools, and every
conclusion it reaches can be checked in a file on their disk.

---

## 2. Phases

| Phase | Span | State | Log |
|---|---|---|---|
| Extensions | 2026-04-23 → | **active** | `logs/PROGRESS.md` |

The phase is named for `extensions/` — the installable, tool-native delivery model that is the current
and only scope. A second phase would open if the deferred standalone web app (`src/backend`,
`src/frontend`, see `genesis/GENESIS.md` §6) were ever started.

---

## 3. `kia-context/` — the harness

Four levels, split by **authority**, not by topic.

### `kia-context/genesis/` — where this came from · written at t=0, rarely after

| File | What it is |
|---|---|
| `SEED.md` | **The original prompts were never captured and have not been reconstructed.** The file explains that, and points at the closest surviving artifact. |
| `GENESIS.md` | Why the project exists. Reconstructed on 2026-09-11 from `IDEA.md`, the git history and the owner's statement of intent. |
| `IDEA.md` | The original design document, self-subtitled "Master Seed Document". **Frozen** — lived at `docs/IDEA.md` until 2026-09-11 (D14). Cited by section as provenance from `GENESIS.md`, `MANIFESTO.md`, `ARCHITECTURE.md` and `BRAINSTORM.md`, which is why it is kept rather than deleted. Its own banner lists the five places it is now wrong. |

### `kia-context/specs/` — the law · read-only unless explicitly refactoring

| File | What it is |
|---|---|
| `MANIFESTO.md` | The product boundary. Nine numbered rules. **Rules 6, 7 and 9 were written by the agent from observed behaviour and are not yet confirmed by the owner** — the file says which. |
| `ARCHITECTURE.md` | The technical blueprint: the seven-step protocol, the session state machine, the artifact contract, the one-source-fourteen-adapters pipeline, what the system refuses to do, and the search layer. |
| ~~`DESIGN.md`~~ | **Deleted 2026-09-11.** The project has no visual interface. Its terminal output contract — orientation blocks, report blocks, native file references — is in `ARCHITECTURE.md` §10 instead. |

### `kia-context/logs/` — state · written every session

| File | What it is |
|---|---|
| `PROGRESS.md` | Milestones M1–M10, all closed. M1–M7 reconstructed from git; M8 onward live. |
| `BRAINSTORM.md` | Decisions D1–D17 and open questions O1–O11, all open. D1–D11 reconstructed; D12 onward live. |

---

## 4. `docs/` — human-facing artifacts

This project had a full `docs/` tree five months before the harness existed, and it is genuinely
maintained — unusually for this section. Treat it as the human-facing layer, and `kia-context/` as the
*why* layer beneath it. Where the two disagree, that is a finding to raise, not a file to ignore.

**`docs/` is for people using or contributing to the project** — contracts, layout, limitations,
troubleshooting, the paper. Documents that were *input context* for building it belong in this harness
instead; see *Retired* below.

| File | What it is |
|---|---|
| `ARTIFACT_CONTRACTS.md` | The per-step `reads:` / `writes:` contract. Load-bearing: update it whenever a command's frontmatter changes. |
| `BRAIN_LAYOUT.md` | The `.brain/` filesystem shape in a user's project. |
| `KNOWN_LIMITATIONS.md` | Eight caveats users will hit, with workarounds. Honest and current. |
| `TROUBLESHOOTING.md` | Common issues by symptom. |
| `CONTRIBUTING.md` | The four contribution paths, in detail. |
| `paper/` | The source paper and a summary of its method and hyperparameters. |

### Retired from `docs/` on 2026-09-11 (`logs/BRAINSTORM.md` D14)

| Was | Now |
|---|---|
| `docs/IDEA.md` | Moved to `genesis/IDEA.md`, frozen. Still cited as provenance, so it stays readable in place. |
| `docs/PHASES.md` | **Deleted.** Superseded by `logs/PROGRESS.md`. Read the original with `git show 027645b:docs/PHASES.md`. Its one unique surviving decision — why Phase 1 is sequential — was carried into `BRAINSTORM.md` D13 before deletion. |

`AGENTS.md` at the repo root is the developer-facing init doc for agents working on OSP itself, and
carries the Golden Rule. Not part of this harness, but read it before editing anything under
`extensions/`.

---

## 5. Which file answers which question

| If you are asking… | Open |
|---|---|
| What is this project, and what must stay true? | `specs/MANIFESTO.md` |
| How is it built? What is the stack? | `specs/ARCHITECTURE.md` |
| What are we building right now? | `logs/PROGRESS.md` |
| Why was it done this way? What was rejected? | `logs/BRAINSTORM.md` |
| Where did this project come from? | `genesis/GENESIS.md` |
| What did we originally ask for? | `genesis/SEED.md` — not recovered; read `genesis/IDEA.md` instead |
| What was the original build plan? | `logs/PROGRESS.md`. The old `docs/PHASES.md` is deleted — `git show 027645b:docs/PHASES.md` |
| What does step N of the review actually read and write? | `docs/ARTIFACT_CONTRACTS.md` |
| Why does it not do X? | `docs/KNOWN_LIMITATIONS.md`, then `logs/BRAINSTORM.md` |
| How do I add a command, skill, tool or provider? | `docs/CONTRIBUTING.md` |
| How do I work on this repo without breaking the 14 adapters? | `AGENTS.md` |

---

## 6. The numbering, and why it never restarts

| Prefix | Means | Lives in | Currently |
|---|---|---|---|
| `M` | Milestone | `PROGRESS.md` | M1–M10, none currently active |
| `D` | Decision | `BRAINSTORM.md` | D1–D17 |
| `O` | Open question | `BRAINSTORM.md` | O1–O11, all open |
| rule *n* | A manifesto rule | `MANIFESTO.md` | rules 1–9 |

These are cited from other documents. **A renumber breaks every citation and nothing errors.** Append;
strike through rather than delete. When a log is split, the numbering continues into the new part.

---

## 7. What references what

Measured on 2026-09-11 with:

```bash
grep -rl "<FILENAME>" . --exclude-dir=.git --exclude-dir=.claude \
  --exclude-dir=.agents --exclude-dir=.opencode --exclude-dir=.hermes
```

The four excluded directories hold the kiacontext skill files installed per tool — three identical
copies of the same harness documentation, not project references. **No reference to any of these files
exists in source code**, only in Markdown: `grep -rn "MANIFESTO" extensions scripts mcp-server | wc -l`
→ 0.

| If you move or rename… | These point at it |
|---|---|
| `kia-context/INDEX.md` | `AGENTS.md`, `CLAUDE.md` — both inside `<!-- kiacontext:begin -->` blocks regenerated by the installer |
| `kia-context/specs/MANIFESTO.md` | `AGENTS.md`, `CLAUDE.md`, `INDEX.md`, `GENESIS.md`, `ARCHITECTURE.md`, `PROGRESS.md`, `BRAINSTORM.md` — and its **rules are cited by number from 1 file** (`BRAINSTORM.md`, rules 1 and 7). Zero code citations so far. Never renumber. |
| `kia-context/specs/ARCHITECTURE.md` | `AGENTS.md`, `CLAUDE.md`, `INDEX.md`, `GENESIS.md`, `MANIFESTO.md`, `PROGRESS.md`, `BRAINSTORM.md` |
| `kia-context/logs/PROGRESS.md` | `AGENTS.md`, `CLAUDE.md`, `INDEX.md`, `BRAINSTORM.md` |
| `kia-context/logs/BRAINSTORM.md` | `AGENTS.md`, `CLAUDE.md`, `INDEX.md`, `GENESIS.md`, `SEED.md`, `MANIFESTO.md`, `ARCHITECTURE.md`, `PROGRESS.md` — and its **`D` numbers are cited from 1 file** (`SEED.md` cites D4) |
| `kia-context/genesis/GENESIS.md` | `AGENTS.md`, `CLAUDE.md`, `INDEX.md`, `SEED.md`, `PROGRESS.md` |
| `kia-context/genesis/SEED.md` | `AGENTS.md`, `CLAUDE.md`, `INDEX.md`, `PROGRESS.md` |
| `kia-context/genesis/IDEA.md` | `INDEX.md`, `GENESIS.md`, `SEED.md`, `MANIFESTO.md`, `ARCHITECTURE.md`, `BRAINSTORM.md`, `PROGRESS.md` — **cited by section number ~20 times**. Moving it again means rewriting all of them. |

> **One stale reference, left deliberately.** `AGENTS.md` and `CLAUDE.md` both list `DESIGN.md` as part of
> `specs/` (twice each), in text the kiacontext installer generated. `DESIGN.md` was deleted on
> 2026-09-11. Those blocks are regenerated by the harness tooling, so editing them here would be undone;
> the deletion is recorded above instead.
