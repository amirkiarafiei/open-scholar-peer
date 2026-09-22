#!/usr/bin/env python3
"""
test_cli.py — the command-line search interface, driven the way an agent drives it.

Every call goes through `bash`, as a subprocess, with stdout and stderr captured
separately. Nothing here imports the CLI: an agent cannot, and a test that does
would miss everything that happens between the shell and `main()` — which is
where the interesting failures live.

**The rule this file exists to enforce**, from which every check below derives:

> No execution path may leave the agent unable to tell "the provider failed"
> from "there are no papers".

So an exit code is never asserted on its own. It is always asserted together
with what was on stdout and what `reason` that carried. A blocked provider and
an empty field both used to exit 0; that is the bug this whole layer was built
to remove, and an exit-code-only assertion would not have seen it.

Offline. `_cli_test_hook.py` fakes providers inside the subprocess through
`sitecustomize`, driven by OSP_TEST_MODE. With that variable unset the hook does
nothing, and nothing in the shipped tree sets it or imports it.

Exit codes:  0 all checks pass · 1 a check failed · 2 the suite could not run.
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MCP_DIR = REPO_ROOT / "mcp-server"
CLI = MCP_DIR / "osp_cli.py"
PY = REPO_ROOT / ".venv" / "bin" / "python"
if not PY.exists():
    PY = Path(sys.executable)

_FAILURES: list[str] = []
_CHECKS = 0
_HOOK_DIR: Path | None = None


def check(label: str, got: object, want: object) -> None:
    global _CHECKS
    _CHECKS += 1
    if got != want:
        _FAILURES.append(f"  - {label}\n      expected: {want!r}\n      got:      {got!r}")


def check_true(label: str, got: object) -> None:
    check(label, bool(got), True)


class Result:
    """One CLI invocation: what the agent can actually see."""

    def __init__(self, rc: int, out: str, err: str, secs: float):
        self.rc, self.out, self.err, self.secs = rc, out, err, secs

    @property
    def json(self) -> object:
        """stdout parsed, or None. `None` here IS a failure of the contract."""
        try:
            return json.loads(self.out)
        except (json.JSONDecodeError, ValueError):
            return None

    @property
    def reason(self) -> str | None:
        """The `reason` an agent would branch on, wherever the tool put it."""
        doc = self.json
        if isinstance(doc, dict):
            return doc.get("reason")
        if isinstance(doc, list) and doc and isinstance(doc[0], dict):
            return doc[0].get("reason")
        return None


def run(args: list[str], mode: str = "", stdin: str | None = None,
        env_extra: dict[str, str] | None = None, timeout: int = 120) -> Result:
    """Run the CLI through bash, exactly as the guide tells an agent to."""
    env = dict(os.environ)
    env.pop("OSP_SOURCES", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if mode:
        env["OSP_TEST_MODE"] = mode
        env["OSP_TEST_MCP_DIR"] = str(MCP_DIR)
        env["PYTHONPATH"] = str(_HOOK_DIR)
    if env_extra:
        env.update(env_extra)
    # shlex.quote, not naive single quotes: a query containing an apostrophe
    # is exactly what breaks a hand-quoted command line, and the guide tells
    # the agent to quote properly or use stdin.
    quoted = " ".join(shlex.quote(a) for a in args)
    cmd = f"'{PY}' '{CLI}' {quoted}"
    t0 = time.monotonic()
    proc = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True,
                          input=stdin, env=env, timeout=timeout)
    return Result(proc.returncode, proc.stdout, proc.stderr, time.monotonic() - t0)


# ---------------------------------------------------------------- the checks

def test_list() -> None:
    r = run(["list"])
    check("list exits 0", r.rc, 0)
    check_true("list names the tool count", "search tools are enabled" in r.out)
    check_true("list tells the agent how to call one", "osp_cli.py call" in r.out)

    j = run(["list", "--json"])
    check("list --json exits 0", j.rc, 0)
    doc = j.json
    check_true("list --json is one JSON document", isinstance(doc, list))
    check("list --json has 22 tools", len(doc or []), 22)
    check_true("every entry carries name, summary and required",
               all({"name", "summary", "required"} <= set(t) for t in doc or []))
    # C6: the whole point of the slim form.
    size = len(j.out.encode())
    check_true(f"list --json is under 5 KB (measured {size} B)", size < 5120)
    check_true("list --json writes nothing to stderr", j.err == "")


def test_schema_every_tool() -> None:
    tools = [t["name"] for t in run(["list", "--json"]).json]
    check("22 tools to describe", len(tools), 22)
    bad = []
    for name in tools:
        r = run(["schema", name])
        doc = r.json
        if r.rc != 0 or not isinstance(doc, dict) or "properties" not in doc:
            bad.append(f"{name}(rc={r.rc})")
    check("schema works for every tool", bad, [])


def test_unknown_and_gated() -> None:
    """The two different things that both exit 2, told apart by `reason`."""
    r = run(["schema", "no_such_tool"])
    check("unknown tool: exit code", r.rc, 2)
    check("unknown tool: reason", r.reason, "bad_request")
    check_true("unknown tool: says how to find the real ones",
               "list" in (r.json or {}).get("error", ""))

    g = run(["schema", "search_zenodo"], env_extra={"OSP_SOURCES": "arxiv"})
    check("switched-off database: exit code", g.rc, 2)
    # The distinction that matters: NOT bad_request. The user chose this, and
    # the agent must record a corpus gap rather than hunt a typo.
    check("switched-off database: reason", g.reason, "unavailable")
    check_true("switched-off database: says nothing was searched",
               "not an empty result" in (g.json or {}).get("error", ""))
    check_true("switched-off database: names OSP_SOURCES",
               "OSP_SOURCES" in (g.json or {}).get("error", ""))


def test_bad_input() -> None:
    r = run(["call", "search_arxiv", "{bad json"])
    check("malformed JSON: exit code", r.rc, 2)
    check("malformed JSON: reason", r.reason, "bad_request")
    check_true("malformed JSON: still one JSON document", r.json is not None)

    r = run(["call", "search_arxiv", "{}"])
    check("missing required argument: exit code", r.rc, 2)
    check("missing required argument: reason", r.reason, "bad_request")

    r = run(["call", "search_arxiv", '["not", "an", "object"]'])
    check("arguments as an array: exit code", r.rc, 2)
    check("arguments as an array: reason", r.reason, "bad_request")

    r = run([])
    check("no subcommand: exit code", r.rc, 2)
    check("no subcommand: reason", r.reason, "bad_request")
    check_true("no subcommand: JSON, not argparse usage text", r.json is not None)

    r = run(["--nonsense"])
    check("unknown flag: exit code", r.rc, 2)
    check_true("unknown flag: JSON, not argparse usage text", r.json is not None)


def test_quoting_and_unicode() -> None:
    """A title with an apostrophe and a double quote, and a non-ASCII query."""
    tricky = 'what\'s "new" in retrieval'
    r = run(["call", "search_arxiv", json.dumps({"query": tricky})],
            mode="canned")
    check("a query with ' and \" survives the shell: exit code", r.rc, 0)
    check_true("a query with ' and \" returns records", isinstance(r.json, list))

    # The documented form for awkward text: JSON on stdin.
    r = run(["call", "search_arxiv", "-"], mode="canned",
            stdin=json.dumps({"query": tricky}))
    check("the same query through stdin: exit code", r.rc, 0)
    check_true("the same query through stdin: returns records",
               isinstance(r.json, list))

    # Non-ASCII under a genuinely ASCII locale used to die with "surrogates not
    # allowed" and be reported as `bad_request`, blaming the agent for the
    # environment.
    #
    # LC_ALL=C is NOT enough to reproduce that: measured on this interpreter it
    # still yields a UTF-8 stdout, because PEP 538 coerces the C locale. The
    # coercion and UTF-8 mode both have to be switched off to get the hostile
    # environment a user on a bare container actually has. Without these two
    # variables this check passes whether or not the CLI does anything right.
    hostile = {"LC_ALL": "C", "LANG": "C",
               "PYTHONCOERCECLOCALE": "0", "PYTHONUTF8": "0"}
    r = run(["call", "search_arxiv", json.dumps({"query": "über Fräulein 数学"})],
            mode="canned", env_extra=hostile)
    check("non-ASCII query under an ASCII locale: exit code", r.rc, 0)
    check("non-ASCII query under an ASCII locale: no bad_request",
          r.reason, None)
    check_true("non-ASCII query under an ASCII locale: stdout is still JSON",
               r.json is not None)

    r = run(["list"], env_extra=hostile)
    check("list under an ASCII locale: exit code", r.rc, 0)
    check_true("list under an ASCII locale: writes nothing to stderr", r.err == "")


def test_stdin_pipe_with_no_data() -> None:
    """An open pipe carrying nothing must not hang.

    An earlier isatty() guard sat waiting until it was killed, which from the
    agent's side is indistinguishable from a slow search. subprocess gives us a
    real pipe, and `input=""` closes it empty — the exact shape that hung.
    """
    r = run(["call", "search_arxiv"], stdin="", timeout=30)
    check("empty stdin pipe: exit code", r.rc, 2)
    check("empty stdin pipe: reason", r.reason, "bad_request")
    check_true(f"empty stdin pipe: returns promptly ({r.secs:.1f}s)", r.secs < 20)


def test_empty_is_not_failure() -> None:
    """The load-bearing distinction, from both directions."""
    e = run(["call", "search_arxiv", '{"query":"zzz"}'], mode="empty")
    check("a search that matched nothing: exit code", e.rc, 0)
    check("a search that matched nothing: is an empty list", e.json, [])
    check("a search that matched nothing: carries no reason", e.reason, None)

    b = run(["call", "search_google_scholar", '{"query":"zzz"}'],
            mode="blocked_provider")
    check("a blocked provider: exit code", b.rc, 1)
    check("a blocked provider: reason", b.reason, "blocked")
    check_true("a blocked provider: is NOT an empty list", b.json != [])
    check_true("a blocked provider: says so in words",
               "blocked" in json.dumps(b.json).lower()
               or "captcha" in json.dumps(b.json).lower())


def test_timeout_bounds_the_process() -> None:
    """A provider that ignores the deadline must not hold the process.

    asyncio.wait_for cancels the wait, not the worker thread, and asyncio.run
    joins the executor on the way out — measured at 6.01s against a 1s timeout.
    """
    r = run(["call", "search_arxiv", '{"query":"x"}', "--timeout", "2"],
            mode="slow", timeout=30)
    check("a stuck provider: exit code", r.rc, 1)
    check("a stuck provider: reason", r.reason, "timeout")
    check_true(f"a stuck provider: exits near the deadline, not the provider's "
               f"30s ({r.secs:.1f}s)", r.secs < 5.0)
    check_true("a stuck provider: still leaves JSON on stdout", r.json is not None)
    check_true("a stuck provider: says nothing was searched",
               "not an empty result" in json.dumps(r.json))

    r = run(["call", "search_arxiv", '{"query":"x"}', "--timeout", "0"])
    check("a timeout of zero: exit code", r.rc, 2)
    check("a timeout of zero: reason", r.reason, "bad_request")


def test_output_is_capped() -> None:
    """A result too large for the caller is cut HERE, where it can be described."""
    r = run(["call", "search_arxiv", '{"query":"x"}'], mode="huge")
    check("an oversized result: exit code", r.rc, 0)
    doc = r.json
    check_true("an oversized result: what arrives is still valid JSON",
               doc is not None)
    check_true(f"an oversized result: fits the cap "
               f"({len(r.out.encode())} B)", len(r.out.encode()) <= 26_000)
    check_true("an oversized result: is still a list", isinstance(doc, list))
    marker = doc[-1] if isinstance(doc, list) and doc else {}
    check("an oversized result: declares that it was cut",
          marker.get("osp_truncated"), True)
    check("an oversized result: says how many of how many",
          (marker.get("osp_returned", 0) < marker.get("osp_total", 0)
           and marker.get("osp_total") == 60), True)
    check_true("an oversized result: warns against reading it as complete",
               "not" in marker.get("osp_note", "").lower())
    # It is NOT an error: the records that arrived are real.
    check("an oversized result: is not reported as a failure", r.reason, None)

    # And --max-bytes is honoured.
    r = run(["call", "search_arxiv", '{"query":"x"}', "--max-bytes", "4000"],
            mode="huge")
    check_true(f"--max-bytes is honoured ({len(r.out.encode())} B)",
               len(r.out.encode()) <= 5_000)


def test_one_document_and_clean_streams() -> None:
    """Exactly one JSON document on stdout, and `2>&1` still parses."""
    for args, mode in ((["list", "--json"], ""),
                       (["schema", "search_arxiv"], ""),
                       (["call", "search_arxiv", '{"query":"x"}'], "canned")):
        r = run(args, mode=mode)
        check_true(f"{args[0]}: stdout is exactly one JSON document",
                   r.json is not None)
        check_true(f"{args[0]}: stdout ends with a single newline",
                   r.out.endswith("\n") and not r.out.rstrip("\n").endswith("\n"))
        check(f"{args[0]}: nothing on stderr", r.err, "")

    # The merged-stream promise, which is what an agent that redirects gets.
    env = dict(os.environ)
    env.update({"OSP_TEST_MODE": "canned", "OSP_TEST_MCP_DIR": str(MCP_DIR),
                "PYTHONPATH": str(_HOOK_DIR), "PYTHONDONTWRITEBYTECODE": "1"})
    env.pop("OSP_SOURCES", None)
    proc = subprocess.run(
        ["bash", "-c", f"'{PY}' '{CLI}' call search_arxiv '{{\"query\":\"x\"}}' 2>&1"],
        capture_output=True, text=True, env=env, timeout=60)
    try:
        json.loads(proc.stdout)
        merged_ok = True
    except (json.JSONDecodeError, ValueError):
        merged_ok = False
    check_true("`call ... 2>&1` still parses as JSON", merged_ok)


def test_blocked_imports() -> None:
    """A broken dependency must not silence the interface.

    Measured before the split: blocking any one of these made the process exit 1
    with ZERO bytes on stdout, while the contract says exit 1 means "read the
    reason". Zero bytes is the worst possible answer — it is indistinguishable
    from a tool that found nothing to say.
    """
    for dep in ("mcp", "arxiv", "requests", "bs4", "semanticscholar", "dotenv"):
        r = run(["list"], mode=f"block:{dep}", timeout=60)
        if r.rc == 0:
            check_true(f"list survives a broken {dep}",
                       "search tools are enabled" in r.out)
        else:
            check(f"a broken {dep} still yields a reason", r.reason is not None, True)
        check_true(f"a broken {dep} never gives empty stdout", r.out.strip() != "")

    # And a call against the broken one degrades to an envelope, not a traceback.
    r = run(["call", "search_arxiv", '{"query":"x"}'], mode="block:arxiv", timeout=60)
    check("a call against a broken dependency: exit code", r.rc, 1)
    check_true("a call against a broken dependency: is JSON", r.json is not None)
    check_true("a call against a broken dependency: says it is an install "
               "problem, not a database problem",
               "install" in json.dumps(r.json).lower())


def test_batch() -> None:
    calls = [{"tool": "search_arxiv", "arguments": {"query": "a"}},
             {"tool": "search_arxiv", "arguments": {"query": "b"}}]
    r = run(["batch", json.dumps(calls)], mode="canned")
    check("batch: exit code", r.rc, 0)
    doc = r.json
    check_true("batch: returns a list", isinstance(doc, list))
    check("batch: one result per call, in order", len(doc or []), 2)
    check_true("batch: each result names its tool and says whether it worked",
               all({"tool", "ok", "result"} <= set(i) for i in doc or []))

    # One bad call must not take the others down. This is the whole promise.
    mixed = [{"tool": "search_arxiv", "arguments": {"query": "a"}},
             {"tool": "no_such_tool", "arguments": {}},
             {"tool": "search_arxiv", "arguments": {}}]
    r = run(["batch", json.dumps(mixed)], mode="canned")
    check("batch with failures: exit code", r.rc, 1)
    doc = r.json or []
    check("batch with failures: still returns every item", len(doc), 3)
    check("batch with failures: the good one still worked", doc[0]["ok"], True)
    check("batch with failures: the unknown tool failed on its own",
          doc[1]["ok"], False)
    check("batch with failures: and carries its own reason",
          doc[1]["result"].get("reason"), "bad_request")
    check("batch with failures: the third is judged separately",
          doc[2]["ok"], False)

    for bad, label in (("[]", "an empty batch"),
                       ('[{"arguments":{}}]', "a call with no tool"),
                       ('{"tool":"search_arxiv"}', "an object instead of an array"),
                       ('[{"tool":"search_arxiv","arguments":[]}]',
                        "arguments that are not an object")):
        r = run(["batch", bad])
        check(f"batch: {label} exits 2", r.rc, 2)
        check(f"batch: {label} carries a reason", r.reason, "bad_request")

    over = json.dumps([{"tool": "search_arxiv", "arguments": {"query": "x"}}] * 33)
    r = run(["batch", over])
    check("batch: over the size limit exits 2", r.rc, 2)
    check("batch: over the size limit carries a reason", r.reason, "bad_request")


def test_gating_is_consistent() -> None:
    """One .env governs both surfaces, so the tool list follows OSP_SOURCES."""
    for sources, want in (("arxiv", 3), ("arxiv,semantic_scholar,google_scholar", 17)):
        r = run(["list", "--json"], env_extra={"OSP_SOURCES": sources})
        check(f"OSP_SOURCES={sources}: tool count", len(r.json or []), want)
    r = run(["list", "--json"], env_extra={"OSP_SOURCES": "not_a_database"})
    check("an unknown OSP_SOURCES falls back to every database",
          len(r.json or []), 22)
    check_true("an unknown OSP_SOURCES does not break the JSON contract",
               r.err == "")


TESTS = [
    ("list", test_list),
    ("schema, every tool", test_schema_every_tool),
    ("unknown vs switched-off", test_unknown_and_gated),
    ("bad input", test_bad_input),
    ("quoting and unicode", test_quoting_and_unicode),
    ("empty stdin pipe", test_stdin_pipe_with_no_data),
    ("empty is not failure", test_empty_is_not_failure),
    ("timeout bounds the process", test_timeout_bounds_the_process),
    ("output is capped", test_output_is_capped),
    ("one document, clean streams", test_one_document_and_clean_streams),
    ("blocked imports", test_blocked_imports),
    ("batch", test_batch),
    ("gating is consistent", test_gating_is_consistent),
]


def main() -> int:
    global _HOOK_DIR
    if not CLI.exists():
        print(f"❌ {CLI} not found")
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="osp-cli-test-"))
    _HOOK_DIR = tmp
    shutil.copy(REPO_ROOT / "scripts" / "_cli_test_hook.py",
                tmp / "sitecustomize.py")
    print("  ▸ command-line interface, driven through bash\n")
    try:
        only = sys.argv[1] if len(sys.argv) > 1 else None
        for name, fn in TESTS:
            if only and only not in name:
                continue
            try:
                fn()
                print(f"  ✓ {name}")
            except subprocess.TimeoutExpired:
                _FAILURES.append(f"  - {name}: the CLI never returned. That is "
                                 f"the worst failure this interface has: an "
                                 f"agent cannot tell it from a slow search.")
                print(f"  ❌ {name}: timed out")
            except Exception as exc:  # noqa: BLE001
                _FAILURES.append(f"  - {name}: {type(exc).__name__}: {exc}")
                print(f"  ❌ {name}: {type(exc).__name__}: {exc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if _FAILURES:
        print(f"\n❌ {len(_FAILURES)} of {_CHECKS} CLI checks failed:\n")
        print("\n".join(_FAILURES))
        return 1
    print(f"\n  ✅ All {_CHECKS} CLI checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
