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
echo "  1)  Claude Code"
echo "  2)  Cursor"
echo "  3)  Antigravity"
echo "  4)  Gemini CLI"
echo "  5)  Copilot CLI"
echo "  6)  Codex CLI"
echo "  7)  Qwen Code"
echo "  8)  OpenCode"
echo "  9)  Junie"
echo "  10) Kiro"
echo "  11) Kimi Code"
echo "  12) Mistral Vibe"
echo "  13) OpenHands"
read -rp "Choice [1-13] (default: 1): " choice; choice="${choice:-1}"

cleanup() {
  if [ "$IS_REMOTE" = true ]; then
    rm -rf "$SOURCE_DIR"
  fi
}

trap cleanup EXIT

case "$choice" in
  1)  bash "$SOURCE_DIR/scripts/install_claude.sh" ;;
  2)  bash "$SOURCE_DIR/scripts/install_cursor.sh" ;;
  3)  bash "$SOURCE_DIR/scripts/install_antigravity.sh" ;;
  4)  bash "$SOURCE_DIR/scripts/install_gemini.sh" ;;
  5)  bash "$SOURCE_DIR/scripts/install_copilot.sh" ;;
  6)  bash "$SOURCE_DIR/scripts/install_codex.sh" ;;
  7)  bash "$SOURCE_DIR/scripts/install_qwen.sh" ;;
  8)  bash "$SOURCE_DIR/scripts/install_opencode.sh" ;;
  9)  bash "$SOURCE_DIR/scripts/install_junie.sh" ;;
  10) bash "$SOURCE_DIR/scripts/install_kiro.sh" ;;
  11) bash "$SOURCE_DIR/scripts/install_kimi.sh" ;;
  12) bash "$SOURCE_DIR/scripts/install_vibe.sh" ;;
  13) bash "$SOURCE_DIR/scripts/install_openhands.sh" ;;
  *)  bash "$SOURCE_DIR/scripts/install_claude.sh" ;;
esac
