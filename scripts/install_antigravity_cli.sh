#!/usr/bin/env bash
# Open ScholarPeer — Antigravity CLI installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Antigravity CLI${NC}\n"

if command -v agy &>/dev/null; then
  echo -e "  ${GREEN}✅ Antigravity CLI (agy) detected${NC}"
else
  echo -e "  ${YELLOW}⚠️  Antigravity CLI (agy) not found. Follow installation guides to install it.${NC}"
fi

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.agents"
DEST="./.agents"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "antigravity-cli"
# Copy everything except AGENTS.md (it goes to project root, merged separately)
find "$SRC" -mindepth 1 -maxdepth 1 -not -name 'AGENTS.md' -exec cp -r {} "$DEST/" \;
echo -e "  ${GREEN}✅ Adapter copied → ./.agents/${NC}"

# 2. AGENTS.md — merge into project root (preserves user content)
if [[ -f "$SRC/AGENTS.md" ]]; then
  bash "$SCRIPTS_DIR/merge_agents_md.sh" "$SRC/AGENTS.md" "./AGENTS.md"
  echo -e "  ${GREEN}✅ AGENTS.md OSP block merged at project root${NC}"
fi

# 3. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 4. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 5. Antigravity CLI MCP config — ./.agents/mcp_config.json
python3 "$SCRIPTS_DIR/merge_mcp_config.py" "./.agents/mcp_config.json" "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER"

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo -e "  (1) Run ${CYAN}/open-scholar-peer${NC} in Antigravity CLI"
echo    "      The orchestrator reads your session state and guides you from there."
