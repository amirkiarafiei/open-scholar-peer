#!/usr/bin/env bash
# Open ScholarPeer — Grok Build installer
#
# Grok Build keeps MCP servers in TOML, one named table per server, and ships
# a non-interactive `grok mcp add` that writes the project scope directly.
# That command is preferred: it edits the user's config the way the vendor
# intends. Writing the file ourselves is the fallback for when grok is not yet
# on PATH.
#
# Two discovery rules of Grok Build's shape this script:
#   - rules under .grok/rules/ are "always scanned", unlike the .claude and
#     .cursor compatibility directories a user can switch off;
#   - files ignored by .gitignore are skipped during discovery, so ignoring
#     .grok/ silently removes the rules.

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Grok Build${NC}\n"

if command -v grok &>/dev/null; then
  echo -e "  ${GREEN}✅ Grok Build detected${NC}"
else
  echo -e "  ${YELLOW}⚠️  grok not found. Install per https://docs.x.ai/build/overview${NC}"
fi

# 1. Copy adapter (wipe stale OSP-managed files first; user content preserved)
SRC="$ROOT_DIR/extensions/.grok"
DEST="./.grok"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "grok"
cp -r "$SRC/." "$DEST/"
echo -e "  ${GREEN}✅ Adapter copied → ./.grok/ (commands + skills + agents + rules)${NC}"

# 2. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 3. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 4. Grok MCP — project scope. `grok mcp add --scope project` writes
#    ./.grok/config.toml and preserves the rest of the file.
GROK_CONFIG="$DEST/config.toml"
if command -v grok >/dev/null 2>&1 &&
   timeout 90 grok mcp add --scope project osp -- "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER" </dev/null >/dev/null 2>&1 &&
   timeout 90 grok mcp add --scope project markitdown -- uvx markitdown-mcp </dev/null >/dev/null 2>&1; then
  echo -e "  ${GREEN}✅ MCP servers configured → $GROK_CONFIG (via grok mcp add)${NC}"
elif python3 "$SCRIPTS_DIR/merge_mcp_toml.py" "$GROK_CONFIG" \
       "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER" --style table >/dev/null 2>&1; then
  echo -e "  ${GREEN}✅ MCP servers configured → $GROK_CONFIG${NC}"
else
  echo -e "\n  ${YELLOW}⚠️  Could not configure MCP — $GROK_CONFIG was left untouched.${NC}"
  echo "     Once Grok Build is installed, run:"
  echo "         grok mcp add --scope project osp -- $OSP_MCP_PYTHON $OSP_MCP_SERVER"
  echo "         grok mcp add --scope project markitdown -- uvx markitdown-mcp"
fi

# 5. Grok Build skips gitignored files when discovering rules and skills.
if [[ -f .gitignore ]] && grep -qE '^\s*\.grok/?\s*$' .gitignore; then
  echo -e "\n  ${YELLOW}⚠️  .gitignore ignores .grok/ — Grok Build skips gitignored files${NC}"
  echo -e "     ${YELLOW}when it discovers rules and skills, so OSP would be invisible.${NC}"
  echo "     Remove that line to keep the OSP rules loading."
fi

# Closing message — shared wording lives in _post_install.sh
. "$SCRIPTS_DIR/_post_install.sh"
osp_post_install "Grok Build" \
  "Grok Build loads project rules only for a trusted folder — accept the trust prompt, or start it with: grok --trust"
