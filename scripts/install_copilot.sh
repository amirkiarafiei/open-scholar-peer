#!/usr/bin/env bash
# Open ScholarPeer — GitHub Copilot CLI installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → GitHub Copilot CLI${NC}\n"

if command -v copilot &>/dev/null; then
  echo -e "  ${GREEN}✅ Copilot CLI detected${NC}"
else
  echo -e "  ${YELLOW}⚠️  Copilot CLI not found. Install per https://docs.github.com/en/copilot/how-tos/copilot-cli/${NC}"
fi

# Hard prereq: this installer uses python3 for the AGENTS.md merge AND init_mcp
# uses it for the venv. Fail early with a friendly message if absent.
if ! command -v python3 &>/dev/null; then
  echo -e "  ${RED}✗ python3 not found in PATH.${NC}"
  echo "     The Copilot installer needs python3 for AGENTS.md merging and the MCP venv."
  echo "     Install Python 3.10+ and re-run."
  exit 1
fi

# 1. Copy adapter to .github/ + AGENTS.md at project root.
#    Wipe stale OSP-managed files in .github/ first; user content preserved.
SRC="$ROOT_DIR/extensions/.github"
DEST="./.github"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "copilot"
cp -r "$SRC/." "$DEST/"
echo -e "  ${GREEN}✅ Adapter copied → ./.github/${NC}"

# AGENTS.md handling: idempotent merge using markers, preserves user content.
OSP_BEGIN="<!-- OSP-BEGIN: managed by install_copilot.sh; do not edit between markers -->"
OSP_END="<!-- OSP-END -->"
if [[ -f "$DEST/AGENTS.md" ]]; then
  if [[ -f "./AGENTS.md" ]]; then
    # Use a Python helper to merge safely (handles existing markers, multi-line content)
    python3 - "$OSP_BEGIN" "$OSP_END" "$DEST/AGENTS.md" "./AGENTS.md" <<'PYEOF'
import sys, re
begin, end, src, dst = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
with open(src) as f: osp_content = f.read().rstrip()
osp_block = f"{begin}\n{osp_content}\n{end}"
with open(dst) as f: text = f.read()
if begin in text:
    new = re.sub(re.escape(begin) + r".*?" + re.escape(end), osp_block.replace("\\", r"\\"), text, count=1, flags=re.DOTALL)
    print("updated")
else:
    new = text.rstrip() + "\n\n" + osp_block + "\n"
    print("appended")
with open(dst, "w") as f: f.write(new)
PYEOF
    echo -e "  ${GREEN}✅ AGENTS.md OSP block merged (user content preserved)${NC}"
  else
    {
      echo "$OSP_BEGIN"
      cat "$DEST/AGENTS.md"
      echo "$OSP_END"
    } > "./AGENTS.md"
    echo -e "  ${GREEN}✅ AGENTS.md created at project root (with OSP markers for future updates)${NC}"
  fi
fi

# 2. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 3. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 4. Copilot CLI MCP config (~/.copilot/mcp-config.json)
# Per https://docs.github.com/en/copilot/how-tos/copilot-cli/cli-best-practices
COPILOT_MCP_CONFIG="${HOME}/.copilot/mcp-config.json"
mkdir -p "$(dirname "$COPILOT_MCP_CONFIG")"
python3 "$SCRIPTS_DIR/merge_mcp_config.py" "$COPILOT_MCP_CONFIG" "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER"

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo    "  (1) Restart the Copilot CLI session  (picks up the new MCP servers)"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
