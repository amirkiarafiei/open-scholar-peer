#!/usr/bin/env bash
# Open ScholarPeer — Antigravity installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Antigravity${NC}\n"

# 1. Copy adapter to ./.agents/, where Antigravity reads workspace skills and
#    rules (antigravity.google/docs/rules, /docs/skills). An older OSP also wrote
#    the legacy ./.agent/; it is swept, not rewritten, because the IDE reads both
#    and every command would otherwise appear twice. User content is preserved.
SRC="$ROOT_DIR/extensions/.agent"
DEST="./.agents"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "antigravity"
bash "$SCRIPTS_DIR/clean_adapter.sh" "./.agent" "antigravity"
rmdir ./.agent 2>/dev/null || true
cp -r "$SRC/." "$DEST/"
echo -e "  ${GREEN}✅ Adapter copied → ./.agents/${NC}"

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

# Closing message — shared wording lives in _post_install.sh
. "$SCRIPTS_DIR/_post_install.sh"
osp_post_install "Antigravity" "Restart Antigravity  (picks up the new MCP servers)"
