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

# 5. Vibe MCP — write ./.vibe/config.toml directly.
#    Vibe reads ./.vibe/config.toml (project-local) and ~/.vibe/config.toml
#    (global), union-merging `mcp_servers` by name, so the project entry wins
#    and the user's own servers survive. Project-local is what OSP wants: one
#    paper folder must not overwrite another's server path.
#    `transport` is a pydantic discriminator — an entry without it invalidates
#    the entire config file, not just that entry. See merge_mcp_toml.py.
VIBE_CONFIG="./.vibe/config.toml"
SNIPPET_PATH="./.open-scholar-peer/vibe_mcp_snippet.toml"

if python3 "$SCRIPTS_DIR/merge_mcp_toml.py" "$VIBE_CONFIG" "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER" >/dev/null 2>&1; then
  echo -e "  ${GREEN}✅ MCP servers configured → $VIBE_CONFIG${NC}"
else
  # Only reached when the user already has a config.toml we cannot read back
  # safely. Their file is left exactly as it was.
  cat > "$SNIPPET_PATH" << TOML
[[mcp_servers]]
name = "osp"
transport = "stdio"
command = "$OSP_MCP_PYTHON"
args = ["$OSP_MCP_SERVER"]

[[mcp_servers]]
name = "markitdown"
transport = "stdio"
command = "uvx"
args = ["markitdown-mcp"]
TOML
  echo -e "\n  ${YELLOW}⚠️  Could not merge into your existing $VIBE_CONFIG — it was left${NC}"
  echo "     untouched. Append these entries yourself:"
  echo "         $SNIPPET_PATH"
fi

echo -e "\n  ${YELLOW}ℹ️  Vibe documents independent agent profiles but no general subagent${NC}"
echo "     delegation — /5-osp-qa falls back to self-reflection mode (see"
echo "     docs/KNOWN_LIMITATIONS.md)."

# Closing message — shared wording lives in _post_install.sh
. "$SCRIPTS_DIR/_post_install.sh"
osp_post_install "Mistral Vibe"
