#!/usr/bin/env bash
# Open ScholarPeer — Antigravity CLI installer

set -e
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPTS_DIR/.." && pwd)"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "\n${CYAN}Open ScholarPeer → Antigravity CLI${NC}\n"

# Antigravity CLI references both `.agents/` (legacy default) and `.agent/` (newer).
# Sync script generates both — copy whichever exists, prefer .agents/ since that's
# what most current Antigravity CLI versions still discover.

# 1. Copy adapter to project. Wipe stale OSP-managed files in BOTH .agents/
#    (legacy discovery) and .agent/ (newer) before re-copy; user content preserved.
SRC="$ROOT_DIR/extensions/.agents"
DEST_PRIMARY="./.agents"
DEST_FUTURE="./.agent"
mkdir -p "$DEST_PRIMARY" "$DEST_FUTURE"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST_PRIMARY" "antigravity"
bash "$SCRIPTS_DIR/clean_adapter.sh" "$DEST_FUTURE" "antigravity"
cp -r "$SRC/." "$DEST_PRIMARY/"
cp -r "$ROOT_DIR/extensions/.agent/." "$DEST_FUTURE/"
echo -e "  ${GREEN}✅ Adapter copied → ./.agents/ and ./.agent/${NC}"

# 2. Brain
"$SCRIPTS_DIR/init_brain.sh"

# 3. MCP server runtime
. "$SCRIPTS_DIR/init_mcp.sh"

# 4. Antigravity CLI MCP config — ~/.gemini/antigravity/mcp_config.json (global, JSON,
#    mcpServers format). Per https://antigravity.google/docs/mcp.
AG_MCP_CONFIG="${HOME}/.gemini/antigravity/mcp_config.json"
mkdir -p "$(dirname "$AG_MCP_CONFIG")"
python3 "$SCRIPTS_DIR/merge_mcp_config.py" "$AG_MCP_CONFIG" "$OSP_MCP_PYTHON" "$OSP_MCP_SERVER"

# Save a ready-to-paste snippet alongside the project for manual verification.
: "${OSP_MCP_PYTHON:?OSP_MCP_PYTHON not set; run init_mcp.sh first}"
: "${OSP_MCP_SERVER:?OSP_MCP_SERVER not set; run init_mcp.sh first}"
python3 - <<'PY'
import json
import os
import sys
from pathlib import Path

try:
    osp_python = os.environ["OSP_MCP_PYTHON"]
    osp_server = os.environ["OSP_MCP_SERVER"]
except KeyError as exc:
    print(
        f"ERROR: {exc.args[0]} is not set. Run init_mcp.sh before writing the Antigravity CLI snippet.",
        file=sys.stderr,
    )
    raise SystemExit(1)

snippet = {
    "mcpServers": {
        "osp": {
            "command": osp_python,
            "args": [osp_server],
        },
        # The merged config at ~/.gemini/antigravity/mcp_config.json includes both
        # OSP and the markitdown MCP server, so the snippet mirrors the same pair
        # of MCP servers for easy copy/paste.
        "markitdown": {
            "command": "uvx",
            "args": ["markitdown-mcp"],
        },
    }
}
path = Path("./.open-scholar-peer/antigravity_mcp_snippet.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(snippet, indent=2) + "\n", encoding="utf-8")
PY

echo -e "\n  ${GREEN}ℹ️  Antigravity CLI supports subagents — /5-osp-qa uses subagent mode.${NC}"

echo -e "\n${GREEN}Done!${NC}\n"
echo -e "Next:"
echo    "  (1) Restart Antigravity CLI  (picks up the new MCP servers)"
echo -e "  (2) Run ${CYAN}/open-scholar-peer${NC} — the orchestrator guides you from there."
