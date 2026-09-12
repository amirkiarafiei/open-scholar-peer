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
last_updated: "2026-09-12"
---

# 📜 MANIFESTO — What we are building, and why

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

**Open ScholarPeer lets a researcher run Google's published ScholarPeer peer-review protocol inside the
AI tool they already pay for, and read every step of its reasoning on their own disk.**

## 2. The North Star

> **A reviewer runs the whole method with the tools and subscriptions they already have — and can check
> every conclusion it reaches.**

Both halves are load-bearing. Drop the first and this becomes another product to buy, which is the thing
it was built to replace. Drop the second and it becomes a machine that hands down verdicts on other
people's work with no way to tell whether they are sound — which, in peer review, is worse than useless.

## 3. What it does

1. Installs into the directory holding the paper, for whichever AI tool the reviewer uses.
2. Asks which venue the review is for, and fetches that venue's real reviewing criteria.
3. Reads the paper and extracts its claims, its method, and the evidence offered for them.
4. Searches the live literature in three passes, then builds a history of the sub-field from what it found.
5. Hunts, adversarially, for baselines and datasets the authors should have compared against and did not.
6. Interrogates the paper criterion by criterion, verifying each answer against what it retrieved.
7. Writes one review in the venue's own format, drawn only from the evidence gathered in the steps above.

Every step writes a file the reviewer can open, and stops so they can read it.

## 4. Who it is for

| Reader | What they need from it |
|---|---|
| **A reviewer with a stack of submissions** | A rigorous first pass that catches the missing baseline and the concurrent pre-print they would not have found, in the format their venue expects. |
| **An author before submitting** | The adversarial review their paper is about to get, while there is still time to answer it. |
| **A researcher studying automated review** | A faithful, legible implementation of a published protocol, with every intermediate artifact kept. |
| **A contributor** | One place to edit that reaches every supported tool at once. |

## 5. Non-negotiable rules

These may not be traded away for speed, cost, or output quality.

> **Provenance of these rules.** Rules 1–5 and 8 are stated outright in `genesis/GENESIS.md`, `AGENTS.md`,
> `extensions/_shared/rules/osp-rules.md` or the skill files, and are quoted from there. Rules 6, 7 and 9
> are the agent's reading of behaviour the system already enforces everywhere, written down here for the
> first time on 2026-09-11 — **confirm them with the owner before treating them as settled law.**

1. **The user's existing tools are the whole delivery mechanism.** Open ScholarPeer never requires a
   subscription, an account, a hosted service, or a vendor's marketplace to run the protocol. It ships as
   plain files copied into the user's project. If a feature only works through one vendor's storefront,
   it does not ship.

2. **The published method is the specification.** The seven steps, their order, and their separation are
   what the protocol's results rest on. Steps are not silently merged, skipped, reordered, or "optimised"
   into one pass. Where the implementation must depart from the paper, it is written down as a known
   limitation rather than quietly absorbed.

3. **Every claim is auditable on the user's disk.** Each step writes plain markdown recording what it
   did, what it produced, and where that came from. A reviewer must always be able to ask "why does it
   say that?" and get an answer from a file. No black box.

4. **Never invent a citation.** Every paper referenced in a review traces back to something actually
   retrieved. A fabricated reference in a peer review is the single most damaging thing this system could
   produce, and no amount of fluency compensates for it.

5. **The manuscript stays the user's.** Working state lives in a directory that is gitignored from the
   moment it is created, because it holds a paper that is usually confidential and often under embargo.
   Nothing leaves the machine except to the search tools the user configured.

6. **The human decides when to advance.** The system stops at every phase boundary so the user can read
   what it just produced. It never chains the whole protocol together unattended. The pauses are the
   product, not friction to be smoothed away.

7. **Every supported tool runs the same protocol.** A review produced in one tool and a review produced
   in another differ in the model behind them, never in the method. Where a tool genuinely cannot support
   part of the protocol, the substitute is documented as weaker rather than presented as equivalent.

8. **Fail loudly; never degrade in silence.** When an input is missing or a search tool is unreachable,
   the system says so and stops, or records the gap in the artifact. It never produces a thinner result
   that looks like a complete one.

9. **It drafts; the reviewer signs.** The output is a draft for a human reviewer to interrogate, edit and
   take responsibility for. Open ScholarPeer does not submit reviews, does not decide, and is not a
   substitute for the person whose name goes on it.

## 6. What this is NOT

- **Not an automated reviewer.** It does not replace the human judgement at the end of the process. See
  rule 9.
- **Not a web app or a SaaS.** A standalone application was designed at the outset and deliberately
  deferred. Building it first would recreate exactly the hosted interface this project exists to avoid.
- **Not a plugin for one vendor.** Marketplace packaging was considered and refused as the primary model.
- **Not a paper summariser.** Summarising is step 1 of 7, and on its own it is the shallow output that
  motivated the paper in the first place.
- **Not affiliated with the ScholarPeer authors or with Google.** It is a community implementation of a
  published method, and says so wherever it is cited.

## 7. Boundaries on scope creep

What would have to be true before the product grew in a given direction:

- **A new AI tool** — it can host both per-command prompts and always-on instructions, and the full
  protocol survives the translation. If the Q&A step cannot run with isolation, the tool is still
  supportable, but the gap is published alongside it.
- **A new literature source** — it exposes a stable interface, credentials are the user's own, and it
  fits as an atomic search function. A source that needs orchestration to be useful does not qualify.
- **Anything clever inside the search layer** — no. Deciding what to search and when to stop is the
  agent's work, permanently.
- **The standalone web application** — only once the installable version is stable and only if a user can
  still run everything locally with their own keys. It may not become the primary way to use the product.
- **Automating across phase boundaries** — only with explicit opt-in per run, and never as the default.
