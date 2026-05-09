#!/usr/bin/env bash
# Open ScholarPeer — OpenCode installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → OpenCode${NC}\n"

if command -v opencode &>/dev/null; then
  echo -e "  ${GREEN}✅ OpenCode detected${NC}"
else
  echo -e "  ${YELLOW}⚠️  OpenCode not found. Install per https://opencode.ai/docs/${NC}"
fi

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.opencode"
DEST="./.opencode"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "opencode"
find "$SRC" -mindepth 1 -maxdepth 1 -not -name 'AGENTS.md' -exec cp -r {} "$DEST/" \;
echo -e "  ${GREEN}✅ Adapter copied → ./.opencode/${NC}"

# 2. AGENTS.md — merge into project root
if [[ -f "$SRC/AGENTS.md" ]]; then
  bash "$SCRIPTS_DIR/merge_agents_md.sh" "$SRC/AGENTS.md" "./AGENTS.md"
  echo -e "  ${GREEN}✅ AGENTS.md OSP block merged at project root${NC}"
fi

# 3. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 4. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 5. OpenCode MCP — opencode.json uses a non-standard `mcp` key with stdio block.
#    Emit a snippet rather than auto-merging, since the schema differs from
#    other tools' mcpServers format.
SNIPPET_PATH="./.open-scholar-peer/opencode_mcp_snippet.json"
cat > "$SNIPPET_PATH" << JSON
{
  "mcp": {
    "osp": {
      "type": "local",
      "command": ["$OSP_MCP_PYTHON", "$OSP_MCP_SERVER"]
    },
    "markitdown": {
      "type": "local",
      "command": ["uvx", "markitdown-mcp"]
    }
  }
}
JSON

echo -e "\n  ${YELLOW}⚠️  Wire the OSP MCP server with one of:${NC}"
echo ""
echo "     (a) OpenCode CLI (recommended):"
echo "         opencode mcp add osp -- $OSP_MCP_PYTHON $OSP_MCP_SERVER"
echo ""
echo "     (b) Or paste the snippet manually into opencode.json:"
echo "         $SNIPPET_PATH"

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo    "  (1) Wire the MCP server (opencode mcp add osp ... or paste snippet)"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
