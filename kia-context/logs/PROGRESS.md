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
status: closed
covers: "Extensions phase, 2026-04-23 → 2026-09-20 — M1–M13. Closed by the split; M14 onward is in PROGRESS_2.md."
last_updated: "2026-09-21"
---

# 📈 PROGRESS — What we are building

> **M1–M7 were reconstructed from git history and the retired `docs/PHASES.md` on 2026-09-11, not
> captured from the work as it happened.** Treat them as approximate: the commits say what changed,
> rarely why, and the acceptance criteria shown are the ones `PHASES.md` recorded at the time, not
> invented afterwards. **Everything from M8 onward was recorded live.**
>
> `PHASES.md` was deleted the same day (`BRAINSTORM.md` D14) because this file supersedes it. To read
> the original: `git show 027645b:docs/PHASES.md`.

> **← Previous:** none. This is part one, and it is **closed** — M1–M13, through 2026-09-20.
> **Next →** [`PROGRESS_2.md`](PROGRESS_2.md) — M14 onward. New entries go there, never here.

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
| **[M14 onward →](PROGRESS_2.md)** | **Part two — the prompt and protocol work** |

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
| **M11** | Repair the three existing providers | Every retrieval bug from the 2026-09-19 audit is fixed, each proved with a before/after measurement | M10 | ✅ Done 2026-09-20 |
| **M12** | Read the paper, not just its title | The agent can get full text for arXiv papers and for open-access biomedical papers | M11 | ✅ Done 2026-09-20 |
| **M13** | More open sources, and let the user pick them | Zenodo and OpenAlex work, and the installer lets the user choose databases and optionally enter keys | M12 | ✅ Done 2026-09-20 |
| **M14** | Source judgement, not a tool list | No prompt names a search tool it cannot guarantee | M13 | ✅ Done 2026-09-21 · [part two](PROGRESS_2.md) |
| **M15** | No step is a gate | Every phase runs with its inputs missing, and records the skip | M14 | ✅ Done 2026-09-21 · [part two](PROGRESS_2.md) |
| **M16** | One phase block | All 14 blocks come from one definition, enforced by a test | M15 | ✅ Done 2026-09-21 · [part two](PROGRESS_2.md) |

> **Numbering never restarts.** Part two continues at M14. The rows above are kept whole so this
> table stays the one place to see every milestone; the M14–M16 entries live in part two.

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

### Second review round — 2026-09-20 (late)

The live-API reviewer reported after M11 was already committed. It found one defect that made a
documented feature fail **every single time**, and one that inverted the milestone's headline fix.

| | Defect | Fix |
|---|---|---|
| 1 | **`sort=` was broken 100% of the time.** It forces the bulk endpoint, and `/paper/search/bulk` does not accept `tldr` — which B6 had just added to the field list. Every sorted search returned `Unrecognized or unsupported fields: [tldr]`. Nothing tested `sort`. | `tldr` is dropped when `bulk` is set. Verified live: `sort="citationCount:desc"` now returns `[193201, 121183, 69949, 62710, 35738]`. |
| 2 | **The block detector matched prose, and Google echoes your query.** `"unusual traffic"`, `"not a robot"` and `"our systems have detected"` appear in real papers — a results page for *"I'm not a robot: (Deep) Learning to Break Semantic Image CAPTCHAs"* was reported as a block. **This is B9 inverted**: telling the agent the provider is down when it answered perfectly, and doing it to exactly the reviews most likely to search those words. | Detection is now structural — HTTP status, the `/sorry/` redirect, and interstitial element ids matched in attribute position. A paper that merely discusses reCAPTCHA cannot trip it. Both directions are tested. |
| 3 | **An `&` in a query silently truncated it.** The package pastes the query into a URL, so `"Q&A over documents"` searched for **"Q"**. Bibliography titles hit this constantly. | Percent-encoded before the package sees it. |
| 4 | **A crafted category re-opened the boolean group.** `categories=["cs.CL) OR (cat:quant-ph"]` produced `(x) AND (cat:cs.CL) OR (cat:quant-ph)`, where the AND binds nothing — **the exact failure B2 existed to fix**. | Categories are validated against arXiv's own shape. |
| 5 | **`num_results` never reached Google** — no `num` parameter was sent, so the documented 1–20 was capped at Google's default 10. | Sent. |

**The instrument was lying too.** `scripts/test_providers.py` printed "✅ every check that could run
passed" and exited 0 when Semantic Scholar had verified *nothing* — and S2 was rate-limiting this
machine for most of the session, which is precisely when defect 1 would have been caught. It now says
**"NOTHING WAS PROVED"** in a banner, reports how many checks actually ran, and takes `--strict` to make
it an exit code. A run that proves nothing must not look like a run that passed.

**Cleared by that review**, worth recording because re-deriving it is the expensive half: B4 was checked
at **all 13 paging call sites** with the HTTP layer stubbed to always advertise another page — every one
makes exactly one request, and the control without `islice` reached 1,201 items over 13 requests and was
still going. B3's shared client was verified by identity under four concurrent threads: minimum gap
3.68 s, never more than one `Client.results()` in flight, no deadlock. The session-timeout patch does not
break the package's own retry. Every name in all three `fields=` lists is valid; `tldr` on bulk was the
only 400.

