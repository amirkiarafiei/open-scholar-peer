#!/usr/bin/env bash
# mirror_skills.sh — copy OSP's skills into the shared ./.agents/skills/ folder.
#
# Several tools read `.agents/skills/`, and the eight command skills differ
# between them (the Q&A command is written for each tool's subagent support).
# So the shared folder gets only what is the same everywhere — the persona
# skills — unless the tool reads nothing else, in which case it needs all of it.
#
# Usage: bash mirror_skills.sh <src_skills_dir> <dest_skills_dir> personas|all
#   personas  osp-*/ only. For tools that also read their own skills folder.
#   all       every skill, the eight commands included. For Codex, whose only
#             project skill folder is .agents/skills/.
#
# Only OSP-owned names are ever removed: osp-*/ always; with `all`, also
# [0-9]-osp-*/ and open-scholar-peer/. A user's own skills are never touched.

set -e

SRC="${1:?usage: mirror_skills.sh <src_skills_dir> <dest_skills_dir> personas|all}"
DEST="${2:?usage: mirror_skills.sh <src_skills_dir> <dest_skills_dir> personas|all}"
MODE="${3:?usage: mirror_skills.sh <src_skills_dir> <dest_skills_dir> personas|all}"

[[ -d "$SRC" ]] || exit 0
mkdir -p "$DEST"

find "$DEST" -maxdepth 1 -type d -name 'osp-*' -exec rm -rf {} + 2>/dev/null || true

case "$MODE" in
  personas)
    find "$SRC" -mindepth 1 -maxdepth 1 -type d -name 'osp-*' -exec cp -r {} "$DEST/" \; ;;
  all)
    find "$DEST" -maxdepth 1 -type d \( -name '[0-9]-osp-*' -o -name 'open-scholar-peer' \) \
      -exec rm -rf {} + 2>/dev/null || true
    cp -r "$SRC/." "$DEST/" ;;
  *)
    echo "mirror_skills.sh: mode must be 'personas' or 'all', got '$MODE'" >&2
    exit 1 ;;
esac
