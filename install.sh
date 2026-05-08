#!/usr/bin/env bash
# Open ScholarPeer — Universal Selective Installer

set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
DEST_DIR=$(pwd)
SOURCE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
IS_REMOTE=false

if [[ "$DEST_DIR" != "$SOURCE_DIR" ]] && [[ ! -d "$SOURCE_DIR/scripts" ]]; then
  IS_REMOTE=true
  echo -e "  ${CYAN}Open ScholarPeer → One-liner setup${NC}\n"
  TEMP_DIR=$(mktemp -d)
  git clone --depth 1 https://github.com/amirkiarafiei/open-scholar-peer "$TEMP_DIR" >/dev/null 2>&1
  SOURCE_DIR="$TEMP_DIR"
fi

echo -e "\n${CYAN}Open ScholarPeer (OSP) — Universal Selective Installer${NC}"
echo -e "A context-aware multi-agent framework for automated peer review.\n"

echo "Choose your primary AI tool environment:"
echo "  1) Claude Code"
echo "  2) Cursor"
echo "  3) Antigravity"
echo "  4) Gemini CLI"
echo "  5) Copilot CLI"
read -rp "Choice [1-5] (default: 3): " choice; choice="${choice:-3}"

cleanup() {
  if [ "$IS_REMOTE" = true ]; then
    rm -rf "$SOURCE_DIR"
  fi
}

trap cleanup EXIT

case "$choice" in
  1) bash "$SOURCE_DIR/scripts/install_claude.sh" ;;
  2) bash "$SOURCE_DIR/scripts/install_cursor.sh" ;;
  3) bash "$SOURCE_DIR/scripts/install_antigravity.sh" ;;
  4) bash "$SOURCE_DIR/scripts/install_gemini.sh" ;;
  5) bash "$SOURCE_DIR/scripts/install_copilot.sh" ;;
  *) bash "$SOURCE_DIR/scripts/install_antigravity.sh" ;;
esac
