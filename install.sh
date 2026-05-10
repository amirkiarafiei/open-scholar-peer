#!/usr/bin/env bash
# Open ScholarPeer — Universal Selective Installer

set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
DEST_DIR=$(pwd)
SOURCE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
IS_REMOTE=false

# Remote-mode detection: when invoked via `curl ... | bash`, BASH_SOURCE[0] is
# empty and SOURCE_DIR collapses to the user's CWD. The reliable signal is
# simply: "do I have a scripts/ subdir adjacent to me?" If not, clone.
if [[ ! -d "$SOURCE_DIR/scripts" ]]; then
  IS_REMOTE=true
  echo -e "  ${CYAN}Open ScholarPeer → One-liner setup${NC}\n"
  if ! command -v git &>/dev/null; then
    echo "  ✗ git not found in PATH; needed to fetch the OSP repo. Install git and re-run."
    exit 1
  fi
  TEMP_DIR=$(mktemp -d)
  if ! git clone --depth 1 https://github.com/amirkiarafiei/open-scholar-peer "$TEMP_DIR" >/dev/null 2>&1; then
    echo "  ✗ Failed to clone open-scholar-peer from GitHub. Check your network and retry."
    exit 1
  fi
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

# When piped from `curl | bash`, stdin is the pipe (drained), so a normal `read`
# would return EOF immediately and silently default. Read the user's choice from
# the controlling terminal in that case so the menu actually works. If no tty
# is attached at all (truly non-interactive — CI, nohup, etc.), fall through to
# the default. Using `read` itself as the test avoids set -e killing us when
# /dev/tty exists in metadata but isn't actually openable.
choice=""
if [[ -t 0 ]]; then
  read -rp "Choice [1-13] (default: 1): " choice || true
elif read -rp "Choice [1-13] (default: 1): " choice </dev/tty 2>/dev/null; then
  : # tty input collected
else
  echo "  (no terminal available — defaulting to 1: Claude Code)"
fi
choice="${choice:-1}"

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
