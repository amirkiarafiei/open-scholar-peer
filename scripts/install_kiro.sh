#!/usr/bin/env bash
# Open ScholarPeer — Amazon Kiro installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Kiro${NC}\n"

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.kiro"
DEST="./.kiro"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "kiro"
cp -r "$SRC/." "$DEST/"
echo -e "  ${GREEN}✅ Adapter copied → ./.kiro/${NC}"

# 2. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 3. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 4. Kiro MCP config — .kiro/settings/mcp.json (project-local, JSON, mcpServers format)
#    Per https://kiro.dev/docs/cli/mcp/
KIRO_MCP_CONFIG="./.kiro/settings/mcp.json"
mkdir -p "$(dirname "$KIRO_MCP_CONFIG")"
python3 "$SCRIPTS_DIR/merge_mcp_config.py" "$KIRO_MCP_CONFIG" "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER"

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo    "  (1) Type / in Kiro IDE chat to see the Open ScholarPeer hooks"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
