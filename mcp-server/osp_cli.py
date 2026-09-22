#!/usr/bin/env python3
"""
osp_cli.py — the Open ScholarPeer search tools, as a command-line program.

Why this exists
---------------
Not every agent speaks MCP. Pi ships no MCP client and says so deliberately
("No MCP. Build CLI tools with READMEs"), yet it does have `bash`. Without a
path like this one, such a tool could run the review protocol but could not
retrieve a single paper — and a review with no literature is not a review.

So this is a bridge, not a second implementation. Every tool it exposes is
the *same function object* the MCP server registers, reached through the same
`OSP_SOURCES` gating and returning the same error envelope. There is no second
list of tools to fall out of step with the first: the surface is read back off
the MCP server at run time.

Usage
-----
    osp_cli.py list                      # every enabled tool, one per line
    osp_cli.py list --json               # the same, machine-readable
    osp_cli.py schema <tool>             # one tool's JSON input schema
    osp_cli.py call <tool> '<json>'      # run it; '-' or omitted reads stdin

Examples
--------
    osp_cli.py call search_arxiv '{"query": "retrieval augmented generation",
                                   "max_results": 5}'
    echo '{"arxiv_id": "2310.11511"}' | osp_cli.py call get_arxiv_paper_details

Output
------
Always a single JSON document on stdout. Errors use the same envelope as the
MCP server — `{"error": ..., "reason": ...}` — so an agent branches on exactly
one contract whichever way it called us.

Exit codes
----------
    0  the call ran. An empty list is a 0: it means the search matched nothing.
    1  the call ran and returned an error envelope (read `reason`).
    2  the command line itself was wrong — unknown tool, bad JSON.

The distinction in 0 vs 1 is the point. "The provider refused" and "there are
no such papers" are different facts, and collapsing them is the bug this
project has spent a milestone removing.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import sys
from pathlib import Path
from typing import Any

# The MCP server lives beside this file and imports `providers` as a top-level
# package, so this directory has to be importable no matter where the agent's
# shell happened to be when it ran us.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import osp_mcp  # noqa: E402  (deliberately after the path fix)


def _envelope(message: str, reason: str) -> dict[str, str]:
    """A CLI-level failure, in the server's own error shape."""
    return {"error": message, "reason": reason}


