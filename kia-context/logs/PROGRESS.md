---
description: >
  The execution log and the working memory of the project. Milestones, their deliverables, the acceptance
  criteria each one is judged against, and a short report written when each is done. This is the file an
  agent opens first every session to find out what to build next, and the file it writes to when the
  build moves. Append-only and chronological.
  NOT here: why a choice was made (BRAINSTORM.md), or any rule that outlives the milestone
  (MANIFESTO.md / ARCHITECTURE.md).
authority: state
writes: agent, every session
status: active
covers: "{{phase name}}, {{YYYY-MM-DD}} onward — M1 onward"
last_updated: "{{YYYY-MM-DD}}"
---

# 📈 PROGRESS — What we are building

> **The layout below is a sample, not a requirement.** Keep it, drop it, reorder it, or replace it
> entirely with whatever this project actually needs — you are not filling in a form, and an empty
> section is worse than a missing one. The one thing that must **not** change is the frontmatter above:
> those six fields are what make this file part of kiacontext.

> **← Previous:** none. This is part one.
> **Next →** none yet. When this file is split, the pointer goes here and in the new part.

**Contents**

| § | |
|---|---|
| [The loop](#the-loop) | How a deliverable gets done |
| [Circuit breakers](#circuit-breakers) | What happens when it does not |
| [Milestones](#milestones) | The table |

> Add a row here per milestone as it is opened.

---

## The loop

1. Take the first unchecked deliverable (`- [ ]`) under the active milestone.
2. Build it. Verify it against its **acceptance criteria**.
3. **Pass:** mark `[x]`, write a one or two sentence **Report**, move on.
4. **Fail:** apply the circuit breakers. Do **not** mark `[x]`.

## Circuit breakers

- **Three attempts.** Three consecutive failed verification passes on one deliverable and you stop.
- **Then:** revert the uncommitted work, mark the deliverable `[BLOCKED]`, write one paragraph on what
  was tried and what it did, and halt for a human.
- **No tampering, ever.** Never modify a test, a verifier or an acceptance criterion to force a pass.
  If a criterion is genuinely wrong, say so in the report and leave it failing until a human changes it.
- **Never fake progress.** A blocked deliverable that is honest is worth more than a ticked one that lies.

---

## Milestones

| | Milestone | Done when | Depends on | Status |
|---|---|---|---|---|
| **M1** | {{name}} | {{the one sentence that decides it}} | — | ⬜ Not started |
| **M2** | {{name}} | {{…}} | M1 | ⬜ Not started |

> **Numbering never restarts.** When this file is split, part two continues at the next M.

---

## 🏁 Milestone M1: {{Title}}

**Target.** {{One or two sentences. What is true when this is done that is not true now.}}

### Deliverables

- [ ] **{{Thing built}}** — {{one line of detail}}
- [ ] **{{Thing built}}** — {{one line of detail}}

### Acceptance criteria

> Each one must be checkable by somebody who did not build it. *"Works well"* is not a criterion;
> *"filtering by a state yields exactly the rows carrying that state"* is.

1. {{criterion}}
2. {{criterion}}

**Depends on:** {{M0 / nothing}}. **Issue:** {{#n}}.

### Report — {{YYYY-MM-DD}}

> Written when the milestone closes. One or two paragraphs. What was actually built, what surprised us,
> and any number you measured — never a number you estimated. If something was left out, say so here
> rather than quietly dropping it.

---

> **← Previous:** none.
> **Next →** none yet.
