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
last_updated: "{{YYYY-MM-DD}}"
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

> Replace this with five lines a newcomer could read and know what they are looking at. What it is, who
> it is for, what stage it is at, and the one thing that must stay true. No more than five.

---

## 2. Phases

A project has one phase until it has two. Add a row when a phase opens, and set the previous one to
`closed` on the same day.

| Phase | Span | State | Log |
|---|---|---|---|
| {{name this phase}} | {{YYYY-MM-DD}} → | **active** | `logs/PROGRESS.md` |

> **Illustration only — delete this block.** The same table on a project that has been running a while,
> where one phase closed and a second log was opened beside it:
>
> | Phase | Span | State | Log |
> |---|---|---|---|
> | Prototype | 2026-01-04 → 2026-03-18 | closed | `logs/PROGRESS.md` |
> | Public beta | 2026-03-19 → | **active** | `logs/PROGRESS_2.md` |

---

## 3. `kia-context/` — the harness

Four levels, split by **authority**, not by topic.

### `kia-context/genesis/` — where this came from · written at t=0, rarely after

| File | What it is |
|---|---|
| `SEED.md` | The first prompts that started the project, lightly cleaned. Written once. |
| `GENESIS.md` | Why the project exists — the catalyst, the parties, the problem at t=0. |

### `kia-context/specs/` — the law · read-only unless explicitly refactoring

| File | What it is |
|---|---|
| `MANIFESTO.md` | The product boundary. Numbered rules that may not be traded away. Plain English. |
| `ARCHITECTURE.md` | The technical blueprint — the domain it models and the rules it enforces, as well as the stack and the layout. |
| `DESIGN.md` | The interface blueprint. Tokens, rationale, and the don'ts with their measurements. **Delete it if this project has no interface** — a library, a service or a pipeline does not need one. |

### `kia-context/logs/` — state · written every session

| File | What it is |
|---|---|
| `PROGRESS.md` | Milestones, deliverables, acceptance criteria, reports. What we are building now. |
| `BRAINSTORM.md` | Numbered decisions and open questions. Why we chose what we chose. |

---

## 4. `docs/` — human-facing artifacts

Written **only when a human asks for one**. Agents do not maintain them, and nothing in the harness
depends on them being current. They may carry diagrams, screenshots and long prose; the `kia-context/` files
may not.

| File | What it is |
|---|---|
| `SOFTWARE_ARCHITECTURE.md` | How the code is organised, for a human reader. |
| `SYSTEM_ARCHITECTURE.md` | How the running system is laid out, for a human reader. |
| `DEPLOYMENT.md` | How it gets deployed and operated. |
| `AUTHENTICATION.md` | Who can sign in, and how. |
| `SECURITY.md` | The threat model and what is done about it. |

> Delete any of these that this project does not have. An unwritten one costs nothing; a wrong one does.

---

## 5. Which file answers which question

| If you are asking… | Open |
|---|---|
| What is this project, and what must stay true? | `specs/MANIFESTO.md` |
| How is it built? What is the stack? | `specs/ARCHITECTURE.md` |
| What should the interface look like? | `specs/DESIGN.md` |
| What are we building right now? | `logs/PROGRESS.md` |
| Why was it done this way? | `logs/BRAINSTORM.md` |
| Where did this project come from? | `genesis/GENESIS.md` |
| What did we originally ask for? | `genesis/SEED.md` |

---

## 6. The numbering, and why it never restarts

| Prefix | Means | Lives in |
|---|---|---|
| `M` | Milestone | `PROGRESS.md` |
| `D` | Decision | `BRAINSTORM.md` |
| `O` | Open question | `BRAINSTORM.md` |
| rule *n* | A manifesto rule | `MANIFESTO.md` |

These are cited from code comments and from other documents. **A renumber breaks every citation and
nothing errors.** Append; strike through rather than delete. When a log is split, the numbering continues
into the new part.

---

## 7. What references what

The only place the link graph is recorded. **Measure it with `grep` — do not assume it.** Anything in
**bold** is a reference from source code, where no link checker will ever find it.

| If you move or rename… | These point at it |
|---|---|
| `kia-context/INDEX.md` | `AGENTS.md`, `CLAUDE.md` |
| `kia-context/specs/MANIFESTO.md` | {{measured list}} — and its **rules are cited by number from {{n}} files**. Never renumber. |
| `kia-context/specs/ARCHITECTURE.md` | {{measured list}} |
| `kia-context/specs/DESIGN.md` | {{measured list}} |
| `kia-context/logs/PROGRESS.md` | {{measured list}} |
| `kia-context/logs/BRAINSTORM.md` | {{measured list}} — and its **`D` numbers are cited from {{n}} files** |

State the command you measured with, beside the number. A count nobody can reproduce goes stale silently.
