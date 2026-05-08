# `_shared/` Manifest — Single Source of Truth

This file enumerates every canonical asset under `extensions/_shared/`. The sync script (`scripts/sync_adapters.py`) reads this manifest to know what to translate into per-tool adapter directories.

**Rule of thumb:** humans only ever edit files in `_shared/`. Per-tool directories (`extensions/.claude/`, `.cursor/`, `.gemini/`, `.agent/`, `.agents/`, `.github/`) are **generated artifacts**.

## Files in `_shared/`

### Skills (8 — one per persona + one orchestrator)

| Path | Persona | Triggered by |
|---|---|---|
| `skills/osp-orchestrator/SKILL.md` | Top-level brain protocol + dispatcher behavior | Any review-related phrasing or `/open-scholar-peer` |
| `skills/osp-summary-agent/SKILL.md` | Internal Compression — extract claims/method/evidence | `/1-osp-summary` |
| `skills/osp-literature-review-agent/SKILL.md` | External retrieval — 3-round strategy | `/2-osp-literature` |
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
| `commands/2-osp-literature.md` | `/2-osp-literature` | Invokes Literature Review Agent (3 rounds) |
| `commands/3-osp-historian.md` | `/3-osp-historian` | Invokes Historian Agent |
| `commands/4-osp-baseline-scout.md` | `/4-osp-baseline-scout` | Invokes Baseline Scout Agent |
| `commands/5-osp-qa.md` | `/5-osp-qa` | Invokes Query Agent (loops criteria, delegates to Answer Generator) |
| `commands/6-osp-review.md` | `/6-osp-review` | Invokes Reviewer Agent |

### Rules (always-on)

| Path | Notes |
|---|---|
| `rules/osp-rules.md` | Brain protocol summary — read session.json, load prior artifacts, update session.json, prefer subagent over self-reflection |

### Defaults (templates and fallback content)

| Path | Used by |
|---|---|
| `defaults/generic_review_guidelines.md` | `/0-osp-onboarding` when venue lookup fails and user has no guidelines |
| `defaults/qa_pair_template.md` | `/5-osp-qa` to enforce the N-pair structure per criterion (N = `session.json.qa_pairs_per_criterion`, default 2) |
| `defaults/round_strategy_template.md` | `/2-osp-literature` to enforce the 3-round structure |

## What gets generated where

For each canonical file in `_shared/`, the sync script produces a tool-specific equivalent:

| Source (in `_shared/`) | Claude (`.claude/`) | Cursor (`.cursor/`) | Gemini (`.gemini/`) | Antigravity (`.agent/` + `.agents/`) | Copilot CLI (`.github/`) |
|---|---|---|---|---|---|
| `commands/<name>.md` | `commands/<name>.md` (frontmatter) | `commands/<name>.md` | `commands/<name>.toml` | `workflows/<name>.md` | `prompts/<name>.md` |
| `skills/<name>/SKILL.md` | `skills/<name>/SKILL.md` | `skills/<name>/SKILL.md` | `skills/<name>/SKILL.md` | `skills/<name>/SKILL.md` | `skills/<name>/SKILL.md` |
| `rules/osp-rules.md` | `rules/osp-rules.md` | `rules/osp-rules.mdc` | `GEMINI.md` (always-on) | `rules/osp-rules.md` | `instructions/osp-rules.md` + `AGENTS.md` |
| `defaults/*.md` | `defaults/*.md` | `defaults/*.md` | `defaults/*.md` | `defaults/*.md` | `defaults/*.md` |

## Capability flags per tool

The sync script encodes a capability matrix that customizes the Q&A workflow:

| Tool | Subagents | Q&A mode | MCP config path |
|---|---|---|---|
| Claude Code | yes | subagent (osp-answer-generator-agent) | `.mcp.json` |
| Cursor | yes | subagent | `.cursor/mcp.json` |
| Gemini CLI | yes | subagent | `.gemini/extensions/<ext>/gemini-extension.json` |
| GitHub Copilot CLI | yes | subagent | `.github/copilot-cli/mcp.json` (TBD — see Phase 5) |
| Antigravity | **no** | **self-reflection** (turn markers) | `~/.gemini/antigravity/mcp_config.json` (global, manual) |
