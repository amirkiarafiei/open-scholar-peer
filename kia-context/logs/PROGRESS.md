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
| **M8** | Context harness | The harness holds a true picture of the project | M7 | ✅ Done 2026-09-11 |
| **M9** | Installer experience | Installing OSP is a guided, keyboard-driven flow instead of a numbered prompt, and the README says where to type the slash command | M8 | ✅ Done 2026-09-11 |
| **M10** | Antigravity gains subagents | Antigravity is treated like every other subagent-capable tool — no self-reflection fallback, and nothing anywhere still claims it cannot delegate | M9 | ✅ Done 2026-09-11 |

> **Numbering never restarts.** When this file is split, part two continues at the next M.

---

## ✅ M1–M7 — reconstructed summary

*Measured: `git rev-list --count 453a3d5` → 66 commits, `4e84c35` (2026-04-23) through `453a3d5`
(2026-09-11). Tags: `v1.0.0` 2026-05-09, `v1.1.0` 2026-05-10.*

**M1 · Foundation** — 2026-04-23 → 2026-05-08. The paper was added, summarised, and turned into a design
document (`genesis/IDEA.md`), then into an implementation plan (`PHASES.md`, since retired), the `.brain/` filesystem
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
- [x] **`docs/` narrowed to project documentation** — `IDEA.md` moved to `genesis/`, `PHASES.md` deleted, every reference updated (D14).
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

Harness filled. `GENESIS.md`, `MANIFESTO.md`, `ARCHITECTURE.md` and this file written from `genesis/IDEA.md`,
`docs/PHASES.md` (both since retired — D14), `docs/paper/SUMMARY.md`, `docs/ARTIFACT_CONTRACTS.md`,
`docs/KNOWN_LIMITATIONS.md`, the
canonical prompt sources, 66 commits of history, and a statement of intent from the owner. `DESIGN.md` was
deleted — the project has no interface, and the terminal output contract it might have held is documented
in `ARCHITECTURE.md` §10 where it belongs. `SEED.md` was kept but not reconstructed: the original prompts
were never captured and inventing them would fabricate a historical record.

Criteria 1–4 pass; criterion 5 is open because the installer scope has not been set. Four defects found
while reading are logged as O1–O4 in `BRAINSTORM.md` — none is blocking, two are user-visible.

**Second pass, same day.** `docs/` was narrowed to what a user or contributor needs: `IDEA.md` moved to
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

---

> **← Previous:** none.
> **Next →** none yet.
