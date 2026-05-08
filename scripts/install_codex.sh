#!/usr/bin/env bash
# Open ScholarPeer — OpenAI Codex CLI installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Codex CLI${NC}\n"

if command -v codex &>/dev/null; then
  echo -e "  ${GREEN}✅ Codex CLI detected${NC}"
else
  echo -e "  ${YELLOW}⚠️  Codex CLI not found. Install per https://github.com/openai/codex${NC}"
fi

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.codex"
DEST="./.codex"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "codex"
# Copy everything except AGENTS.md (it goes to project root, merged separately)
find "$SRC" -mindepth 1 -maxdepth 1 -not -name 'AGENTS.md' -exec cp -r {} "$DEST/" \;
echo -e "  ${GREEN}✅ Adapter copied → ./.codex/${NC}"

# 2. AGENTS.md — merge into project root (preserves user content)
if [[ -f "$SRC/AGENTS.md" ]]; then
  bash "$SCRIPTS_DIR/merge_agents_md.sh" "$SRC/AGENTS.md" "./AGENTS.md"
  echo -e "  ${GREEN}✅ AGENTS.md OSP block merged at project root${NC}"
fi

# 3. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 4. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 5. Codex MCP snippet for ~/.codex/config.toml (Codex uses TOML; cannot safely
#    auto-merge user TOML files — emit a snippet for the user to paste.)
SNIPPET_PATH="./.open-scholar-peer/codex_mcp_snippet.toml"
cat > "$SNIPPET_PATH" << TOML
[mcp_servers.osp]
command = "$OSP_MCP_PYTHON"
args = ["$OSP_MCP_SERVER"]

[mcp_servers.markitdown]
command = "uvx"
args = ["markitdown-mcp"]
TOML

echo -e "\n  ${YELLOW}⚠️  Add the MCP entries below to your Codex config:${NC}"
echo "         ~/.codex/config.toml   (or  ./.codex/config.toml)"
echo ""
echo "     A ready-to-paste snippet has been saved to:"
echo "         $SNIPPET_PATH"

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo    "  (1) Paste the MCP snippet into your Codex config.toml"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
