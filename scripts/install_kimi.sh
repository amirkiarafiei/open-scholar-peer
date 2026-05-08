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

# 5. Kimi MCP snippet for ~/.kimi/config.toml (global config, TOML)
SNIPPET_PATH="./.open-scholar-peer/kimi_mcp_snippet.toml"
cat > "$SNIPPET_PATH" << TOML
[mcp_servers.osp]
command = "$OSP_MCP_PYTHON"
args = ["$OSP_MCP_SERVER"]

[mcp_servers.markitdown]
command = "uvx"
args = ["markitdown-mcp"]
TOML

echo -e "\n  ${YELLOW}⚠️  Kimi uses a GLOBAL MCP config. Add the entries below to:${NC}"
echo "         ~/.kimi/config.toml"
echo ""
echo "     A ready-to-paste snippet has been saved to:"
echo "         $SNIPPET_PATH"

echo -e "\n  ${YELLOW}ℹ️  Kimi support for parallel subagents is limited — /5-osp-qa${NC}"
echo "     falls back to self-reflection mode (see docs/KNOWN_LIMITATIONS.md)."

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo    "  (1) Paste the MCP snippet into ~/.kimi/config.toml"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
