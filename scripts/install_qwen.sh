#!/usr/bin/env bash
# Open ScholarPeer — Qwen Code installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Qwen Code${NC}\n"

if command -v qwen &>/dev/null; then
  echo -e "  ${GREEN}✅ Qwen Code detected${NC}"
else
  echo -e "  ${YELLOW}⚠️  Qwen Code not found. Install per https://github.com/QwenLM/qwen-code${NC}"
fi

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.qwen"
DEST="./.qwen"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "qwen"
# Copy everything except QWEN.md (it goes to project root, merged separately)
find "$SRC" -mindepth 1 -maxdepth 1 -not -name 'QWEN.md' -exec cp -r {} "$DEST/" \;
echo -e "  ${GREEN}✅ Adapter copied → ./.qwen/${NC}"

# 2. QWEN.md — merge into project root
if [[ -f "$SRC/QWEN.md" ]]; then
  bash "$SCRIPTS_DIR/merge_agents_md.sh" "$SRC/QWEN.md" "./QWEN.md"
  echo -e "  ${GREEN}✅ QWEN.md OSP block merged at project root${NC}"
fi

# 3. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 4. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 5. Qwen MCP config — merge into ./.qwen/settings.json (Qwen's local MCP config)
python3 "$SCRIPTS_DIR/merge_mcp_config.py" "./.qwen/settings.json" "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER"

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo    "  (1) Restart your Qwen Code session  (picks up the new MCP servers)"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
