#!/usr/bin/env bash
# Open ScholarPeer — Oh My Pi (omp) installer
#
# omp is a hard fork of Pi, not a wrapper around it, and its layout is its own:
# .omp/commands/, .omp/skills/, .omp/agents/, .omp/mcp.json. Nothing from the
# Pi adapter is reused here.
#
# Two omp specifics shape this script:
#   - .omp/RULES.md is the "sticky" rule: carried in full on every request and
#     never demoted. A file under .omp/rules/ would be conditional instead.
#   - omp can delegate to a named agent with its own context window, but it
#     cannot dispatch a *skill* that way, so each persona also ships as an
#     agent definition under .omp/agents/.

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Oh My Pi${NC}\n"

if command -v omp &>/dev/null; then
  echo -e "  ${GREEN}✅ Oh My Pi detected${NC}"
else
  echo -e "  ${YELLOW}⚠️  omp not found. Install per https://omp.sh/docs${NC}"
fi

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.omp"
DEST="./.omp"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "ohmypi"
find "$SRC" -mindepth 1 -maxdepth 1 -not -name 'RULES.md' -exec cp -r {} "$DEST/" \;
echo -e "  ${GREEN}✅ Adapter copied → ./.omp/ (commands + skills + agents)${NC}"

# 2. RULES.md — merged, not overwritten. It is a file the user may already own,
#    so only the block between the OSP markers is managed.
if [[ -f "$SRC/RULES.md" ]]; then
  bash "$SCRIPTS_DIR/merge_agents_md.sh" "$SRC/RULES.md" "$DEST/RULES.md"
  echo -e "  ${GREEN}✅ OSP block merged into ./.omp/RULES.md (always-apply rule)${NC}"
fi

# 3. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 4. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 5. omp MCP — project-local ./.omp/mcp.json, standard `mcpServers` shape.
#    There is no `omp mcp add` subcommand; /mcp add is an in-session wizard.
#    So the file is written directly, which is also what keeps the servers
#    scoped to this paper's folder rather than to every project.
OMP_MCP_CONFIG="$DEST/mcp.json"
if python3 "$SCRIPTS_DIR/merge_mcp_config.py" "$OMP_MCP_CONFIG" \
     "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER" >/dev/null 2>&1; then
  echo -e "  ${GREEN}✅ MCP servers configured → $OMP_MCP_CONFIG${NC}"
else
  echo -e "\n  ${YELLOW}⚠️  Could not merge into $OMP_MCP_CONFIG — it was left untouched.${NC}"
  echo "     Add the servers from inside omp with:  /mcp add"
fi

# 6. omp skips gitignored files during command discovery, so a project that
#    ignores .omp/ would install cleanly and then show no commands at all.
if [[ -f .gitignore ]] && grep -qE '^\s*\.omp/?\s*$' .gitignore; then
  echo -e "\n  ${YELLOW}⚠️  .gitignore ignores .omp/ — omp skips gitignored files when it${NC}"
  echo -e "     ${YELLOW}looks for commands, so the OSP commands will not appear.${NC}"
  echo "     Remove that line, or un-ignore .omp/commands/."
fi

# Closing message — shared wording lives in _post_install.sh
. "$SCRIPTS_DIR/_post_install.sh"
osp_post_install "Oh My Pi"
