#!/usr/bin/env bash
# Open ScholarPeer — JetBrains Junie installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Junie${NC}\n"

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.junie"
DEST="./.junie"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "junie"
cp -r "$SRC/." "$DEST/"
echo -e "  ${GREEN}✅ Adapter copied → ./.junie/${NC}"

# 2. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 3. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 4. Junie MCP config — .junie/mcp/mcp.json (project-local, JSON, mcpServers format)
#    Per https://junie.jetbrains.com/docs/junie-cli-mcp-configuration.html
JUNIE_MCP_CONFIG="./.junie/mcp/mcp.json"
mkdir -p "$(dirname "$JUNIE_MCP_CONFIG")"
python3 "$SCRIPTS_DIR/merge_mcp_config.py" "$JUNIE_MCP_CONFIG" "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER"

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo    "  (1) Type / in Junie chat to see the Open ScholarPeer commands"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
