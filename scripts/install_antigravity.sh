#!/usr/bin/env bash
# Open ScholarPeer — Antigravity installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Antigravity${NC}\n"

# Antigravity references both `.agents/` (legacy default) and `.agent/` (newer).
# Sync script generates both — copy whichever exists, prefer .agents/ since that's
# what most current Antigravity versions still discover.

# 1. Copy adapter to project. Wipe stale OSP-managed files in BOTH .agents/
#    (legacy discovery) and .agent/ (newer) before re-copy; user content preserved.
SRC="$ROOT_DIR/extensions/.agent"
DEST_PRIMARY="./.agents"
DEST_FUTURE="./.agent"
mkdir -p "$DEST_PRIMARY" "$DEST_FUTURE"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST_PRIMARY" "antigravity"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST_FUTURE" "antigravity"
cp -r "$SRC/." "$DEST_PRIMARY/"
cp -r "$SRC/." "$DEST_FUTURE/"
echo -e "  ${GREEN}✅ Adapter copied → ./.agents/ and ./.agent/${NC}"

# 2. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 3. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 4. Antigravity MCP config — merge into global config directories
AG_MCP_CONFIG_LEGACY="${HOME}/.gemini/antigravity/mcp_config.json"
AG_MCP_CONFIG_SHARED="${HOME}/.gemini/config/mcp_config.json"

mkdir -p "$(dirname "$AG_MCP_CONFIG_LEGACY")"
mkdir -p "$(dirname "$AG_MCP_CONFIG_SHARED")"

python3 "$SCRIPTS_DIR/merge_mcp_config.py" "$AG_MCP_CONFIG_LEGACY" "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER"
python3 "$SCRIPTS_DIR/merge_mcp_config.py" "$AG_MCP_CONFIG_SHARED" "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER"

echo -e "\n  ${YELLOW}ℹ️  Antigravity does NOT support general subagents — /5-osp-qa falls${NC}"
echo "     back to self-reflection mode (see docs/KNOWN_LIMITATIONS.md)."

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo    "  (1) Restart Antigravity  (picks up the new MCP servers)"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
