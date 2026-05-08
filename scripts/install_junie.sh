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

# 3. MCP runtime (Junie does not have a documented MCP config path; we still
#    set up the venv so the user can wire it manually if they enable MCP later.)
. "$SCRIPTS_DIR/init_mcp.sh"

echo -e "\n  ${YELLOW}ℹ️  Junie has no documented MCP config path — paper retrieval${NC}"
echo "     tools (arxiv, semantic_scholar) will not be available unless you wire"
echo "     them manually. Phases that don't need retrieval still work."

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo    "  (1) Type / in Junie chat to see the Open ScholarPeer commands"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
