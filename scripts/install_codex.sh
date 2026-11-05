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

# 1. Codex reads project skills only from .agents/skills/ and has no project
#    commands at all, so all sixteen skills — the eight commands included — go
#    there, with the defaults they point at. ./.codex/ only holds what an older
#    OSP wrote, which is swept. User content is preserved.
SRC="$ROOT_DIR/extensions/.codex"
bash "$SCRIPTS_DIR/clean_adapter.sh" "./.codex" "codex"
rmdir ./.codex 2>/dev/null || true
bash "$SCRIPTS_DIR/mirror_skills.sh" "$SRC/skills" "./.agents/skills" all
mkdir -p "./.agents/defaults"
cp -r "$SRC/defaults/." "./.agents/defaults/"
echo -e "  ${GREEN}✅ Skills and defaults → ./.agents/${NC}"

# 2. AGENTS.md — merge into project root (preserves user content)
if [[ -f "$SRC/AGENTS.md" ]]; then
  bash "$SCRIPTS_DIR/merge_agents_md.sh" "$SRC/AGENTS.md" "./AGENTS.md"
  echo -e "  ${GREEN}✅ AGENTS.md OSP block merged at project root${NC}"
fi

# 3. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 4. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 5. Codex MCP — run `codex mcp add`, which edits ~/.codex/config.toml through
#    toml_edit, so the user's comments and formatting survive. It is
#    non-interactive, idempotent (a second run overwrites the same entry), and
#    exits non-zero on failure.
#    Scope is global: Codex only reads a project-local .codex/config.toml for
#    folders the user has marked trusted, and that same setting also governs
#    approval policy and sandbox mode — not something an installer should write
#    on the user's behalf. So the last install wins, as it already does for
#    Kimi and Copilot.
SNIPPET_PATH="./.open-scholar-peer/codex_mcp_snippet.toml"
cat > "$SNIPPET_PATH" << TOML
[mcp_servers.osp]
command = "$OSP_MCP_PYTHON"
args = ["$OSP_MCP_SERVER"]

[mcp_servers.markitdown]
command = "uvx"
args = ["markitdown-mcp"]
TOML

if command -v codex >/dev/null 2>&1 &&
   codex mcp add osp -- "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER" >/dev/null 2>&1 &&
   codex mcp add markitdown -- uvx markitdown-mcp >/dev/null 2>&1; then
  echo -e "  ${GREEN}✅ MCP servers configured → ~/.codex/config.toml${NC}"
else
  if command -v codex >/dev/null 2>&1; then
    echo -e "\n  ${YELLOW}⚠️  \`codex mcp add\` did not succeed. Add the servers yourself:${NC}"
  else
    echo -e "\n  ${YELLOW}⚠️  Codex CLI is not on PATH, so the MCP servers were not wired.${NC}"
    echo "     Once Codex is installed, run:"
  fi
  echo "         codex mcp add osp -- $OSP_MCP_PYTHON $OSP_MCP_SERVER"
  echo "         codex mcp add markitdown -- uvx markitdown-mcp"
  echo "     Or paste this into ~/.codex/config.toml:"
  echo "         $SNIPPET_PATH"
fi

# Closing message — shared wording lives in _post_install.sh
. "$SCRIPTS_DIR/_post_install.sh"
osp_post_install "Codex CLI" \
  "In Codex, OSP commands are skills: type \$open-scholar-peer (and \$1-osp-summary, ...), or pick one from /skills"
