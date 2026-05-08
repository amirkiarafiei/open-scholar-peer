#!/usr/bin/env bash
# init_mcp.sh — Set up self-contained .scholar-peer/mcp/ in the current project.
# Copies the OSP MCP server, builds a Python venv, installs requirements.
# Idempotent — re-running with an existing .venv preserves it (only re-installs).
#
# Outputs (env vars, exported on stdout via `eval $(... | grep ^export)` style):
#   OSP_MCP_PYTHON     — absolute path to the venv's Python
#   OSP_MCP_SERVER     — absolute path to osp_mcp.py inside the project
#
# Called by every per-tool installer.

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_DIR="$(pwd)/.scholar-peer/mcp"
SOURCE_DIR="$ROOT_DIR/mcp-server"

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo -e "  ${RED}✗ mcp-server source not found at $SOURCE_DIR${NC}"
  return 1 2>/dev/null || exit 1
fi

# Wipe stale managed files before re-copy, but preserve `.venv/` so we don't
# pay the venv-rebuild + pip-install cost on every re-install.
if [[ -d "$TARGET_DIR" ]]; then
  find "$TARGET_DIR" -mindepth 1 -maxdepth 1 -not -name '.venv' -exec rm -rf {} +
fi

# Copy server files (overwrite — server source is authoritative)
mkdir -p "$TARGET_DIR"
cp -r "$SOURCE_DIR/." "$TARGET_DIR/"
echo -e "  ${GREEN}✅ MCP server copied → .scholar-peer/mcp/${NC}"

# Set up venv
VENV_DIR="$TARGET_DIR/.venv"
if [[ ! -d "$VENV_DIR" ]]; then
  if ! command -v python3 &>/dev/null; then
    echo -e "  ${RED}✗ python3 not found in PATH; install Python 3.10+ and re-run${NC}"
    return 1 2>/dev/null || exit 1
  fi
  python3 -m venv "$VENV_DIR"
  echo -e "  ${GREEN}✅ Virtualenv created → .scholar-peer/mcp/.venv${NC}"
else
  echo -e "  ${YELLOW}ℹ️  Reusing existing venv at .scholar-peer/mcp/.venv${NC}"
fi

# Install requirements (always run — pip is fast on no-op)
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$TARGET_DIR/requirements.txt"
echo -e "  ${GREEN}✅ Python dependencies installed${NC}"

# Add .scholar-peer/ to .gitignore
GITIGNORE="./.gitignore"
if [[ -f "$GITIGNORE" ]]; then
  if ! grep -qF ".scholar-peer/" "$GITIGNORE" 2>/dev/null; then
    printf "\n# Open ScholarPeer MCP runtime (venv + server, gitignored)\n.scholar-peer/\n" >> "$GITIGNORE"
    echo -e "  ${GREEN}✅ Added .scholar-peer/ to .gitignore${NC}"
  fi
else
  printf "# Open ScholarPeer MCP runtime\n.scholar-peer/\n" > "$GITIGNORE"
  echo -e "  ${GREEN}✅ Created .gitignore with .scholar-peer/ entry${NC}"
fi

# Optional: prompt for Semantic Scholar API key
if [[ -z "$SEMANTIC_SCHOLAR_API_KEY" ]]; then
  echo ""
  echo -e "  ${YELLOW}ℹ️  Semantic Scholar API key not set — anonymous rate limits will apply.${NC}"
  echo "     Get a free key at https://www.semanticscholar.org/product/api#api-key"
  echo "     Then add to your shell profile: export SEMANTIC_SCHOLAR_API_KEY=sk-..."
fi

# Create .env at project root if it doesn't exist (for API keys)
ENV_FILE="./.env"
if [[ ! -f "$ENV_FILE" ]]; then
  cat > "$ENV_FILE" << 'ENVEOF'
# Open ScholarPeer — API keys (this file is gitignored)
# Uncomment and fill in to enable higher rate limits.

# Semantic Scholar API key — free at https://www.semanticscholar.org/product/api
# SEMANTIC_SCHOLAR_API_KEY=sk-...
ENVEOF
  echo -e "  ${GREEN}✅ Created .env at project root — add your API keys there${NC}"
else
  echo -e "  ${YELLOW}ℹ️  .env already exists at project root${NC}"
fi

# Add .env to .gitignore if not already there
if [[ -f "$GITIGNORE" ]]; then
  if ! grep -qxF ".env" "$GITIGNORE" 2>/dev/null; then
    printf "\n# API keys (never commit)\n.env\n" >> "$GITIGNORE"
    echo -e "  ${GREEN}✅ Added .env to .gitignore${NC}"
  fi
fi

# Export paths so the calling installer can write them into MCP config
export OSP_MCP_PYTHON="$VENV_DIR/bin/python"
export OSP_MCP_SERVER="$TARGET_DIR/osp_mcp.py"
