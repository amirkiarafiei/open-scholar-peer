#!/usr/bin/env python3
"""Merge the OSP MCP servers into a tool's TOML config.

Two tools keep MCP servers in TOML, and they disagree about the shape.

`--style array` — Mistral Vibe, an array of tables:

    [[mcp_servers]]
    name = "osp"
    transport = "stdio"
    command = "/path/to/python"
    args = ["/path/to/osp_mcp.py"]

`transport` is a pydantic discriminator there. An entry without it does not
merely fail to load — it invalidates the whole config file, so every entry the
user had is lost. It is not optional.

`--style table` — Grok Build, one named table per server:

    [mcp_servers.osp]
    command = "/path/to/python"
    args = ["/path/to/osp_mcp.py"]

Grok Build has no discriminator at all: "Transport inferred: `command`→stdio,
`url`→HTTP/SSE." It does constrain the *name* — start with a letter or
underscore, `[A-Za-z0-9_-]`, no trailing underscore — which `osp` and
`markitdown` both satisfy.

Why this is done textually rather than with a TOML writer: the user's file is
theirs. Appending preserves their comments, ordering and formatting exactly,
and Python ships a TOML *reader* but no writer. So the only edits made here are
(a) drop the blocks OSP itself wrote earlier, and (b) append fresh ones.

The safety contract is the one `merge_mcp_config.py` honours for JSON:
    - refuse to touch a file that does not already parse;
    - re-parse after writing, and restore the original if the result is broken.

Usage:  merge_mcp_toml.py <config.toml> <python> <server.py> [--style array|table]
Exit:   0 merged · 1 unusable, caller should fall back
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:  # 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - older interpreters
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:
        tomllib = None  # type: ignore

OSP_NAMES = ("osp", "markitdown")
_ARRAY_HEADER = "[[mcp_servers]]"
# TOML permits whitespace inside the brackets, and either quote style. An exact
# string compare missed `[[ mcp_servers ]]` entirely: the block was not
# recognised as ours, so a re-install appended a second `osp` beside the stale
# one — and Vibe takes the first, so the dead path won permanently.
_ARRAY_RE = re.compile(r"^\s*\[\[\s*mcp_servers\s*\]\]\s*$")
_NAME_RE = re.compile(r"""^\s*name\s*=\s*["']([^"']+)["']""")
# `[mcp_servers.osp]`, tolerating the whitespace TOML permits inside brackets.
_TABLE_RE = re.compile(r'^\s*\[\s*mcp_servers\s*\.\s*([A-Za-z0-9_-]+)\s*\]\s*$')


def toml_str(value: str) -> str:
    """Quote a value as a TOML basic string.

    Interpolating a bare path used to be fine until it was not: a Windows path
    carries backslashes, which TOML reads as escapes, and a path may contain a
    quote. Both silently produce a file that parses into the wrong thing, or
    does not parse at all.
    """
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def render(python: str, server: str, style: str) -> str:
    """The two entries OSP owns, in the shape this tool expects."""
    py, srv = toml_str(python), toml_str(server)
    if style == "table":
        return (
            f"\n[mcp_servers.osp]\n"
            f"command = {py}\n"
            f"args = [{srv}]\n"
            f"\n[mcp_servers.markitdown]\n"
            f'command = "uvx"\n'
            f'args = ["markitdown-mcp"]\n'
        )
    # array — `transport` is mandatory here, see the module docstring.
    return (
        f"\n{_ARRAY_HEADER}\n"
        f'name = "osp"\n'
        f'transport = "stdio"\n'
        f"command = {py}\n"
        f"args = [{srv}]\n"
        f"\n{_ARRAY_HEADER}\n"
        f'name = "markitdown"\n'
        f'transport = "stdio"\n'
        f'command = "uvx"\n'
        f'args = ["markitdown-mcp"]\n'
    )


def _block_end(lines: list[str], start: int) -> int:
    """Index one past the block opened at `start` — it runs to the next table header.

    Trailing blank and comment lines are handed back. A comment immediately
    above the next table introduces *that* table, and deleting it with our
    block would break the promise in the module docstring that the user's
    comments are preserved. The same applies at end of file, where a trailing
    note is the user's, not ours.
    """
    j = start + 1
    while j < len(lines) and not lines[j].lstrip().startswith("["):
        j += 1
    while j - 1 > start:
        prev = lines[j - 1].strip()
        if prev == "" or prev.startswith("#"):
            j -= 1
        else:
            break
    return j


# The two shapes OSP itself writes: a command inside the project's own runtime
# directory, or the markitdown entry, which has no project path to recognise.
_OSP_PATH_MARK = ".open-scholar-peer/mcp"


def _is_ours(block: list[str]) -> bool:
    """Does this block look like one OSP wrote?

    A name match alone is not ownership. `merge_mcp_config.py` learned this for
    JSON and keeps a sidecar; here the evidence is in the block itself, which
    is enough because both entries OSP writes are recognisable on sight. A
    user's own server that happens to be called `osp` is left exactly where it
    is — losing it would be the same failure this whole area exists to prevent.
    """
    text = "\n".join(block)
    if _OSP_PATH_MARK in text:
        return True
    return "markitdown-mcp" in text and "uvx" in text


def strip_osp_blocks(
    text: str,
    names: tuple[str, ...] = OSP_NAMES,
    style: str = "array",
    foreign: list[str] | None = None,
) -> str:
    """Remove the server blocks OSP wrote, leaving everything else alone.

    A block carrying one of our names but none of our fingerprints belongs to
    the user. It is kept, and its name is appended to `foreign` so the caller
    can refuse the merge rather than write a duplicate entry beside it.
    """
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        name = None
        if style == "table":
            m = _TABLE_RE.match(lines[i])
            if m:
                name = m.group(1)
        elif _ARRAY_RE.match(lines[i]):
            j = _block_end(lines, i)
            for line in lines[i:j]:
                nm = _NAME_RE.match(line)
                if nm:
                    name = nm.group(1)
                    break

        if name is None:
            out.append(lines[i])
            i += 1
            continue

        j = _block_end(lines, i)

        # A named table can have sub-tables — `[mcp_servers.osp.env]` is the
        # ordinary way to write an environment block. Removing the parent and
        # leaving those behind produces a config that still declares a server
        # named osp, with nothing but our leftovers in it.
        if style == "table" and name is not None:
            sub = re.compile(rf"^\s*\[\s*mcp_servers\s*\.\s*{re.escape(name)}\s*\.")
            while True:
                # `_block_end` hands back trailing blanks and comments, so look
                # past them for the sub-table rather than stopping at the gap.
                k = j
                while k < len(lines) and (
                    lines[k].strip() == "" or lines[k].lstrip().startswith("#")
                ):
                    k += 1
                if k < len(lines) and sub.match(lines[k]):
                    j = _block_end(lines, k)
                else:
                    break

        if name in names:
            if _is_ours(lines[i:j]):
                i = j
                while out and out[-1].strip() == "":
                    out.pop()  # do not leave the hole behind
                continue
            if foreign is not None and name not in foreign:
                foreign.append(name)

        out.extend(lines[i:j])
        i = j
    return "\n".join(out)


def _osp_present(parsed: dict, style: str) -> bool:
    servers = parsed.get("mcp_servers")
    if style == "table":
        return isinstance(servers, dict) and "osp" in servers
    if not isinstance(servers, list):
        return False
    return any(isinstance(s, dict) and s.get("name") == "osp" for s in servers)


def _read_raw(path: Path) -> str:
    """Read without universal-newline translation.

    `Path.read_text()` turns CRLF into LF on the way in, so a detector that
    runs afterwards can never see what the file actually used — and the file
    comes back rewritten end to end on a Windows checkout.
    """
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def _write_raw(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def _newline_of(text: str) -> str:
    """The line ending this file already uses, so we hand it back unchanged."""
    return "\r\n" if "\r\n" in text else "\n"


def _retab(text: str, newline: str) -> str:
    if newline == "\n":
        return text.replace("\r\n", "\n")
    return text.replace("\r\n", "\n").replace("\n", "\r\n")


def merge(path: Path, python: str, server: str, style: str = "array") -> tuple[bool, str]:
    """Returns (merged, message)."""
    original = _read_raw(path) if path.exists() else ""
    newline = _newline_of(original)

    if not original.strip():
        # Nothing to merge with, so nothing to parse. This is the common case:
        # OSP creates the directory itself, and it works on any Python.
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_raw(path, render(python, server, style).lstrip("\n"))
        return True, "2 MCP server(s) configured"

    if tomllib is None:
        # Merging into someone else's file without being able to read it back
        # is exactly the kind of guess that loses their config.
        return False, ("cannot merge into an existing config without a TOML "
                       "parser (needs Python 3.11+, or tomli)")

    try:
        tomllib.loads(original)
    except Exception as exc:
        # Someone else's broken or exotic file. Not ours to repair.
        return False, f"existing config does not parse ({exc.__class__.__name__})"

    foreign: list[str] = []
    body = strip_osp_blocks(original, style=style, foreign=foreign).rstrip("\r\n")
    if foreign:
        # Appending beside it would either duplicate a TOML key or leave two
        # servers fighting over one name. Neither is ours to decide.
        return False, (
            f"a server named {', '.join(foreign)} already exists in this config and "
            f"was not written by OSP — refusing to touch it"
        )
    merged = _retab((body + "\n" if body else "") + render(python, server, style), newline)

    try:
        parsed = tomllib.loads(merged)
    except Exception as exc:
        return False, f"merge would produce invalid TOML ({exc.__class__.__name__})"

    if not _osp_present(parsed, style):
        return False, "merged file does not contain the osp entry"

    path.parent.mkdir(parents=True, exist_ok=True)
    _write_raw(path, merged)

    # Read back from disk: what matters is the file, not the string we built.
    try:
        tomllib.loads(_read_raw(path))
    except Exception:
        _write_raw(path, original)
        return False, "wrote invalid TOML, original restored"

    servers = parsed.get("mcp_servers")
    count = len(servers) if isinstance(servers, (list, dict)) else 0
    return True, f"{count} MCP server(s) configured"


_REEXEC_ENV = "OSP_TOML_REEXEC"
_PROBE = (
    "import importlib.util as u, sys; "
    "sys.exit(0 if (u.find_spec('tomllib') or u.find_spec('tomli')) else 1)"
)


def hand_over_to_a_parser(config_path: Path) -> None:
    """Re-exec under an interpreter that can read TOML, if this one cannot.

    Debian and Ubuntu ship `python3` as 3.10, which has no `tomllib`, and the
    installers invoke us with whatever `python3` is. Left alone, that means a
    *second* install of Grok Build or Mistral Vibe cannot update its own
    entry: the config now exists, so the no-parser path fires and the merge is
    refused. Looking for a parser is cheaper and far less surprising than
    telling the user to install one.

    Only done when it would change the outcome — there is an existing config
    to read — and only once, guarded by an environment flag so a candidate
    that turns out to be no better cannot loop.
    """
    if tomllib is not None or os.environ.get(_REEXEC_ENV):
        return
    try:
        if not config_path.exists() or not config_path.read_text(encoding="utf-8").strip():
            return  # a fresh write needs no parser at all
    except OSError:
        return

    # The project venv first: it is the interpreter OSP itself built, and it
    # carries a TOML reader. Then any newer system Python.
    candidates = [os.environ.get("OSP_MCP_PYTHON", ""),
                  "python3.13", "python3.12", "python3.11"]
    for cand in candidates:
        if not cand:
            continue
        exe = cand if os.path.isabs(cand) else shutil.which(cand) or ""
        if not exe or not os.access(exe, os.X_OK):
            continue
        try:
            probe = subprocess.run([exe, "-c", _PROBE], timeout=15,
                                   capture_output=True)
        except (OSError, subprocess.SubprocessError):
            continue
        if probe.returncode != 0:
            continue
        env = dict(os.environ)
        env[_REEXEC_ENV] = "1"
        os.execve(exe, [exe, str(Path(__file__).resolve()), *sys.argv[1:]], env)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config_path")
    parser.add_argument("python_path")
    parser.add_argument("server_path")
    parser.add_argument(
        "--style",
        default="array",
        choices=("array", "table"),
        help="array = Mistral Vibe [[mcp_servers]]; table = Grok Build [mcp_servers.<name>]",
    )
    args = parser.parse_args()

    config_path = Path(args.config_path)
    hand_over_to_a_parser(config_path)  # may replace this process

    ok, msg = merge(config_path, args.python_path,
                    args.server_path, args.style)
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
