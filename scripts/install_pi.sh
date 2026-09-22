#!/usr/bin/env bash
# Open ScholarPeer — Pi installer
#
# Pi is the one supported tool with no MCP client. That is a stated design
# choice by its author, not a gap: "No MCP. Build CLI tools with READMEs (see
# Skills)." Pi also ships no web search and no URL fetch — its built-in tools
# are read, bash, edit, write, grep, find, ls — so without a path of our own
# the review protocol would run with nothing to retrieve.
#
# So OSP follows Pi's own convention: the same 22 search tools are exposed as a
# command-line program, and the always-on rules tell the agent how to call it.
# The Python venv is still built, because that program lives inside it.

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Pi${NC}\n"

if command -v pi &>/dev/null; then
  echo -e "  ${GREEN}✅ Pi detected${NC}"
else
  echo -e "  ${YELLOW}⚠️  Pi not found. Install per https://pi.dev/docs/latest${NC}"
fi

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.pi"
DEST="./.pi"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "pi"
find "$SRC" -mindepth 1 -maxdepth 1 -not -name 'AGENTS.md' -exec cp -r {} "$DEST/" \;
echo -e "  ${GREEN}✅ Adapter copied → ./.pi/ (prompts + skills)${NC}"

# 2. AGENTS.md — merge into project root.
#    This is deliberate, not incidental: AGENTS.md is the only thing Pi loads
#    "regardless of project trust". Everything under .pi/ waits for the trust
#    prompt, so the rules have to arrive by a route that cannot be gated.
if [[ -f "$SRC/AGENTS.md" ]]; then
  bash "$SCRIPTS_DIR/merge_agents_md.sh" "$SRC/AGENTS.md" "./AGENTS.md"
  echo -e "  ${GREEN}✅ AGENTS.md OSP block merged at project root${NC}"
fi

# 3. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 4. Search runtime. Named for what it is on this tool — the venv exists so
#    osp_cli.py can run, not so an MCP server can be launched.
. "$SCRIPTS_DIR/init_mcp.sh"
echo -e "  ${GREEN}✅ Search tools available as a program → ${OSP_SEARCH_CLI#./}${NC}"
echo -e "     ${CYAN}Pi has no MCP client, so the agent calls it through bash.${NC}"

# 5. Sanity check: the bridge must actually run in this project.
if "$OSP_MCP_PYTHON" "$OSP_SEARCH_CLI" list >/dev/null 2>&1; then
  echo -e "  ${GREEN}✅ Search bridge answers — verified by running it${NC}"
else
  echo -e "  ${YELLOW}⚠️  The search bridge did not run. Try it yourself to see why:${NC}"
  echo "         $OSP_MCP_PYTHON $OSP_SEARCH_CLI list"
fi

# Closing message — shared wording lives in _post_install.sh
. "$SCRIPTS_DIR/_post_install.sh"
osp_post_install "Pi" \
  "Start Pi here and answer YES to the project trust prompt — until you do, Pi ignores everything under .pi/ and the OSP commands will not exist" \
  "If you already answered no, run /trust and then restart Pi (the running session is not reloaded)"
