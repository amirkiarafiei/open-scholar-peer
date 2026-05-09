#!/usr/bin/env bash
# Open ScholarPeer — Mistral Vibe installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Mistral Vibe${NC}\n"

# 1. Copy adapter — Vibe loads skills from .vibe/skills/ AND .agents/skills/.
SRC="$ROOT_DIR/extensions/.vibe"
DEST="./.vibe"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "vibe"
find "$SRC" -mindepth 1 -maxdepth 1 -not -name 'AGENTS.md' -exec cp -r {} "$DEST/" \;
echo -e "  ${GREEN}✅ Adapter copied → ./.vibe/${NC}"

# Mirror skills to .agents/skills/ (Vibe's universal skill discovery path)
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

# 5. Vibe MCP snippet — TOML, can't auto-merge user TOML safely. Vibe reads
#    ./.vibe/config.toml (project-local) AND ~/.vibe/config.toml (global).
#    Per https://docs.mistral.ai/mistral-vibe/terminal/configuration#mcp-server-configuration
SNIPPET_PATH="./.open-scholar-peer/vibe_mcp_snippet.toml"
cat > "$SNIPPET_PATH" << TOML
[[mcp_servers]]
name = "osp"
command = "$OSP_MCP_PYTHON"
args = ["$OSP_MCP_SERVER"]

[[mcp_servers]]
name = "markitdown"
command = "uvx"
args = ["markitdown-mcp"]
TOML

echo -e "\n  ${YELLOW}⚠️  Vibe uses TOML config (we cannot safely auto-merge). Append the${NC}"
echo "     entries below to either of:"
echo "         ./.vibe/config.toml      (project-local)"
echo "         ~/.vibe/config.toml      (global)"
echo ""
echo "     A ready-to-paste snippet has been saved to:"
echo "         $SNIPPET_PATH"

echo -e "\n  ${YELLOW}ℹ️  Vibe documents independent agent profiles but no general subagent${NC}"
echo "     delegation — /5-osp-qa falls back to self-reflection mode (see"
echo "     docs/KNOWN_LIMITATIONS.md)."

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo    "  (1) Paste the MCP snippet into your Vibe config.toml"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
