#!/usr/bin/env bash
# Open ScholarPeer — Google Antigravity IDE installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Google Antigravity IDE${NC}\n"

# Antigravity references both `.agents/` (legacy default) and `.agent/` (newer).
# Sync script generates both — copy whichever exists, prefer .agents/ since that's
# what most current Antigravity versions still discover.

# 1. Copy adapter to project. Wipe stale OSP-managed files in BOTH .agents/
#    (legacy discovery) and .agent/ (newer) before re-copy; user content preserved.
SRC="$ROOT_DIR/extensions/.agents"
DEST_PRIMARY="./.agents"
DEST_FUTURE="./.agent"
mkdir -p "$DEST_PRIMARY" "$DEST_FUTURE"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST_PRIMARY" "antigravity"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST_FUTURE" "antigravity"
cp -r "$SRC/." "$DEST_PRIMARY/"
cp -r "$ROOT_DIR/extensions/.agent/." "$DEST_FUTURE/"
echo -e "  ${GREEN}✅ Adapter copied → ./.agents/ and ./.agent/${NC}"

# 2. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 3. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 4. Antigravity uses a GLOBAL MCP config — we cannot programmatically write to
# ~/.gemini/antigravity/mcp_config.json without user consent. Output a snippet
# the user can paste manually.
SNIPPET_PATH="./.scholar-peer/antigravity_mcp_snippet.json"
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

echo -e "\n  ${YELLOW}⚠️  Antigravity uses a GLOBAL MCP config. Add the entries below to:${NC}"
echo "         ~/.gemini/antigravity/mcp_config.json"
echo ""
echo "     A ready-to-paste snippet has been saved to:"
echo "         $SNIPPET_PATH"
echo ""
echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Note: Antigravity does NOT support subagents — /5-osp-qa falls back to"
echo "  self-reflection mode (see docs/KNOWN_LIMITATIONS.md)."
echo ""
echo -e "Next:"
echo    "  (1) Paste the MCP snippet into ~/.gemini/antigravity/mcp_config.json"
echo    "      (saved to $SNIPPET_PATH)"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
