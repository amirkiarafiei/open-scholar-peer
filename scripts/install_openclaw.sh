#!/usr/bin/env bash
# Open ScholarPeer — OpenClaw installer
#
# OpenClaw is not a project-scoped coding agent. It is one long-lived Gateway
# per host, fronting chat channels, with a configured *workspace* that is its
# home. Discovery does not walk up from a nested folder to a parent repository,
# so installing here does not make this folder visible on its own.
#
# What that means in practice:
#   - The files land in this folder in the two places OpenClaw reads when it
#     runs here: ./.agents/skills/ and ./AGENTS.md. When a session executes
#     from another folder, "OpenClaw also loads that workspace's skills/ and
#     .agents/skills/ directories", and that folder's AGENTS.md is appended as
#     project context.
#   - Choosing the workspace stays with the user. Repointing
#     agents.defaults.workspace would move their whole assistant's home, which
#     is not an installer's decision to make. The options are printed instead.
#   - ~/.openclaw/openclaw.json is never written by this script. OpenClaw
#     "only accepts configurations that fully match the schema" and an unknown
#     key makes the Gateway refuse to start — taking the user's chat channels
#     and cron with it. MCP goes in through `openclaw mcp add`.

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → OpenClaw${NC}\n"

if command -v openclaw &>/dev/null; then
  echo -e "  ${GREEN}✅ OpenClaw detected${NC}"
else
  echo -e "  ${YELLOW}⚠️  openclaw not found. Install per https://docs.openclaw.ai/install${NC}"
fi

# 1. Copy adapter into the cross-tool skills location OpenClaw reads.
SRC="$ROOT_DIR/extensions/.openclaw"
DEST="./.agents"
mkdir -p "$DEST"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST" "openclaw"
mkdir -p "$DEST/skills"
cp -r "$SRC/skills/." "$DEST/skills/"
cp -r "$SRC/defaults" "$DEST/defaults"
echo -e "  ${GREEN}✅ Adapter copied → ./.agents/skills/ (8 commands + 8 personas)${NC}"

# 2. AGENTS.md — merge into project root. OpenClaw loads it from the
#    execution folder as project context.
if [[ -f "$SRC/AGENTS.md" ]]; then
  bash "$SCRIPTS_DIR/merge_agents_md.sh" "$SRC/AGENTS.md" "./AGENTS.md"
  echo -e "  ${GREEN}✅ AGENTS.md OSP block merged at project root${NC}"
fi

# 3. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 4. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 5. OpenClaw MCP — through the CLI only, for the reason in the header.
#    `openclaw mcp add` refuses a name that already exists and has no --force,
#    so without removing first a re-install could never update a stale path —
#    and a moved project or a rebuilt venv leaves exactly that. It also probes
#    the server live by default, which needs uvx and a network round trip.
MCP_OK=0
if command -v openclaw >/dev/null 2>&1; then
  for srv in osp markitdown; do
    timeout 30 openclaw mcp remove "$srv" </dev/null >/dev/null 2>&1 || true
  done
  timeout 90 openclaw mcp add osp --no-probe \
    --command "$OSP_MCP_PYTHON" --arg "$OSP_MCP_SERVER" </dev/null >/dev/null 2>&1 || true
  timeout 90 openclaw mcp add markitdown --no-probe \
    --command uvx --arg markitdown-mcp </dev/null >/dev/null 2>&1 || true
  if timeout 30 openclaw mcp list </dev/null 2>/dev/null | grep -q 'osp'; then
    MCP_OK=1
  fi
fi

if [[ $MCP_OK -eq 1 ]]; then
  echo -e "  ${GREEN}✅ MCP servers configured (global, read back and verified)${NC}"
else
  if command -v openclaw >/dev/null 2>&1; then
    echo -e "\n  ${YELLOW}⚠️  \`openclaw mcp add\` did not succeed. Run these yourself:${NC}"
  else
    echo -e "\n  ${YELLOW}⚠️  OpenClaw is not on PATH, so the MCP servers were not wired.${NC}"
    echo "     Once it is installed, run:"
  fi
  echo "         openclaw mcp remove osp            # only if it already exists"
  echo "         openclaw mcp add osp --no-probe --command $OSP_MCP_PYTHON --arg $OSP_MCP_SERVER"
  echo "         openclaw mcp add markitdown --no-probe --command uvx --arg markitdown-mcp"
  echo -e "     ${YELLOW}Do not hand-edit ~/.openclaw/openclaw.json — one unknown key stops${NC}"
  echo -e "     ${YELLOW}the whole Gateway from starting.${NC}"
fi

# Closing message — shared wording lives in _post_install.sh
#
# The workspace step is genuinely manual: OpenClaw has one home per agent and
# picking it is the user's call. It is stated here, where the user is standing,
# rather than buried in the documentation.
. "$SCRIPTS_DIR/_post_install.sh"
OPENCLAW_ACTIONS=()
[[ $MCP_OK -eq 0 ]] && OPENCLAW_ACTIONS+=("Run the two openclaw mcp add commands printed above — until then the search tools are not registered")
osp_post_install "OpenClaw" \
  "${OPENCLAW_ACTIONS[@]}" \
  "Point OpenClaw at this folder — it does not find a nested project on its own. Simplest: run it from here with  openclaw agent exec --cwd . --message-file task.md" \
  "For an ongoing agent instead, set its workspace to $(pwd) — per-agent via agents.entries.<id>.workspace, or for one run via OPENCLAW_WORKSPACE_DIR" \
  "Then ask it to run the review; the OSP commands appear as slash commands once this folder is its workspace"
