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
covers: "Extensions phase, 2026-04-23 onward — D1 onward, O1 onward"
last_updated: "2026-09-11"
---

# 🧠 BRAINSTORM — Why we chose what we chose

> **D1–D11 were reconstructed from git history and `docs/` on 2026-09-11, not captured from the work as
> it happened.** Treat them as approximate. Where a document states the reasoning outright it is quoted;
> where only a commit exists, the entry says the reasoning is inferred. **D12 onward was recorded live.**

> **← Previous:** none. This is part one.
> **Next →** none yet. When this file is split, the pointer goes here and in the new part.

**Contents**

| § | |
|---|---|
| [What earns an entry](#what-earns-an-entry) | The test, before you write |
| [Decision log](#decision-log) | D1 onward |
| [Open questions](#open-questions) | O1 onward |

---

## What earns an entry

> **An entry earns its place when an alternative was rejected, or when a measurement changed our minds.**

Not every fix. Not every refactor. If an outsider would read it later and ask *"why was it done this
way?"*, write it; otherwise the commit message already covers it. Number permanently, date absolutely,
and always say what was **rejected** — that is the part that stops it being re-proposed in three months.

---

## Decision log

### D1 · Ship as tool-native files, not a plugin or a web app — 2026-04-23

**Considered:** marketplace plugins per vendor / a hosted web app first / plain files copied in by a shell installer
**Chose:** plain files, ReviewerOS-style installers
**Because:** `genesis/IDEA.md` §1 — *"Eliminate vendor lock-in and UI dependency… The system must live where the developers and researchers already work."*
**Rejected marketplaces because:** a per-vendor package is exactly the lock-in the project exists to remove.
**Rejected web-app-first because:** it rebuilds the proprietary interface being avoided. Designed in full (`genesis/IDEA.md` §8) and deferred to `src/backend` / `src/frontend`.
**Rule that follows:** MANIFESTO rule 1.

### D2 · One canonical source, generated adapters — 2026-04-23 (design) / 2026-05-08 (built)

**Considered:** maintain each tool's directory by hand / generate all of them from one source
**Chose:** generate
**Because:** `genesis/IDEA.md` §3.4 names drift as the known risk of the plain-files model. Fourteen hand-maintained copies of an eight-step protocol diverge silently.
**Rejected hand-maintenance because:** nothing errors when two adapters disagree; the user just gets a different review.
**Rule that follows:** ARCHITECTURE §7, and the Golden Rule in `AGENTS.md`.

### D3 · MCP exposes dumb tools only — 2026-04-23

**Considered:** rich tools (`fetch_literature` doing search + filter + dedup) / atomic stateless functions
**Chose:** atomic
**Because:** `genesis/IDEA.md` §3.3 — *"MCP is NEVER used for agentic logic, orchestration, or multi-step heuristics."* Deciding what to search and when to stop is the reasoning the paper is about; moving it into a server hides it.
**Rejected rich tools because:** they make the interesting half of the method invisible and untunable.
**Rule that follows:** MANIFESTO §7 (permanent no), ARCHITECTURE §9.

### D4 · Enforce paper hyperparameters structurally, not numerically — 2026-05-08

**Considered:** a config field for `k` and `N_QA` / enforce by required file structure
**Chose:** file structure — three round files must exist on disk
**Because:** host tools expose no hyperparameters to a slash command, and a model asked to "do three rounds" will report three rounds without doing three. A file that must exist cannot be hallucinated.
**Rejected config because:** there is nothing to configure — no process reads it.
**Cost accepted:** temperature 0.7 is simply unreachable and is documented as lost.
**Rule that follows:** ARCHITECTURE §4; `docs/KNOWN_LIMITATIONS.md` §7.

### D5 · Subagents where available, self-reflection where not — 2026-05-08

**Considered:** subagents only (drop unsupported tools) / self-reflection everywhere (uniform) / subagents with a documented fallback
**Chose:** the fallback, published as weaker
**Because:** `genesis/IDEA.md` §3.2 prefers real context isolation; dropping three tools would contradict D1.
**Rejected uniform self-reflection because:** it would degrade the 11 tools that can do it properly.
**Rejected silent fallback because:** presenting a weaker method as equivalent is the dishonesty MANIFESTO rule 7 exists to prevent.
**Measured:** 11 of 14 tools support subagents.
**Superseded in part by D16 (2026-09-11):** the decision stands, but the count does not — Antigravity gained
subagents, so it is 12 of 14 and the fallback covers only Mistral Vibe and OpenHands. Left as written
because it was true on 2026-05-08; read D16 for the current shape.

### D6 · `N_QA` 10 → user-configurable, default 2 — 2026-05-08

**Considered:** the paper's fixed 10 / a fixed lower number / user-chosen with a low default
**Chose:** user-chosen at `/5-osp-qa` start, default 2, persisted in `session.json`
**Because:** cost is criteria × pairs. A seven-criterion venue at 10 pairs is 70 subagent calls before the review is even written.
**Rejected fixed 10 because:** it made a first run prohibitively slow and expensive for a user evaluating the tool.
**Trade accepted:** a departure from the paper, so the step now prints the multiplication and a guide (2 quick / 5 thorough / 10 exhaustive) and lets the user choose.
**Commit:** `dd5ac6f`.

### D7 · One literature round per invocation — 2026-05-08

**Considered:** all three rounds in one command / one round per invocation with a progress banner
**Chose:** one per invocation
**Because:** three rounds is 25–35 tool calls and several minutes with no output; users could not tell it apart from a hang.
**Rejected all-at-once because:** it hid progress and gave no point to inspect a round before the next.
**Commit:** `7b60b3a`.

### D8 · Self-contained venv per project, not PyPI — 2026-05-08

**Considered:** publish `osp-mcp` to PyPI / build a venv in the user's project
**Chose:** per-project venv at `.open-scholar-peer/mcp/`
**Because:** nothing to install globally, nothing to keep in step with a release, and the server version always matches the adapter that was installed with it.
**Rejected PyPI because:** it adds a global dependency and a release cadence to a project whose whole pitch is "run it with what you already have". Still listed as deferred, not refused.

### D9 · arXiv via the official package, not raw HTTP — 2026-05-08

**Considered:** hand-rolled HTTP against the arXiv API / the `arxiv` Python package
**Chose:** the package
**Because:** rate limiting and result paging are handled correctly rather than approximately.
**Commit:** `473b7a1`. *Reasoning inferred from the commit message; no document records it.*

### D10 · Drop the `_osp_managed` marker from merged MCP configs — 2026-05-08

**Considered:** keep a marker key so the installer knows which entries it owns / drop it
**Chose:** drop it
**Because:** a measurement changed our minds — the extra key failed Gemini CLI's config validation and broke the tool outright.
**Consequence accepted:** ownership tracking moved to a sidecar file rather than an inline key.
**Commit:** `cdda9dd`.

### D11 · Per-call timeout 30s → 90s — 2026-05-10 → 2026-06

**Considered:** 30s / 90s / no timeout
**Chose:** 90s, overridable via `OSP_CALL_TIMEOUT` in `.env`
**Because:** real Semantic Scholar and Google Scholar calls exceeded 30s often enough that the timeout was the failure, not the API.
**Rejected no timeout because:** one hung HTTP call wedges a stdio server with no way for the user to see why.
**Commits:** `7e58e90`, `a184822`, `c26a091`.

### D12 · Adopt kiacontext as the project's memory — 2026-09-11

**Considered:** keep everything in `docs/` and `AGENTS.md` / add a context harness beside them
**Chose:** the harness, with `docs/` kept as the human-facing layer
**Because:** `docs/` records *what* was built and `AGENTS.md` records *how to work on it*, but nothing recorded *why* — five months of decisions existed only in commit messages, and commit messages do not say what was rejected.
**Rejected docs-only because:** `docs/PHASES.md` had already gone stale in exactly this way — every phase ticked at the top, every underlying deliverable checkbox left unticked.
**Rule that follows:** none yet; this is process, not product.

### D13 · Phase 1 stays sequential, not parallel — before 2026-07-31

**Considered:** run Summary, Literature, Historian and Baseline Scout concurrently / keep them sequential
**Chose:** sequential
**Because:** simplicity and fidelity to the method. The paper's Phase 1 is drawn as two parallel tracks, so the parallel version is the more faithful reading of the diagram — but Historian consumes the Literature corpus and the Scout leans on it too, so only part of it is genuinely parallelisable.
**Rejected parallel because:** the sequencing is also what gives the user a point to stop and read each artifact, which later became MANIFESTO rule 6.
**Status:** deferred, not refused.
**Source:** recorded only in `docs/PHASES.md` "Out of Scope"; carried here on 2026-09-11 when that file was retired, otherwise it would have been lost.

### D14 · Retire `IDEA.md` and `PHASES.md` from `docs/` — 2026-09-11

**Considered:** keep both in `docs/` / delete both outright / move the origin document into the harness and delete the build plan
**Chose:** `docs/IDEA.md` → `kia-context/genesis/IDEA.md` (frozen); `docs/PHASES.md` deleted
**Because:** `docs/` is for people using and contributing to the project — contracts, layout, limitations, troubleshooting. Those two were *input context* for building it, which is what the harness is for. `IDEA.md` is cited as provenance ~20 times across `kia-context/` and stays live so those citations remain checkable; `PHASES.md` is fully superseded by `logs/PROGRESS.md`.
**Rejected deleting IDEA too because:** it would leave every provenance citation pointing at a file you can only recover with `git show`, which is the sort of friction that gets a citation ignored rather than followed.
**Rejected keeping both because:** `PHASES.md` had already gone stale in the way D12 describes, and a second, competing progress tracker beside `PROGRESS.md` would go stale again.
**Consequence:** the release procedure in `AGENTS.md` now updates `PROGRESS.md` instead of `PHASES.md` checkboxes.

### D15 · Commit the kiacontext skills so cloners get them — 2026-09-11

**Considered:** leave the per-tool skill installs local and gitignored (the repo's existing convention for root tool directories) / commit them
**Chose:** commit `skills/kia-context-*/` under `.claude/`, `.agents/`, `.opencode/` and `.hermes/`
**Because:** the harness is only useful if the agent working in a clone can actually run `/kia-context-sync`. Making every contributor install it separately means most will not, and the context files rot.
**Rejected committing the whole of `/.agents/` because:** it also holds a locally-installed copy of the OSP Antigravity-CLI adapter, which duplicates `extensions/.agents/` and would drift against it silently. Only the kiacontext skills are tracked; the rest of each tool directory stays ignored.
**Rule that follows:** none — this is repository hygiene, not product.

### D16 · Antigravity moves from self-reflection to subagents — 2026-09-11

**Considered:** leave the classification alone / flip the capability flag / flip it *and* ship custom subagent definition files under `.agents/agents/`
**Chose:** flip the flag, and treat Antigravity exactly like the other subagent-capable tools
**Because:** Antigravity 2.0 documents an asynchronous subagent framework — `invoke_subagent`, custom subagents at `.agents/agents/<name>.md`, an `/agents` panel, a 10-level nesting cap. The old classification was not a preference, it was a fact that expired, and while it stood every Antigravity user got the documented *weaker* Q&A phase (D5) for no reason.
**Rejected leaving it because:** self-reflection is a substitute, not an equivalent — MANIFESTO rule 7.
**Rejected shipping custom subagent files because:** no other tool has them. OSP's personas are skills, and a tool-specific agent-definition format would be a new artifact type for the sync script to produce and keep in parity. Parity with the other 13 *is* the fix here. Noted as O8 instead.
**Measured:** subagent-capable tools 11 → 12 of 14; self-reflection now covers only Mistral Vibe and OpenHands. Blast radius before starting: 14 files carried the claim, 8 of them canonical or code.
**Rule that follows:** none new — ARCHITECTURE §4 and `docs/KNOWN_LIMITATIONS.md` §1 updated in place.

---

## Open questions

> Noticed and deliberately not decided. Raised again later, never silently dropped.

| | Question | Raised | State |
|---|---|---|---|
| **O1** | Four commands repeat "The skill writes `<artifact>`" as two consecutive numbered steps (`1-osp-summary` 4–5, `3-osp-historian` 5–6, `4-osp-baseline-scout` 6–7, `6-osp-review` 5–6). Looks like a bad edit synced to all 14 adapters. Cosmetic, or does it cause a double write? | 2026-09-11 | open |
| **O2** | `6-osp-review.md` prerequisites still require "all `05_qa_<slug>.md` files exist with **10 pairs** each" — stale since D6 made the count configurable. User-visible: the step may refuse a valid session. | 2026-09-11 | open |
| **O3** | `.brain-template/session.json` never declares `phases.literature.rounds_completed`, which `2-osp-literature.md` reads. Works by defaulting to 0; should the schema declare it? | 2026-09-11 | open |
| **O4** | Kiro's adapter maps commands to `hooks/` while every other tool uses a commands-like directory (`sync_adapters.py`, `ToolCaps` for `kiro`). Deliberate, or a mistake nobody has run into? | 2026-09-11 | open |
| **O5** | The live end-to-end run on a real paper is marked done (`b8aa4df`) but no artifact records its result. Should a reference run be committed as evidence? | 2026-09-11 | open |
| **O6** | Cascading invalidation — re-running an early phase leaves downstream artifacts stale with no warning (`KNOWN_LIMITATIONS.md` §8). Deferred, not solved. | 2026-09-11 | open |
| **O7** | Drift between `_shared/` and the adapters is caught only when someone remembers to run `--check`. A pre-commit hook or CI job was scoped and deferred. | 2026-09-11 | open |
| **O8** | Antigravity supports *custom* subagent definitions (`.agents/agents/<name>.md`, YAML frontmatter with `tools`, `model`, `commandExecutionPolicy`). Should `osp-answer-generator-agent` ship as a real one there, rather than relying on the host to route a skill? It would tighten the Q&A isolation, but it is a tool-specific artifact type no other adapter has. See D16. | 2026-09-11 | open |
| **O10** | `scripts/test_install.sh` merged throwaway `/tmp` paths into the developer's real global MCP configs on every run, for six installers, since the smoke test was written. Fixed by redirecting `HOME` — but nothing stops the next test harness from doing the same. Should running any `install_*.sh` outside a sandbox be made harder? | 2026-09-11 | open |
| **O9** | A tool's capability can expire without anyone noticing — Antigravity's did, and OSP shipped the weaker Q&A path for months (D16). Nothing re-checks the capability matrix against vendor docs. Is that worth automating, or is it inherently a human job? | 2026-09-11 | open |

---

> **← Previous:** none.
> **Next →** none yet.
