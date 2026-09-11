---
name: kia-context-init
description: Fills in kiacontext for the first time in a repository. Handles a brand-new project and one already half-built — reverse-engineering ARCHITECTURE and DESIGN from the code, inferring a rough PROGRESS and BRAINSTORM from git history and flagging both as inferred, and asking the human a short, optional set of questions for GENESIS and MANIFESTO. Use once per repository, after the installer has scaffolded the files.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# kia-context-init — fill in the context for the first time

The installer created the files. This fills them in. **Run it once per repository.**

## The one rule

**Never write something you do not know.** A confidently wrong context file is worse than an empty one,
because it gets believed for months. Where you infer, say you inferred. Where you cannot know, leave the
placeholder and say why.

## Step 1 — work out which situation this is

```bash
git rev-list --count HEAD 2>/dev/null || echo 0    # how much history is there
git log -1 --format=%ad 2>/dev/null                 # how old
```

Then look at the tree. Two situations:

- **New project** — little or no code, few commits. Almost everything comes from the conversation.
- **Existing project** — real code and real history. Most of it comes from reading, some from asking,
  and one file cannot be recovered at all.

## Step 2 — fill what the code can tell you

These need no human input. Read the repository and write them.

| File | Where it comes from |
|---|---|
| `specs/ARCHITECTURE.md` | Reverse-engineer it — properly. See the recipe below; a stack table and a folder list is a failed pass. |
| `specs/DESIGN.md` | Reverse-engineer it from the stylesheets, theme file or component library — real token values, not invented ones. **If the project has no interface, delete the file** rather than filling it with defaults. |
| `INDEX.md` | Write it last, once you know what the other files actually contain. |

### Reverse-engineering ARCHITECTURE.md — the part that goes wrong

The stack and the folder tree are the two cheapest facts in any repository, so a shallow pass always
stops there. They are also the two a reader could get for themselves in one command. **Gather them
first, then keep going.** The file's own *How deep to go* section lists the questions it has to answer;
this is where the answers live in a codebase.

| What you are looking for | Where it usually lives |
|---|---|
| The things this system deals with, and how they relate | Data models, schemas, migrations, type definitions. The tables and their foreign keys *are* the domain model. |
| Anything that moves through states, and who moves it | Status columns and their enums, constants named for states, the functions that write them, and any permission check guarding those writes. Reconstruct the machine — it is the most common thing missing. |
| What the system refuses to do | Validation, constraints, unique indexes, guard clauses, anything that raises or rejects. A refusal is as much a fact as an action. |
| What happens end to end | Entry points — routes, handlers, commands, jobs, event consumers — followed through one full path. End-to-end tests are usually the clearest description of a flow anyone has written down. |
| What it exposes and what it depends on | The public API surface, the events published and consumed, the external services called. |
| Terms an outsider would misread | Names that recur across modules and mean something specific to this domain. |

**This table is where to look, not what to call things.** Name the sections you write after the
project's own subject matter, never after a row of this table. How many sections, what they are called
and in what order is the agent's judgement, made per project.

Put the command beside a count. For anything a command cannot produce — a domain model, a lifecycle, a
rule — **cite the path you read it from**; a file path beside a state machine is as verifiable as a
`wc -l` beside a number. **Never drop a section just because no command produces it.** That is how the
expensive half of the file goes missing while the cheap half looks thorough. Where the code contradicts
the README or a comment, the code wins — and say so.

**Before you move on, re-read the six questions and check each one is answered.** If the file says what
the system is built *with* but not what it is *about*, it is not finished.

## Step 3 — infer the history, and label it as inferred

Only for an existing project. Git is the only record of what happened before kiacontext existed, and it
is a weak one — commit messages say what changed, almost never why.

```bash
git log --oneline --no-merges | head -100
git tag --sort=-creatordate | head -20
```

- **`logs/PROGRESS.md`** — group the history into a few coarse milestones, marked done. Short, high
  level, no acceptance criteria invented after the fact.
- **`logs/BRAINSTORM.md`** — only decisions the history makes genuinely visible: a dependency swapped, a
  module rewritten, an approach abandoned and replaced. Usually a handful. Skip anything that needs a
  reason the commits do not give.

**Both files open with this line, and every inferred entry says so:**

> **Reconstructed from git history on {{date}}, not captured from the work as it happened.** Treat it as
> approximate. Everything below this point was recorded live.

Numbering starts at M1 and D1 as normal — an inferred entry still owns its number permanently.

## Step 4 — ask the human, briefly, once

`GENESIS.md` and `MANIFESTO.md` cannot be reverse-engineered. Code shows what a project does, never why
it exists or what it must never do.

**Ask in one batch. Keep it to four or five questions. Offer to skip.** Something like:

- Why does this project exist — what happened that made it start?
- Who is it for?
- What is the one thing about it that must stay true?
- Is there anything it deliberately does *not* do?

Then write both files from the answers, in their words rather than yours. If they decline or answer
thinly, write what you have, leave the rest as placeholders, and move on — do not push. An empty section
is honest; an invented one is not.

Do not ask anything you could have found by reading the repository first.

## Step 5 — SEED.md

`SEED.md` holds the first prompts that started the project. For an existing project **those conversations
are gone and cannot be recovered.** Say so plainly and offer the choice: paste them if they still have
them somewhere, or delete the file.

Never reconstruct it. An invented first prompt is a fabricated historical record.

## Step 6 — finish

- Set every `last_updated` to today and every `covers` to something true.
- Write `INDEX.md`, including §7's link graph — **measure it with grep, do not guess it.**
- Delete every template file the project does not need, and every `> How to use this file` block from the
  ones it does.

## Step 7 — report

Tell the human, in a few lines:

- which files you filled, and from what;
- which are marked inferred;
- which are still placeholders and what you would need to finish them;
- **anything you decided not to write, and why** — a section you could not verify, a question you could
  not answer from the code. Narrowing the job quietly is the failure mode here; saying so is not;
- anything you found while reading that they may not know.
