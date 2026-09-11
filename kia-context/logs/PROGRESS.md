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
covers: "Extensions phase, 2026-04-23 onward — M1 onward"
last_updated: "2026-09-11"
---

# 📈 PROGRESS — What we are building

> **M1–M7 were reconstructed from git history and `docs/PHASES.md` on 2026-09-11, not captured from the
> work as it happened.** Treat them as approximate: the commits say what changed, rarely why, and the
> acceptance criteria shown are the ones `docs/PHASES.md` recorded at the time, not invented afterwards.
> **Everything from M8 onward was recorded live.**

> **← Previous:** none. This is part one.
> **Next →** none yet. When this file is split, the pointer goes here and in the new part.

**Contents**

| § | |
|---|---|
| [The loop](#the-loop) | How a deliverable gets done |
| [Circuit breakers](#circuit-breakers) | What happens when it does not |
| [Milestones](#milestones) | The table |
| [M8](#-milestone-m8-installer-improvements--context-harness) | The active milestone |

---

## The loop

1. Take the first unchecked deliverable (`- [ ]`) under the active milestone.
2. Build it. Verify it against its **acceptance criteria**.
3. **Pass:** mark `[x]`, write a one or two sentence **Report**, move on.
4. **Fail:** apply the circuit breakers. Do **not** mark `[x]`.

**In this project, "verify" has a fixed meaning for any change under `extensions/_shared/`:**

```bash
python3 scripts/sync_adapters.py     # regenerate the 14 adapters
python3 scripts/test_parity.py       # must pass
bash scripts/test_install.sh         # must pass before tagging a release
```

A change to canonical content that has not been synced is not done, however correct the source file is.

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
| **M1** | Foundation — paper, idea, contracts, schema | The protocol is specified on paper: brain layout, artifact contracts, `session.json` v2 | — | ✅ Done 2026-05-08 |
| **M2** | Canonical `_shared/` content | 8 commands, 8 skills, rules and templates authored and self-consistent | M1 | ✅ Done 2026-05-08 |
| **M3** | Consolidated MCP server | One server exposing arXiv, Semantic Scholar and Google Scholar as atomic tools | M1 | ✅ Done 2026-05-08 |
| **M4** | Sync engine and installers | One canonical source generates every adapter; installers wire MCP per tool | M2, M3 | ✅ Done 2026-05-08 |
| **M5** | Validation and first release | Parity and install smoke tests pass; docs complete | M4 | ✅ Done 2026-05-09 · `v1.0.0` |
| **M6** | Hardening | The install path survives real machines and real config files | M5 | ✅ Done 2026-05-10 · `v1.1.0` |
| **M7** | Scale-out and UX | 5 tools → 14; phase orientation, resource warnings, configurable Q&A | M6 | ✅ Done 2026-07-31 |
| **M8** | Installer improvements + context harness | The installer work the owner opened `feat/improve-installer` for is done, and the harness is filled | M7 | 🔵 Active |

> **Numbering never restarts.** When this file is split, part two continues at the next M.

---

## ✅ M1–M7 — reconstructed summary

*Measured: `git rev-list --count 453a3d5` → 66 commits, `4e84c35` (2026-04-23) through `453a3d5`
(2026-09-11). Tags: `v1.0.0` 2026-05-09, `v1.1.0` 2026-05-10.*

**M1 · Foundation** — 2026-04-23 → 2026-05-08. The paper was added, summarised, and turned into a design
document (`docs/IDEA.md`), then into an implementation plan (`docs/PHASES.md`), the `.brain/` filesystem
contract, the per-step artifact contracts, and a v2 `session.json` schema carrying venue and criteria.
No code — specs and templates only, deliberately.

**M2 · Canonical content** — 2026-05-08. The eight persona skills and eight slash commands authored in
`extensions/_shared/`, with the rules file, the three enforcing templates, and `MANIFEST.md`.

**M3 · Search server** — 2026-05-08. `osp_mcp.py` with three providers behind one server.

**M4 · Sync and install** — 2026-05-08. `sync_adapters.py` with its capability matrix,
`merge_mcp_config.py`, per-tool installers, and the self-contained per-project venv.

**M5 · Validation and release** — 2026-05-08 → 2026-05-09. Parity validator, installer smoke test,
release docs, `AGENTS.md` rewritten as a developer-facing init doc. Tagged `v1.0.0`.

**M6 · Hardening** — 2026-05-09 → 2026-05-10. A run of fixes against reality rather than design: JSON
merge surviving whitespace, corrupt files and non-dict shapes; stale files wiped on upgrade;
`--check` actually detecting drift (it had not); a marker that broke Gemini's config validation removed;
arXiv moved onto the official package; Semantic Scholar expanded 4 → 10 tools; per-call timeouts added.
Tagged `v1.1.0`. Then `install.sh` was found to be broken over `curl | bash` — stdin is the pipe, so the
menu read EOF and silently defaulted — and fixed.

**M7 · Scale-out and UX** — 2026-05-09 → 2026-07-31. Support went from 5 tools to 13, then 14 with
Antigravity CLI in June. The UX work in this period is what made the protocol legible to a first-time
user: one literature round per invocation instead of three at once, a configurable Q&A pair count
defaulting to 2, an orientation block at the start of every phase, reports that state findings rather
than the next command, resource warnings before expensive steps, installer spinners, `.env` for API keys,
and the `.scholar-peer/` → `.open-scholar-peer/` rename.

**Report — 2026-09-11 (written at reconstruction).** What exists today: 21 canonical files generating 282
adapter files across 14 tools, a 15-tool MCP server, 14 installers. Drift check, parity test and syntax
checks all pass. `docs/PHASES.md` marks every phase complete except the **manual live end-to-end run**,
which its own exit criteria call a manual milestone; commit `b8aa4df` marks it done for v1, but no
artifact in the repository records the result. Treat "the full protocol has been driven end to end on a
real paper" as asserted, not evidenced.

---

## 🏁 Milestone M8: Installer improvements + context harness

**Target.** The `feat/improve-installer` branch delivers whatever the owner opened it for, and this
harness holds a true picture of the project so the next session does not start from nothing.

### Deliverables

- [x] **kiacontext installed and committed** — harness files, plus the pointer blocks in `AGENTS.md` and `CLAUDE.md`.
- [x] **Harness filled from history and docs** — genesis, manifesto, architecture, progress, brainstorm written from `docs/`, the git log and the owner's statement of intent.
- [ ] **Installer improvements** — *not yet defined.* The branch name is the only statement of intent so far; the specific changes need to come from the owner before this can be built or judged.

### Acceptance criteria

1. Every `kia-context/` file has all six frontmatter fields, a real `last_updated`, and no `{{…}}` placeholder left standing except where the file states why it is unfillable.
2. Every count in `ARCHITECTURE.md` is accompanied by the command that produced it, and re-running that command reproduces it.
3. Anything inferred rather than recorded is labelled as inferred in the file itself, not only in a chat message.
4. `python3 scripts/sync_adapters.py --check` and `python3 scripts/test_parity.py` still pass — the harness must not disturb generated content.
5. *(Installer deliverable)* criteria to be written with the owner once the scope is known.

**Depends on:** M7.

### Report — 2026-09-11

Harness filled. `GENESIS.md`, `MANIFESTO.md`, `ARCHITECTURE.md` and this file written from `docs/IDEA.md`,
`docs/PHASES.md`, `docs/paper/SUMMARY.md`, `docs/ARTIFACT_CONTRACTS.md`, `docs/KNOWN_LIMITATIONS.md`, the
canonical prompt sources, 66 commits of history, and a statement of intent from the owner. `DESIGN.md` was
deleted — the project has no interface, and the terminal output contract it might have held is documented
in `ARCHITECTURE.md` §10 where it belongs. `SEED.md` was kept but not reconstructed: the original prompts
were never captured and inventing them would fabricate a historical record.

Criteria 1–4 pass; criterion 5 is open because the installer scope has not been set. Four defects found
while reading are logged as O1–O4 in `BRAINSTORM.md` — none is blocking, two are user-visible.

---

> **← Previous:** none.
> **Next →** none yet.
