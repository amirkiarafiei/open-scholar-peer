#!/usr/bin/env bash
# test_cli_faults.sh — does test_cli.py actually fail when the thing it checks
# is broken?
#
# A test suite that passes is evidence of nothing until you have seen it fail.
# Every guarantee below was a real defect in this interface at some point, and
# each fault re-creates one. The suite must catch every single one.
#
# Restores from a backup in a temp directory, and verifies the tree is
# byte-identical afterwards — a fault left switched on would be far worse than
# no fault test at all.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"; [ -x "$PY" ] || PY=python3
BACKUP="$(mktemp -d)"
TARGETS=(mcp-server/core.py mcp-server/osp_cli.py)
GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; NC=$'\033[0m'

for f in "${TARGETS[@]}"; do install -D "$ROOT/$f" "$BACKUP/$f"; done
restore() { for f in "${TARGETS[@]}"; do cp "$BACKUP/$f" "$ROOT/$f"; done; }
trap 'restore; rm -rf "$BACKUP"' EXIT

pass=0; fail=0

# name | the guarantee | file | sed expression that breaks it
run_fault() {
  local name="$1" file="$2" expr="$3" only="${4:-}"
  restore
  if ! sed -i "$expr" "$ROOT/$file"; then
    echo "  ${RED}✗ $name — the fault could not be applied (stale pattern?)${NC}"
    fail=$((fail+1)); return
  fi
  if cmp -s "$ROOT/$file" "$BACKUP/$file"; then
    echo "  ${RED}✗ $name — the fault changed nothing (stale pattern)${NC}"
    fail=$((fail+1)); return
  fi
  if "$PY" "$ROOT/scripts/test_cli.py" $only >/dev/null 2>&1; then
    echo "  ${RED}✗ $name — SUITE STILL PASSED. That guarantee is not tested.${NC}"
    fail=$((fail+1))
  else
    echo "  ${GREEN}✓ caught: $name${NC}"
    pass=$((pass+1))
  fi
}

echo "  ▸ injecting faults into the CLI, one at a time"
echo

# 1. A failure that looks like an empty result — the defect the layer exists for.
run_fault "an error envelope stops being detected" mcp-server/osp_cli.py \
  's/^    if isinstance(result, list):$/    if False:/' "empty"

# 2. The output cap stops declaring the cut, so a partial corpus reads as whole.
run_fault "a truncated result stops saying so" mcp-server/osp_cli.py \
  's/"osp_truncated": True,/"osp_truncated": False,/' "capped"

# 3. The cap stops applying, so the host truncates mid-document instead.
run_fault "the output cap stops applying" mcp-server/osp_cli.py \
  's/^    _emit_and_exit(_cap(result))$/    _emit_and_exit(result)/' "capped"

# 4. The process waits for a stuck worker again.
run_fault "the timeout stops bounding the process" mcp-server/osp_cli.py \
  's/^    os._exit(code)$/    sys.exit(code)/' "timeout"

# 5. Providers load eagerly, so one broken dependency takes the surface down.
run_fault "providers load eagerly again" mcp-server/core.py \
  's/^    spec.loader = importlib.util.LazyLoader(spec.loader)$//' "blocked"

# 6. stderr leaks, so `call ... 2>&1` stops parsing as JSON.
run_fault "logging leaks onto stderr" mcp-server/osp_cli.py \
  's/level=logging.INFO if verbose else logging.CRITICAL,/level=logging.INFO,/' "streams"

# 7. A switched-off database becomes indistinguishable from a typo.
run_fault "a switched-off database reads as an unknown tool" mcp-server/core.py \
  's/^    return name in REGISTRY and name not in enabled_tools()$/    return False/' \
  "switched-off"

# 8. A failing call in a batch stops being reported as its own failure.
#    (Not return_exceptions: run_one catches everything itself, so that flag is
#    belt-and-braces and flipping it proves nothing. The guard that actually
#    carries the promise is the per-item envelope.)
run_fault "a failed call in a batch stops carrying its own reason" mcp-server/osp_cli.py \
  's/return {"tool": name, "ok": False, "result": why}/raise RuntimeError(why["error"])/' \
  "batch"

# 9. Non-ASCII input blames the agent for the environment.
run_fault "UTF-8 reconfiguration is dropped" mcp-server/osp_cli.py \
  's/^            stream.reconfigure(encoding="utf-8", errors="replace")$/            pass/' \
  "unicode"

restore
echo
if ! cmp -s "$ROOT/mcp-server/core.py" "$BACKUP/mcp-server/core.py" \
  || ! cmp -s "$ROOT/mcp-server/osp_cli.py" "$BACKUP/mcp-server/osp_cli.py"; then
  echo "  ${RED}❌ THE TREE WAS NOT RESTORED. Check git status before committing.${NC}"
  exit 2
fi
echo "  restored, byte-identical"
if [ "$fail" -gt 0 ]; then
  echo "  ${RED}❌ $fail of $((pass+fail)) faults went undetected${NC}"
  exit 1
fi
echo "  ${GREEN}✅ all $pass faults caught${NC}"