def _emit(payload: Any) -> None:
    json.dump(payload, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def _registered() -> dict[str, Any]:
    """The tools the MCP server is actually serving, name -> Tool."""
    return {t.name: t for t in asyncio.run(osp_mcp.mcp.list_tools())}


def _is_gated_off(name: str) -> bool:
    """True when `name` is a real tool that this project switched off.

    Derived, not listed. `tool_for` leaves a disabled tool's function in the
    module and simply never registers it, so "present but unregistered" is
    precisely the set turned off by OSP_SOURCES — no second table to maintain.

    The two exclusions matter. A private helper like `_run` is an async
    function in this module but not a tool, and reporting it as "a database
    you switched off" would send someone editing `.env` over a typo. And a
    coroutine imported from elsewhere is not ours to describe at all.
    """
    if name.startswith("_"):
        return False
    fn = getattr(osp_mcp, name, None)
    return (
        inspect.iscoroutinefunction(fn)
        and getattr(fn, "__module__", None) == osp_mcp.__name__
    )


def _required(tool: Any) -> list[str]:
    return list(tool.inputSchema.get("required", []))


def _is_error(result: Any) -> bool:
    """Is this result an error envelope, however the tool chose to wrap it?

    This is the whole contract, so it is worth being exact. A *search* tool
    declares `list[dict]` and therefore returns its failure as `[_err(...)]` —
    a one-element list — while a lookup tool declares `dict` and returns
    `_err(...)` bare. Measured in `osp_mcp.py`: 14 of the 22 tools take the
    list form, and they are precisely the search tools an agent calls most.

    Inspecting only the dict form made every one of those 14 exit 0, which is
    the code that means "the search ran and matched nothing". A blocked
    provider would have been indistinguishable from an empty field — the exact
    confusion M11 spent a milestone removing, reintroduced through a new
    calling convention.
    """
    if isinstance(result, dict):
        return "error" in result and "reason" in result
    if isinstance(result, list):
        return any(
            isinstance(item, dict) and "error" in item and "reason" in item
            for item in result
        )
    return False


def cmd_list(as_json: bool) -> int:
    tools = _registered()
    if as_json:
        _emit([
            {
                "name": name,
                "description": (t.description or "").strip(),
                "required": _required(t),
                "input_schema": t.inputSchema,
            }
            for name, t in sorted(tools.items())
        ])
        return 0

    print(f"{len(tools)} search tools are enabled in this project.")
    print("Call one with:  osp_cli.py call <tool> '<json arguments>'")
    print()
    for name, t in sorted(tools.items()):
        summary = (t.description or "").strip().splitlines()
        first = summary[0] if summary else ""
        req = ", ".join(_required(t)) or "no required arguments"
        print(f"  {name}")
        print(f"      {first}")
        print(f"      required: {req}")
    print()
    print("Full argument list for one tool:  osp_cli.py schema <tool>")
    return 0


def cmd_schema(name: str) -> int:
    tools = _registered()
    if name not in tools:
        return _reject_unknown(name, tools)
    _emit(tools[name].inputSchema)
    return 0


def _reject_unknown(name: str, tools: dict[str, Any]) -> int:
    """Say which of the two different things went wrong."""
    if _is_gated_off(name):
        _emit(_envelope(
            f"{name} is a real tool, but its database is switched off for this "
            f"project. This is not an empty result — nothing was searched. "
            f"Edit OSP_SOURCES in .env at the project root to enable it, or "
            f"use one of: {', '.join(sorted(tools))}.",
            "unavailable",
        ))
    else:
        _emit(_envelope(
            f"No tool named {name}. Run `osp_cli.py list` to see the "
            f"{len(tools)} tools this project has.",
            "bad_request",
        ))
    return 2


def _read_args(raw: str | None) -> tuple[dict[str, Any] | None, int]:
    """Parse the JSON argument blob from argv or stdin.

    Reading stdin when nothing is piped in would sit there until killed, which
    from an agent's side is indistinguishable from a slow search. So a terminal
    on stdin is handled explicitly: no argument at all means no arguments, and
    an explicit `-` says plainly that there is nothing to read.
    """
    if raw is None and sys.stdin.isatty():
        return {}, 0
    if raw == "-" and sys.stdin.isatty():
        _emit(_envelope(
            "asked to read arguments from stdin, but stdin is a terminal — "
            "pipe the JSON in, or pass it as an argument.",
            "bad_request",
        ))
        return None, 2
    if raw is None or raw == "-":
        raw = sys.stdin.read()
    raw = (raw or "").strip()
    if not raw:
        return {}, 0
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        _emit(_envelope(f"arguments are not valid JSON: {exc}", "bad_request"))
        return None, 2
    if not isinstance(parsed, dict):
        _emit(_envelope(
            f"arguments must be a JSON object naming each one, not a "
            f"{type(parsed).__name__}. Example: '{{\"query\": \"...\"}}'",
            "bad_request",
        ))
        return None, 2
    return parsed, 0


def cmd_call(name: str, raw_args: str | None) -> int:
    tools = _registered()
    if name not in tools:
        return _reject_unknown(name, tools)

    kwargs, code = _read_args(raw_args)
    if kwargs is None:
        return code

    missing = [k for k in _required(tools[name]) if k not in kwargs]
    if missing:
        _emit(_envelope(
            f"{name} needs {', '.join(missing)}. "
            f"Run `osp_cli.py schema {name}` for the full argument list.",
            "bad_request",
        ))
        return 2

    fn = getattr(osp_mcp, name)
    try:
        result = asyncio.run(fn(**kwargs))
    except TypeError as exc:
        # Wrong argument names reach us as a TypeError from the call itself.
        _emit(_envelope(
            f"{name} rejected those arguments: {exc}. "
            f"Run `osp_cli.py schema {name}`.",
            "bad_request",
        ))
        return 2
    except Exception as exc:  # noqa: BLE001 — mirror the server's own catch-all
        _emit(osp_mcp._err(name, exc))
        return 1

    _emit(result)
    # The tools return their own envelope rather than raising, so the exit code
    # has to be read back off the result.
    return 1 if _is_error(result) else 0


class _JsonArgumentParser(argparse.ArgumentParser):
    """An argument parser that fails in the same shape as everything else here.

    The contract this file advertises is "always a single JSON document on
    stdout". Stock argparse breaks it: a missing subcommand or an unknown flag
    prints usage text and exits, so an agent that pipes stdout into a JSON
    parser gets a decode error instead of a `reason` it can act on.
    """

    def error(self, message: str) -> Any:  # noqa: D102 - argparse override
        _emit(_envelope(
            f"{message}. Run `osp_cli.py list` to see the available tools.",
            "bad_request",
        ))
        raise SystemExit(2)


def main() -> int:
    parser = _JsonArgumentParser(
        prog="osp_cli.py",
        description="Open ScholarPeer search tools over the command line, "
                    "for agents without an MCP client.",
    )
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="show every enabled search tool")
    p_list.add_argument("--json", action="store_true", dest="as_json",
                        help="machine-readable, with full input schemas")

    p_schema = sub.add_parser("schema", help="show one tool's arguments")
    p_schema.add_argument("tool")

    p_call = sub.add_parser("call", help="run one tool")
    p_call.add_argument("tool")
    p_call.add_argument("arguments", nargs="?", default=None,
                        help="JSON object; omit or pass '-' to read stdin")

    args = parser.parse_args()

    if args.command == "list":
        return cmd_list(args.as_json)
    if args.command == "schema":
        return cmd_schema(args.tool)
    if args.command == "call":
        return cmd_call(args.tool, args.arguments)

    _emit(_envelope(
        "no command given. Use `list`, `schema <tool>` or `call <tool> '<json>'`.",
        "bad_request",
    ))
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except KeyboardInterrupt:
        _emit(_envelope("interrupted", "failed"))
        sys.exit(2)
    except BaseException as exc:  # noqa: BLE001
        # Anything that escapes — an import failure, a broken provider at
        # start-up — still leaves JSON on stdout. A traceback here would be
        # read by an agent as a malformed result rather than a failure it can
        # branch on, which is the one thing this interface must never do.
        _emit(_envelope(f"{type(exc).__name__}: {exc}", "failed"))
        sys.exit(1)
