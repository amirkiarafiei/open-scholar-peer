# `_shared/` Manifest — Single Source of Truth

This file enumerates every canonical asset under `extensions/_shared/`. It is documentation for humans: the sync script (`scripts/sync_adapters.py`) does **not** read it — it walks the filesystem, globbing `commands/`, `skills/`, `defaults/` and `rules/osp-rules.md`. So a new file here needs no registration to be synced, but it does need a row below, or the next reader will not know it exists.

**Rule of thumb:** humans only ever edit files in `_shared/`. Every `extensions/.<tool>/` directory is a **generated artifact**, wiped and rewritten on each sync.

## Files in `_shared/`

### Skills (8 — one per persona + one orchestrator)

| Path | Persona | Triggered by |
|---|---|---|
| `skills/osp-orchestrator/SKILL.md` | Top-level brain protocol + dispatcher behavior | Any review-related phrasing or `/open-scholar-peer` |
| `skills/osp-summary-agent/SKILL.md` | Internal Compression — extract claims/method/evidence | `/1-osp-summary` |
| `skills/osp-literature-review-agent/SKILL.md` | External retrieval — 3-round strategy, 3 recommended not required | `/2-osp-literature` |
| `skills/osp-historian-agent/SKILL.md` | Domain narrative compression | `/3-osp-historian` |
| `skills/osp-baseline-scout-agent/SKILL.md` | Adversarial baseline auditor | `/4-osp-baseline-scout` |
| `skills/osp-query-agent/SKILL.md` | Probing question generator (main thread) | `/5-osp-qa` |
| `skills/osp-answer-generator-agent/SKILL.md` | Verifier/responder (subagent or self-reflection) | spawned by query agent |
| `skills/osp-reviewer-agent/SKILL.md` | Final synthesis | `/6-osp-review` |

### Commands (8 — one dispatcher + 7 numbered steps)

| Path | Slash command | Notes |
|---|---|---|
| `commands/open-scholar-peer.md` | `/open-scholar-peer` | Stateless dispatcher — reads `session.json`, prints status, advises next command |
| `commands/0-osp-onboarding.md` | `/0-osp-onboarding` | Venue lookup, paper detection, criteria scaffolding |
| `commands/1-osp-summary.md` | `/1-osp-summary` | Invokes Summary Agent |
| `commands/2-osp-literature.md` | `/2-osp-literature` | Invokes Literature Review Agent (up to 3 rounds; the user chooses) |
| `commands/3-osp-historian.md` | `/3-osp-historian` | Invokes Historian Agent |
| `commands/4-osp-baseline-scout.md` | `/4-osp-baseline-scout` | Invokes Baseline Scout Agent |
| `commands/5-osp-qa.md` | `/5-osp-qa` | Invokes Query Agent (loops criteria, delegates to Answer Generator) |
| `commands/6-osp-review.md` | `/6-osp-review` | Invokes Reviewer Agent |

### Rules (always-on)

| Path | Notes |
|---|---|
| `rules/osp-rules.md` | Brain protocol summary — read session.json, load prior artifacts, update session.json, prefer subagent over self-reflection |
| `rules/search_via_cli.md` | Appended to the always-on file **only** for a tool whose `search_mode` is `cli` — one with no MCP client. Tells the agent to reach the search tools by running `osp_cli.py`. Today that is Pi alone. Not synced on its own; it is merged into the rules content at sync time. |

### Defaults (templates and fallback content)

| Path | Used by |
|---|---|
| `defaults/generic_review_guidelines.md` | `/0-osp-onboarding` when venue lookup fails and user has no guidelines |
| `defaults/qa_pair_template.md` | `/5-osp-qa` to enforce the N-pair structure per criterion (N = `session.json.qa_pairs_per_criterion`, default 2) |
| `defaults/round_strategy_template.md` | `/2-osp-literature` — one file per round actually run |
| `defaults/phase_block_template.md` | every phase — the one definition of the opening and closing blocks printed to the **terminal**. Never written to `.brain/` |

## What gets generated where

The shape differs per tool, and the authority is the `ToolCaps` matrix in `scripts/sync_adapters.py` —
not this file. Reproduce it whenever you need it:

```bash
python3 -c "import sys; sys.path.insert(0,'scripts'); from sync_adapters import TOOLS
for n,t in TOOLS.items(): print(f'{n:16} {t.command_dir:10} .{t.command_ext:5} skills={t.skill_dir:8} rules={t.rule_dir} qa={t.qa_mode}')"
```

In outline, every tool gets the same four kinds of asset:

| Source (in `_shared/`) | Becomes |
|---|---|
| `commands/<name>.md` | a command file under the tool's command directory — Markdown for most, TOML for Gemini CLI — or, on a tool where a skill *is* a slash command (`commands_as_skills`), a skill directory `<skill_dir>/<name>/SKILL.md` |
| `skills/<name>/SKILL.md` | `<skill_dir>/<name>/SKILL.md`, plus a flat `<agent_dir>/<name>.md` on the tools whose delegation resolves an agent file rather than a skill |
| `rules/osp-rules.md` | the tool's always-on file: a rules directory, or `AGENTS.md` / `GEMINI.md` / `QWEN.md` / `RULES.md` / `guidelines.md` at its root |
| `defaults/*.md` | `defaults/*.md`, unchanged, for every tool |

The single content-level branch is the Q&A banner, which `adapt_qa_body_for_tool()` injects into
`5-osp-qa` with one of three outcomes: `subagent`, `prefer-subagent`, `self-reflection`.
