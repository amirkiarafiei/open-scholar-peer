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
last_updated: "2026-09-20"
---

# 📈 PROGRESS — What we are building

> **M1–M7 were reconstructed from git history and the retired `docs/PHASES.md` on 2026-09-11, not
> captured from the work as it happened.** Treat them as approximate: the commits say what changed,
> rarely why, and the acceptance criteria shown are the ones `PHASES.md` recorded at the time, not
> invented afterwards. **Everything from M8 onward was recorded live.**
>
> `PHASES.md` was deleted the same day (`BRAINSTORM.md` D14) because this file supersedes it. To read
> the original: `git show 027645b:docs/PHASES.md`.

> **← Previous:** none. This is part one.
> **Next →** none yet. When this file is split, the pointer goes here and in the new part.

**Contents**

| § | |
|---|---|
| [The loop](#the-loop) | How a deliverable gets done |
| [Circuit breakers](#circuit-breakers) | What happens when it does not |
| [Milestones](#milestones) | The table |
| [M8](#-milestone-m8-installer-improvements--context-harness) | Context harness (done) |
| [M9](#-milestone-m9-installer-experience) | Installer experience (done) |
| [M10](#-milestone-m10-antigravity-gains-subagents) | Antigravity subagents (done) |
| [M11](#-milestone-m11-repair-the-three-existing-providers) | Provider bug fixes |
| [M12](#-milestone-m12-read-the-paper-not-just-its-title) | Full-text access |
| [M13](#-milestone-m13-more-open-sources-and-let-the-user-pick-them) | New sources + installer picker |
| [Reference](#-reference-links-and-measurements-for-m11m13) | Every URL and number M11–M13 needs |

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

## Releases

| Tag | Date | Contains |
|---|---|---|
| `v1.0.0` | 2026-05-09 | First release — 5 tools, the seven-step protocol, the MCP server |
| `v1.1.0` | 2026-05-10 | Hardening: config-merge robustness, drift detection, arXiv via the official package, per-call timeouts, `curl \| bash` fix |
| `v1.2.0` | 2026-09-11 | M8–M10: the context harness, the keyboard-driven installer, Antigravity subagents with graceful fallback, and the `$HOME` sandbox fix for the smoke test |

> **Release procedure** is in `AGENTS.md`. Step 4 — a manual end-to-end run on a real paper — cannot be
> done by an agent; it needs a person driving a real tool. For `v1.2.0` it was **not** performed: the
> automated gates (drift, parity, 14/14 installer smoke, syntax) all passed and the installer was driven
> through a terminal emulator, but no review was run end to end on a paper. Treat that as outstanding.

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
| **M8** | Context harness | The harness holds a true picture of the project | M7 | ✅ Done 2026-09-11 |
| **M9** | Installer experience | Installing OSP is a guided, keyboard-driven flow instead of a numbered prompt, and the README says where to type the slash command | M8 | ✅ Done 2026-09-11 |
| **M10** | Antigravity gains subagents | Antigravity is treated like every other subagent-capable tool — no self-reflection fallback, and nothing anywhere still claims it cannot delegate | M9 | ✅ Done 2026-09-11 |
| **M11** | Repair the three existing providers | Every retrieval bug from the 2026-09-19 audit is fixed, each proved with a before/after measurement | M10 | ⬜ Not started |
| **M12** | Read the paper, not just its title | The agent can get full text for arXiv papers and for open-access biomedical papers | M11 | ⬜ Not started |
| **M13** | More open sources, and let the user pick them | Zenodo and OpenAlex work, and the installer lets the user choose databases and optionally enter keys | M12 | ⬜ Not started |

> **Numbering never restarts.** When this file is split, part two continues at the next M.

---

## ✅ M1–M7 — reconstructed summary

*Measured: `git rev-list --count 453a3d5` → 66 commits, `4e84c35` (2026-04-23) through `453a3d5`
(2026-09-11). Tags: `v1.0.0` 2026-05-09, `v1.1.0` 2026-05-10.*

**M1 · Foundation** — 2026-04-23 → 2026-05-08. The paper was added, summarised, and turned into a design
document (`docs/IDEA.md`, since retired), then into an implementation plan (`PHASES.md`, also retired), the `.brain/` filesystem
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
checks all pass. `PHASES.md` marked every phase complete except the **manual live end-to-end run**,
which its own exit criteria called a manual milestone; commit `b8aa4df` marks it done for v1, but no
artifact in the repository records the result. Treat "the full protocol has been driven end to end on a
real paper" as asserted, not evidenced.

---

## 🏁 Milestone M8: Installer improvements + context harness

**Target.** The `feat/improve-installer` branch delivers whatever the owner opened it for, and this
harness holds a true picture of the project so the next session does not start from nothing.

### Deliverables

- [x] **kiacontext installed and committed** — harness files, plus the pointer blocks in `AGENTS.md` and `CLAUDE.md`.
- [x] **Harness filled from history and docs** — genesis, manifesto, architecture, progress, brainstorm written from `docs/`, the git log and the owner's statement of intent.
- [x] **`docs/` narrowed to project documentation** — `IDEA.md` and `PHASES.md` retired, every reference updated (D14, amended by D18).
- [x] **kiacontext skills tracked for cloners** — `skills/kia-context-*/` committed under `.claude/`, `.agents/`, `.opencode/`, `.hermes/`; the rest of each directory stays ignored (D15).
- [x] **Installer improvements** — moved to its own milestone, M9, once the owner named the two reference implementations to follow.

### Acceptance criteria

1. Every `kia-context/` file has all six frontmatter fields, a real `last_updated`, and no `{{…}}` placeholder left standing except where the file states why it is unfillable.
2. Every count in `ARCHITECTURE.md` is accompanied by the command that produced it, and re-running that command reproduces it.
3. Anything inferred rather than recorded is labelled as inferred in the file itself, not only in a chat message.
4. `python3 scripts/sync_adapters.py --check` and `python3 scripts/test_parity.py` still pass — the harness must not disturb generated content.
5. *(Installer deliverable)* criteria to be written with the owner once the scope is known.

**Depends on:** M7.

### Report — 2026-09-11

Harness filled. `GENESIS.md`, `MANIFESTO.md`, `ARCHITECTURE.md` and this file written from `docs/IDEA.md`,
`docs/PHASES.md` (both since retired — D14), `docs/paper/SUMMARY.md`, `docs/ARTIFACT_CONTRACTS.md`,
`docs/KNOWN_LIMITATIONS.md`, the
canonical prompt sources, 66 commits of history, and a statement of intent from the owner. `DESIGN.md` was
deleted — the project has no interface, and the terminal output contract it might have held is documented
in `ARCHITECTURE.md` §10 where it belongs. `SEED.md` was kept but not reconstructed: the original prompts
were never captured and inventing them would fabricate a historical record.

Criteria 1–4 pass; criterion 5 is open because the installer scope has not been set. Four defects found
while reading are logged as O1–O4 in `BRAINSTORM.md` — none is blocking, two are user-visible.

**Second pass, same day.** *(The `IDEA.md` half of this was reversed on 2026-09-12 — see D18. Left as
written because it is what happened.)* `docs/` was narrowed to what a user or contributor needs: `IDEA.md` moved to
`genesis/` (frozen, with a banner listing the five places it is now wrong) and `PHASES.md` deleted after
its one unique decision was carried into D13. All 24 references across `README.md`, `AGENTS.md` and the
harness were rewritten; the release procedure in `AGENTS.md` now updates this file instead of `PHASES.md`.
The kiacontext skills were tracked for all four locally-installed tools — verified with `git check-ignore`
that the OSP adapter copy under `/.agents/` stays ignored, and read `scripts/clean_adapter.sh` to confirm
an OSP re-install will not delete them (it only matches `osp-*` patterns). Drift check and parity test
re-run clean.

---

## 🏁 Milestone M9: Installer experience

**Target.** `bash install.sh` becomes a guided, keyboard-driven flow — arrow keys, checkboxes, a framed
Install button — instead of a numbered prompt read with `read -rp`. A user can install for more than one
agent in a single run, and the README stops implying the slash command is typed into a shell.

**Reference implementations**, both by the owner, both bash 3.2 and `/dev/tty`-driven so they survive
`curl | bash`: `~/Desktop/PiA_projects/subagent-cli-skills/install.sh` (banner, `read_key`, in-place
`rewind`, single- and multi-select menus, the pinned framed Install button) and
`~/Desktop/kia-context/install.sh` (the same, plus responsive layout tiers and an inline button fallback
for short terminals).

### Deliverables

- [x] **Interactive `install.sh`** — capability detection, `/dev/tty` input, arrow-key menus, multi-select tool list, framed Install button, in-place redraw. 607 lines, bash 3.2.
- [x] **Multi-tool install in one run** — the per-tool `install_*.sh` scripts stay the unit of work and are driven in sequence; one failure does not abort the rest.
- [x] **Non-interactive path** — `--tool`, `--dir`, `--list`, `--help`.
- [x] **Consolidated summary** — per-tool result plus one shared next-steps block.
- [x] **Shared closing message** — `scripts/_post_install.sh`; the "where do I type this?" wording now lives in one file instead of 14, and per-tool scripts suppress it when `install.sh` is driving (`OSP_DRIVEN=1`).
- [x] **README corrected** — "Then start using Slash Command:" replaced in both places: open your code agent in the directory, and run the slash command in its interactive chat. Kept short at the owner's request — no explanatory warning block.

### Acceptance criteria

1. `bash -n install.sh` passes, and `bash install.sh --help` exits 0 without a TTY.
2. With no TTY and no `--tool`, the installer explains what to do and exits non-zero — it does not silently install a default tool.
3. `bash install.sh --tool claude --dir <tmp>` installs exactly as `scripts/install_claude.sh` does today: adapter, `.brain/`, MCP venv, `.mcp.json`.
4. Selecting several tools installs all of them and reports a per-tool result; one failure does not abort the rest.
5. `bash scripts/test_install.sh` still passes — it calls the per-tool scripts directly, which this milestone does not change.
6. No `docs/` or harness reference to the installer is left stale.
7. A reviewing subagent finds no correctness defect in the new script. ✅ — 11 found, 11 fixed, verdict "ship it".

**Depends on:** M8.

### Report — 2026-09-11

`install.sh` went from an 88-line numbered `read -rp` prompt to a 607-line keyboard-driven TUI, modelled
on the two reference installers. What it does now that it did not: multi-select, so one run can install
for several tools; a framed **Install** button pinned under the list that is the only thing that starts
the install (Enter on a tool row toggles, never installs); a "where?" step, so `curl | bash` in the wrong
directory is caught before anything is written; and `--tool` / `--dir` for scripted use.

Two behaviour changes worth knowing. **With no TTY and no `--tool`, the installer now exits 1 with
guidance instead of silently installing Claude Code** — a silent default was the wrong answer for someone
piping this in CI. And the per-tool scripts no longer each print "Run /open-scholar-peer"; that block is
printed once, by `install.sh`, with the corrected wording.

Two robustness fixes found while testing rather than by review: the tool hints were built with a literal
`·`, which is mojibake in a non-UTF-8 locale, so they are now assembled from `$DOT` after capability
detection; and remote-mode detection tested only for a `scripts/` directory, which misfires when
`curl | bash` runs inside an unrelated project that happens to have one — it now requires
`scripts/init_brain.sh` and `extensions/_shared/`.

**Verified:** `--help` exits 0 without a TTY; no-TTY-no-`--tool` exits 1 with guidance; an unknown slug
exits 2 and lists the valid ones; `--tool claude,cursor,codex --dir <tmp>` installs all three with
adapters, `.brain/`, `.env`, `.mcp.json`, `.cursor/mcp.json` and the venv all present; the full
interactive path was driven through a pty (space → End → Enter) and produced the same result; and
`bash scripts/test_install.sh` passes for all 14 tools, as do the drift check and parity test.

Acceptance criteria 1–6 pass.

### Review round — 2026-09-11

Criterion 7: a reviewing subagent drove the TUI through a terminal emulator at nine terminal heights,
plus piped stdin, remote-clone mode, Ctrl-C, `q`, an ASCII locale and a deliberately-failing installer.
It found six confirmed defects; all six are fixed:

| | Defect | Fix |
|---|---|---|
| 1 | **Resize corrupted the menu permanently.** `rows`/`layout`/`win` were measured once before the redraw loop, so shrinking the window made every later `rewind` clamp at row 0 — title and cursor clipped off the top, arrow keys apparently dead, unrecoverable without `q`. | Geometry is re-measured every frame, and `cur` is re-clamped. |
| 2 | **The success block printed even when every installer failed** — "0 installed, 2 failed" followed by instructions to go use an integration that was never written. | Guarded on `installed > 0`. |
| 3 | **Tight layout wasted 5 rows** (it reused layout 0's chrome constant) and clipped the title at ≤ 8 rows. | Chrome constant corrected to 4 + one row in hand; window floor lowered. Title, button and cursor now visible at every height from 6 rows up. |
| 4 | The no-TTY refusal **gave the wrong reason** when stdout was merely redirected. | The refusal stays — a TUI drawn into a pipe is invisible — but now says which of the two cases it is. |
| 5 | `--dir` plus the interactive menu drew **two horizontal rules back to back**. | Step 1's separator moved inside the block it belongs to. |
| 6 | `--tool claude,claude` **installed twice** and reported "2 tool(s)". | Duplicate indices skipped. |

A second round covered the rest of the report — five more, all fixed:

| | Defect | Fix |
|---|---|---|
| 7 | `--tool ""` fell through to the interactive menu instead of erroring. | The gate now tests whether the flag was *seen*, not whether its value is non-empty. |
| 8 | `_post_install.sh` ran caller-supplied action text through `%b`, which would silently eat a backslash in any future action string (a `\n`, a Windows path). | `%s` for the text; `%b` kept only for the `echo -e`-style colour literals that need it. |
| 9 | `TEMP_DIR` leaked a multi-MB clone into `/tmp` if the terminal was closed mid-fetch. | `HUP` added to the trap. |
| 10 | `read_key` decoded `tab` and no menu handled it — the obvious "jump to Install" affordance was produced and dropped. | `tab` jumps to the button, and the help line says so. |
| 11 | The banner and the `↑/↓` in three help lines were hard-coded UTF-8, bypassing the locale gate, so they were mojibake under `LANG=C`. | Banner gated on the UTF-8 flag, `$UPDN` added, and the em dashes in printed strings replaced. The menu is now pure ASCII under `LANG=C` — verified by grepping the rendered screen for non-ASCII bytes. |

Findings 10 and 11 are inherited from the reference installers rather than introduced here.

### What the review cleared

Worth recording, because it is the expensive half to re-derive and nobody should pay for it twice.

- **Redraw arithmetic** — every layout tier rendered through a terminal emulator at rows
  40/26/24/23/20/16/12/10/8/6 while driving Up/Down/space/`a`/`n`/Home/End/PgUp/PgDn/Enter/`q`. No defect
  in `drawn` line-count accounting: layout 0 = n+10, layout 1 = n+7, layout 2 = win+3 (+1 with the scroll
  indicator); `draw_button`'s `+3` and `draw_button_inline`'s `+1` both correct.
- **Scroll window** — no off-by-one. The last window renders indices n-win..n-1 correctly, and
  home/end/pgup/pgdn/wrap-around all re-clamp on the next frame.
- **Button focus** (`cur == n`) — Enter on a tool row only ever toggles and never installs; Enter on the
  button installs only when something is selected; the window correctly freezes while the button has focus.
- **Cursor restore** — `?25l`/`?25h` counts matched on normal exit, `q`, Ctrl-C, and Ctrl-C during the
  remote clone. Bash does not run the EXIT trap inside the `$(read_key)` command substitution, so the
  clone is not deleted on every keypress.
- **Quoting and word splitting** — installs into a target with a space in its name work through both
  `--dir` and the interactive prompt. `SELECTED_IDX` is digits-only, so the deliberate unquoted
  `for i in $SELECTED_IDX` is safe. Every `printf` in both files audited programmatically: zero
  format/argument mismatches, and no user-controlled string reaches a `printf` *format* argument.
- **The `OSP_DRIVEN` contract** — honoured uniformly. Diffing all 14 installers against `027645b`, every
  tool-specific `(1) …` line survives verbatim as the helper's first argument; the only thing removed is
  the per-tool `(2) Run /open-scholar-peer` line the helper replaces. Nothing was dropped by the
  mechanical rewrite.
- **Early-exit cleanup** — the EXIT trap fires before `TEMP_DIR` exists, but the `:-` defaults make every
  early exit safe. Only SIGHUP was uncovered, which is finding 9.

**Verdict: ship it.** Quoting the reviewer: *"the redraw arithmetic is correct in all three tiers, the
scroll window has no off-by-one, button focus is clean, the cursor survives every exit path, `curl | bash`
genuinely works, spaces in paths survive both entry routes, bash 3.2 is respected."* It rated 1 and 2 the
only real blockers; both were fixed before the verdict was written, and 7–11 have since been fixed too.

Finding 1 is the one that mattered: it exists in both reference installers too, and bites hardest here
because OSP has the longest list — layout 0 needs a 27-row terminal, so it is the tier most likely to be
resized out from under. Worth reporting upstream to `subagent-cli-skills` and `kia-context`.

Re-verified after the fixes: the resize scenario now re-lays out correctly (40 → 18 rows, cursor and
title still visible); title/button/cursor present at rows 6, 8, 12, 16, 20, 24, 30, 40; all-fail exits 1
with no success block; duplicate slug installs once; and the smoke test, drift check and parity test
all still pass.

---

## 🏁 Milestone M10: Antigravity gains subagents

**Target.** Antigravity 2.0 ships an asynchronous subagent framework (`invoke_subagent`, custom subagents
under `.agents/agents/<name>.md`, an `/agents` panel, a 10-level nesting limit). OSP classified it as
having no subagents and routed `/5-osp-qa` through the self-reflection fallback. That is now wrong, and
being wrong here costs review quality: self-reflection is the documented weaker substitute, so every
Antigravity user has been getting a worse Q&A phase than the tool can support.

After this milestone Antigravity is treated exactly like the other subagent-capable tools, and the
self-reflection path survives only for the two tools that still need it — Mistral Vibe and OpenHands.

**Blast radius, measured before starting.** `grep -rn` for Antigravity near self-reflection wording:
**14 files** hold the claim, of which **8 are canonical or code** and the rest are generated adapters that
the sync script rewrites.

| Canonical / code | Why it mentions Antigravity |
|---|---|
| `scripts/sync_adapters.py` | the capability flag itself — `supports_subagent`, `qa_mode` |
| `extensions/_shared/commands/5-osp-qa.md` | mode-selection prose, ×2 |
| `extensions/_shared/rules/osp-rules.md` | the always-on fallback list |
| `extensions/_shared/skills/osp-query-agent/SKILL.md` | "Self-reflection fallback (Antigravity only)" |
| `extensions/_shared/skills/osp-answer-generator-agent/SKILL.md` | frontmatter + operating mode, ×2 |
| `extensions/_shared/MANIFEST.md` | capability-flag table |
| `scripts/install_antigravity.sh` | prints a "does NOT support subagents" notice |
| `install.sh` | the tool hint shown in the picker |
| `README.md`, `AGENTS.md`, `docs/KNOWN_LIMITATIONS.md`, `docs/ARTIFACT_CONTRACTS.md`, `docs/TROUBLESHOOTING.md` | user- and contributor-facing claims |

### Deliverables

- [x] **Capability flag flipped** — `sync_adapters.py` marks Antigravity `supports_subagent=True`, `qa_mode="subagent"`; adapters regenerated.
- [x] **Canonical prompts** — Antigravity removed from every self-reflection list; the fallback now reads "Mistral Vibe and OpenHands" and stays intact for them.
- [x] **Docs** — README support table, `AGENTS.md`, `KNOWN_LIMITATIONS.md` §1, `ARTIFACT_CONTRACTS.md`, `TROUBLESHOOTING.md`.
- [x] **Installer** — the "does NOT support subagents" notice removed from `install_antigravity.sh`; the picker hint in `install.sh` updated.
- [x] **Harness** — `ARCHITECTURE.md` subagent count and glossary; a decision entry recording what changed and when.

### Acceptance criteria

1. `grep -rin "antigrav" | grep -i "self-reflect"` returns nothing outside historical log entries.
2. `extensions/.agent/workflows/5-osp-qa.md` carries the **subagent** banner, and `.vibe` / `.openhands` still carry the self-reflection one.
3. 12 of 14 tools report `supports_subagent`; the two remaining are Mistral Vibe and OpenHands.
4. `sync_adapters.py --check`, `test_parity.py` and `test_install.sh` all pass.
5. Every count that was "11" or "three tools" is updated wherever it appears, including in the harness.
6. A reviewing subagent finds no stale claim and no over-reach beyond the capability change.

**Depends on:** M9.

### Report — 2026-09-11

Six canonical/code files and five doc files changed; the 14 adapter directories regenerated from them.
Antigravity is now `supports_subagent=True` / `qa_mode="subagent"`, and the self-reflection path survives
intact for the two tools that still need it. Verified: 12 of 14 report subagent support, the two
remaining are Mistral Vibe and OpenHands, `extensions/.agent/workflows/5-osp-qa.md` carries the subagent
banner while `.vibe` and `.openhands` still carry the self-reflection one, and a `grep` for Antigravity
near self-reflection wording returns nothing outside the log entries that record the change. Drift check,
parity test and all 14 installer smoke tests pass.

**Scope held deliberately.** Antigravity also documents *custom subagent definition files*
(`.agents/agents/<name>.md`, YAML frontmatter carrying `tools`, `model`, `commandExecutionPolicy`). Not
built: no other adapter has such a file, so it would be a new artifact type for the sync script to
generate and keep in parity, and parity with the other thirteen is precisely what this milestone was for.
Logged as O8.

**Found while auditing, fixed in passing.** `KNOWN_LIMITATIONS.md` §4 claimed the Antigravity installer
prints a paste-ready MCP snippet the user must apply by hand. It has not done that for some time — it
auto-merges both global config files, which is also what the README's support table says. The section now
describes what actually happens, and names Kimi Code, which writes globally too and was missing from it.

**The uncomfortable part**, recorded as O9: this classification was wrong for as long as it took someone
to read a vendor changelog. Nothing in the project re-checks the capability matrix against vendor docs, so
the same silent expiry can happen to any of the other thirteen.

### Review round — 2026-09-11

The reviewing subagent found three defects **introduced by this milestone**, all in the one file the
commit had touched as a "correctness fix" — a reminder that a rewrite justified as fixing an error is
exactly where the next error hides:

| | Defect | Fix |
|---|---|---|
| 1 | `KNOWN_LIMITATIONS.md` §1 said "use one of the subagent-capable tools **listed above**" — the same diff had replaced that list with "the other twelve". | The workaround names all twelve. |
| 2 | The §4 rewrite said **three** tools write outside the project. Four do — `install_antigravity_cli.sh` merges `~/.gemini/antigravity-cli/mcp_config.json` as well as the project-local file. | §4 is now a table built from what the installers actually do, verified by grepping every `merge_mcp_config.py` call site. |
| 3 | §4 claimed TOML was why a config is not auto-merged. It is not the dividing line: OpenCode and OpenHands emit JSON snippets and are not merged either. | The table's third row names all four snippet-only tools. |

### The bigger finding — `$HOME` was never sandboxed

Asked to run `scripts/test_install.sh`, the reviewer discovered it **merges throwaway `/tmp` paths into
the developer's real global MCP configs on every run**. Six installers write under `$HOME`; the harness
sandboxed only the project directory. When the sandbox is deleted, a dead `osp` entry pointing at a
vanished `/tmp` path is left behind in `~/.gemini/antigravity/`, `~/.gemini/config/`,
`~/.gemini/antigravity-cli/`, `~/.kimi/` and `~/.copilot/`.

This is not new — `~/.copilot/mcp-config.json` on this machine still points at a `.scholar-peer/` path,
a directory name retired in May (`43cd32b`), so it has been happening for months. But it was being made
worse on every verification run, including three in this session, and "all 14 installer smoke tests pass"
was being cited as evidence the work was safe.

Fixed: `run_install_smoke()` now runs each installer with `HOME` pointed at a directory inside the
sandbox. Verified by md5-summing all five real config files before and after a full run — unchanged,
and all 14 still pass. Logged as O10, because nothing stops the next harness from repeating it.

## 🏁 Milestone M11: Repair the three existing providers

**Branch:** `feat/richer-search` (created 2026-09-19 from `750a658`).

**Target.** Search actually returns what it is asked for. Today three of the four bugs below silently
return wrong or thin results, and the fourth reports a block as "no papers found". All four were measured,
not guessed. Decisions: `BRAINSTORM.md` D19.

### Deliverables

- [x] **B1 — arXiv date filter.** `mcp-server/providers/arxiv.py`, `search()`. It fetches `max_results+10` by relevance, then filters by date in Python, so a narrow window returns almost nothing. Replace with arXiv's native range inside `search_query`: `submittedDate:[YYYYMMDDTTTT TO YYYYMMDDTTTT]`. **Measured 2026-09-19:** `search("large language model", max_results=5, date_from="2026-01-01")` → **1 result**. Native range, same window → **5/5, all inside it**.
- [x] **B2 — arXiv category filter does nothing.** Same file, `search()` builds `f"({query}) ({cat_filter})"` with no operator, so arXiv ORs the two. Insert `AND`. **Measured 2026-09-19:** `(transformer) (cat:cs.CL)` → **3 of 25** hits actually in `cs.CL`, 7 unrelated categories including `quant-ph`. `(transformer) AND (cat:cs.CL)` → **16 of 25**, 4 related categories.
- [x] **B3 — arXiv rate etiquette.** `arxiv.Client()` is constructed inside both `search()` and `get_details()`. `_last_request_dt` is per-instance, so back-to-back calls fire with no gap. The Literature skill tells the agent to call providers *simultaneously*. Use one module-level client. arXiv Terms of Use: *"no more than one request every three seconds… a single connection at a time"*, applying *"to all of the machines under your control as a whole"*.
- [x] **B4 — stop the S2 auto-pagination.** `mcp-server/providers/semantic_scholar.py`. `PaginatedResults.__iter__` is `yield from self._items; while self._has_next_page(): yield from self._get_next_page()` — it pages to exhaustion. Our list comprehensions iterate the whole object. `search_paper` uses `max_results=1000`; citations/references get the constructor default **10000**. So one `limit=10` search can be ~100 HTTP requests and one `limit=50` citations call ~200. Fix with `itertools.islice(results, limit)`. **This is the worst one**: a Semantic Scholar API key is rate-limited to **1 request per second**, so 100 requests takes ~100 s and blows the 90 s `OSP_CALL_TIMEOUT`. A key currently makes OSP *slower*, not faster.
- [x] **B5 — pass `fields=`.** Same file. With `fields=None` the package requests **76** `Paper.FIELDS`, including `embedding` plus 21 nested `citations.*` and 21 nested `references.*` fields (each with their own abstracts). `_paper_to_dict` returns **10** keys. S2 caps a response at 10 MB, so `get_paper` 400s on a heavily-cited paper. Pass an explicit field list per tool.
- [x] **B6 — keep the fields we already pay for.** Still in `_paper_to_dict`: the package already fetches `tldr`, `openAccessPdf`, `isOpenAccess`, `publicationDate`, `fieldsOfStudy` and we throw all five away. `tldr` is an auto-written one-line summary — useful to the Literature agent for triage. `openAccessPdf` is the input to M12.
- [x] **B7 — expose the S2 search filters.** `search_paper()` accepts 13 parameters; `semantic_scholar.py` passes **one** (`limit`). Surface at least `year`, `publication_date_or_year` (the temporal round), `open_access_pdf`, `min_citation_count`, `fields_of_study`, `venue`, `sort`. Also add **`match_title=True`** as its own tool — it hits `/paper/search/match` and returns the closest title match with a `matchScore`. That is the right way to resolve a bibliography line to an ID, i.e. deduplication.
- [x] **B8 — fix the snippet tool.** `search_snippets()` reads `getattr(s, "snippetId")`, which does not exist on `Snippet` → always `null`. It also calls `_slim_paper(s.paper)`, but `SnippetPaper` only has `corpus_id`, `title`, `authors`, `open_access_info` — so `paperId`/`year`/`citationCount` come back null and `authors` is a list of **plain strings**, which `_slim_paper` maps to `{"name": null, "authorId": null}` for every author. **Note:** `Snippet.text` *does* work — it is a documented shortcut for `snippet.text`. Only the id and the paper block are broken. Snippet `limit` can be up to **1000**; we cap at 20.
- [x] **B9 — Google Scholar must fail loudly.** `mcp-server/providers/google_scholar.py`, `_parse_results()`. A CAPTCHA/block page contains no `gs_ri` divs, so it returns `[]` — **byte-identical to a genuine zero-hit search**. Verified 2026-09-19. The agent then writes "no papers found" when the truth is "we were blocked". This breaks MANIFESTO rule 8 and means the Literature skill never records the provider as unavailable in Provenance. **The owner asked for several approaches to be tested first, the best chosen, and only then applied** — see the deliverable below.
- [x] **B10 — choose the Google Scholar approach by test, not by guess.** Try at least: (a) detect the block page by marker (`gs_captcha_ccl`, `/sorry/index`, "unusual traffic"); (b) rotate the User-Agent across several real browser strings; (c) retry with backoff; (d) optional proxy via an env var. The competitor already does all four in `paper_search_mcp/academic_platforms/google_scholar.py` — `_is_captcha_page()`, UA rotation, `max_retries`/`retry_delay`, `GOOGLE_SCHOLAR_PROXY_URL`. **MIT licence, so borrowing is allowed with attribution.** Whatever wins, a block must raise a distinct error, never `[]`.
- [x] **B11 — pin the dependencies.** `mcp-server/requirements.txt` says `arxiv>=2.1.0` and `semanticscholar>=0.7.0`. A fresh install on 2026-09-19 pulls **arxiv 4.0.1** and **semanticscholar 0.12.0** — two major versions up. arxiv 4.x removed `Search.results`, `Result.download_pdf` and the `arxiv.arxiv` shim; our `Client().results(search)` survives by luck. Pin ranges, e.g. `arxiv>=3.0,<5`.

### Acceptance criteria

1. B1: a 12-month window returns a full page of in-window papers, not one. Show the before/after count.
2. B2: with `categories=["cs.CL"]`, at least 80% of results have `primary_category == "cs.CL"`. Show before/after.
3. B4: one tool call makes **one** page request unless the caller asks for more. Prove it by counting HTTP calls.
4. B5: `get_semantic_scholar_paper` on a paper with >1000 citations returns without a 10 MB error.
5. B8: every author in a snippet result has a real name; `snippetId` is either correct or removed from the output.
6. B9/B10: a simulated block page produces an **error**, not `[]`. A real empty search still produces `[]`.
7. `sync_adapters.py --check`, `test_parity.py` and `test_install.sh` still pass.
8. No tool gains agentic logic — every fix stays atomic and stateless (MANIFESTO §7, D3).

**Depends on:** M10.

---

### Report — 2026-09-20

All eleven deliverables done. Every number below was measured on 2026-09-20, not reasoned.

| | Before | After |
|---|---|---|
| **B1** arXiv date window (`date_from=2026-01-01`, 5 asked for) | 1 paper | **5 papers, all inside the window** |
| **B2** arXiv `categories=["cs.CL"]`, 25 asked for | 3 in `cs.CL`, 7 unrelated categories including `quant-ph` | **25 of 25 in `cs.CL`**, 16 of them as primary |
| **B3** spacing between arXiv calls | none — a new client per call | **3.1 s, 3.1 s** |
| **B4** HTTP requests for one `limit=10` S2 search | still paging after 78 s | **1 request, 12 s** |

**B2 needs its acceptance criterion corrected.** Criterion 2 asked for "at least 80% of results with
`primary_category == cs.CL`" and the measured figure is 64%. That criterion measures the wrong thing:
arXiv's `cat:` operator matches a paper in *any* of its categories, so a paper whose primary is `cs.LG`
and which is cross-listed to `cs.CL` is a correct hit. By membership — the thing the filter actually
promises — the score is 25 of 25. The filter works; the criterion was written before we knew the
semantics.

**B5 was partly wrong about where the problem was.** `get_paper` does default to all 76 `Paper.FIELDS`,
including `embedding` and the nested `citations.*`/`references.*` trees, and that is the 10 MB failure.
But `search_paper`, `get_papers`, `get_author_papers` and `get_recommended_papers` already defaulted to
the 21-field `Paper.SEARCH_FIELDS`, so they were never asking for 76. What those 21 *do* lack is `tldr`,
which is why it is now requested explicitly.

**B9/B10, decided by test rather than by guess, as asked.** Five requests to Google Scholar about eight
seconds apart, from one ordinary address:

- Every one answered **HTTP 429**.
- Four User-Agent strings — Chrome 124 Windows, Chrome 131 macOS, Firefox 133 Linux, and none at all —
  returned **byte-identical** 429 bodies. **Rotating the User-Agent achieves nothing.** The block is on
  the address, not the client string.
- Later in the same session Google stopped answering altogether and the requests timed out.

So retrying a 429 only spends the caller's time budget on a host that has already refused. The provider
**does not retry a block**; it fails at once and says what happened, leaving the time for the other
providers. Retries are kept for faults that can pass on their own — a dropped connection, a timeout, a
5xx. UA rotation is kept because it is three lines and harmless, and recorded as unmeasured benefit.

There is now one exception family. `GoogleScholarUnavailable` covers every failure and
`GoogleScholarBlocked` is the subclass for a refusal, so a caller can catch "we did not get to look"
without listing types, and every message carries the same instruction: record the provider as
unavailable, never as "no papers found".

### The bigger finding — the server could not start on a fresh install

`requirements.txt` said `mcp>=1.2.0` with no ceiling. That resolves to **mcp 2.2.0** today, and mcp 2.x
deleted `mcp.server.fastmcp` and renamed `FastMCP` to `MCPServer`. `osp_mcp.py` line 28 imports
`from mcp.server.fastmcp import FastMCP`, so **a clean install could not import the server at all** —
it fails with `ModuleNotFoundError` before any tool is registered. Reproduced in an empty virtualenv,
then fixed by pinning `mcp<2.0`; the same empty virtualenv now imports the server and registers all 16
tools. Lifting that ceiling means migrating to `MCPServer` first.

This is the exact failure B11 predicted for `arxiv` and nobody thought to check for `mcp`. Logged as O15.

Also removed: the `fastmcp` package. Nothing imports it — `FastMCP` comes from inside `mcp` — and it was
pulling its own dependency tree into every user's install.

### Two test harnesses, because there were none

Nothing in this repository loaded `mcp-server/providers/` before today. The adapter tests and the
installer smoke test never touch it, and the syntax check listed four files by name, none of them a
provider.

- **`scripts/test_providers_unit.py`** — offline, about a second, **58 checks**. It holds the things the
  live internet cannot prove on demand: that a captcha page raises while a genuine zero-hit page returns
  `[]`, that every query the builder emits is the one intended, that each search filter reaches the
  client under the right name, and that the Google Scholar retry budget still fits inside
  `OSP_CALL_TIMEOUT`.
- **`scripts/test_providers.py`** — live, opt-in, one `--only` switch per provider and a per-provider
  time budget. It separates "this is broken" from "this API will not talk to us", which matters: by the
  end of this session Semantic Scholar was refusing connections and Google Scholar was timing out, and
  neither is a defect in our code.

`AGENTS.md` now globs `mcp-server/**/*.py` instead of naming four files, and uses `compile()` rather than
`ast.parse()`. That is not pedantry: `ast.parse` accepted a real mistake made in this session — reading a
module global before declaring `global` in the same function — which Python itself refuses. `compile()`
catches it.

**Not verified, and honestly so.** The Semantic Scholar live checks for the year filter, `get_paper` on a
heavily-cited paper, title matching and snippets did not run: the anonymous API began refusing
connections partway through the session. The filter wiring for all of them is covered offline instead,
which is stronger, but the round trip against the real API is still owed. Re-run
`.venv/bin/python scripts/test_providers.py --only semantic_scholar`.

**Verified:** 58 offline checks, arXiv live checks all pass, one HTTP request per S2 call measured,
a clean virtualenv imports the server with 16 tools, `sync_adapters.py --check` and `test_parity.py`
pass, all 14 installer smoke tests pass, and the five real global MCP config files are untouched.

Acceptance criteria 1, 3, 4, 6, 7 and 8 pass. Criterion 2 passes on the corrected measure. Criterion 5
is covered offline and still owed a live run.

### Review round — 2026-09-20

Two subagents, two lenses: one against the live APIs, one on contracts and rules. The contract audit
found four defects **introduced or left standing by this milestone**, all four reproduced independently
before being fixed.

| | Defect | Fix |
|---|---|---|
| 1 | **`matchScore` was always `null`.** `Paper` declares no such property and never assigns one, so `getattr(paper, "matchScore")` answers `None` for every call. This is the snippetId bug (B8) repeated one function later, in the tool sold as "the right way to resolve a reference". `/paper/search/match` always returns its best guess — there is no "no match" — so without the score the agent binds a bibliography line to whatever came back, with nothing to judge it by. | Read from `paper.raw_data`. The skill now also says a low score means no real match. |
| 2 | **The shared arXiv client could wedge the provider for the life of the process.** `arxiv.Client` calls `session.get()` with **no timeout**, so a hung socket holds the lock forever, and `asyncio.to_thread` cannot cancel the thread holding it. Every later arXiv call would queue behind it and time out. Before this milestone each call had its own client and was independent, so the lock that fixed the rate etiquette created this. | Two bounds: a 20 s request timeout patched onto the package's session, and `_arxiv_turn()`, which waits at most 25 s for the connection and raises `ArxivBusy` instead of queueing. |
| 3 | **The Semantic Scholar 429 retry storm was never fixed, and B4 did not touch it.** The package reports HTTP 429 as `ConnectionRefusedError` and retries it ten times with exponential backoff (5 s to 60 s): about **375 s inside one call**. The tool layer gives up at 90 s, but the worker thread keeps hammering the API for minutes afterwards, making the next call likelier to be throttled too. | `SemanticScholar(api_key=..., retry=False)`, and a 429 is translated into `SemanticScholarRateLimited` telling the user to set a key. **Measured: the same call went from stalling past a 300 s timeout to failing in 1.3 s.** |
| 4 | **`publicationDate` was a `datetime` object.** Worse than reported: `json.dumps` refuses it outright, and any coercion invents a midnight component the API never sent. | Formatted to `YYYY-MM-DD`, with a test that the whole record serializes. |

It also caught one of our own checks asserting nothing — `any(key in r for r in rows)` is always true when
the serializer is a dict literal, so the only B6 check would have passed with every value `None` — and
that the block-versus-empty warning had been written into one of the three Google Scholar docstrings.

**Errors now carry a reason.** The prose alone made the agent guess. Every error record has a `reason`:
`blocked`, `rate_limited`, `busy`, `timeout`, `bad_request` or `failed`. Only `[]` means the search ran
and matched nothing. The Literature skill states the rule.

### Found while re-reviewing: partial dates silently lost most of the year

Not from either reviewer. `dateutil.parser.parse` fills the gaps in a partial date from **today**, so
`date_from="2024"` became **2024-09-20** on the day this was written, and `"2024-06"` became the 20th of
June. A caller asking for "everything from 2024" would quietly lose January to September and nothing
would look wrong — the same shape of failure as B1, in the code written to fix B1. Partial dates are now
widened to the period they name, leap years included. Verified live: a 2024 window returns papers from
January onward.

### The prompt that would have wasted the whole milestone

The contract audit's most valuable finding was not a defect in the code. Round 3 of the literature
protocol is *"filter to last 12 months"* — the reason B1 and B7 exist — and
`skills/osp-literature-review-agent/SKILL.md` listed the three search tools with **no mention that any
filter exists**. The agent would have kept running a plain keyword search for the temporal round and none
of this milestone's main win would ever have fired. The skill now names the date and filter parameters
for each provider, and `match_semantic_scholar_title`, which no prompt mentioned at all.

`mcp-server/README.md` was also badly stale: it listed 9 tools, **three of which do not exist**
(`get_semantic_scholar_paper_details`, `get_semantic_scholar_author_details`,
`get_semantic_scholar_citations_and_references`), and told readers to build a virtualenv inside
`mcp-server/` — which `init_mcp.sh` then copies into every user's project. Both rewritten, and the tool
list is now cross-checked against the source.

---

## 🏁 Milestone M12: Read the paper, not just its title

**Target.** Every OSP tool today returns metadata only. The Baseline Scout and the Q&A engine cannot check
*"does the cited paper actually report that number?"* from an abstract. This milestone gives the agent the
actual text, for the two sources where it is free and legal. Decisions: `BRAINSTORM.md` D20.

> **Correction to the 2026-09-19 review.** It said OSP "has no full-text access". That was wrong, and the
> owner caught it. arXiv gives full text to anyone — a free PDF and the LaTeX source. The gap is in our
> code: we store `pdf_url` and never open it.

### Deliverables

- [ ] **F1 — arXiv download/read tools.** `arxiv` 4.0.1 **removed** `Result.download_pdf` and `download_source`; `Result` now exposes only `get_short_id()` and `source_url`. So fetch by plain HTTP from the URLs we already serialize. Two routes, and the second is the better one: **PDF** (`pdf_url`) always exists but needs a PDF reader and comes out messy for two-column text and maths; **LaTeX source** (`source_url`) is the real text, clean, equations intact, but arrives as `.tar.gz` and must be unpacked.
- [ ] **F2 — make it easy for an agent to use** (owner's explicit request). Prefer a tool that takes an arXiv ID and returns text directly, over one that returns a file path. **A read tool must not write to disk** — the competitor's `download_*` tools persist to `./downloads`, which would break our stateless rule (D3). Returning text keeps it atomic.
- [ ] **F3 — Europe PMC provider.** Open-access biomedical, **no key at all**, and it serves **full text over REST as XML — no PDF parsing**. This is the cheapest full-text path that exists. Verified 2026-09-19: a keyword search returned HTTP 200 with **2,304 hits**, and each record carried `fullTextUrlList` and an `isOpenAccess` flag.
- [ ] **F4 — find the current Europe PMC docs before coding** (owner's request). Start at `https://europepmc.org/RestfulWebService`. Working endpoint shape confirmed on 2026-09-19: `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=<q>&format=json&pageSize=<n>&resultType=core`. `resultType=core` is what returns the abstract and `fullTextUrlList`.
- [ ] **F5 — why Europe PMC matters here.** About **5 or 6 of the owner's ~30 reviewed papers are health or biology** (the Frontiers paper, `Sage/digital-health-mental-fatigue`, `MDPI/information_urinary_infection`, `MDPI/information_explain_mental_health`). arXiv covers almost none of that. This is a measured gap, not a hypothetical one.
- [ ] **F6 — test the tools against the live API** before declaring the milestone done (owner's request).

### Acceptance criteria

1. Given an arXiv ID, a tool returns readable body text, not a link and not a file path.
2. Nothing is written to disk by any read tool.
3. Given a biomedical query, Europe PMC returns results with abstracts, and open-access ones expose a full-text route.
4. Both new tools carry the same rich docstrings the existing 15 have — that is what the agent reads to choose.
5. Provider failures return a structured error, never an empty list (the M11 B9 rule applies to new providers too).

**Depends on:** M11 (B5/B6 supply `openAccessPdf`, which this uses).

---

## 🏁 Milestone M13: More open sources, and let the user pick them

**Target.** Add the two remaining agreed sources, and give the installer a way to choose databases —
because OpenAlex is the first source after Semantic Scholar that wants a key, and the user should see that
before installing. Decisions: `BRAINSTORM.md` D19 and D21.

### Deliverables

- [ ] **S1 — Zenodo provider.** Open, no key. Verified 2026-09-19: `https://zenodo.org/api/records?q=<q>&size=<n>&type=software` returned HTTP 200 and **12,570** software records for a test query. Docs: `https://developers.zenodo.org/`.
- [ ] **S2 — use Zenodo for the right question.** It does not find papers. It finds code, datasets and software releases. Give it its own job: *"did the authors release their code and data?"* — a reproducibility criterion on most venue review forms that the agent currently cannot check at all. Do **not** put it in the literature rounds.
- [ ] **S3 — OpenAlex provider.** ~**327,426,920** works (live `meta.count`, 2026-09-19). Its unique value is **`is_retracted`** — **135,702** flagged works. Nothing else we have can tell the agent that a cited paper was retracted, and recommending "accept" on a paper leaning on retracted work is exactly the failure that catches. Also gives `referenced_works`, `topics`, ROR-linked institutions, `best_oa_location`, `fwci`.
- [ ] **S4 — OpenAlex key handling.** OpenAlex moved to free API keys on **2026-02-13**. Keyless still answers but is capped at **100 credits/day**, and a list call costs **10** — about **10 searches a day**, which is unusable. A free key gives **100,000/day at 100 req/s**. So OpenAlex is *optional-key* in the same sense as Semantic Scholar, and must be labelled that way in the installer. One gotcha: **OpenAlex returns abstracts as an inverted index** and they must be reconstructed into text.
- [ ] **S5 — installer database picker** (owner's design). Extend the M9 TUI so the user explicitly selects which paper-search databases to enable. Show a readable table with, per database: **free / key required / optional key**, and **which domain it covers**. Keep the existing keyboard model — arrows, space to toggle, the framed Install button.
- [ ] **S6 — optional key entry during install.** After selecting, offer to type each key right there, with a clear skip. If skipped, tell the user the `.env` file exists and they can add keys later. Never require a key to finish the install.
- [ ] **S7 — the table content** (as agreed 2026-09-19): arXiv — free, preprints, CS/physics/maths. Semantic Scholar — optional key (speed only), all fields. Google Scholar — free, broad, best-effort scraping. Europe PMC — free, biomedical, full text. Zenodo — free, code/data/software. OpenAlex — optional key, all fields, retraction flags.

### Acceptance criteria

1. Zenodo and OpenAlex tools work against the live APIs and return structured errors on failure.
2. OpenAlex abstracts come back as readable text, not an inverted index.
3. The installer table states the key status and domain of every database correctly.
4. An install with no keys entered completes and works; the user is told where `.env` is.
5. Tool count stays manageable — see O12 on tool-list growth.

**Depends on:** M12.

---

## 📎 Reference: links and measurements for M11–M13

Kept here on purpose, so an implementation session that has lost the conversation still has every source.

**Semantic Scholar** — `https://api.semanticscholar.org/api-docs/graph` · `https://api.semanticscholar.org/api-docs/recommendations` · `https://www.semanticscholar.org/product/api/tutorial`
Rate limits as documented: *"1000 requests per second shared among all unauthenticated users"*; *"The introductory rate limit for an API key is 1 RPS on all endpoints"* — no per-endpoint difference.
Known upstream bug: in `semanticscholar` 0.12.0, `get_paper_citations`, `get_paper_references`, `get_author_papers` and `get_paper_authors` call `PaginatedResults.create(...)` **without** `headers=self.auth_header`, so those four run anonymously even when a key is set. Only `search_paper` and `search_author` pass it.

**arXiv** — `https://info.arxiv.org/help/api/index.html` · `https://info.arxiv.org/help/arxiv_identifier_for_services.html` · `https://info.arxiv.org/help/bulk_data.html` · `https://info.arxiv.org/help/bulk_data_s3.html` · `https://info.arxiv.org/help/rss.html`
Rate limits live in `tou.html`, not in `index.html` or `basics.html`.
`ir.html` is **Institutional Repository Interoperability** — not search semantics. It does not say what it looks like it says.
Already correct, do not "fix": `get_arxiv_paper_details` uses `id_list`, which the manual explicitly prefers *"to properly handle article versions"*; versioned (`2305.14314v2`) and old-style (`cs.CL/0306050`) IDs both work.

**OpenAlex** — the full set the owner supplied on 2026-09-20, written out so none is lost to abbreviation:
`https://help.openalex.org/api/`
`https://help.openalex.org/api/llm-quick-reference/`
`https://help.openalex.org/api/filtering/`
`https://help.openalex.org/api/searching/`
`https://help.openalex.org/api/semantic-search/`
`https://help.openalex.org/api/sorting/`
`https://help.openalex.org/api/grouping/`
`https://help.openalex.org/api/paging/`
`https://help.openalex.org/api/selecting-fields/`
`https://help.openalex.org/api/get-single-entities/`
`https://help.openalex.org/api/autocomplete/`
`https://help.openalex.org/api/endpoints/`
`https://help.openalex.org/api/deprecations/`
API root used in testing: `https://api.openalex.org/works?search=<q>&per-page=<n>`. Client option: `pyalex`, or plain `requests`.

**Europe PMC** — `https://europepmc.org/RestfulWebService` · tested endpoint `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=<q>&format=json&pageSize=<n>&resultType=core`

**Zenodo** — `https://developers.zenodo.org/` · tested endpoint `https://zenodo.org/api/records?q=<q>&size=<n>&type=software`

**bioRxiv / medRxiv (researched, deferred — see D19)** — `https://api.biorxiv.org/` · `https://api.medrxiv.org/`
No keyword, title, abstract or author search exists. Query options are date interval, DOI, cursor, **subject category**, and funder ROR. Records **do** include `abstract`, plus `jatsxml` (a free full-text XML link) and `published` (the journal DOI once a preprint is published). Volume measured 2026-09-19: bioRxiv one month unfiltered = **5,906** papers (~60 calls at 100/page); with `?category=bioinformatics` = **631** (~7 calls). There is a `/details/<server>/<N>d/json` recent-days endpoint. **Neither API documents a rate limit.**

**Competitor — `https://github.com/openags/paper-search-mcp`** · MIT, 2,661 stars, last push 2026-08-17. Borrowing is allowed with attribution.
Worth borrowing: `academic_platforms/google_scholar.py` (CAPTCHA detection, UA rotation, retries, proxy env var) and `academic_platforms/unpaywall.py` (DOI → legal OA PDF).
**Do not borrow:** `download_scihub` or the Sci-Hub step in `download_with_fallback` — MIT licensing does not cure copyright. Also do not copy its write-to-disk `download_*`/`read_*` pattern; it breaks our stateless rule.
Where we are already ahead: it has **no** citation-graph traversal at all — no references, citations, recommendations, author tools or snippet search. Do not regress that.

**Dead or excluded** — DBLP: dead on 2026-09-19, four probes hit an Anubis proof-of-work bot wall including with the competitor's own User-Agent; the `dblp.py` on `feat/all-databases` will not work. ACM DL: no public API, needs a subscription. IEEE Xplore: paid key, metadata only — both break MANIFESTO rule 1. Crossref, PubMed, bioRxiv/medRxiv: redundant against what we already have. CORE: flaky, returned HTTP 500 on a second probe.

---

> **← Previous:** none.
> **Next →** none yet.
