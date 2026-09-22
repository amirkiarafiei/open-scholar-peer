#!/usr/bin/env bash
# init_mcp.sh — Set up self-contained .open-scholar-peer/mcp/ in the current project.
# Copies the OSP MCP server, builds a Python venv, installs requirements.
# Idempotent — re-running with an existing .venv preserves it (only re-installs).
#
# Outputs (env vars, exported on stdout via `eval $(... | grep ^export)` style):
#   OSP_MCP_PYTHON     — absolute path to the venv's Python
#   OSP_MCP_SERVER     — absolute path to osp_mcp.py inside the project
#
# Called by every per-tool installer.

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'

# _spin PID MESSAGE
# Shows a braille spinner beside MESSAGE while PID is running, then erases the line.
# Prints a one-shot log line in non-TTY mode (CI, piped output).
#
# IMPORTANT: _spin must NEVER call `wait` itself. The caller (`wait $! || ...`
# or `if wait $!; then ...`) is the one that reaps the background process and
# reads its real exit status. If _spin reaps first, the caller's `wait $!`
# returns 127 ("not a child of this shell") and the error-handling branch
# fires even on success — which is what was breaking init_mcp.sh in non-TTY.
_spin() {
  local pid=$1 msg=$2
  local frames='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏' i=0
  if [[ ! -t 1 ]]; then
    echo "  $msg"
    # Poll without reaping so the caller's `wait $!` still returns the real status.
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
  printf "\r\033[K"   # erase spinner line
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_DIR="$(pwd)/.open-scholar-peer/mcp"
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
# Do not ship this machine's bytecode. It is stale the moment it is copied, it
# is not ours to put in someone's project, and it grows every time a file is
# added to mcp-server/.
#
# -maxdepth 2 on purpose. The venv lives INSIDE $TARGET_DIR and is deliberately
# preserved by the wipe above; an unbounded find walks straight into it and
# deletes site-packages' bytecode too — measured at 348 directories and 2,945
# .pyc files on a normal install, on every re-install, for nothing.
find "$TARGET_DIR" -maxdepth 2 -name '__pycache__' -type d -not -path "$TARGET_DIR/.venv/*" \
  -prune -exec rm -rf {} + 2>/dev/null || true
echo -e "  ${GREEN}✅ MCP server copied → .open-scholar-peer/mcp/${NC}"

# Set up venv
VENV_DIR="$TARGET_DIR/.venv"

# A venv is a set of symlinks to one interpreter. If the OS removed that
# interpreter — a distro upgrade past the version it was built against — the
# directory is still there and still looks valid, but nothing in it runs. The
# install then failed at `pip install` with a log, which is legible but is not
# the same as fixing itself. Rebuild instead: the venv holds nothing the user
# owns.
if [[ -d "$VENV_DIR" ]] && ! "$VENV_DIR/bin/python" -V &>/dev/null; then
  echo -e "  ${YELLOW}⚠️  The existing virtualenv no longer runs — its Python is gone."
  echo -e "      Rebuilding it.${NC}"
  rm -rf "$VENV_DIR"
fi

if [[ ! -d "$VENV_DIR" ]]; then
  if ! command -v python3 &>/dev/null; then
    echo -e "  ${RED}✗ python3 not found in PATH; install Python 3.10+ and re-run${NC}"
    return 1 2>/dev/null || exit 1
  fi
  # On Debian/Ubuntu, `python3` ships without `ensurepip`/`venv` until the
  # `python3-venv` apt package is installed. Detect that up-front so users get
  # an actionable error instead of a generic "Failed to create virtualenv".
  if ! python3 -c "import ensurepip" &>/dev/null; then
    py_minor=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "3")
    echo -e "  ${RED}✗ python3 venv module is missing (ensurepip not available).${NC}"
    echo "     On Debian/Ubuntu, install it with:"
    echo "         sudo apt install python${py_minor}-venv"
    echo "     On other systems, ensure your Python install includes the venv module."
    return 1 2>/dev/null || exit 1
  fi
  python3 -m venv "$VENV_DIR" &>/dev/null &
  _spin $! "Creating Python virtualenv…"
  wait $! || { echo -e "  ${RED}✗ Failed to create virtualenv${NC}"; exit 1; }
  echo -e "  ${GREEN}✅ Virtualenv created → .open-scholar-peer/mcp/.venv${NC}"
else
  echo -e "  ${YELLOW}ℹ️  Reusing existing venv at .open-scholar-peer/mcp/.venv${NC}"
fi

# Upgrade pip silently
"$VENV_DIR/bin/pip" install --quiet --upgrade pip &>/dev/null &
_spin $! "Upgrading pip…"
wait $! || true  # non-fatal

