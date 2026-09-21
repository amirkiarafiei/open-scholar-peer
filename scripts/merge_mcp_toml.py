#!/usr/bin/env python3
"""Merge the OSP MCP servers into a Mistral Vibe `config.toml`.

Vibe stores MCP servers as an array of tables:

    [[mcp_servers]]
    name = "osp"
    transport = "stdio"
    command = "/path/to/python"
    args = ["/path/to/osp_mcp.py"]

`transport` is a pydantic discriminator. An entry without it does not merely
fail to load — it invalidates the whole config file, so every entry the user
had is lost. It is not optional.

Why this is done textually rather than with a TOML writer: the user's file is
theirs. Appending an array-of-tables block preserves their comments, ordering
and formatting exactly, and Python ships a TOML *reader* but no writer. So the
only edits made here are (a) drop the blocks OSP itself wrote earlier, and
(b) append fresh ones.

The safety contract is the same one `merge_mcp_config.py` honours for JSON:
    - refuse to touch a file that does not already parse;
    - re-parse after writing, and restore the original if the result is broken.

Usage:  merge_mcp_toml.py <config.toml> <python> <server.py>
Exit:   0 merged · 1 unusable, caller should fall back to a snippet
"""

from __future__ import annotations

import re
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
_HEADER = "[[mcp_servers]]"
_NAME_RE = re.compile(r'^\s*name\s*=\s*"([^"]+)"')


def render(python: str, server: str) -> str:
    """The two entries OSP owns. `transport` is mandatory — see the module docstring."""
    return (
        f'\n{_HEADER}\n'
        f'name = "osp"\n'
        f'transport = "stdio"\n'
        f'command = "{python}"\n'
        f'args = ["{server}"]\n'
        f'\n{_HEADER}\n'
        f'name = "markitdown"\n'
        f'transport = "stdio"\n'
        f'command = "uvx"\n'
        f'args = ["markitdown-mcp"]\n'
    )


def strip_osp_blocks(text: str, names: tuple[str, ...] = OSP_NAMES) -> str:
    """Remove the `[[mcp_servers]]` blocks OSP wrote, leaving everything else alone."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].strip() != _HEADER:
            out.append(lines[i])
            i += 1
            continue

        # A block runs until the next table header at any indent, or EOF.
        j = i + 1
        while j < len(lines) and not lines[j].lstrip().startswith("["):
            j += 1
        block = lines[i:j]

        name = None
        for line in block:
            m = _NAME_RE.match(line)
            if m:
                name = m.group(1)
                break

        if name in names:
            i = j
            while out and out[-1].strip() == "":
                out.pop()  # do not leave the hole behind
            continue

        out.extend(block)
        i = j
    return "\n".join(out)


def merge(path: Path, python: str, server: str) -> tuple[bool, str]:
    """Returns (merged, message)."""
    original = path.read_text(encoding="utf-8") if path.exists() else ""

    if not original.strip():
        # Nothing to merge with, so nothing to parse. This is the common case:
        # OSP creates `.vibe/` itself, and it works on any Python.
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(python, server).lstrip("\n"), encoding="utf-8")
        return True, "2 MCP server(s) configured"

    if tomllib is None:
        # Merging into someone else's file without being able to read it back
        # is exactly the kind of guess that loses their config.
        return False, "cannot merge into an existing config without a TOML parser (needs Python 3.11+, or tomli)"

    if original.strip():
        try:
            tomllib.loads(original)
        except Exception as exc:
            # Someone else's broken or exotic file. Not ours to repair.
            return False, f"existing config does not parse ({exc.__class__.__name__})"

    body = strip_osp_blocks(original).rstrip("\n")
    merged = (body + "\n" if body else "") + render(python, server)

    try:
        parsed = tomllib.loads(merged)
    except Exception as exc:
        return False, f"merge would produce invalid TOML ({exc.__class__.__name__})"

    names = [s.get("name") for s in parsed.get("mcp_servers", [])]
    if "osp" not in names:
        return False, "merged file does not contain the osp entry"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(merged, encoding="utf-8")

    # Read back from disk: what matters is the file, not the string we built.
    try:
        tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        path.write_text(original, encoding="utf-8")
        return False, "wrote invalid TOML, original restored"

    return True, f"{len(names)} MCP server(s) configured"


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 1
    ok, msg = merge(Path(sys.argv[1]), sys.argv[2], sys.argv[3])
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
