#!/usr/bin/env bash
# Open ScholarPeer — GitHub Copilot CLI installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Copilot CLI${NC}\n"

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
if [[ -f "$DEST/AGENTS.md" ]]; then
  bash "$SCRIPTS_DIR/merge_agents_md.sh" "$DEST/AGENTS.md" "./AGENTS.md"
  echo -e "  ${GREEN}✅ AGENTS.md OSP block merged at project root${NC}"
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
