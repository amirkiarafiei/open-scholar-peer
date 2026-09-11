---
description: >
  The product boundary and the North Star. A short, numbered list of rules that may not be traded away
  for speed, cost or convenience, plus what this product is and is explicitly NOT. Every agent reads it
  before proposing a feature, and code cites its rules by number.
  Written in plain English for a human reader — no jargon, no framework names, no implementation words.
  If a sentence needs the reader to know the stack, it belongs in ARCHITECTURE.md.
  NOT here: how anything is built, why a rule was chosen (that is BRAINSTORM.md), or a roadmap.
authority: law
writes: agent, from what the human decided
status: active
covers: the whole product
last_updated: "{{YYYY-MM-DD}}"
---

# 📜 MANIFESTO — What we are building, and why

> **The layout below is a sample, not a requirement.** Keep it, drop it, reorder it, or replace it
> entirely with whatever this project actually needs — you are not filling in a form, and an empty
> section is worse than a missing one. The one thing that must **not** change is the frontmatter above:
> those six fields are what make this file part of kiacontext.

**Contents**

| § | |
|---|---|
| [1](#1-one-sentence) | One sentence |
| [2](#2-the-north-star) | The North Star |
| [3](#3-what-it-does) | What it does |
| [4](#4-who-it-is-for) | Who it is for |
| [5](#5-non-negotiable-rules) | Non-negotiable rules |
| [6](#6-what-this-is-not) | What this is NOT |
| [7](#7-boundaries-on-scope-creep) | Boundaries on scope creep |

---

## 1. One sentence

**{{What this is, in one sentence a stranger would understand. If it takes two, it is not clear yet.}}**

## 2. The North Star

> **{{The one thing that must stay true. Everything else is negotiable.}}**

> Two or three sentences on why this is the North Star and what breaks if it stops being true.

## 3. What it does

> Three to six lines, in the order a user experiences them. Plain verbs.

## 4. Who it is for

| Reader | What they need from it |
|---|---|
| {{role}} | {{what they come here to do}} |
| {{role}} | {{what they come here to do}} |

## 5. Non-negotiable rules

These may not be traded away for speed, cost, or output quality.

> A rule that describes **how the system is built** belongs in `ARCHITECTURE.md`, even when it sounds
> like a business rule. See *Where a finding goes* in `AGENTS.md` for the split.

> **Numbering is permanent.** These rules get cited from code comments as `MANIFESTO rule 4`. Renumbering
> breaks every citation and nothing errors. **Append. Strike through rather than delete.**
>
> **Write them in plain English.** A rule a non-technical owner cannot read is a rule nobody enforces.
> Say what must be true and what happens if it is not — not how it is implemented.

1. **{{Short bold claim.}}** {{Two or three sentences: what must be true, and what breaks if it is not.}}
2. **{{Short bold claim.}}** {{…}}
3. **{{Short bold claim.}}** {{…}}

## 6. What this is NOT

> The nearby things people will mistake it for, listed and denied. This section prevents more scope creep
> than section 7 does, because it names the specific wrong idea rather than a general principle.

- **Not {{a thing it resembles}}.** {{One line on why not.}}
- **Not {{a thing it resembles}}.** {{One line on why not.}}

## 7. Boundaries on scope creep

> What would have to be true before this product grew in a given direction. One line each. If a proposal
> does not clear one of these, it is a no, and the reasoning goes in `BRAINSTORM.md` rather than here.
