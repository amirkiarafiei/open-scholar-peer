#!/usr/bin/env bash
# Open ScholarPeer — Claude Code installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Claude Code${NC}\n"

# 1. Copy adapter into .claude/ (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.claude"
DEST="./.claude"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "claude"
cp -r "$SRC/." "$DEST/"
echo -e "  ${GREEN}✅ Adapter copied → ./.claude/${NC}"

# 2. Initialize .brain/
"$SCRIPTS_DIR/init_brain.sh"

# 3. Set up self-contained MCP server in .scholar-peer/mcp/
. "$SCRIPTS_DIR/init_mcp.sh"

# 4. Merge MCP entries into ./.mcp.json
python3 "$SCRIPTS_DIR/merge_mcp_config.py" "./.mcp.json" "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER"

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo -e "  (1) Run ${CYAN}/open-scholar-peer${NC} in Claude Code"
echo    "      The orchestrator reads your session state and guides you from there."