# Install requirements — first install can take 1-2 minutes
_pip_log=$(mktemp)
"$VENV_DIR/bin/pip" install --quiet -r "$TARGET_DIR/requirements.txt" >"$_pip_log" 2>&1 &
_spin $! "Installing MCP server dependencies (first install ~1 min)…"
if wait $!; then
  rm -f "$_pip_log"
  echo -e "  ${GREEN}✅ Python dependencies installed${NC}"
else
  echo -e "  ${RED}✗ pip install failed:${NC}"
  cat "$_pip_log"
  rm -f "$_pip_log"
  exit 1
fi

# Add .open-scholar-peer/ to .gitignore
GITIGNORE="./.gitignore"
if [[ -f "$GITIGNORE" ]]; then
  if ! grep -qF ".open-scholar-peer/" "$GITIGNORE" 2>/dev/null; then
    printf "\n# Open ScholarPeer MCP runtime (venv + server, gitignored)\n.open-scholar-peer/\n" >> "$GITIGNORE"
    echo -e "  ${GREEN}✅ Added .open-scholar-peer/ to .gitignore${NC}"
  fi
else
  printf "# Open ScholarPeer MCP runtime\n.open-scholar-peer/\n" > "$GITIGNORE"
  echo -e "  ${GREEN}✅ Created .gitignore with .open-scholar-peer/ entry${NC}"
fi

# Optional: mention the Semantic Scholar key, unless install.sh already took one
if [[ -z "$SEMANTIC_SCHOLAR_API_KEY" && "$OSP_KEY_NAMES" != *SEMANTIC_SCHOLAR_API_KEY* ]]; then
  echo ""
  echo -e "  ${YELLOW}ℹ️  Semantic Scholar API key not set — anonymous rate limits will apply.${NC}"
  echo "     Get a free key at https://www.semanticscholar.org/product/api#api-key"
  echo "     Then add to your shell profile: export SEMANTIC_SCHOLAR_API_KEY=sk-..."
fi

# Create .env at project root if it doesn't exist (for API keys + tunables)
ENV_FILE="./.env"
if [[ ! -f "$ENV_FILE" ]]; then
  cat > "$ENV_FILE" << 'ENVEOF'
# Open ScholarPeer — config (this file is gitignored)
# Uncomment and fill in to override defaults. The MCP server reads this
# file on startup via python-dotenv, so changes take effect on next launch.

# --- API keys ---------------------------------------------------------------

# Every database works without a key. A key only lifts a rate limit.

# Semantic Scholar — free at https://www.semanticscholar.org/product/api
# Anonymous access is one pool shared by every unauthenticated caller
# everywhere, so it is throttled unpredictably and can refuse outright.
# SEMANTIC_SCHOLAR_API_KEY=sk-...

# OpenAlex — free at https://openalex.org. Keyless works but the daily
# budget is small enough to run out during one heavy review.
# OPENALEX_API_KEY=...

# OpenAlex asks callers to identify themselves, and gives them a faster
# lane for doing it.
# OPENALEX_MAILTO=you@example.org

# Zenodo — free at https://zenodo.org. Anonymous callers get roughly
# 30-60 requests a minute and 2,000 an hour; a token raises that.
# ZENODO_API_TOKEN=...

# Google Scholar has no key. If it blocks your address, a proxy is the
# only thing that helps — rotating the User-Agent was measured to do
# nothing.
# GOOGLE_SCHOLAR_PROXY_URL=http://user:pass@host:port

# --- Databases --------------------------------------------------------------

# Which paper databases the agent may search, as a comma-separated list.
# Only the ones named here have their tools registered, which keeps the
# agent's tool list short. Remove the line entirely to enable all of them.
# Known: arxiv, semantic_scholar, google_scholar, europepmc, zenodo, openalex
# OSP_SOURCES=arxiv,semantic_scholar,google_scholar,europepmc,zenodo,openalex

# --- Tunables ---------------------------------------------------------------

# Per-tool-call timeout in seconds. Applies to every provider. Bump higher
# if you routinely see TimeoutError on slow networks; lower if you would
# rather fail fast. Default: 90.
# OSP_CALL_TIMEOUT=90
ENVEOF
  echo -e "  ${GREEN}✅ Created .env at project root — add your API keys there${NC}"
else
  echo -e "  ${YELLOW}ℹ️  .env already exists at project root${NC}"
fi

