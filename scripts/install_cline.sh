#!/usr/bin/env bash
# Open ScholarPeer — Cline installer
#
# Two findings decide the shape of this script, and both contradict Cline's
# own published docs, so they were taken from the source at HEAD:
#
#   - MCP config is global, at ~/.cline/data/settings/cline_mcp_settings.json,
#     and the CLI and the VS Code extension now share it. It is a plain file
#     under ~/.cline/, not VS Code extension storage, so it is safe to merge.
#     Both $CLINE_MCP_SETTINGS_PATH and $CLINE_DATA_DIR override the location
#     and are honoured here. The docs' ~/.cline/mcp.json and .cline/mcp.json
#     are read by nothing.
#   - Slash commands are skills now. Workflows still resolve in code but have
#     been dropped from the documentation, so the eight commands ship as
#     skill directories under .cline/skills/.
#
# Cline's subagents cannot reach MCP servers, which is most of what an OSP
# answer needs, so the Q&A engine uses self-reflection here.

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Cline${NC}\n"

if command -v cline &>/dev/null; then
  echo -e "  ${GREEN}✅ Cline CLI detected${NC}"
else
  echo -e "  ${YELLOW}ℹ️  Cline CLI not on PATH. The IDE extension works too —${NC}"
  echo -e "     ${YELLOW}both read the same files. See https://docs.cline.bot${NC}"
fi

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.cline"
DEST="./.cline"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "cline"
cp -r "$SRC/." "$DEST/"
echo -e "  ${GREEN}✅ Adapter copied → ./.cline/ (skills + rules)${NC}"

# 2. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 3. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 4. Cline MCP — global, shared by the CLI and the IDE extension.
if [[ -n "${CLINE_MCP_SETTINGS_PATH:-}" ]]; then
  CLINE_MCP_CONFIG="$CLINE_MCP_SETTINGS_PATH"
else
  # Cline resolves the data dir as $CLINE_DATA_DIR, else $CLINE_DIR/data,
  # else ~/.cline/data. Missing CLINE_DIR meant a green tick on a file
  # Cline never reads.
  CLINE_MCP_CONFIG="${CLINE_DATA_DIR:-${CLINE_DIR:-$HOME/.cline}/data}/settings/cline_mcp_settings.json"
fi
mkdir -p "$(dirname "$CLINE_MCP_CONFIG")"

if python3 "$SCRIPTS_DIR/merge_mcp_config.py" "$CLINE_MCP_CONFIG" \
     "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER" >/dev/null 2>&1; then
  echo -e "  ${GREEN}✅ MCP servers configured → $CLINE_MCP_CONFIG${NC}"
elif command -v cline >/dev/null 2>&1 &&
     timeout 90 cline mcp install osp --yes -- "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER" </dev/null >/dev/null 2>&1 &&
     timeout 90 cline mcp install markitdown --yes -- uvx markitdown-mcp </dev/null >/dev/null 2>&1; then
  echo -e "  ${GREEN}✅ MCP servers configured via cline mcp install${NC}"
else
  echo -e "\n  ${YELLOW}⚠️  Could not configure MCP — $CLINE_MCP_CONFIG was left untouched.${NC}"
  echo "     Add the servers yourself with:"
  echo "         cline mcp install osp --yes -- $OSP_MCP_PYTHON $OSP_MCP_SERVER"
  echo "         cline mcp install markitdown --yes -- uvx markitdown-mcp"
fi

# Closing message — shared wording lives in _post_install.sh
. "$SCRIPTS_DIR/_post_install.sh"
osp_post_install "Cline" \
  "Cline's MCP config is per-machine, not per-project — installing OSP in a second paper folder repoints these servers at that folder"
