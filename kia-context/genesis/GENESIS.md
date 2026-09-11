---
description: >
  Why this project exists. Captures the catalyst and the inception rationale at t=0 — the spark, the
  business problem, the people, and what success was supposed to look like before any code was written.
  Read it when a decision stops making sense and you need to know what the project was originally for.
  NOT here: how it is built (ARCHITECTURE.md), what it must never do (MANIFESTO.md), or anything decided
  after the project started (BRAINSTORM.md).
authority: background
writes: agent, at t=0 — rarely after
status: frozen
covers: "t=0, 2026-04-23"
last_updated: "2026-09-11"
---

# 🌱 GENESIS — Why this project exists

> **Written on 2026-09-11, five months after t=0.** The opening conversation was not captured. This file
> was reconstructed from `IDEA.md` (which self-describes as the project's "Master Seed Document"),
> `docs/paper/SUMMARY.md`, the git history from 2026-04-23, and a statement of intent from the project
> owner. Where a claim came from the owner rather than from a file in this repository, it says so.

**Contents**

| § | |
|---|---|
| [1](#1-the-parties) | The parties |
| [2](#2-the-catalyst) | The catalyst |
| [3](#3-the-problem-in-one-page) | The problem, in one page |
| [4](#4-what-success-looked-like-at-t0) | What success looked like at t=0 |
| [5](#5-constraints-that-existed-before-any-code) | Constraints that existed before any code |
| [6](#6-what-we-deliberately-did-not-do) | What we deliberately did not do |

---

## 1. The parties

| Party | Who |
|---|---|
| **Client / user** | Researchers who review papers — programme-committee members, area chairs, and graduate students carrying a review load. People who already pay for an AI coding tool. |
| **Us** | A community implementation, built in the open by the repository owner. **Not affiliated with the paper's authors or with Google** — stated explicitly in `README.md`. |
| **Owner** | The repository owner decides scope. |

## 2. The catalyst

Google published *ScholarPeer: A Context-Aware Multi-Agent Framework for Automated Peer Review*
(arXiv 2601.22638 — Goyal, Parmar, Song, Palangi, Pfister, Yoon). The paper describes a seven-agent
protocol that fixes the failure mode every other LLM reviewer shares, and reports it working.

Per the project owner, the method is not merely a paper result: its components are used in **PAT
(Peer-review Assistant Tool)** at Google, deployed at **ICML and NeurIPS in 2026**. So the protocol is
state of the art *and* battle-tested at the venues whose reviewers would most want it.

**And there was no way to run it.** A paper describes a method; it does not ship one. This project is a
paper-to-code implementation: take a published, proven protocol and make it executable by the people it
was designed for.

> *Not independently verified by the agent:* the PAT / ICML / NeurIPS 2026 deployment claim comes from
> the owner, not from a document in this repository. The repository's own `README.md` attributes the
> paper to Google; the owner referred to it as Google DeepMind.

## 3. The problem, in one page

A reviewer sitting down with an unfamiliar submission has to answer questions that reading the paper
cannot answer: *Is this actually new? Which obvious baseline is missing? Has someone already published
this three months ago?*

Asking a general-purpose LLM does not help, because of what the paper calls the **parametric vacuum**.
The model evaluates the submission against frozen training data. It has no live picture of the field, so
it produces a fluent summary and a confident, wrong verdict on novelty — precisely the judgement the
reviewer needed help with, and the one place a plausible-sounding answer does real damage.

The tools that *do* address this were the second half of the problem. They arrive as someone else's web
application: a new subscription, a new interface, an upload box for a manuscript that is often
confidential and under embargo, and no way to see how a conclusion was reached.

Meanwhile the reviewer already has an AI agent — one they pay for, that runs on their machine, reads
their files, and calls tools. The capability was already bought and sitting idle. Nothing connected it
to the method.

## 4. What success looked like at t=0

From `IDEA.md`, written at the start:

> *"Eliminate vendor lock-in and UI dependency. Users must be able to leverage this methodology using
> their own API keys, local LLMs, or existing agentic environments without being forced into a specific
> subscription or proprietary web interface. The system must live where the developers and researchers
> already work."*

Concretely, at t=0 success meant: a researcher runs one install script in the directory holding their
paper, then drives the full seven-step protocol with slash commands inside whichever AI tool they
already use — and every intermediate artifact lands on their disk as readable markdown they can check.

## 5. Constraints that existed before any code

These were fixed before the first commit and explain most of what followed.

| Constraint | Where it came from |
|---|---|
| **No marketplace plugins as the packaging model.** Plain files copied in by a shell installer. | `IDEA.md` §1.1C — locked scope decision. Marketplaces are per-vendor, and a vendor-specific package is the lock-in the project exists to avoid. |
| **Must run inside tools that already exist**, with no control over their internals — no access to temperature, sampling, or the model itself. | The delivery model. It is why the paper's hyperparameters are enforced by *file structure* rather than configuration. |
| **MCP is for atomic, stateless functions only** — never orchestration or multi-step heuristics. | `IDEA.md` §3.3. The cognitive work belongs to the agent; the server only fetches. |
| **One manager agent that swaps persona**, rather than a fleet of hardcoded agents — with real subagents used wherever the host tool supports them. | `IDEA.md` §3.1–3.2. |
| **The `.brain/` state-directory pattern**, adopted from the prior `reviewer-os` project. | `IDEA.md` §10.2. |
| **Manuscripts are confidential.** Working state is gitignored from the first commit. | `.gitignore`, commit `5d0688e`. |

## 6. What we deliberately did not do

Cut on day one, and still cut:

- **The web application.** `IDEA.md` §8 specifies a full standalone app — DeepAgents JS backend, a
  forked Deep Agents UI frontend with a phase stepper. It was scoped, designed, and then explicitly
  deferred to `src/backend` / `src/frontend` in a later phase. Shipping it first would have rebuilt the
  proprietary web interface the project exists to avoid.
- **Publishing the MCP server to PyPI.** Each project gets a self-contained venv instead. One less thing
  a user must install globally or keep in step with a release.
- **Multi-paper sessions.** One paper per `.brain/`. Reviewing a second paper means a second directory.
- **Any agentic logic inside MCP.** Named as a temptation and refused up front.
