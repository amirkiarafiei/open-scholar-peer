#!/usr/bin/env bash
# clean_adapter.sh — Remove OSP-managed files from a tool's adapter directory.
#
# Per-tool installers call this BEFORE re-copying fresh adapter content, so
# files renamed or removed in extensions/_shared/ between installs don't leave
# stale orphans in the user's project.
#
# OSP-managed naming patterns (preserved across all 21 tools):
#   - commands/workflows/prompts/hooks:  [0-9]-osp-*.{md,toml}, open-scholar-peer.{md,toml}
#     The digit is deliberate. OSP owns 0-osp-* .. 6-osp-*; a bare *-osp-* would
#     also match a user's own `team-osp-eval` and delete it.
#   - skills/agents:                     {skills,agents}/osp-*/
#     …and on tools where skills ARE the slash commands (Hermes, Cline,
#     OpenClaw), the eight commands live there too, as [0-9]-osp-*/ and
#     open-scholar-peer/. Cleaning only osp-*/ would leave those behind.
#   - subagent definitions:              agents/osp-*.md  (flat files, not dirs)
#   - rules:                             varies (rules/osp-rules.{md,mdc}, GEMINI.md, AGENTS.md,
#                                        QWEN.md, RULES.md, guidelines.md, steering/osp-rules.md, …)
#   - defaults:                          defaults/  (entirely ours)
#
# User-authored files NOT matching these patterns (e.g. ./.claude/skills/my-thing/)
# are NEVER touched.
#
# Usage: bash clean_adapter.sh <dest_dir> <tool_name>
#   tool_name ∈ {claude, cursor, gemini, antigravity, antigravity-cli, copilot,
#                junie, kiro, codex, kimi, qwen, vibe, opencode, openhands,
#                pi, ohmypi, grok, hermes, cline, kilo, openclaw}

set -e

DEST="${1:?usage: clean_adapter.sh <dest_dir> <tool_name>}"
TOOL="${2:?usage: clean_adapter.sh <dest_dir> <tool_name>}"

# Nothing to clean if the dest doesn't exist yet
[[ -d "$DEST" ]] || exit 0

# Defaults; individual tools override below.
cmd_subdir="commands"
cmd_ext="md"
skill_subdir="skills"
agent_subdir=""          # only tools with separate subagent definitions
commands_are_skills=0    # the 8 commands live in skill_subdir as directories
legacy_cmd_subdir=""     # a command layout a previous OSP wrote and we no longer use

case "$TOOL" in
  claude|cursor|kimi|vibe|openhands)
    : ;;
  gemini)
    cmd_ext="toml" ;;
  antigravity)
    cmd_subdir="workflows" ;;
  antigravity-cli)
    # Commands are skills here now. `legacy_cmd_subdir` still sweeps the
    # workflows an older OSP wrote: the tool stopped reading them, so leaving
    # them behind is dead litter in someone's project that nothing would ever
    # remove.
    commands_are_skills=1
    legacy_cmd_subdir="workflows" ;;
  copilot)
    cmd_subdir="prompts" ;;
  junie)
    : ;;
  kiro)
    cmd_subdir="hooks" ;;
  codex)
    cmd_subdir="prompts" ;;
  qwen)
    skill_subdir="agents" ;;
  opencode)
    skill_subdir="agents" ;;
  pi)
    cmd_subdir="prompts" ;;
  ohmypi)
    agent_subdir="agents" ;;
  grok)
    agent_subdir="agents" ;;
  kilo)
    agent_subdir="agents" ;;
  hermes|cline|openclaw)
    commands_are_skills=1 ;;
  *)
    echo "clean_adapter.sh: unknown tool '$TOOL'" >&2
    exit 1 ;;
esac

# Commands / workflows / prompts (numbered + dispatcher), when they are files
if [[ $commands_are_skills -eq 0 && -d "$DEST/$cmd_subdir" ]]; then
  find "$DEST/$cmd_subdir" -maxdepth 1 -type f \
    \( -name "[0-9]-osp-*.$cmd_ext" -o -name "open-scholar-peer.$cmd_ext" \) \
    -delete 2>/dev/null || true
fi

# A command layout we used to write and no longer do. Swept so an upgrade does
# not leave files the tool has stopped reading.
if [[ -n "$legacy_cmd_subdir" && -d "$DEST/$legacy_cmd_subdir" ]]; then
  find "$DEST/$legacy_cmd_subdir" -maxdepth 1 -type f \
    \( -name "[0-9]-osp-*.md" -o -name "open-scholar-peer.md" \) \
    -delete 2>/dev/null || true
  rmdir "$DEST/$legacy_cmd_subdir" 2>/dev/null || true
fi

# Skills / agents. Always the osp-*/ personas; plus the command directories on
# tools where a skill is how a slash command is expressed.
if [[ -d "$DEST/$skill_subdir" ]]; then
  find "$DEST/$skill_subdir" -maxdepth 1 -type d -name 'osp-*' \
    -exec rm -rf {} + 2>/dev/null || true
  if [[ $commands_are_skills -eq 1 ]]; then
    find "$DEST/$skill_subdir" -maxdepth 1 -type d \
      \( -name '[0-9]-osp-*' -o -name 'open-scholar-peer' \) \
      -exec rm -rf {} + 2>/dev/null || true
  fi
fi

# Subagent definitions — flat markdown files, one per persona
if [[ -n "$agent_subdir" && -d "$DEST/$agent_subdir" ]]; then
  find "$DEST/$agent_subdir" -maxdepth 1 -type f -name 'osp-*.md' \
    -delete 2>/dev/null || true
fi

# Rules / always-on instructions (varies by tool)
case "$TOOL" in
  claude|antigravity)
    rm -f "$DEST/rules/osp-rules.md" ;;
  cursor)
    rm -f "$DEST/rules/osp-rules.mdc" ;;
  gemini)
    rm -f "$DEST/GEMINI.md" ;;
  copilot)
    rm -f "$DEST/instructions/osp-rules.md" ;;
  junie)
    rm -f "$DEST/guidelines.md" ;;
  kiro)
    rm -f "$DEST/steering/osp-rules.md" ;;
  qwen)
    rm -f "$DEST/QWEN.md" ;;
  codex|kimi|vibe|opencode|openhands|pi|hermes|kilo|openclaw)
    rm -f "$DEST/AGENTS.md" ;;
  ohmypi)
    # Deliberately nothing. Unlike every other entry here, omp's rules file
    # lives INSIDE the adapter directory (.omp/RULES.md) and is a file the user
    # may already own. Deleting it here would run before merge_agents_md.sh and
    # destroy their content — the merge script manages the OSP-BEGIN/OSP-END
    # block and must be the only thing that touches this file.
    : ;;
  grok|cline)
    rm -f "$DEST/rules/osp-rules.md" ;;
  antigravity-cli)
    rm -f "$DEST/AGENTS.md"
    rm -f "$DEST/rules/osp-rules.md" ;;
  *)
    echo "clean_adapter.sh: no rules rule for '$TOOL'" >&2
    exit 1 ;;
esac

# Defaults (entirely OSP-managed in every tool)
rm -rf "$DEST/defaults"
