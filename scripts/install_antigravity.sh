#!/usr/bin/env bash
# Open ScholarPeer — Antigravity installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='[0;32m'; YELLOW='[1;33m'; CYAN='[0;36m'; NC='[0m'

echo -e "\n${CYAN}Open ScholarPeer → Antigravity${NC}\n"

SRC="$ROOT_DIR/extensions/.agent"
DEST_PRIMARY="./.agents"
DEST_FUTURE="./.agent"
mkdir -p "$DEST_PRIMARY" "$DEST_FUTURE"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST_PRIMARY" "antigravity"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST_FUTURE" "antigravity"
cp -r "$SRC/." "$DEST_PRIMARY/"
cp -r "$SRC/." "$DEST_FUTURE/"
echo -e "  ${GREEN}✅ Adapter copied → ./.agents/ and ./.agent/${NC}"

# 2. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 3. Set up self-contained CLI scripts in .open-scholar-peer/
. "$SCRIPTS_DIR/init_scripts.sh"

echo -e "\n  ${YELLOW}ℹ️  Antigravity does NOT support general subagents — /5-osp-qa falls${NC}"
echo "     back to self-reflection mode (see docs/KNOWN_LIMITATIONS.md)."

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo -e "  (1) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