# Write the choices install.sh collected into .env, touching only the lines
# OSP owns. A re-install must not disturb anything the user put there, and
# this runs once per selected tool, so it has to be idempotent.
osp_env_set() {
  local key=$1 value=$2
  [[ -z "$value" ]] && return 0
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    # Rewrite in place without sed -i, which differs on BSD and GNU.
    local tmp
    if ! tmp=$(mktemp "${ENV_FILE}.XXXXXX" 2>/dev/null); then
      echo -e "  ${YELLOW}⚠️  Could not update ${key} in .env (cannot write"
      echo -e "     a temporary file here). Set it by hand.${NC}"
      return 0
    fi
    while IFS= read -r line || [[ -n "$line" ]]; do
      if [[ "$line" == "${key}="* ]]; then
        printf '%s=%s\n' "$key" "$value"
      else
        printf '%s\n' "$line"
      fi
    done < "$ENV_FILE" > "$tmp"
    if ! mv "$tmp" "$ENV_FILE" 2>/dev/null; then
      rm -f "$tmp"
      echo -e "  ${YELLOW}⚠️  Could not update ${key} in .env. Set it by hand.${NC}"
      return 0
    fi
  else
    # A file with no final newline would otherwise have our line glued onto
    # the user's last setting: `LAST=value` + `OSP_SOURCES=...` on one line,
    # corrupting their setting AND losing the database choice silently.
    if [ -s "$ENV_FILE" ] && [ -n "$(tail -c1 "$ENV_FILE")" ]; then
      printf '\n' >> "$ENV_FILE"
    fi
    printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}

if [[ -n "$OSP_SOURCES" ]]; then
  osp_env_set "OSP_SOURCES" "$OSP_SOURCES"
fi
for _osp_var in $OSP_KEY_NAMES; do
  # The name is spliced into an eval, so accept only real variable names.
  # install.sh always passes safe ones, but a per-tool installer can be run
  # directly with OSP_KEY_NAMES inherited from the environment.
  if [[ ! "$_osp_var" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    echo -e "  ${YELLOW}⚠️  Ignoring malformed key name: ${_osp_var}${NC}"
    continue
  fi
  eval "_osp_val=\${OSP_KEY_$_osp_var:-}"
  osp_env_set "$_osp_var" "$_osp_val"
done
unset _osp_var _osp_val

# .env holds API keys. Nobody else needs to read it.
chmod 600 "$ENV_FILE" 2>/dev/null || true

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
# The same search tools over argv. Every tool gets this: it is the documented
# fallback when MCP is unavailable, not a special case for one vendor.
export OSP_SEARCH_CLI="$TARGET_DIR/osp_cli.py"

# Prove the search layer actually runs in THIS project, by running it.
#
# This file is sourced by all 21 installers, so one check here serves all of
# them, and it runs before each tool's MCP wiring — so a broken venv is
# reported before the tool-specific output that would bury it. The guard makes
# it run once even when the user installs for several tools in one pass.
#
# THREE probes, because one is not enough and it took a reviewer to notice:
#
#   1. `osp_cli.py list` — the CLI surface and the OSP_SOURCES gating. On its
#      own this is a weak check: providers are imported lazily, so `list`
#      answers "22 tools" happily on an interpreter where arxiv, requests, bs4
#      and semanticscholar are all missing. It proves the registry, not the
#      install.
#   2. the real dependency imports — what `list` does not touch.
#   3. `osp_mcp.py` — which needs the `mcp` package, and is the DEFAULT
#      interface for 20 of the 21 tools. Checking only the fallback and calling
#      the install verified was exactly backwards.
#
# Not fatal. A user with a working editor and a broken venv should still get
# their prompts installed, and be told exactly what to run to see the error.
if [ -z "${OSP_RUNTIME_VERIFIED:-}" ]; then
  export OSP_RUNTIME_VERIFIED=1
  _osp_why=""
  if ! "$OSP_MCP_PYTHON" "$OSP_SEARCH_CLI" list >/dev/null 2>&1; then
    _osp_why="the command-line search tools did not run"
  elif ! "$OSP_MCP_PYTHON" -c "
import sys
sys.path.insert(0, '$TARGET_DIR')
import core, sys as _s
broken = core.warm_providers()          # actually import every enabled provider
_s.exit(1 if broken else 0)
" >/dev/null 2>&1; then
    _osp_why="a search provider could not be imported — a dependency is missing"
  elif ! "$OSP_MCP_PYTHON" -c "
import sys
sys.path.insert(0, '$TARGET_DIR')
import osp_mcp                 # needs the mcp package; the default interface
" >/dev/null 2>&1; then
    _osp_why="the MCP server could not start — the 'mcp' package is missing"
  fi

  if [ -z "$_osp_why" ]; then
    _osp_tools="$("$OSP_MCP_PYTHON" "$OSP_SEARCH_CLI" list --json 2>/dev/null \
      | grep -c '"name"' || true)"
    echo -e "  ${GREEN}✅ Search layer verified — ${_osp_tools:-?} tools, both interfaces${NC}"
    unset _osp_tools
  else
    echo -e "  ${YELLOW}⚠️  Search layer problem: ${_osp_why}."
    echo -e "      Your prompts are installed, but searches will fail. To see why:${NC}"
    echo "         $OSP_MCP_PYTHON $OSP_SEARCH_CLI list"
    echo "         $OSP_MCP_PYTHON $OSP_MCP_SERVER"
  fi
  unset _osp_why
fi
