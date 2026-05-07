#!/usr/bin/env bash
# Open ScholarPeer — Gemini CLI installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Gemini CLI${NC}\n"

if command -v gemini &>/dev/null; then
  echo -e "  ${GREEN}✅ Gemini CLI detected${NC}"
else
  echo -e "  ${YELLOW}⚠️  Gemini CLI not found. Install with: npm install -g @google/gemini-cli${NC}"
fi

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.gemini"
DEST="./.gemini"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "gemini"
cp -r "$SRC/." "$DEST/"
echo -e "  ${GREEN}✅ Adapter copied → ./.gemini/${NC}"

# 2. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 3. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 4. Merge MCP entries into ./.gemini/settings.json
python3 "$SCRIPTS_DIR/merge_mcp_config.py" "./.gemini/settings.json" "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER"

echo -e "\n${GREEN}Done!${NC}\n"
echo "In Gemini CLI:"
echo "  - Run '/commands reload' (or restart) to pick up new TOML commands."
echo "  - Type /open-scholar-peer to see status, then /0-osp-onboarding to start."
echo "  - Drop your paper into ./.brain/input/ before running /0-osp-onboarding."
