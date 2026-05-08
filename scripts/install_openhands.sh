#!/usr/bin/env bash
# Open ScholarPeer — OpenHands (All-Hands-AI) installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → OpenHands${NC}\n"

# 1. Copy adapter — OpenHands prefers .agents/skills/ (current) and falls back
#    to .openhands/ (legacy). Drop content into both.
SRC="$ROOT_DIR/extensions/.openhands"
DEST="./.openhands"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "openhands"
find "$SRC" -mindepth 1 -maxdepth 1 -not -name 'AGENTS.md' -exec cp -r {} "$DEST/" \;
echo -e "  ${GREEN}✅ Adapter copied → ./.openhands/${NC}"

# Mirror skills to .agents/skills/ (OpenHands' current preferred location)
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

# 5. OpenHands MCP — configured via UI Settings → MCP, or per-skill YAML.
#    Emit a snippet showing both options.
SNIPPET_PATH="./.open-scholar-peer/openhands_mcp_snippet.json"
cat > "$SNIPPET_PATH" << JSON
{
  "mcpServers": {
    "osp": {
      "command": "$OSP_MCP_PYTHON",
      "args": ["$OSP_MCP_SERVER"]
    },
    "markitdown": {
      "command": "uvx",
      "args": ["markitdown-mcp"]
    }
  }
}
JSON

echo -e "\n  ${YELLOW}⚠️  Add the MCP servers via OpenHands → Settings → MCP:${NC}"
echo "     A ready-to-paste snippet has been saved to:"
echo "         $SNIPPET_PATH"

echo -e "\n  ${YELLOW}ℹ️  OpenHands subagent support is partial — /5-osp-qa falls back${NC}"
echo "     to self-reflection mode (see docs/KNOWN_LIMITATIONS.md)."

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo    "  (1) Register the MCP servers in OpenHands → Settings → MCP"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
