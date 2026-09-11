---
name: kia-context-help
description: Explains kiacontext in plain language — what the kia-context/ and docs/ folders are, what each file is for, where a given piece of information belongs, and how to work with the system day to day. Use when someone asks what kiacontext is, what one of these files is for, where something should be written down, or how this system is meant to be used.
allowed-tools: Read, Glob
---

# kiacontext — what it is, in plain language

**A kit of Markdown files that keeps a project's context for and by agents. Nothing more.**

It is not a framework, a workflow, or a methodology. There is nothing to learn and nothing to obey. It
is the set of documents most people end up asking an agent to write anyway — standardised, so the agent
knows where to put things without being told each time.

## Answer the question that was asked

If the human asked something specific — *"what goes in BRAINSTORM?"*, *"where do I write this decision?"* —
answer that in two or three sentences and stop. Only give the full tour below if they asked for one.

Read `kia-context/INDEX.md` before answering; this project's version may differ from the default.

## The whole system

```
kia-context/       the agent reads and writes this
  INDEX.md         the map — what exists and where
  genesis/         where the project came from. Written once, at the start
    SEED.md          the first prompts that started it
    GENESIS.md       why it exists — the catalyst and the problem
  specs/           the law. Changes rarely, in place
    MANIFESTO.md     what this is, and the rules that may not be traded away
    ARCHITECTURE.md  how it is built — stack, layout, whatever else matters
    DESIGN.md        the design system, if there is an interface
  logs/            state. Written every session
    PROGRESS.md      milestones, deliverables, what is done
    BRAINSTORM.md    numbered decisions — why we chose what we chose

docs/              humans read this, and only when someone asks for it
```

## Where a thing goes

| The thing | Goes in |
|---|---|
| What we are building next | `logs/PROGRESS.md` |
| Why we picked this over that | `logs/BRAINSTORM.md` |
| A rule that must not be broken | `specs/MANIFESTO.md` |
| How the system is put together | `specs/ARCHITECTURE.md` |
| Colours, type, components | `specs/DESIGN.md` |
| Why the project exists at all | `genesis/GENESIS.md` |
| A document for people to read | `docs/` — but only when asked |

## How it is used in practice

**You talk to the agent normally.** Nobody fills in forms. The agent writes and maintains these files as
a side effect of the work, the way it writes commit messages.

The human's part is the part only a human can do:

1. **Talk it through** until a decision gets made. The agent records it in `BRAINSTORM.md` — but only if
   it was a real decision, not every exchange.
2. **Decide the milestones** and let the agent write them into `PROGRESS.md` with acceptance criteria.
3. **Work through them** — one at a time, several at once, however suits. That part is not prescribed.

## It is loop-friendly

A finished milestone list with acceptance criteria is exactly what an autonomous loop needs: a next task,
a definition of done, and a place to record the outcome. Once the milestones exist, they can be looped
over. `PROGRESS.md` carries its own loop protocol and circuit breakers, so the loop has somewhere to stop.

That is a property of the format, not a feature to configure. Nothing here requires a loop.

## Two other things worth knowing

**Frontmatter is the strict part.** Six fields on every file — `description`, `authority`, `writes`,
`status`, `covers`, `last_updated`. They are what make a file part of kiacontext. Everything below the
frontmatter is a suggestion that any project may reshape.

**Seven rules keep the files honest**, and they are in `AGENTS.md`. They are all about maintaining
documents — never renumber, grep after a rename, never copy a rule into two files, and so on. None of
them tell anyone how to write code.

## The other two skills

- `kia-context-init` — set it up in a repository for the first time.
- `kia-context-sync` — bring the files back in line after work has happened.
