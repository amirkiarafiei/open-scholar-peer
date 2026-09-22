#!/usr/bin/env bash
# Open ScholarPeer — Kilo Code installer
#
# Target the CURRENT Kilo layout, not the one most guides still describe.
# `.kilocode/` belongs to the legacy IDE extensions, which reached end of life
# on 2026-07-31; the current CLI reads `.kilo/` and `kilo.json`. The Kilo CLI
# is a fork of OpenCode, so its MCP block is OpenCode's shape — the same
# writer serves both.
#
# One rule worth stating, because it is the opposite of what the directory
# name suggests: `.kilo/rules/` is NOT read unless it is listed in an
# `instructions` key. A rules file dropped there is a silent no-op. AGENTS.md
# is read automatically and cannot be switched off, so the rules go there.

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Kilo Code${NC}\n"

if command -v kilo &>/dev/null; then
  echo -e "  ${GREEN}✅ Kilo Code detected${NC}"
else
  echo -e "  ${YELLOW}⚠️  kilo not found. Install with: npm install -g @kilocode/cli${NC}"
fi

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.kilo"
DEST="./.kilo"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "kilo"
find "$SRC" -mindepth 1 -maxdepth 1 -not -name 'AGENTS.md' -exec cp -r {} "$DEST/" \;
echo -e "  ${GREEN}✅ Adapter copied → ./.kilo/ (commands + skills + agents)${NC}"

# 2. AGENTS.md — merge into project root. This is the rules path on Kilo.
if [[ -f "$SRC/AGENTS.md" ]]; then
  bash "$SCRIPTS_DIR/merge_agents_md.sh" "$SRC/AGENTS.md" "./AGENTS.md"
  echo -e "  ${GREEN}✅ AGENTS.md OSP block merged at project root${NC}"
fi

# 3. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 4. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 5. Kilo MCP — project-local ./.kilo/kilo.json, root key `mcp`, entries in
#    OpenCode's {type: local, command: [argv...]} shape. A `kilo mcp add`
#    subcommand exists, but the file is written directly so the entry is
#    project-scoped and a re-run is idempotent.
KILO_CONFIG="$DEST/kilo.json"
if python3 "$SCRIPTS_DIR/merge_mcp_config.py" "$KILO_CONFIG" \
     "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER" --key mcp --style opencode >/dev/null 2>&1; then
  echo -e "  ${GREEN}✅ MCP servers configured → $KILO_CONFIG${NC}"
else
  echo -e "\n  ${YELLOW}⚠️  Could not merge into $KILO_CONFIG — it was left untouched.${NC}"
  echo "     Add an \"mcp\" block there yourself, or use /mcps inside Kilo."
fi

# Closing message — shared wording lives in _post_install.sh
. "$SCRIPTS_DIR/_post_install.sh"
osp_post_install "Kilo Code"
