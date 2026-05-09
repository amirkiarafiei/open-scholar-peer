#!/usr/bin/env bash
# merge_agents_md.sh — Idempotent merge of an OSP-managed rules block into a
# project-root markdown file (AGENTS.md, QWEN.md, etc.)
#
# Many AI coding tools load an always-on instruction file from the project root:
#   Codex, Kimi, Vibe, OpenCode, OpenHands → AGENTS.md
#   Qwen Code                              → QWEN.md
#   GitHub Copilot CLI                     → AGENTS.md
#
# This script preserves the user's existing content and only manages the block
# between OSP-BEGIN/OSP-END markers. Re-running replaces just that block.
#
# Usage: bash merge_agents_md.sh <src_managed_md> <dest_root_md>
#   src_managed_md = OSP-generated content (e.g. extensions/.codex/AGENTS.md)
#   dest_root_md   = project-root file to merge into (e.g. ./AGENTS.md)

set -e

SRC="${1:?usage: merge_agents_md.sh <src> <dest>}"
DEST="${2:?usage: merge_agents_md.sh <src> <dest>}"

[[ -f "$SRC" ]] || { echo "merge_agents_md.sh: source not found: $SRC" >&2; exit 1; }

OSP_BEGIN="<!-- OSP-BEGIN: managed by Open ScholarPeer; do not edit between markers -->"
OSP_END="<!-- OSP-END -->"

if [[ -f "$DEST" ]]; then
  python3 - "$OSP_BEGIN" "$OSP_END" "$SRC" "$DEST" <<'PYEOF'
import sys, re
begin, end, src, dst = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
with open(src) as f: osp_content = f.read().rstrip()
osp_block = f"{begin}\n{osp_content}\n{end}"
with open(dst) as f: text = f.read()
# Match either the new generic marker or the legacy install_copilot.sh marker
legacy_begin = "<!-- OSP-BEGIN: managed by install_copilot.sh; do not edit between markers -->"
if begin in text:
    pat = re.escape(begin) + r".*?" + re.escape(end)
    new = re.sub(pat, osp_block.replace("\\", r"\\"), text, flags=re.DOTALL)
elif legacy_begin in text:
    pat = re.escape(legacy_begin) + r".*?" + re.escape(end)
    new = re.sub(pat, osp_block.replace("\\", r"\\"), text, flags=re.DOTALL)
else:
    new = text.rstrip() + "\n\n" + osp_block + "\n"
with open(dst, "w") as f: f.write(new)
PYEOF
else
  {
    echo "$OSP_BEGIN"
    cat "$SRC"
    echo "$OSP_END"
  } > "$DEST"
fi
