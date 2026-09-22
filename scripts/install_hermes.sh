#!/usr/bin/env bash
# Open ScholarPeer — Hermes Agent installer
#
# Hermes has no file-based slash commands: every installed skill becomes one.
# So OSP's eight commands ship as skill directories alongside the eight
# personas, and both live under .hermes/skills/.
#
# Two Hermes rules shape this script:
#   - Exactly ONE project context file is loaded, first match wins:
#     .hermes.md > AGENTS.override.md > AGENTS.md > CLAUDE.md. Writing
#     .hermes.md would therefore silently suppress a user's own AGENTS.md, so
#     OSP merges into AGENTS.md instead of claiming a higher slot.
#   - Project skills are ignored until the project root is trusted.
#
# ~/.hermes/config.yaml also holds the user's model, keys and approvals, so
# this script never templates over it — MCP goes in through `hermes mcp add`.

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Hermes${NC}\n"

if command -v hermes &>/dev/null; then
  echo -e "  ${GREEN}✅ Hermes detected${NC}"
else
  echo -e "  ${YELLOW}⚠️  hermes not found. Install per https://hermes-agent.nousresearch.com/docs/${NC}"
fi

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.hermes"
DEST="./.hermes"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "hermes"
find "$SRC" -mindepth 1 -maxdepth 1 -not -name 'AGENTS.md' -exec cp -r {} "$DEST/" \;
echo -e "  ${GREEN}✅ Adapter copied → ./.hermes/skills/ (8 commands + 8 personas)${NC}"

# 2. AGENTS.md — merge into project root
if [[ -f "$SRC/AGENTS.md" ]]; then
  bash "$SCRIPTS_DIR/merge_agents_md.sh" "$SRC/AGENTS.md" "./AGENTS.md"
  echo -e "  ${GREEN}✅ AGENTS.md OSP block merged at project root${NC}"
fi

# 3. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 4. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 5. Hermes MCP — global ~/.hermes/config.yaml under `mcp_servers`. That file
#    is shared with the user's model and credentials, and there is no TOML/YAML
#    writer we can rely on, so the vendor's own command does the editing.
#    `hermes mcp add` is interactive even for a stdio server: it asks before
#    overwriting an existing entry, then probes the server and asks which tools
#    to enable. Left alone it blocks forever on a terminal. Worse, every exit
#    path returns None — including the cancelled one — so the shell sees 0 and
#    an install that wired nothing would report success.
#
#    Hence all three of: answers on stdin, a wall-clock bound, and a read-back
#    that decides the message. The exit code is not evidence here.
HERMES_MCP_OK=0
if command -v hermes >/dev/null 2>&1; then
  # `--args` is nargs=REMAINDER, so it stays last on both lines.
  printf 'y\ny\n' | timeout 90 hermes mcp add osp \
    --command "$OSP_MCP_PYTHON" --args "$OSP_MCP_SERVER" >/dev/null 2>&1 || true
  printf 'y\ny\n' | timeout 90 hermes mcp add markitdown \
    --command uvx --args markitdown-mcp >/dev/null 2>&1 || true
  if timeout 30 hermes mcp list </dev/null 2>/dev/null | grep -q 'osp'; then
    HERMES_MCP_OK=1
  fi
fi

if [[ $HERMES_MCP_OK -eq 1 ]]; then
  echo -e "  ${GREEN}✅ MCP servers configured → ~/.hermes/config.yaml (read back and verified)${NC}"
else
  if command -v hermes >/dev/null 2>&1; then
    echo -e "\n  ${YELLOW}⚠️  \`hermes mcp add\` did not succeed. Add the servers yourself:${NC}"
  else
    echo -e "\n  ${YELLOW}⚠️  Hermes is not on PATH, so the MCP servers were not wired.${NC}"
    echo "     Once Hermes is installed, run:"
  fi
  echo "         hermes mcp add osp --command $OSP_MCP_PYTHON --args $OSP_MCP_SERVER"
  echo "         hermes mcp add markitdown --command uvx --args markitdown-mcp"
fi

# 6. Project trust. Hermes returns no project skills at all until the root is
#    trusted, so an untrusted install looks like a broken one.
TRUSTED=0
if command -v hermes >/dev/null 2>&1; then
  if hermes skills trust "$(pwd)" </dev/null >/dev/null 2>&1; then
    TRUSTED=1
    echo -e "  ${GREEN}✅ Project trusted for skill discovery${NC}"
  fi
fi
if [[ $TRUSTED -eq 0 ]]; then
  echo -e "\n  ${YELLOW}⚠️  Hermes ignores project skills until this folder is trusted.${NC}"
  echo "     Run this here, once:"
  echo "         hermes skills trust"
fi

# Closing message — shared wording lives in _post_install.sh
. "$SCRIPTS_DIR/_post_install.sh"
if [[ $TRUSTED -eq 1 ]]; then
  osp_post_install "Hermes"
else
  osp_post_install "Hermes" "Run  hermes skills trust  in this folder, or the OSP commands will not appear"
fi
