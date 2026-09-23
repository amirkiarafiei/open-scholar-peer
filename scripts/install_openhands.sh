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

# 5. OpenHands MCP — ~/.openhands/mcp.json, read by the OpenHands CLI.
#    The schema is the same {"mcpServers": {...}} shape every other tool uses,
#    so merge_mcp_config.py handles it with its sidecar tracking and stale-path
#    recognizer. Home-scoped, not project-scoped: OpenHands has no project-local
#    MCP file, so the last install wins — the same accepted behaviour as Kimi
#    and Copilot. The web UI keeps its MCP config in a database behind
#    Settings → MCP and cannot be reached from a file; the snippet is for those
#    users only.
OH_CONFIG="$HOME/.openhands/mcp.json"
SNIPPET_PATH="./.open-scholar-peer/openhands_mcp_snippet.json"
mkdir -p "$(dirname "$OH_CONFIG")"

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

if python3 "$SCRIPTS_DIR/merge_mcp_config.py" "$OH_CONFIG" \
     "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER" >/dev/null 2>&1; then
  echo -e "  ${GREEN}✅ MCP servers configured → ~/.openhands/mcp.json (CLI)${NC}"
else
  echo -e "\n  ${YELLOW}⚠️  Could not write ~/.openhands/mcp.json — it was left untouched.${NC}"
  echo "     Paste this into OpenHands → Settings → MCP:"
  echo "         $SNIPPET_PATH"
fi

echo -e "  ${CYAN}ℹ️  Using the OpenHands web UI instead of the CLI? Its MCP settings live${NC}"
echo "     in the app, not a file — paste $SNIPPET_PATH into Settings → MCP."

echo -e "\n  ${YELLOW}ℹ️  OpenHands subagent support is partial — /5-osp-qa falls back${NC}"
echo "     to self-reflection mode (see docs/KNOWN_LIMITATIONS.md)."

# Closing message — shared wording lives in _post_install.sh
. "$SCRIPTS_DIR/_post_install.sh"
osp_post_install "OpenHands"
