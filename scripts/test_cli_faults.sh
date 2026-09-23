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
REAL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$REAL_ROOT/.venv/bin/python"; [ -x "$PY" ] || PY=python3
GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; NC=$'\033[0m'

# Faults are injected into a COPY, never into the tracked tree.
#
# The previous version edited mcp-server/*.py in place and restored them from an
# EXIT trap. That is correct for a clean exit and for Ctrl-C, and wrong for
# SIGKILL, a closed terminal, an OOM kill, or two runs at once — and
# `test_all.sh` runs this suite by default, so a contributor's first ever run
# was the exposure. The damage would be silent: fault 5 deletes one line and
# leaves something that still imports, still looks like working code, and still
# passes most of the suite. You would find it days later, or commit it.
ROOT="$(mktemp -d)/repo"
mkdir -p "$ROOT"
tar -c -C "$REAL_ROOT" --exclude=./.venv --exclude=./.git \
    --exclude=__pycache__ --exclude='*.pyc' --exclude=./.env . | tar -x -C "$ROOT"
TARGETS=(mcp-server/core.py mcp-server/osp_cli.py)
BACKUP="$(mktemp -d)"
for f in "${TARGETS[@]}"; do install -D "$ROOT/$f" "$BACKUP/$f"; done
restore() { for f in "${TARGETS[@]}"; do cp "$BACKUP/$f" "$ROOT/$f"; done; }
trap 'rm -rf "$BACKUP" "$(dirname "$ROOT")"' EXIT

pass=0; fail=0

# name | the guarantee | file | sed expression that breaks it
run_fault() {
  local name="$1" file="$2" expr="$3" only="${4:-}"
  restore
  # Not `sed -i`: GNU reads the next argument as the expression, BSD reads it
  # as a backup suffix and then treats the filename as the script. On macOS
  # every fault would report "could not be applied", which looks like a stale
  # pattern rather than a portability problem.
  if ! sed "$expr" "$ROOT/$file" > "$ROOT/$file.tmp" || ! mv "$ROOT/$file.tmp" "$ROOT/$file"; then
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
  's/_emit_and_exit(_cap(result), code=/_emit_and_exit(result, code=/' "capped"

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

# 10. A failure that does not fit comes back as exit 0 with no reason.
#     TWO mechanisms prevent this — the exit code is read off the UNCAPPED
#     result, and the cap refuses to drop an error envelope — and either alone
#     is sufficient. So this fault disables both; removing just one leaves the
#     suite green, which is the point of having two.
run_fault "a failure that does not fit exits 0" mcp-server/osp_cli.py \
  's/_emit_and_exit(_cap(result), code=1 if _is_error(result) else 0)/_emit_and_exit(_cap(result))/;
   s/^            if _must_survive(item):$/            if False:/' \
  "survives the cap"

# 11. A shortened full-text window stops correcting its own paging contract,
#     so half a paper reports itself as whole.
run_fault "a cut document stops correcting next_offset" mcp-server/osp_cli.py \
  's/^    out\["next_offset"\] = end if end < total else None$/    pass/' \
  "says it is cut"

# 12. The cap stops protecting error envelopes from being dropped.
run_fault "the cap drops error envelopes again" mcp-server/osp_cli.py \
  's/^            if _must_survive(item):$/            if False:/' \
  "survives the cap"

# 13. The batch budget goes back to being divided, so the recommended path
#     returns less the more you ask for.
run_fault "the batch budget is divided across items" mcp-server/osp_cli.py \
  's/item\["result"\] = _cap(item\["result"\], MAX_BYTES)/item["result"] = _cap(item["result"], max(2_000, MAX_BYTES \/\/ len(plans)))/' \
  "worse deal"

# 14. The cap goes back to shrinking only the largest STRING, so a record whose
#     weight is a list is emitted over the limit while claiming to be cut.
run_fault "the cap only shrinks strings again" mcp-server/osp_cli.py \
  's/^            elif isinstance(value, (list, tuple)) and len(value) > 0:$/            elif False:/' \
  "actually caps"

# 15. The failure test looks only at the top level again, so a batch item
#     carrying an envelope under "result" stops counting as a failure and can
#     be dropped to save space.
# Two mechanisms keep a failure in a batch: the bound is set clear of the worst
# nesting overhead, and a failure is never the item dropped. Either alone is
# enough, so this disables both.
run_fault "a batch item's failure stops being protected" mcp-server/osp_cli.py \
  's/^    if item.get("ok") is False:$/    if False:/;
   s/^    return _is_error(item.get("result")) if "result" in item else False$/    return False/;
   s/whole = (MAX_BYTES \* len(plans) \* 2 + 8192) if MAX_BYTES > 0 else 0/whole = (MAX_BYTES * len(plans)) if MAX_BYTES > 0 else 0/' \
  "never drops a failure"

# 16. A warning naming what did not resolve stops being protected from the cut.
run_fault "a warning record stops being protected" mcp-server/osp_cli.py \
  's/^    if "warning" in item:$/    if False:/' "never cut away"

# 17. A write failure other than a broken pipe goes back to discarding the
#     buffer, which is zero bytes with exit 1 — the state this file says it
#     removed.
run_fault "a failed write reports nothing at all" mcp-server/osp_cli.py \
  's/^            json.dump(_envelope($/            raise SystemExit(1) or json.dump(_envelope(/' \
  "cannot be written"

echo
# The point of the copy: prove the tracked tree was never written to at all.
for f in "${TARGETS[@]}"; do
  if ! cmp -s "$REAL_ROOT/$f" "$BACKUP/$f"; then
    echo "  ${RED}❌ $f CHANGED IN THE REAL TREE. Check git status before committing.${NC}"
    exit 2
  fi
done
echo "  the tracked tree was never written to"
if [ "$fail" -gt 0 ]; then
  echo "  ${RED}❌ $fail of $((pass+fail)) faults went undetected${NC}"
  exit 1
fi
echo "  ${GREEN}✅ all $pass faults caught${NC}"
