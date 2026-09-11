---
description: >
  The decision log. A chronological record of investigations, analysis and conversations between the
  human and the agent, and the decisions they produced. It exists so that months later anyone can read
  it and see that on a given date we considered three options, chose the second, and why — the
  traceability of how the project got its shape. Append-only, dated, numbered, and deliberately terse.
  NOT here: the resulting rule itself (that goes to MANIFESTO.md or ARCHITECTURE.md), the work done
  (PROGRESS.md), or a write-up of every fix — see the entry test below.
authority: background
writes: agent, whenever a decision is made
status: active
covers: "{{phase name}}, {{YYYY-MM-DD}} onward — D1 onward, O1 onward"
last_updated: "{{YYYY-MM-DD}}"
---

# 🧠 BRAINSTORM — Why we chose what we chose

> **The layout below is a sample, not a requirement.** Keep it, drop it, reorder it, or replace it
> entirely with whatever this project actually needs — you are not filling in a form, and an empty
> section is worse than a missing one. The one thing that must **not** change is the frontmatter above:
> those six fields are what make this file part of kiacontext.

> **← Previous:** none. This is part one.
> **Next →** none yet. When this file is split, the pointer goes here and in the new part.

**Contents**

| § | |
|---|---|
| [What earns an entry](#what-earns-an-entry) | The test, before you write |
| [How to write one](#how-to-write-one) | The format |
| [Decision log](#decision-log) | D1 onward |
| [Open questions](#open-questions) | O1 onward |

---

## What earns an entry

**Most things do not.** A decision log that records every fix becomes unreadable, and an unreadable log
is the same as no log. Before appending, apply the test:

> **An entry earns its place when an alternative was rejected, or when a measurement changed our minds.**

That is the whole filter. In practice:

| Write it down | Do not |
|---|---|
| We considered three approaches and picked one | We fixed a bug |
| A measurement contradicted what we assumed | A test went green |
| A rule changed, or gained an exception | A refactor with no choice in it |
| We chose a library, a pattern, a boundary | Routine work already in `PROGRESS.md` |
| We reversed an earlier decision | A conversation that reached no decision |

The question to ask: **would an outsider read this later and ask "why was it done this way?"** If yes,
write it. If not, the commit message already covers it.

## How to write one

**Short. A diagram or a three-row table beats a paragraph.** These entries are read by an agent with a
budget, and a 400-word entry costs more than it teaches.

- Number it. `D1`, `D2`, … Numbers are **permanent** — they get cited from code comments and from other
  documents. Append; strike through rather than delete. Never renumber.
- Date it. Absolute dates, never "last week".
- Say what was **rejected**, not only what was chosen. The rejected option is the part that stops
  somebody re-proposing it in three months.
- If a measurement decided it, **give the number and the command that produced it.**

```markdown
### D7 · {{The decision, as a short claim}} — {{YYYY-MM-DD}}

**Considered:** {{option A}} / {{option B}} / {{option C}}
**Chose:** {{B}}
**Because:** {{one or two sentences, or a table, or a diagram}}
**Rejected {{A}} because:** {{one line}}
**Measured:** {{the number, and the command}}
**Rule that follows:** {{where it landed — MANIFESTO rule n, ARCHITECTURE §n, or none}}
```

---

## Decision log

### D1 · {{The decision}} — {{YYYY-MM-DD}}

{{Use the shape above. Delete the fields that do not apply — an entry with three real lines beats one
with six empty ones.}}

---

## Open questions

> Things we noticed and deliberately did not decide. Each one is raised again later, not silently
> dropped. Numbered `O1` onward, same permanence rule.

| | Question | Raised | State |
|---|---|---|---|
| **O1** | {{the question, in one sentence}} | {{YYYY-MM-DD}} | open |

---

> **← Previous:** none.
> **Next →** none yet.
