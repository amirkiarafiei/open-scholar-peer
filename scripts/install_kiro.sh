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

# 3. MCP runtime (Kiro discovers MCP servers via its IDE settings — we set up
#    the venv so the user can register it via Kiro's MCP UI.)
. "$SCRIPTS_DIR/init_mcp.sh"

echo -e "\n  ${YELLOW}ℹ️  Add the OSP MCP server via Kiro's MCP settings:${NC}"
echo "     Command: $OSP_MCP_PYTHON"
echo "     Args:    $OSP_MCP_SERVER"

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo    "  (1) Type / in Kiro IDE chat to see the Open ScholarPeer hooks"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
