#!/usr/bin/env bash
# Open ScholarPeer — Mistral Vibe installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='[0;32m'; YELLOW='[1;33m'; CYAN='[0;36m'; NC='[0m'

echo -e "\n${CYAN}Open ScholarPeer → Mistral Vibe${NC}\n"

# 1. Copy adapter — Vibe loads skills from .vibe/skills/ AND .agents/skills/.
SRC="$ROOT_DIR/extensions/.vibe"
DEST="./.vibe"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "vibe"
find "$SRC" -mindepth 1 -maxdepth 1 -not -name 'AGENTS.md' -exec cp -r {} "$DEST/" \;
echo -e "  ${GREEN}✅ Adapter copied → ./.vibe/${NC}"

# Mirror skills to .agents/skills/ (Vibe's universal skill discovery path)
mkdir -p "./.agents/skills"
if [[ -d "$SRC/skills" ]]; then
  find "./.agents/skills" -maxdepth 1 -type d -name 'osp-*' -exec rm -rf {} + 2>/dev/null || true
  cp -r "$SRC/skills/." "./.agents/skills/"
  echo -e "  ${GREEN}✅ Skills mirrored → ./.agents/skills/${NC}"
fi

# 2. AGENTS.md — merge into project root
if [[ -f "$SRC/AGENTS.md" ]]; then
  bash "$SCRIPTS_DIR/merge_agents_md.sh" "$SRC/AGENTS.md" "./AGENTS.md"
  echo -e "  ${GREEN}✅ AGENTS.md OSP block merged at project root${NC}"
fi

# 3. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 4. Set up self-contained CLI scripts in .open-scholar-peer/
. "$SCRIPTS_DIR/init_scripts.sh"

echo -e "\n  ${YELLOW}ℹ️  Vibe documents independent agent profiles but no general subagent${NC}"
echo "     delegation — /5-osp-qa falls back to self-reflection mode (see"
# Wait, typo in the line below was in the original snippet, let's keep it or fix it: docs/KNOWN_LIMITATIONS.md
echo "     docs/KNOWN_LIMITATIONS.md)."

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo -e "  (1) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