---

## 🏁 Milestone M12: Read the paper, not just its title

**Target.** Every OSP tool today returns metadata only. The Baseline Scout and the Q&A engine cannot check
*"does the cited paper actually report that number?"* from an abstract. This milestone gives the agent the
actual text, for the two sources where it is free and legal. Decisions: `BRAINSTORM.md` D20.

> **Correction to the 2026-09-19 review.** It said OSP "has no full-text access". That was wrong, and the
> owner caught it. arXiv gives full text to anyone — a free PDF and the LaTeX source. The gap is in our
> code: we store `pdf_url` and never open it.

### Deliverables

- [x] **F1 — arXiv download/read tools.** `arxiv` 4.0.1 **removed** `Result.download_pdf` and `download_source`; `Result` now exposes only `get_short_id()` and `source_url`. So fetch by plain HTTP from the URLs we already serialize. Two routes, and the second is the better one: **PDF** (`pdf_url`) always exists but needs a PDF reader and comes out messy for two-column text and maths; **LaTeX source** (`source_url`) is the real text, clean, equations intact, but arrives as `.tar.gz` and must be unpacked.
- [x] **F2 — make it easy for an agent to use** (owner's explicit request). Prefer a tool that takes an arXiv ID and returns text directly, over one that returns a file path. **A read tool must not write to disk** — the competitor's `download_*` tools persist to `./downloads`, which would break our stateless rule (D3). Returning text keeps it atomic.
- [x] **F3 — Europe PMC provider.** Open-access biomedical, **no key at all**, and it serves **full text over REST as XML — no PDF parsing**. This is the cheapest full-text path that exists. Verified 2026-09-19: a keyword search returned HTTP 200 with **2,304 hits**, and each record carried `fullTextUrlList` and an `isOpenAccess` flag.
- [x] **F4 — find the current Europe PMC docs before coding** (owner's request). Start at `https://europepmc.org/RestfulWebService`. Working endpoint shape confirmed on 2026-09-19: `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=<q>&format=json&pageSize=<n>&resultType=core`. `resultType=core` is what returns the abstract and `fullTextUrlList`.
- [x] **F5 — why Europe PMC matters here.** About **5 or 6 of the owner's ~30 reviewed papers are health or biology** (the Frontiers paper, `Sage/digital-health-mental-fatigue`, `MDPI/information_urinary_infection`, `MDPI/information_explain_mental_health`). arXiv covers almost none of that. This is a measured gap, not a hypothetical one.
- [x] **F6 — test the tools against the live API** before declaring the milestone done (owner's request).

### Acceptance criteria

1. Given an arXiv ID, a tool returns readable body text, not a link and not a file path.
2. Nothing is written to disk by any read tool.
3. Given a biomedical query, Europe PMC returns results with abstracts, and open-access ones expose a full-text route.
4. Both new tools carry the same rich docstrings the existing 15 have — that is what the agent reads to choose.
5. Provider failures return a structured error, never an empty list (the M11 B9 rule applies to new providers too).

**Depends on:** M11 (B5/B6 supply `openAccessPdf`, which this uses).

---

### Report — 2026-09-20

Three tools, 16 to 19. Nothing new in `requirements.txt`: the arXiv reader needs only `tarfile`,
`gzip` and `io` from the standard library, and Europe PMC needs `requests`, which was already there.

| Tool | What it returns | Measured 2026-09-20 |
|---|---|---|
| `read_arxiv_paper` | the author's LaTeX source, preamble and bibliography removed | `1706.03762` → **42,834 chars** |
| `search_europe_pmc` | biomedical records with abstracts and a full-text route | abstract on **3 of 3**, full text on **3 of 3** with `open_access_only` |
| `get_europe_pmc_full_text` | the whole article as text | `PMC12798607` → **54,966 chars**, no tags left |

**F1 — the PDF question answered without a PDF library.** The plan assumed full text might need a PDF
parser. It does not. `scripts/merge_mcp_config.py` already registers **two** MCP servers on every
install — `osp` and `markitdown` — and markitdown returns the complete text of an arXiv PDF, tables
included (checked on `arxiv.org/pdf/1706.03762`). So OSP adds no PDF dependency at all. It serves the
LaTeX source, which is cleaner than anything scraped out of a two-column PDF, and for the minority of
submissions that carry no source it returns an error naming the PDF URL and the reader the user already
has.

**F2 — text, not a file path.** Both tools return the text itself and write nothing to disk, which is
D20's rule and the reason the competitor's `download_*` pattern was not copied. The archive is unpacked
in memory. Long papers come back in windows: read the first, and if `truncated` is true call again with
`offset` set to `offset + returned_chars`. Verified that the second window continues where the first
stopped rather than overlapping.

Two details that decide whether the output is usable at all:

- **The preamble is dropped.** Without that, the first 400 characters of every paper are `\usepackage`
  lines. `\input` and `\include` children are spliced in reading order, so *Attention Is All You Need* —
  ten separate `.tex` files — comes back as one document that starts at the abstract.
- **Files the main document never includes are kept.** They were being appended after
  `\end{document}`, which the trimmer then cut, so they disappeared without a word. *Attention Is All
  You Need* was losing about 5,000 characters that way — 36,093 before the fix, 41,067 after.
- **`OPEN_ACCESS:Y AND IN_EPMC:Y` is not optional** on a Europe PMC search you intend to read.
  Without it the top hits have no `pmcid` at all and there is nothing to fetch — measured: the first
  result of the plain query had neither.

### Found before the reviewers: every download could outlive its own tool call

`OSP_CALL_TIMEOUT` is 90 seconds. `read_arxiv_paper` could spend 25 waiting for the arXiv connection,
3 on the rate gap and 60 on the request: **88 seconds**, which leaves the agent a bare "timed out"
instead of an error it can act on. Worse, `requests`' `timeout` applies to each socket operation, not to
the transfer, so a slow trickle had no bound at all. Both streaming loops now carry a wall-clock
deadline, each pinned by a test. (The figures first recorded here — 73 s and 55 s — were themselves
wrong, and the review round below says how: `requests` spends its timeout on the connect *and* on each
read, and an in-loop check overshoots by one read. The honest worst cases are **78 s** for arXiv and
**60 s** for Europe PMC, and the tests assert those.) Europe PMC's search was also calling `resp.json()` straight off the stream, walking around the
size cap it had just set; it now reads through the cap.

### The prompts

Adding a tool nobody is told about changes nothing, so five canonical files under `extensions/_shared/`
name the new sources: the Literature skill (Europe PMC joins the rounds for biomedical papers), the
Baseline Scout (**read the baseline, do not guess at it** — its whole job is checking claimed numbers),
the Answer Generator, `defaults/round_strategy_template.md` and `commands/2-osp-literature.md`. The
round template now also has a line for tools that returned an error, with the reason.

The prompts say plainly that not every database is installed in every project, because M13 makes that
true.

**Verified:** 104 offline checks, every live check for both new providers, `sync_adapters.py --check`,
`test_parity.py`, and the tool list in `mcp-server/README.md` cross-checked against the source so a
phantom tool cannot survive again.

### Review round — 2026-09-20

Two subagents: one on resource safety and adversarial input, one on whether an agent would use these
tools correctly and whether the text it gets back is usable. The second found the things that mattered,
and several of them were not bugs in the code but bugs in what the code promised.

| | Defect | Fix |
|---|---|---|
| 1 | **Citations do not resolve, and the docstring implied they would.** arXiv source carries `\citep{key}` markers; the paper's printed numbers exist nowhere in it, and no reference list ships — `1706.03762` has no `.bbl` and no `.bib` at all. The tool was sold as the way to check "does reference [12] report 92%?", which is the one thing it cannot do alone. | The docstring says so and points at `get_semantic_scholar_paper_references`. The return carries a `bibliography` field saying the same. |
| 2 | **The title and the author list were being thrown away.** `\title` and `\author` live in the preamble, which was dropped whole, so the agent got a paper it could not identify and a bare `\maketitle` that means nothing. | Both are carried over. Parsed with balanced braces, because `\thanks{}` nesting defeats a regex. |
| 3 | **`\label` was stripped while `\ref` survived** — 21 live cross-references pointing at nothing, on one paper. | Labels kept. They cost about thirty characters each. |
| 4 | **A mistyped PMCID looked like an outage.** Europe PMC answers **HTTP 500**, not 404, for an unusable identifier — confirmed on `PMC99999999`, `PMCNONE` and `PMC0`. That was reported as `reason: unavailable`, which by our own definition means "record the provider as unavailable and carry on without it". One typo would have retired Europe PMC for the rest of the review. | Format is validated before the request, and a 500 on a full-text path becomes `EuropePmcNotFound` → `reason: not_found`. |
| 5 | **Windows cut mid-number.** At one boundary the text split `$1.2\cdot10^` / `{21}$`. The dangerous version is a cut between `26.3` and `0`, which leaves a plausible, wrong number. | A shared `providers.window()` snaps the end back to a paragraph break, then a line break, then a space, and returns `next_offset` so nobody does the arithmetic. Round-trip reassembly is asserted byte-for-byte, live and offline. |
| 6 | **Four defects in the Europe PMC rendering**: the abstract heading appeared twice; `<label>` already says "Table", so placeholders read `[Table Table 1: …]`; and dropping the reference list left a bare `## References` heading, which reads as "this article has no bibliography". | The renderer was rewritten: a section with no content emits no heading, and a dropped reference list becomes `[Reference list omitted — 49 entries]`. |
| 7 | **Table contents are not included, only captions** — and the docstring called that "labelled placeholders". For a tool whose headline use is checking a reported number, and where the number is usually in a table, that is far too soft. | Said plainly, with the advice to follow `fullTextUrls` for it. |
| 8 | **`search_semantic_scholar_snippets` was a magnet for the wrong job.** Its docstring said "use when you need to verify that a paper actually discusses a specific concept" — but it searches the whole corpus and cannot be scoped to one paper. | Rewritten to say it is for *discovering* which paper to read, and to name the read tools for checking a specific one. |

**Found while fixing, and worse than the reported bug:** a `.tex` file the main document never
includes was appended after `\end{document}`, which the trimmer then cut. It disappeared without a
word. *Attention Is All You Need* was losing about 5,000 characters this way.

**Two of my own tests were wrong and one hid a real bug.** The window snap guard read
`len(chunk) > 200`, which is false when `max_chars` is exactly 200 — so the snapping never ran for
small windows and the cut landed mid-word. The test that caught it had itself been asserting the wrong
thing.

### The prompts had the words but not the slots

The most useful finding was not about code. Both skills gained good prose about reading the paper, but
the **numbered procedure and the output template** — the parts an agent actually executes — were
untouched, and an agent fills the template it is given. The Baseline Scout had nowhere to record that
it had read anything, and its brief mentioned catching a **misquoted** number with no table to put one
in. `commands/4-osp-baseline-scout.md` still listed `osp-mcp.search_*`, a glob that excludes both new
tools, and `commands/2-osp-literature.md` still said "3 databases".

Fixed: a **Papers read in full** field and a **Misreported comparisons** table in the Baseline Scout, a
read step in the Answer Generator's verification protocol and its output template, corrected tool lists
and effort estimates in both commands, and a rewritten tools block in
`defaults/round_strategy_template.md` that separates *called*, *not installed*, *out of scope* and
*failed* instead of collapsing them into one line. A fallback route was added for the common case:
no arXiv id → `match_semantic_scholar_title` → `externalIds.ArXiv` → read; still nothing → the
open-access PDF through markitdown; no route at all → **say so** rather than reading the abstract and
calling it a check.

Fixed in passing: `commands/4-osp-baseline-scout.md` had steps 6 and 7 as the same line twice — one of
the four instances recorded in **O1**.

**Safety, checked by running rather than reading.** A tarball whose `.tex` unpacks to 200 MB is refused
without being read into memory; 5,000 members stop at the cap; a member named `../../tmp/...` writes
nothing, verified against the filesystem. An XML entity bomb is refused. 400 levels of nesting do not
exhaust the stack. Paging no longer re-downloads the paper for every window — a 2-entry cache, with its
own lock, because providers run in worker threads.

**Verified:** 156 offline checks, every live check for both providers, exact round-trip reassembly of a
43,180-character paper, `sync_adapters.py --check`, `test_parity.py`, and the README tool list
cross-checked against the source.

---

### Second review round — 2026-09-20 (resource safety)

The safety reviewer ran the providers rather than reading them, and found **four ways to take the
server down** with a file small enough to slip under every existing cap.

| | Defect | Measured | Fix |
|---|---|---|---|
| 1 | **gzip bomb.** The single-file branch called `gzip.decompress()` with no ceiling. Only `_MAX_DOWNLOAD` applied, and gzip reaches about 1030:1. | a **4.7 MB** e-print expanded to **1,073,741,864 characters and 3.1 GB of RSS** — and returned *successfully*. At 4 GiB it raised MemoryError. | read through the unpacked cap instead. Refused in 0.1 s. |
| 2 | **`tf.getmembers()` built the whole index** before `_MAX_MEMBERS` was ever consulted. | 2M empty members → 914 MB and 34.9 s; 9M → **4 GB and 157 s**, well past the call timeout, on a thread that cannot be cancelled. | iterate the archive lazily, with a parse budget. 0.04 s. |
| 3 | **Quadratic bibliography regex.** `\begin{...}.*?\end{...}` with `re.S` rescans to end-of-file for every unmatched opener. | 508 KB → 10.6 s; at the per-file cap, about **1.8 hours**. | `find()` instead of a regex. 0.00 s. |
| 4 | **Quadratic `_braced`**, and it runs first. | 64 KB of unclosed `\title{` → 22.1 s; at the cap, roughly **ten days**. The archive compressed to 2.5 KB. | bounded on both axes. 0.03 s. |

Any twenty of these would have filled the default thread pool and wedged every later call.

Six smaller ones in the same pass: `read_paper` returned `total_chars: 0` with **no error** for a body
that was entirely comments, which reads as "this paper is empty"; namespaced JATS lost the whole
article, because `.//article-title` does not match `{ns}article-title` — and then reported it as
"probably not open access", the wrong reason sent to someone who would go looking in the wrong place;
an article with one paragraph and no title was rejected the same way; 500 nested sections raised
`RecursionError`; two input errors bypassed `_err` and carried no `reason`; and the transfer budget was
**wrong by measurement** — 76.1 s against a slow server, because `requests` spends its timeout on the
connect *and* on each read, and an in-loop deadline check overshoots by one read. The deadline now
starts before the request. Re-measured: 42.0 s against a 35 s budget, inside the margin the comment
claims.

**The cache added in M12 was two-thirds wrong.** A re-audit measured it: nine concurrent readers of the
*same* paper caused **six downloads**, and three of them were refused with `ArxivBusy` for a paper
already being fetched — reachable whenever the Q&A engine runs subagents in parallel on one paper. And
at two entries, a phase reading three papers in turn missed on **every single read** (41/41/40 downloads
over 200 reads) while still paying the three-second gap on each miss. Now one download per paper however
many callers ask at once, and eight entries: nine threads → **1 download, no refusals**; the round robin
→ **3 downloads instead of 30**.

**What the safety pass cleared**, and it is the half worth not re-deriving: **nothing is written to
disk**, proved by `strace` on real reads — zero non-read file operations — and independently by patching
`open`/`os.open`. Hostile member names (`../../etc/...`, absolute paths, symlinks, device nodes) write
nothing. XML entity expansion is refused, and pushing the DOCTYPE past the sniff window does not get
through either. The windowing has **no off-by-one**: consecutive windows partition the text whatever the
snap does, checked over 18 adversarial shapes × 9 sizes, 3,000 random texts and 2,000 random offsets,
with zero failures.

---

## 🏁 Milestone M13: More open sources, and let the user pick them

**Target.** Add the two remaining agreed sources, and give the installer a way to choose databases —
because OpenAlex is the first source after Semantic Scholar that wants a key, and the user should see that
before installing. Decisions: `BRAINSTORM.md` D19 and D21.

### Deliverables

- [x] **S1 — Zenodo provider.** Open, no key. Verified 2026-09-19: `https://zenodo.org/api/records?q=<q>&size=<n>&type=software` returned HTTP 200 and **12,570** software records for a test query. Docs: `https://developers.zenodo.org/`.
- [x] **S2 — use Zenodo for the right question.** It does not find papers. It finds code, datasets and software releases. Give it its own job: *"did the authors release their code and data?"* — a reproducibility criterion on most venue review forms that the agent currently cannot check at all. Do **not** put it in the literature rounds.
- [x] **S3 — OpenAlex provider.** ~**327,426,920** works (live `meta.count`, 2026-09-19). Its unique value is **`is_retracted`** — **135,702** flagged works. Nothing else we have can tell the agent that a cited paper was retracted, and recommending "accept" on a paper leaning on retracted work is exactly the failure that catches. Also gives `referenced_works`, `topics`, ROR-linked institutions, `best_oa_location`, `fwci`.
- [x] **S4 — OpenAlex key handling.** OpenAlex moved to free API keys on **2026-02-13**. Keyless still answers but is capped at **100 credits/day**, and a list call costs **10** — about **10 searches a day**, which is unusable. A free key gives **100,000/day at 100 req/s**. So OpenAlex is *optional-key* in the same sense as Semantic Scholar, and must be labelled that way in the installer. One gotcha: **OpenAlex returns abstracts as an inverted index** and they must be reconstructed into text.
- [x] **S5 — installer database picker** (owner's design). Extend the M9 TUI so the user explicitly selects which paper-search databases to enable. Show a readable table with, per database: **free / key required / optional key**, and **which domain it covers**. Keep the existing keyboard model — arrows, space to toggle, the framed Install button.
- [x] **S6 — optional key entry during install.** After selecting, offer to type each key right there, with a clear skip. If skipped, tell the user the `.env` file exists and they can add keys later. Never require a key to finish the install.
- [x] **S7 — the table content** (as agreed 2026-09-19): arXiv — free, preprints, CS/physics/maths. Semantic Scholar — optional key (speed only), all fields. Google Scholar — free, broad, best-effort scraping. Europe PMC — free, biomedical, full text. Zenodo — free, code/data/software. OpenAlex — optional key, all fields, retraction flags.

### Acceptance criteria

1. Zenodo and OpenAlex tools work against the live APIs and return structured errors on failure.
2. OpenAlex abstracts come back as readable text, not an inverted index.
3. The installer table states the key status and domain of every database correctly.
4. An install with no keys entered completes and works; the user is told where `.env` is.
5. Tool count stays manageable — see O12 on tool-list growth.

**Depends on:** M12.

---

### Report — 2026-09-20

Two databases, three tools, and a picker that actually does something. 19 to 22 with everything on —
and, for the first time, a project can carry fewer.

| | Measured 2026-09-20 |
|---|---|
| **S1/S2 Zenodo** | `type=software` search returns typed records, every one with a DOI, many with a GitHub link in `relatedIdentifiers` |
| **S3 OpenAlex** | the Wakefield 1998 MMR paper returns `isRetracted: true`; *Deep Learning* returns `false`; **135,737** flagged works in the index |
| **S4 inverted index** | abstracts come back as readable text on 3 of 3 — OpenAlex stores them as `{word: [positions]}` |
| **S5/S6/S7 the picker** | a real install with `--sources arxiv,openalex,europepmc` wrote `.env` and the server registered **7 tools, not 22** |

**The picker had to shorten the tool list, or it was theatre.** D21 rejected "always on" precisely
because a longer tool list costs the agent on every request, so recording the choice and ignoring it
would have missed the point. `install.sh` writes `OSP_SOURCES` to `.env`; `osp_mcp.py` reads it once at
start-up and registers only those tools, through a `@tool_for("<source>")` decorator in place of
`@mcp.tool()`.

Measured across the range: unset → 22 tools, three sources → 17, one source → 3. An unknown name warns
and is ignored but does not disable a valid name beside it (`arxiv,nonsense` → 3). A value naming
nothing valid falls back to **all** rather than leaving the agent with no tools at all. `europe_pmc`,
`epmc`, `s2` and `scholar` are understood, and case and spacing do not matter.

**Unset means everything**, so an install made before today is untouched, as is anyone running a
per-tool script directly.

### The installer

The database picker is step 3 of 3, after the agent menu. `menu_databases()` follows `menu_tools()` exactly — index-aligned arrays, marks as a
`0`/`1` string for bash 3.2, the framed button as index `n`, and **geometry re-measured every frame**,
which is the defect the M9 review found and the reason that comment exists. The rows carry two extra
columns, key status and domain, which is S7's table.

Keys are offered once, before anything is installed, read with `read -rs` so they are never echoed and
never reach a log. Skipping is a keypress and the install finishes regardless: no database here needs a
key, and requiring one would break MANIFESTO rule 1.

`scripts/init_mcp.sh` is **sourced once per selected tool**, up to fourteen times in one install, so it
cannot prompt. Everything is collected once in `install.sh` and exported. `init_mcp.sh` then upserts
only the lines OSP owns — verified: a user's own `.env` content survives byte for byte, a stale
`OSP_SOURCES` is replaced rather than duplicated, and the file ends up `chmod 600` because it holds
keys.

`--sources` mirrors `--tool` for scripted use, rejects an unknown name with exit 2 and a list of the
valid ones, and defaults to all six when only `--tool` is given.

### What the agents were told

A tool nobody is told about changes nothing. OpenAlex joins the literature rounds as a general source.
Zenodo explicitly does **not** — it finds code, not papers, and the literature skill says so, because an
agent that searches Zenodo for papers pollutes the corpus.

Both new checks went to the Baseline Scout, which is the adversarial persona and the right home for
them:

- *Was the code or data released?* Most review forms ask, and nothing in this system could check it.
- *Has anything the paper leans on been retracted?* One retracted load-bearing citation changes a
  verdict, and `isRetracted` is the only way to see it.

Each has a slot in the output template and its own table, not just a paragraph — the M12 review's
lesson was that an agent fills the template it is given.

### The numbers in ARCHITECTURE were all stale, and are now measured

§9 said "15 MCP tools over three providers" with a per-provider table and a self-verifying grep. All of
it was wrong, and nothing in the repository checks such a claim. Re-measured against the code:
22 tools, 3/11/3/2/1/2 across six databases, 1,455 lines of canonical prompt markdown against 5,226 of
Python and 2,254 of shell. The grep in the file now reads `grep -c '^@tool_for('`, which is the honest
command.

The section's "what this section claims, and where the code does not deliver it" table — three
admissions written on 2026-09-19 — is replaced by a then/now table, because M11 fixed all three. The
warning that **an API key made OSP slower** is gone with them: that was the auto-pagination issuing
100–200 requests where one was asked for.

**Verified:** 179 offline checks, every live check for both new providers, a real end-to-end install
proving the gate, all 14 installer smoke tests, `sync_adapters.py --check`, `test_parity.py`, and every
count in `ARCHITECTURE.md` re-derived from the source programmatically rather than by hand.

---

### Review round — 2026-09-20

Two reviewers: one on the two new providers and the gate, one on the installer.

**The gate came through clean**, which matters because it is the milestone. 45 values were probed and
every source's tool set checked for exact equality: arXiv 3, Semantic Scholar 11, Google Scholar 3,
Europe PMC 2, Zenodo 1, OpenAlex 2 — summing to 22 with no overlap and no gap, and all 15 pairs giving
exactly the union. Every one of the 22 tools was checked against the provider its body actually calls;
none is filed under the wrong source. Aliases, case, whitespace, tabs, newlines, outer quotes, an
unbalanced quote, doubled commas, duplicates and a 5,000-item list all resolve correctly. `nonsense`,
`arx`, `all`, `*`, `arxiv;rm -rf /` and 20,000 junk characters all warn and fall back to every source —
**never toolless**. Warnings go to stderr, so they cannot corrupt the stdio protocol.

Six findings, all in the new providers:

| | Defect | Fix |
|---|---|---|
| 1 | **A missing record was reported as an outage.** `OpenAlexError` covered 404 too, so it landed in `reason: unavailable` — which by our own definition means "record the provider as unavailable and carry on without it". The headline use of this milestone is feeding it every DOI in a bibliography, so **the first un-indexed DOI would stop the agent checking retractions for the rest of the review**. | `OpenAlexNotFound` and `ZenodoNotFound`, both mapped to `not_found`. |
| 2 | **Bare PMIDs and arXiv ids did not work, and both docstrings promised them.** OpenAlex needs the `pmid:` namespace and has no arXiv one at all. | digits route to `pmid:`; the docstring stops promising arXiv ids and says where to get the DOI. |
| 3 | **An upper-case `doi.org` URL raised `IndexError`** — the test lower-cased but the split did not — surfacing as "failed: list index out of range". `dx.doi.org` was not recognised at all. | one case-insensitive regex. |
| 4 | Three input errors returned straight from the provider and carried no `reason`. | they raise, so `_err` tags them `bad_request`. |
| 5 | The Zenodo rate-limit message quoted the documented 60/minute; the live API reports **30**, and the cap a long review actually reaches is 2,000/hour. | both stated, with `Retry-After` when Zenodo sends it. |
| 6 | The 429 message pointed at `ZENODO_API_TOKEN`, which the generated `.env` never mentioned. | documented in the template. |

Found while fixing: both new providers had a single 60-second `timeout`, which on its own could outlast
the 90-second call ceiling. Given the same budget as the others — 30 s worst case.

**The installer was driven, not read.** Through a pty at nine terminal heights from 40 down to 6: the
title and the Continue button are reachable at every one, and the scroll window engages correctly below
12 rows. **Resizing 40 → 14 mid-menu recovers** — the M9 defect is not reintroduced, which was the main
risk in copying that function. Under `LANG=C` the rendered screen contains **zero non-ASCII bytes** and
falls back to `[x]`/`[ ]`. The cursor is balanced on every exit path. The `eval` used to hold a typed
key is not injectable: `$(...)`, backticks, quotes, backslashes and pipes are all stored literally, with
nothing executed.

`.env` handling survives a two-tool install, where `init_mcp.sh` is sourced twice: `OSP_SOURCES` is
written **once**, a stale value is replaced rather than duplicated, the user's own lines come through
byte-identical, the file ends up `chmod 600`, and no `.env.XXXXXX` is left behind.

---

### Follow-up — 2026-09-20: a blocker this milestone introduced

The installer reviewer reported after M13 was committed, and found a release blocker **created by this
milestone**.

**`bash install.sh --tool claude > install.log` refused to run.** The no-TTY guard used to hang off
`TOOL_FLAG_SEEN`; adding `--sources` re-parented it to `SOURCES_FLAG_SEEN`, so naming a tool up front no
longer satisfied it. Every pipe, `tee`, redirect, CI job and Dockerfile broke, along with the line in
`README.md` that recommends exactly that command — and it silently contradicted finding 7 of the M9
review, which had established that the gate tests whether the *flag was seen*. Confirmed by running the
same command against `7b3c6da`: exit 0 and a full install before, exit 1 after. The mirror case,
`--sources` with no `--tool` and no terminal, fell through to the menu and died with "Cancelled" instead
of the helpful message.

The guard is its own block again, testing `TOOL_FLAG_SEEN`. Re-verified across the matrix: `--tool` with
stdout redirected installs and writes all six sources; `--tool --sources arxiv` installs and writes one;
`--sources` alone and a bare invocation both give the guidance and exit 1; a bogus database exits 2.

**A `.env` with no trailing newline lost the database choice.** The rewrite branch handled a missing
final newline; the append branch did not, so `LAST_LINE=nonewline` + `OSP_SOURCES=...` became one line —
corrupting the user's last setting *and* leaving `grep -c '^OSP_SOURCES='` at zero, so the picker's whole
output went nowhere. Fixed and tested.

Four more from the same pass: Zenodo's token was documented in `.env` but the picker labelled Zenodo
free and never offered it, so it is optional-key now like the other two; a pasted key keeps its
whitespace and a silently-wrong key is worse than none, so keys are trimmed; `osp_env_set` returned 1 on
a `mktemp` failure, which under `set -e` killed a *sourced* installer after the venv was already built,
so it warns and carries on; and the variable **name** spliced into an `eval` is now validated, because a
per-tool installer can be run directly with `OSP_KEY_NAMES` inherited from the environment.

**What the installer pass cleared, having driven it rather than read it:** the `drawn` line-count
arithmetic is exact at every layout tier for both menus — 17/17, 13/13, 9/9, 7/7, 5/5 — checked by
matching each rewind against the newlines the previous frame actually emitted. The resize defect did not
return, across fifteen heights and every layout boundary including a six-times hard 40↔6 flip. Keys,
cursor balance on all seven exit paths, four non-UTF-8 locales, the full `--sources` matrix, and a typed
key appearing nowhere in the pty byte stream: all clean. bash 3.2 respected.

**One real gap left open, pre-existing and shared with the tools menu:** both smear below about 78
columns, because `hr()` assumes 80 and the frame wraps. Recorded as **O19**.

---

### Independent review — 2026-09-20: Antigravity, Gemini 3.8 Flash (High)

The owner asked for two reviews from outside this session, run through their own CLIs. This is the
first. It read all five commits with no knowledge of how they were produced, ran the four verification
gates, and was told to report only what the six in-session reviewers had missed. It found twelve
things, and **one of them proves a claim already written into this file was false.**

| | Defect | Severity | Fix |
|---|---|---|---|
| 1 | **The XML entity guard could be walked past.** It sniffed only `xml[:8192]`, so 9 KB of leading comment put the `<!ENTITY` declaration outside the window and the bomb parsed and expanded. **This file claimed the opposite** — the M12 review round said "pushing the DOCTYPE past the sniff window does not get through either", on the word of an in-session reviewer who tested it and got it wrong. Reproduced here in one command. | **HIGH** | Two guards now: the scan covers the whole document, which is capped anyway, and expat is given an `EntityDeclHandler` that refuses the declaration outright. Three padding variants tested, and an ordinary external-DTD DOCTYPE still parses. |
| 2 | **The arXiv retry arithmetic was wrong, and so was the test that pinned it.** `Client._parse_feed` starts at `_try_index = 0` and recurses while `_try_index < num_retries`, so the default of 3 means **four** requests, not three. 4 × 20 s plus spacing is 89 s inside `results()` alone; with `_LOCK_WAIT` the worst case was **104 s** against a 90 s ceiling — on a thread that cannot be cancelled and that keeps the lock. | **HIGH** | `num_retries` is pinned at 2 (three attempts) and the timeout cut to 15 s. Worst case **66 s**, and the test now uses `num_retries + 1`. |
| 3 | `get_arxiv_paper_details` on an unknown id **returned a dict**, so it never passed through `_err` and carried no `reason`. | MEDIUM | raises `ArxivNotFound`. |
| 4 | `get_google_scholar_author_info` did the same for a missing profile, and re-raised a bare `ConnectionError`, which arrived as `failed` rather than `unavailable`. | MEDIUM | `GoogleScholarNotFound` — deliberately *not* a subclass of `GoogleScholarUnavailable`, because the provider answered — and anything else is wrapped. |
| 5 | The Semantic Scholar package raises its own `ObjectNotFoundException` and `BadQueryParametersException`, neither of which `_err` knew, so both arrived as `failed`. | MEDIUM | matched by name, so a missing optional dependency cannot break error reporting. |
| 6 | **A 429 from OpenAlex or Zenodo was reported as `unavailable`** — which by our own contract tells the agent to stop using the provider, when a key would fix it. | MEDIUM | `OpenAlexRateLimited` and `ZenodoRateLimited`. |
| 7 | The live runner did not know those two types either, so a 429 from them **failed the run** as if it were a local defect. | MEDIUM | added to `_rate_limited()`. |
| 8 | Stale figures in `ARCHITECTURE.md`: the cache is 8 entries not 2, `_LOCK_WAIT` 15 s not 25, the arXiv download budget 35 s not 45, Europe PMC 60 s not 55, and the Python line count 1,640 against a real 5,851. Rule 7 again. | LOW | every number re-derived from the source. |
| 9 | `open_alex` was not an alias, although `europe_pmc`, `s2` and `scholar` all are — so a user writing it by analogy silently got all six databases, and `install.sh --sources open_alex` exited 2. | LOW | aliased in both, and `install.sh` now accepts every alias the server does. |
| 10 | `openalex.get_work`'s own docstring still promised arXiv ids after the M13 round removed that promise from the tool. | LOW | corrected. |
| 11 | `.bbl` files are collected now, so the reference list *is* in the output — while the `bibliography` field still said "not included". | LOW | the field reports what is actually there. |
| 12 | `--sources` skipped the key prompt along with the picker, so an interactive user who pre-selected databases was never offered a key. | LOW | the prompt is offered whichever way the databases were chosen. |

**What it cleared:** the tool gate across quoting, whitespace and aliases; bash 3.2 compliance and the
`osp_env_set` trailing-newline handling; every resource bound in the archive reader and the lazy tar
iteration; the windowing algorithm's byte-exact reassembly; `islice` on every paging call site; the
percent-encoding fix; `sort` stripping `tldr`; and the structural block detector, which it confirmed no
longer false-positives on papers about CAPTCHAs.

**The lesson worth keeping.** Finding 1 existed because this file recorded a *reviewer's* conclusion as
a fact. The in-session reviewer had tested the bypass, reported that it was safe, and I wrote that down
without re-running it. Rule 7 says every number is measured; the same applies to every security claim.
It is now a test, not a sentence.

---

### Installer follow-up — 2026-09-21, after the owner used it

Three commits of refinement on M13's picker, from the owner watching it run. Recorded here rather than
as a milestone because it is one feature being finished, not new scope.

**What changed** (`503a574`, `0fbb826`): the agent picker now comes **before** the database picker; the
database picker opens with **arXiv and Semantic Scholar** ticked rather than all six; keys are behind a
single **yes/no question** instead of a prompt per database, defaulting to No and asked only when a
selected database takes a key that is not already set; and the closing "what to do next" text became a
framed panel with all-caps headings and indented values, chosen from five rendered designs.

Whichever picker runs last carries the Install button, so its label is computed per frame — "Continue"
while a key question still follows, "Install" when it does not.

**The review found nine defects, and one was mine twice over** (`c2c86b9`). Renaming a help line from
"tab jumps to Install" to "tab jumps to the button" took it from 77 to **80 visible columns**. Below 80
it wraps to two terminal rows while `drawn` counts one, so every rewind falls a line short and the menu
walks down the screen — **the M9 defect, in the width dimension instead of the height one**. Measured:
the parent was clean to 77 columns; the new commit broke at 79, 78 and 77. The line is 60 columns now.

That is the second time a width assumption has bitten this file, and it is why **O19 stays open**: both
menus are still bounded by a pre-existing 77-column footnote, and nothing measures width the way the
redraw loop measures height.

Also fixed: the agent button still promised "Install" and then asked for keys on the `--sources` path;
the panel reported "api keys none set" immediately after the user typed one, because it read `$var`
while `collect_keys` writes `OSP_KEY_$var`; the panel assumed 78 columns and shredded below that;
`${#plain}` measured characters rather than display columns, so a CJK path pushed the border out; a
failed tool was listed as installed four lines under its own failure notice; and truncation was silent.

**Verified:** 251 offline checks, 14/14 installer smoke tests, the help line measured at every column
from 76 to 100, and the panel uniform at both 60 and 100 columns.

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

> **← Previous:** none. This is part one.
> **Next →** [`PROGRESS_2.md`](PROGRESS_2.md) — M14 onward.
