#!/usr/bin/env bash
# Open ScholarPeer — Qwen Code installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='[0;32m'; YELLOW='[1;33m'; CYAN='[0;36m'; NC='[0m'

echo -e "\n${CYAN}Open ScholarPeer → Qwen Code${NC}\n"

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.qwen"
DEST="./.qwen"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "qwen"
find "$SRC" -mindepth 1 -maxdepth 1 -not -name 'QWEN.md' -exec cp -r {} "$DEST/" \;
echo -e "  ${GREEN}✅ Adapter copied → ./.qwen/${NC}"

# 2. QWEN.md — merge into project root (preserves user content)
if [[ -f "$SRC/QWEN.md" ]]; then
  bash "$SCRIPTS_DIR/merge_agents_md.sh" "$SRC/QWEN.md" "./QWEN.md"
  echo -e "  ${GREEN}✅ QWEN.md OSP block merged at project root${NC}"
fi

# 3. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 4. Set up self-contained CLI scripts in .open-scholar-peer/
. "$SCRIPTS_DIR/init_scripts.sh"

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo -e "  (1) Run ${CYAN}/open-scholar-peer${NC} in Qwen Code"
echo    "      The orchestrator reads your session state and guides you from there."
