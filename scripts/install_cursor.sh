#!/usr/bin/env bash
# Open ScholarPeer — Cursor installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='[0;32m'; YELLOW='[1;33m'; CYAN='[0;36m'; NC='[0m'

echo -e "\n${CYAN}Open ScholarPeer → Cursor${NC}\n"

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.cursor"
DEST="./.cursor"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "cursor"
cp -r "$SRC/." "$DEST/"
echo -e "  ${GREEN}✅ Adapter copied → ./.cursor/${NC}"

# 2. Initialize .brain/
"$SCRIPTS_DIR/init_brain.sh"

# 3. Set up self-contained CLI scripts in .open-scholar-peer/
. "$SCRIPTS_DIR/init_scripts.sh"

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo -e "  (1) Restart Cursor (to reload rules)"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
