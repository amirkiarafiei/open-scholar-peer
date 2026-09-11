---
description: >
  The first prompts that started this project, lightly cleaned up but honest to what was actually typed.
  Written once, at the beginning, and almost never touched again. It exists so that later — when the
  project has drifted a long way from where it began — anyone can see the shape of the original ask.
  NOT here: rationale (that is GENESIS.md), decisions (BRAINSTORM.md), or anything added after week one.
authority: background
writes: agent, at t=0 — effectively never again
status: frozen
covers: "the first session, 2026-04-23 — not recovered"
last_updated: "2026-09-11"
---

# 🌰 SEED — The first prompts

## The prompts were not captured

This harness was installed on 2026-09-11, five months after the project started on 2026-04-23. The
conversations that opened it were not recorded anywhere in this repository, and the owner confirmed they
are not available.

**They have not been reconstructed, and must not be.** An invented first prompt is a fabricated
historical record — it would read exactly like a real one and there would be no way to tell. An empty
section here is honest; a plausible one would not be.

**If they still exist somewhere** — a chat history, a notes file, an email — paste them in and delete this
block. Otherwise leave the file as it is, or delete it.

## The closest surviving artifact

`IDEA.md` is the nearest thing. It was committed on 2026-04-27 (`74e54a6`, "docs: add IDEA") and
subtitles itself **"Master Seed Document"**. It is not a prompt — it is already a worked-up design
document, written after the thinking had happened — but it is the earliest record of intent in the
repository, and it carries the locked scope decisions verbatim:

> *"The Core Philosophy: Eliminate vendor lock-in and UI dependency. Users must be able to leverage this
> methodology using their own API keys, local LLMs, or existing agentic environments without being forced
> into a specific subscription or proprietary web interface. The system must live where the developers
> and researchers already work."*

Read it as the project's opening statement of intent, with the caveat that it is a second draft of one,
not the first thing that was typed.

## What we already knew going in

Reconstructed from `IDEA.md` and the first five commits, not from the original session:

- The method was already chosen. The paper (`docs/paper/scholar_peer_arxiv.pdf`) was committed on
  2026-04-23 in the second commit of the repository, before any design document — so the work began from
  a specific published protocol, not from a general wish to automate reviewing.
- `reviewer-os` was the reference implementation to imitate structurally. The `.brain/` pattern and the
  installer-copies-plain-files model both come from it.
- The 14-tool target did not exist yet. `IDEA.md` §1.1B locks the list at **five** tools — Cursor,
  Claude Code, Antigravity, Copilot, Gemini CLI. Nine more were added later.

## What we did not know yet

- How Cursor's MCP configuration worked. `IDEA.md` §10.3 lists it as the one *"open verification
  item"* and says to keep the adapter marked experimental until confirmed.
- Whether the paper's hyperparameters could be honoured at all inside a host tool. They could not, in the
  end — see D4 in `BRAINSTORM.md`.
- That the install path, not the protocol, would absorb most of the debugging effort. Roughly half of
  M6's commits are installer and config-merge fixes against real machines.
