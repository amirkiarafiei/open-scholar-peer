#!/usr/bin/env bash
# test_all.sh — every check this project has, in one command.
#
# The single entry point, for a person and for CI alike. CI calls this file
# rather than listing the suites itself, so the two cannot drift: if it passes
# here it passes there, and a suite added below is picked up by both.
#
# Nothing here touches the network. The live provider round-trip
# (scripts/test_providers.py) is deliberately left out — it depends on six
# third-party services being up, and a red build that means "arXiv is slow
# today" teaches people to ignore the build. Run it by hand before a release.
#
# Usage:  bash scripts/test_all.sh [--quick]
#           --quick  skip the installer smoke test, which is the slow one
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 2

QUICK=0
[ "${1:-}" = "--quick" ] && QUICK=1

PY="$ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3 || true)"
  [ -n "$PY" ] || { echo "no python3 found"; exit 2; }
  echo "  note: no .venv — using $PY. Provider suites need the requirements."
fi

GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; DIM=$'\033[2m'; NC=$'\033[0m'
# A plain string, not an array. Referencing an empty array under `set -u` is
# an unbound-variable error on bash 3.2, which is what stock macOS ships — so
# a fully passing run would have died at the summary line.
failed=""
failed_count=0
started=$(date +%s)

step() {
  local name="$1"; shift
  printf '  %-34s' "$name"
  local out; local rc
  out="$("$@" 2>&1)"; rc=$?
  if [ $rc -eq 0 ]; then
    printf '%s✓%s %s\n' "$GREEN" "$NC" "${DIM}$(printf '%s' "$out" | tail -1 | tr -d '\r')${NC}"
  else
    printf '%s✗%s\n' "$RED" "$NC"
    printf '%s\n' "$out" | tail -25 | sed 's/^/      /'
    failed="$failed $name"
    failed_count=$((failed_count + 1))
  fi
}

echo
echo "  ▸ Open ScholarPeer — full check"
echo

step "adapters regenerate cleanly"  "$PY" scripts/sync_adapters.py --check
step "adapter parity, 21 tools"     "$PY" scripts/test_parity.py
step "providers, offline"           "$PY" scripts/test_providers_unit.py
step "MCP/CLI schema parity"        "$PY" scripts/test_schema_parity.py
step "TOML config merging"          "$PY" scripts/test_merge_toml.py
step "command-line interface"       "$PY" scripts/test_cli.py
step "the CLI tests can fail"       bash scripts/test_cli_faults.sh
step "upgrading an older project"    "$PY" scripts/test_upgrade.py
step "session template is valid"    "$PY" -c \
  "import json;json.load(open('.brain-template/session.json'))"
step "shell syntax"                 bash -c \
  'for f in install.sh scripts/*.sh; do bash -n "$f" || exit 1; done'

if [ "$QUICK" -eq 0 ]; then
  step "installers, all 21"         bash scripts/test_install.sh
else
  printf '  %-34s%s— skipped (--quick)%s\n' "installers, all 21" "$DIM" "$NC"
fi

elapsed=$(( $(date +%s) - started ))
echo
if [ "$failed_count" -gt 0 ]; then
  echo "  ${RED}❌ ${failed_count} failed:${NC}${failed}"
  echo "  ${DIM}(${elapsed}s)${NC}"
  exit 1
fi
echo "  ${GREEN}✅ everything passed${NC} ${DIM}(${elapsed}s)${NC}"
