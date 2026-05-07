#!/usr/bin/env bash
# clean_adapter.sh — Remove OSP-managed files from a tool's adapter directory.
#
# Per-tool installers call this BEFORE re-copying fresh adapter content, so
# files renamed or removed in extensions/_shared/ between installs don't leave
# stale orphans in the user's project.
#
# OSP-managed naming patterns (preserved across all five tools):
#   - commands/workflows/prompts:  *-osp-*.{md,toml}, open-scholar-peer.{md,toml}
#   - skills:                      skills/osp-*/
#   - rules:                       rules/osp-rules.{md,mdc}, GEMINI.md, instructions/osp-rules.md
#   - defaults:                    defaults/  (entirely ours)
#
# User-authored files NOT matching these patterns (e.g. ./.claude/skills/my-thing/)
# are NEVER touched.
#
# Usage: bash clean_adapter.sh <dest_dir> <tool_name>
#   tool_name ∈ {claude, cursor, gemini, antigravity, copilot}

set -e

DEST="${1:?usage: clean_adapter.sh <dest_dir> <tool_name>}"
TOOL="${2:?usage: clean_adapter.sh <dest_dir> <tool_name>}"

# Nothing to clean if the dest doesn't exist yet
[[ -d "$DEST" ]] || exit 0

case "$TOOL" in
  claude|cursor)
    cmd_subdir="commands"; cmd_ext="md" ;;
  gemini)
    cmd_subdir="commands"; cmd_ext="toml" ;;
  antigravity)
    cmd_subdir="workflows"; cmd_ext="md" ;;
  copilot)
    cmd_subdir="prompts"; cmd_ext="md" ;;
  *)
    echo "clean_adapter.sh: unknown tool '$TOOL'" >&2
    exit 1 ;;
esac

# Commands / workflows / prompts (numbered + dispatcher)
if [[ -d "$DEST/$cmd_subdir" ]]; then
  find "$DEST/$cmd_subdir" -maxdepth 1 -type f \
    \( -name "*-osp-*.$cmd_ext" -o -name "open-scholar-peer.$cmd_ext" \) \
    -delete 2>/dev/null || true
fi

# Skills (always osp-*/)
if [[ -d "$DEST/skills" ]]; then
  find "$DEST/skills" -maxdepth 1 -type d -name 'osp-*' \
    -exec rm -rf {} + 2>/dev/null || true
fi

# Rules / always-on instructions (varies by tool)
case "$TOOL" in
  cursor)
    rm -f "$DEST/rules/osp-rules.mdc" ;;
  gemini)
    rm -f "$DEST/GEMINI.md" ;;
  copilot)
    rm -f "$DEST/instructions/osp-rules.md" ;;
  *)
    rm -f "$DEST/rules/osp-rules.md" ;;
esac

# Defaults (entirely OSP-managed in every tool)
rm -rf "$DEST/defaults"
