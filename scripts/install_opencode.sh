#!/usr/bin/env bash
# Open ScholarPeer — OpenCode installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → OpenCode${NC}\n"

if command -v opencode &>/dev/null; then
  echo -e "  ${GREEN}✅ OpenCode detected${NC}"
else
  echo -e "  ${YELLOW}⚠️  OpenCode not found. Install per https://opencode.ai/docs/${NC}"
fi

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.opencode"
DEST="./.opencode"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "opencode"
find "$SRC" -mindepth 1 -maxdepth 1 -not -name 'AGENTS.md' -exec cp -r {} "$DEST/" \;
echo -e "  ${GREEN}✅ Adapter copied → ./.opencode/${NC}"

# 2. AGENTS.md — merge into project root
if [[ -f "$SRC/AGENTS.md" ]]; then
  bash "$SCRIPTS_DIR/merge_agents_md.sh" "$SRC/AGENTS.md" "./AGENTS.md"
  echo -e "  ${GREEN}✅ AGENTS.md OSP block merged at project root${NC}"
fi

# 3. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 4. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 5. OpenCode MCP — write ./.opencode/opencode.json (project-local).
#    OpenCode merges project config into global per key, and the project wins,
#    so the user's own servers survive and one paper folder cannot overwrite
#    another's. `opencode mcp add` exists but writes to the GLOBAL config with
#    no scope flag, which is why it is not used here.
#    Schema: root key `mcp`, entries {"type":"local","command":[argv...]}.
OPENCODE_CONFIG="./.opencode/opencode.json"
SNIPPET_PATH="./.open-scholar-peer/opencode_mcp_snippet.json"
mkdir -p "$(dirname "$OPENCODE_CONFIG")"

if python3 "$SCRIPTS_DIR/merge_mcp_config.py" "$OPENCODE_CONFIG" \
     "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER" --key mcp --style opencode >/dev/null 2>&1; then
  echo -e "  ${GREEN}✅ MCP servers configured → $OPENCODE_CONFIG${NC}"
else
  cat > "$SNIPPET_PATH" << JSON
{
  "mcp": {
    "osp": {
      "type": "local",
      "command": ["$OSP_MCP_PYTHON", "$OSP_MCP_SERVER"],
      "enabled": true
    },
    "markitdown": {
      "type": "local",
      "command": ["uvx", "markitdown-mcp"],
      "enabled": true
    }
  }
}
JSON
  echo -e "\n  ${YELLOW}⚠️  Could not merge into $OPENCODE_CONFIG — it was left untouched.${NC}"
  echo "     Merge these entries yourself, or run:"
  echo "         opencode mcp add osp -- $OSP_MCP_PYTHON $OSP_MCP_SERVER   (writes global config)"
  echo "         $SNIPPET_PATH"
fi

# Closing message — shared wording lives in _post_install.sh
. "$SCRIPTS_DIR/_post_install.sh"
osp_post_install "OpenCode"
