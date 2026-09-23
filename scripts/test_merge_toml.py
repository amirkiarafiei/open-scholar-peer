#!/usr/bin/env python3
"""
test_merge_toml.py — regression tests for `merge_mcp_toml.py`.

Why this file exists: the Mistral Vibe snippet shipped broken for four months
because nobody ever ran it. The merger that replaced it was checked by hand
once and then had no net under it at all. It now serves two tools with two
different TOML shapes, so it gets a real one.

Honesty about coverage. A TOML *reader* is only in the standard library from
Python 3.11. If the interpreter running this file has none, the suite hands
itself to one that does before testing anything — the same move the merger
makes — so group B normally runs against a real parser. Only when no such
interpreter exists anywhere does it fall back to a stub, and then it says so in
the output: those cases prove the *control flow*, not TOML correctness.

Exit codes:  0 all passed · 1 a test failed
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import merge_mcp_toml as M  # noqa: E402

PY = "/proj/.open-scholar-peer/mcp/.venv/bin/python"
SRV = "/proj/.open-scholar-peer/mcp/osp_mcp.py"

PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    (PASS if condition else FAIL).append(f"{name}{(' — ' + detail) if detail and not condition else ''}")


def tmpfile(content: str | None = None) -> Path:
    d = Path(tempfile.mkdtemp(prefix="osp-toml-"))
    p = d / "config.toml"
    if content is not None:
        p.write_text(content, encoding="utf-8")
    return p


# --------------------------------------------------------------------------
# Group A — no TOML parser required. These are real tests on any interpreter.
# --------------------------------------------------------------------------

def group_a() -> None:
    # A1/A2 — a fresh file is written without needing to parse anything.
    for style, must_contain, must_not in (
        ("array", ['[[mcp_servers]]', 'name = "osp"', 'transport = "stdio"'], []),
        ("table", ['[mcp_servers.osp]', '[mcp_servers.markitdown]'], ['transport']),
    ):
        p = tmpfile()
        ok, msg = M.merge(p, PY, SRV, style)
        text = p.read_text()
        check(f"A:{style} fresh write succeeds", ok, msg)
        for frag in must_contain:
            check(f"A:{style} fresh write has {frag!r}", frag in text)
        for frag in must_not:
            check(f"A:{style} fresh write omits {frag!r}", frag not in text)
        check(f"A:{style} fresh write has both servers",
              text.count("markitdown") >= 1 and "osp" in text)
        check(f"A:{style} does not start with a blank line", not text.startswith("\n"))

    # A3 — Vibe's discriminator is mandatory; losing it invalidates the user's
    # whole file. Guard it explicitly, since that is the bug that shipped.
    p = tmpfile()
    M.merge(p, PY, SRV, "array")
    check("A:array transport appears once per entry",
          p.read_text().count('transport = "stdio"') == 2)

    # A4 — Grok Build has no discriminator at all; emitting one would be wrong.
    p = tmpfile()
    M.merge(p, PY, SRV, "table")
    check("A:table emits no transport key", "transport" not in p.read_text())

    # A5 — path escaping. A Windows path or a quote used to corrupt the file.
    check("A:toml_str escapes backslashes",
          M.toml_str(r"C:\Users\a\python.exe") == r'"C:\\Users\\a\\python.exe"')
    check("A:toml_str escapes quotes",
          M.toml_str('/tmp/we"ird/py') == '"/tmp/we\\"ird/py"')
    p = tmpfile()
    M.merge(p, r"C:\Py\python.exe", r"C:\proj\osp_mcp.py", "table")
    check("A:backslash path is escaped in output",
          r"C:\\Py\\python.exe" in p.read_text())

    # A6 — strip removes only our own blocks, array style.
    user_array = (
        '[[mcp_servers]]\n'
        'name = "mine"\n'
        'transport = "stdio"\n'
        'command = "keep-me"\n'
        '\n'
        '[[mcp_servers]]\n'
        'name = "osp"\n'
        'transport = "stdio"\n'
        f'command = "{PY}"\n'
    )
    out = M.strip_osp_blocks(user_array, style="array")
    check("A:array strip keeps the user's server", 'name = "mine"' in out)
    check("A:array strip keeps the user's command", "keep-me" in out)
    check("A:array strip removes our own osp server", PY not in out)

    # A7 — strip removes only our own tables, table style.
    user_table = (
        "# my notes\n"
        "[mcp_servers.mine]\n"
        'command = "keep-me"\n'
        "\n"
        "[mcp_servers.osp]\n"
        f'command = "{PY}"\n'
        "\n"
        "[other]\n"
        "unrelated = true\n"
    )
    out = M.strip_osp_blocks(user_table, style="table")
    check("A:table strip keeps the user's server", "keep-me" in out)
    check("A:table strip keeps the user's comment", "# my notes" in out)
    check("A:table strip keeps unrelated tables", "[other]" in out and "unrelated" in out)
    check("A:table strip removes our own osp table", PY not in out)

    # A8 — a table named `ospreys` must not be mistaken for `osp`.
    lookalike = '[mcp_servers.ospreys]\ncommand = "keep-me"\n'
    check("A:table strip does not match a name with our prefix",
          "keep-me" in M.strip_osp_blocks(lookalike, style="table"))

    # A9 — whitespace inside the brackets is legal TOML and must still match.
    spaced = f'[ mcp_servers . osp ]\ncommand = "{PY}"\n'
    check("A:table strip tolerates spaced brackets",
          PY not in M.strip_osp_blocks(spaced, style="table"))

    # A10 — the array matcher must not fire on a table-style header, or the two
    # styles would corrupt each other's files.
    check("A:array strip ignores table headers",
          PY in M.strip_osp_blocks(f'[mcp_servers.osp]\ncommand = "{PY}"\n', style="array"))

    # A14 — a named table can carry sub-tables. Stripping the parent and
    # leaving `[mcp_servers.osp.env]` behind would declare a server made
    # entirely of our leftovers.
    with_sub = (
        "[mcp_servers.osp]\n"
        f'command = "{PY}"\n'
        "\n"
        "[mcp_servers.osp.env]\n"
        'TOKEN = "x"\n'
        "\n"
        "[other]\n"
        "x = 1\n"
    )
    out = M.strip_osp_blocks(with_sub, style="table")
    check("A:sub-table goes with its parent", "mcp_servers.osp.env" not in out)
    check("A:unrelated table survives the sub-table sweep", "[other]" in out)

    # A15 — and a sub-table of somebody else's server is never touched.
    their_sub = (
        "[mcp_servers.mine]\n"
        'command = "keep-me"\n'
        "\n"
        "[mcp_servers.mine.env]\n"
        'TOKEN = "keep-this-too"\n'
    )
    out = M.strip_osp_blocks(their_sub, style="table")
    check("A:a foreign sub-table is untouched", "keep-this-too" in out)

    # A16 — TOML allows whitespace inside `[[ mcp_servers ]]`. An exact string
    # compare missed it, so a re-install appended a SECOND osp beside the stale
    # one. Vibe takes the first, so the dead path would have won permanently.
    spaced_arr = ('[[ mcp_servers ]]\n'
                  'name = "osp"\n'
                  'transport = "stdio"\n'
                  f'command = "{PY}"\n')
    check("A:array header with inner spaces is recognised",
          PY not in M.strip_osp_blocks(spaced_arr, style="array"))

    # A17 — TOML allows either quote style on the name.
    single = ("[[mcp_servers]]\n"
              "name = 'osp'\n"
              f"command = '{PY}'\n")
    check("A:single-quoted name is recognised",
          PY not in M.strip_osp_blocks(single, style="array"))

    # A18 — a comment above the next table introduces THAT table. The module
    # docstring promises the user's comments survive.
    commented = (
        "[mcp_servers.osp]\n"
        f'command = "{PY}"\n'
        "\n"
        "# notes about my own server\n"
        "[mcp_servers.mine]\n"
        'command = "keep-me"\n'
    )
    out = M.strip_osp_blocks(commented, style="table")
    check("A:a comment introducing the next table is kept",
          "# notes about my own server" in out)

    # A19 — a CRLF file comes back CRLF, not rewritten end to end.
    p = tmpfile('[mcp_servers.mine]\r\ncommand = "keep-me"\r\n')
    ok, _ = M.merge(p, PY, SRV, "table")
    if ok:
        raw = p.read_bytes()
        check("A:CRLF file stays CRLF",
              raw.count(b"\r\n") == raw.count(b"\n") and raw.count(b"\r\n") > 0)
    else:
        # No parser here, so the merge legitimately declined; the detector is
        # still worth checking on its own.
        check("A:CRLF detected", M._newline_of("a\r\nb") == "\r\n")
    check("A:LF is detected as LF", M._newline_of("a\nb") == "\n")

    # A12 — the name is not the owner. A server the USER called `osp` has none
    # of our fingerprints and must survive, with the caller told about it.
    theirs = '[mcp_servers.osp]\ncommand = "/usr/local/bin/my-own-osp"\n'
    seen: list[str] = []
    out = M.strip_osp_blocks(theirs, style="table", foreign=seen)
    check("A:a user's own server named osp is kept", "my-own-osp" in out)
    check("A:and is reported to the caller", seen == ["osp"])

    # A13 — same for the array style, and markitdown counts as ours by shape
    # because it carries no project path to recognise.
    theirs_arr = ('[[mcp_servers]]\nname = "osp"\ntransport = "stdio"\n'
                  'command = "/opt/theirs/bin/osp"\n')
    seen = []
    out = M.strip_osp_blocks(theirs_arr, style="array", foreign=seen)
    check("A:array keeps a user's own osp", "/opt/theirs/bin/osp" in out)
    check("A:array reports it", seen == ["osp"])
    ours_md = '[mcp_servers.markitdown]\ncommand = "uvx"\nargs = ["markitdown-mcp"]\n'
    check("A:our markitdown entry is recognised as ours",
          "uvx" not in M.strip_osp_blocks(ours_md, style="table"))

    # A11 — re-running is idempotent: two installs, one pair of entries.
    p = tmpfile()
    M.merge(p, PY, SRV, "table")
    first = p.read_text()
    # Simulate a re-install on a parser-less box: strip then render by hand.
    second = M.strip_osp_blocks(first, style="table").rstrip("\n")
    second = (second + "\n" if second else "") + M.render(PY, SRV, "table")
    check("A:table re-install leaves one osp table",
          second.count("[mcp_servers.osp]") == 1)


# --------------------------------------------------------------------------
# Group B — needs a parser. Uses the real one when present, a stub otherwise.
# The stub proves the control flow, not TOML correctness.
# --------------------------------------------------------------------------

class _StubToml:
    """Minimal stand-in: fails on text marked broken, else reports our entries.

    Only good enough to drive the merger's decision branches.
    """

    @staticmethod
    def loads(text: str):
        if "!!broken!!" in text:
            raise ValueError("stub: unparseable")
        servers_list = []
        servers_map = {}
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("[mcp_servers.") and s.endswith("]"):
                servers_map[s[len("[mcp_servers."):-1].strip()] = {}
            m = M._NAME_RE.match(line)
            if m:
                servers_list.append({"name": m.group(1)})
        if servers_map:
            return {"mcp_servers": servers_map}
        return {"mcp_servers": servers_list}


def group_b(real_parser: bool) -> None:
    label = "real parser" if real_parser else "stub parser"
    saved = M.tomllib
    if not real_parser:
        M.tomllib = _StubToml  # type: ignore[assignment]
    try:
        # B1 — refuse to touch a file that does not parse. The user's config is
        # not ours to repair.
        broken = "!!broken!!\nthis = is = not = toml\n" if not real_parser else "this = is = not = toml\n"
        p = tmpfile(broken)
        ok, msg = M.merge(p, PY, SRV, "table")
        check(f"B({label}):refuses an unparseable config", not ok, msg)
        check(f"B({label}):leaves the unparseable file byte-identical",
              p.read_text() == broken)

        # B2 — merging into a good existing file keeps the user's content.
        existing = '[mcp_servers.mine]\ncommand = "keep-me"\n'
        p = tmpfile(existing)
        ok, msg = M.merge(p, PY, SRV, "table")
        text = p.read_text()
        check(f"B({label}):merges into an existing config", ok, msg)
        check(f"B({label}):keeps the user's entry", "keep-me" in text)
        check(f"B({label}):adds the osp entry", "[mcp_servers.osp]" in text)

        # B3 — same for the array style.
        existing = '[[mcp_servers]]\nname = "mine"\ntransport = "stdio"\ncommand = "keep-me"\n'
        p = tmpfile(existing)
        ok, msg = M.merge(p, PY, SRV, "array")
        text = p.read_text()
        check(f"B({label}):array merges into an existing config", ok, msg)
        check(f"B({label}):array keeps the user's entry", "keep-me" in text)
        check(f"B({label}):array writes the discriminator",
              text.count('transport = "stdio"') == 3)

        # B4 — no parser at all: refuse rather than guess.
        M.tomllib = None  # type: ignore[assignment]
        p = tmpfile('[mcp_servers.mine]\ncommand = "keep-me"\n')
        ok, msg = M.merge(p, PY, SRV, "table")
        check("B:refuses to merge with no TOML parser available", not ok, msg)
        check("B:no-parser refusal leaves the file untouched",
              "keep-me" in p.read_text() and "osp" not in p.read_text())

        # B5 — but a fresh file still works with no parser. This is the
        # property that keeps the installer working on Python 3.10.
        p = tmpfile()
        ok, _ = M.merge(p, PY, SRV, "table")
        check("B:fresh write still works with no TOML parser", ok)

        # B6 — a user's own server called `osp` stops the merge dead, and the
        # file is left exactly as it was. Writing beside it would either
        # duplicate a TOML key or leave two servers fighting over one name.
        M.tomllib = saved if real_parser else _StubToml  # type: ignore[assignment]
        theirs = '[mcp_servers.osp]\ncommand = "/usr/local/bin/my-own-osp"\n'
        p = tmpfile(theirs)
        ok, msg = M.merge(p, PY, SRV, "table")
        check(f"B({label}):refuses when the user owns the name `osp`", not ok, msg)
        check(f"B({label}):and leaves their file byte-identical",
              p.read_text() == theirs)
    finally:
        M.tomllib = saved  # type: ignore[assignment]


def _reexec_under_a_parser() -> None:
    """Run this suite on an interpreter that can actually read TOML.

    The first version of this file announced "no TOML parser on this box" and
    ran group B against a stub. That was wrong: it had checked `python3` and
    the project venv, and neither is the whole box — `/usr/bin/python3.11`
    was there the whole time. A reviewer found it. The lesson is the project's
    own rule seven: a claim is worth exactly as much as the command behind it.
    """
    if M.tomllib is not None or os.environ.get("OSP_TOML_TEST_REEXEC"):
        return
    probe = ("import importlib.util as u, sys; "
             "sys.exit(0 if (u.find_spec('tomllib') or u.find_spec('tomli')) else 1)")
    for cand in ("python3.13", "python3.12", "python3.11"):
        exe = shutil.which(cand)
        if not exe:
            continue
        try:
            if subprocess.run([exe, "-c", probe], timeout=15,
                              capture_output=True).returncode != 0:
                continue
        except (OSError, subprocess.SubprocessError):
            continue
        env = dict(os.environ, OSP_TOML_TEST_REEXEC="1")
        print(f"  → re-running under {exe} so the TOML can be parsed for real\n")
        os.execve(exe, [exe, str(Path(__file__).resolve()), *sys.argv[1:]], env)


def main() -> int:
    _reexec_under_a_parser()
    real = M.tomllib is not None
    group_a()
    group_b(real)

    for line in PASS:
        print(f"  \u2713 {line}")
    for line in FAIL:
        print(f"  \u2717 {line}")

    print()
    if not real:
        print("  \u26a0\ufe0f  No TOML parser on this interpreter (needs Python 3.11+, or tomli).")
        print("     Group B ran against a stub: it proves the merger's control flow,")
        print("     not that the output is valid TOML. Re-run on 3.11+ for that.")
        print()

    if FAIL:
        print(f"  \u274c {len(FAIL)} failed, {len(PASS)} passed.")
        return 1
    print(f"  \u2705 All {len(PASS)} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
