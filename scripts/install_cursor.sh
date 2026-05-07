#!/usr/bin/env bash
# Open ScholarPeer — Cursor installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Cursor${NC}\n"

# 1. Copy adapter
SRC="$ROOT_DIR/extensions/.cursor"
DEST="./.cursor"
mkdir -p "$DEST"
cp -r "$SRC/." "$DEST/"
echo -e "  ${GREEN}✅ Adapter copied → ./.cursor/${NC}"

# 2. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 3. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 4. Merge MCP entries into ./.cursor/mcp.json
python3 "$SCRIPTS_DIR/merge_mcp_config.py" "./.cursor/mcp.json" "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER"

echo -e "\n${GREEN}Done!${NC}\n"
echo "In Cursor:"
echo "  - Reload window so .cursor/rules/*.mdc and commands take effect."
echo "  - Type /open-scholar-peer to see review status, then /0-osp-onboarding to start."
echo "  - Drop your paper into ./.brain/input/ before running /0-osp-onboarding."
