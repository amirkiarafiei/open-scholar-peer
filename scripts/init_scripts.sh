#!/usr/bin/env bash
# init_scripts.sh — Set up self-contained .open-scholar-peer/ in the current project.
# Copies the OSP CLI tools, builds a Python venv, installs requirements.
# Generates the execution shims.
#
# Called by every per-tool installer.

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'

_spin() {
  local pid=$1 msg=$2
  local frames='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏' i=0
  if [[ ! -t 1 ]]; then
    echo "  $msg"
    while kill -0 "$pid" 2>/dev/null; do
      sleep 0.5
    done
    return 0
  fi
  while kill -0 "$pid" 2>/dev/null; do
    printf "\r  ${CYAN}%s${NC}  %s" "${frames:$((i % ${#frames})):1}" "$msg"
    sleep 0.1
    ((i++)) || true
  done
  printf "\r\033[K"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_DIR="$(pwd)/.brain/runtime"
SOURCE_DIR="$ROOT_DIR/scripts/tools"

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo -e "  ${RED}✗ CLI source not found at $SOURCE_DIR${NC}"
  exit 1
fi

# Wipe stale managed files before copy, preserving `venv`
if [[ -d "$TARGET_DIR" ]]; then
  find "$TARGET_DIR" -mindepth 1 -maxdepth 1 -not -name 'venv' -exec rm -rf {} +
fi

mkdir -p "$TARGET_DIR"
cp -r "$SOURCE_DIR/." "$TARGET_DIR/"
echo -e "  ${GREEN}✅ CLI scripts copied → .brain/runtime/${NC}"

# Check for uv (Fix 9 grace)
VENV_DIR="$TARGET_DIR/venv"
if command -v uv &>/dev/null; then
  echo -e "  ${GREEN}✅ uv detected — using uv for dependency caching${NC}"
else
  # Set up standard venv if uv is absent
  if [[ ! -d "$VENV_DIR" ]]; then
    if ! command -v python3 &>/dev/null; then
      echo -e "  ${RED}✗ python3 not found in PATH; install Python 3.10+ and re-run${NC}"
      exit 1
    fi
    if ! python3 -c "import ensurepip" &>/dev/null; then
      py_minor=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "3")
      echo -e "  ${RED}✗ python3 venv module is missing. Install with: sudo apt install python${py_minor}-venv${NC}"
      exit 1
    fi
    python3 -m venv "$VENV_DIR" &>/dev/null &
    _spin $! "Creating Python virtualenv…"
    wait $! || { echo -e "  ${RED}✗ Failed to create virtualenv${NC}"; exit 1; }
    echo -e "  ${GREEN}✅ Virtualenv created → .brain/runtime/venv${NC}"
  else
    echo -e "  ${YELLOW}ℹ️  Reusing existing venv at .brain/runtime/venv${NC}"
  fi

  # Install requirements
  "$VENV_DIR/bin/pip" install --quiet --upgrade pip &>/dev/null &
  _spin $! "Upgrading pip…"
  wait $! || true

  _pip_log=$(mktemp)
  "$VENV_DIR/bin/pip" install --quiet -r "$TARGET_DIR/requirements.txt" >"$_pip_log" 2>&1 &
  _spin $! "Installing dependencies (this may take ~1 min)…"
  if wait $!; then
    rm -f "$_pip_log"
    echo -e "  ${GREEN}✅ Python dependencies installed${NC}"
  else
    echo -e "  ${RED}✗ pip install failed:${NC}"
    cat "$_pip_log"
    rm -f "$_pip_log"
    exit 1
  fi
fi

# Write the Unix shim
cat > "$TARGET_DIR/osp" << 'SHIM'
#!/usr/bin/env bash
# Open ScholarPeer Universal CLI Shim
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "$DIR/venv/bin/python" ]]; then
  exec "$DIR/venv/bin/python" "$DIR/osp_cli.py" "$@"
elif command -v uv &>/dev/null; then
  exec uv run --script "$DIR/osp_cli.py" "$@"
else
  echo '[{"error": "No Python virtualenv or uv detected. Please run bash install.sh to set up dependencies."}]' >&2
  exit 1
fi
SHIM
chmod +x "$TARGET_DIR/osp"
echo -e "  ${GREEN}✅ Created Unix execution shim → .brain/runtime/osp${NC}"

# Write the Windows shim
cat > "$TARGET_DIR/osp.cmd" << 'SHIM'
@echo off
setlocal
set "DIR=%~dp0"
if exist "%DIR%venv\Scripts\python.exe" (
  "%DIR%venv\Scripts\python.exe" "%DIR%osp_cli.py" %*
) else (
  uv run --script "%DIR%osp_cli.py" %* 2>nul || python "%DIR%osp_cli.py" %*
)
endlocal
SHIM
echo -e "  ${GREEN}✅ Created Windows execution shim → .brain/runtime/osp.cmd${NC}"

# Add .brain/ to .gitignore
GITIGNORE="./.gitignore"
if [[ -f "$GITIGNORE" ]]; then
  if ! grep -qF ".brain/" "$GITIGNORE" 2>/dev/null; then
    printf "\n# Open ScholarPeer working files & runtime (gitignored)\n.brain/\n" >> "$GITIGNORE"
    echo -e "  ${GREEN}✅ Added .brain/ to .gitignore${NC}"
  fi
else
  printf "# Open ScholarPeer working files & runtime\n.brain/\n" > "$GITIGNORE"
  echo -e "  ${GREEN}✅ Created .gitignore with .brain/ entry${NC}"
fi

# Create .env if it doesn't exist
ENV_FILE="./.env"
if [[ ! -f "$ENV_FILE" ]]; then
  cat > "$ENV_FILE" << 'ENVEOF'
# Open ScholarPeer — config (this file is gitignored)
# SEMANTIC_SCHOLAR_API_KEY=sk-...
# OSP_CALL_TIMEOUT=180
ENVEOF
  echo -e "  ${GREEN}✅ Created .env at project root — add your API keys there${NC}"
fi

if [[ -f "$GITIGNORE" ]]; then
  if ! grep -qxF ".env" "$GITIGNORE" 2>/dev/null; then
    printf "\n# API keys (never commit)\n.env\n" >> "$GITIGNORE"
    echo -e "  ${GREEN}✅ Added .env to .gitignore${NC}"
  fi
fi
