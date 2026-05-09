#!/usr/bin/env bash
# Open ScholarPeer — Kimi Code (Moonshot) installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Kimi Code${NC}\n"

# 1. Copy adapter — Kimi reads skills from .agents/skills/ (Anthropic Skill format),
#    so we drop adapter content into BOTH .kimi/ (per-tool) and .agents/skills/.
SRC="$ROOT_DIR/extensions/.kimi"
DEST="./.kimi"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "kimi"
find "$SRC" -mindepth 1 -maxdepth 1 -not -name 'AGENTS.md' -exec cp -r {} "$DEST/" \;
echo -e "  ${GREEN}✅ Adapter copied → ./.kimi/${NC}"

# Mirror skills to .agents/skills/ (Kimi's primary skill discovery path)
mkdir -p "./.agents/skills"
if [[ -d "$SRC/skills" ]]; then
  find "./.agents/skills" -maxdepth 1 -type d -name 'osp-*' -exec rm -rf {} + 2>/dev/null || true
  cp -r "$SRC/skills/." "./.agents/skills/"
  echo -e "  ${GREEN}✅ Skills mirrored → ./.agents/skills/${NC}"
fi

# 2. AGENTS.md — merge into project root
if [[ -f "$SRC/AGENTS.md" ]]; then
  bash "$SCRIPTS_DIR/merge_agents_md.sh" "$SRC/AGENTS.md" "./AGENTS.md"
  echo -e "  ${GREEN}✅ AGENTS.md OSP block merged at project root${NC}"
fi

# 3. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 4. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 5. Kimi MCP config — ~/.kimi/mcp.json (global, JSON, mcpServers format)
#    Per https://moonshotai.github.io/kimi-cli/en/customization/mcp.html
KIMI_MCP_CONFIG="${HOME}/.kimi/mcp.json"
mkdir -p "$(dirname "$KIMI_MCP_CONFIG")"
python3 "$SCRIPTS_DIR/merge_mcp_config.py" "$KIMI_MCP_CONFIG" "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER"

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo    "  (1) Restart your Kimi CLI session  (picks up the new MCP servers)"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
