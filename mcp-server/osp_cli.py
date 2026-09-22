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
import json
import sys
from pathlib import Path
from typing import Any

# The MCP server lives beside this file and imports `providers` as a top-level
# package, so this directory has to be importable no matter where the agent's
# shell happened to be when it ran us.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# `core` is imported inside main(), not here. An ImportError at module level
# escapes before the guard at the bottom of this file is in place, and the
# process then exits 1 with ZERO bytes on stdout — while the contract this file
# advertises says exit 1 means "read the `reason`". Measured: a broken `mcp`,
# `arxiv` or interpreter each produced exactly that. Importing inside main()
# puts every failure inside the guard, so it arrives as JSON.
#
# `mcp` is deliberately NOT imported at all. This program is the fallback for
# when MCP is unavailable; it must not fail with the thing it replaces.
core: Any = None


# Set by main() from --max-bytes. A default, not a limit of the format: the
# host that reads this output is what truncates, and it does so mid-document
# without telling anyone. See _cap().
MAX_BYTES = 24_000

# Slack between the per-call timeout and the outer wall, so the inner one
# normally wins and names the provider that hung.
_GRACE = 0.5


def _configure_io(verbose: bool = False) -> None:
    """Make stdout and stderr behave the same way on every machine.

    Two problems, both measured, both of which blame the agent for the
    environment:

    * Under an ASCII locale a non-ASCII query dies with "surrogates not
      allowed" and is reported as `bad_request`, as though the agent had sent
      something malformed. Reconfiguring to UTF-8 removes the whole class.
    * Two of the three log lines an arXiv call emits come from the `arxiv`
      package, not from OSP, so silencing our own logger is not enough — the
      contract says `call ... 2>&1` still parses as JSON. This owns the ROOT
      logger, which is exactly why core.py must not.

    CRITICAL rather than WARNING: at WARNING a mistyped OSP_SOURCES puts a line
    on stderr and breaks that contract on the likeliest configuration mistake
    there is. The same condition is still visible in the tool list itself.
    """
    import logging

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass  # not a real stream, or already right; neither is fatal
    try:
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    logging.basicConfig(
        level=logging.INFO if verbose else logging.CRITICAL,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


def _envelope(message: str, reason: str) -> dict[str, str]:
    """A CLI-level failure, in the server's own error shape."""
    return {"error": message, "reason": reason}


def _size(payload: Any) -> int:
    return len(json.dumps(payload, indent=2, default=str).encode("utf-8"))


def _cap(payload: Any, max_bytes: int = None) -> Any:
    """Cut an oversized result down, and make the cut impossible to miss.

    Measured: `search_arxiv max_results=50` writes 103,399 bytes, about 24,500
    tokens. A host that truncates that mid-document leaves the agent holding a
    fragment of JSON; it salvages what parsed, writes a Provenance section
    saying nothing was missing, and the review rests on a quarter of the
    corpus. Exit 0, no `reason`, nothing to notice.

    So the cut happens here, where it can be described, instead of downstream
    where it cannot. The shape is preserved — a list stays a list, a record
    stays a record — and a marker says what was lost and how to get it.

    The marker deliberately does NOT use the `error`/`reason` envelope shape.
    A truncated search is not a failed one: the records returned are real and
    complete, and an agent that treated this as an error would throw away good
    papers. The exit code stays 0 and the truth sits in the data.
    """
    limit = MAX_BYTES if max_bytes is None else max_bytes
    if limit <= 0 or _size(payload) <= limit:
        return payload

    if isinstance(payload, list):
        # Error envelopes are kept first and never dropped. A failure that does
        # not fit is still the most important thing in the result, and deleting
        # it to make room turns "the provider refused us" into "this was too
        # big" — losing the distinction the whole layer exists to protect.
        errors = [i for i in payload
                  if isinstance(i, dict) and "error" in i and "reason" in i]
        records = [i for i in payload if i not in errors]
        kept: list[Any] = []
        for env in errors:
            env = dict(env)
            room = limit - _size(kept + [_marker(0, len(payload), "list")])
            if _size([env]) > max(room, 0):
                # Shrink the message rather than the envelope. `reason` and the
                # fact of failure survive at any size.
                env["error"] = str(env.get("error", ""))[:800] + " […cut]"
            kept.append(env)
        for item in records:
            probe = kept + [item, _marker(len(kept) + 1, len(payload), "list")]
            if _size(probe) > limit:
                break
            kept.append(item)
        if len(kept) == len(payload):
            return kept
        return kept + [_marker(len(kept), len(payload), "list")]

    if isinstance(payload, dict):
        # A full-text record carries its OWN paging contract — offset,
        # returned_chars, total_chars, truncated, next_offset — and the agent
        # is told to page until next_offset is null. Cutting `text` and leaving
        # those fields alone made a half-read paper describe itself as whole:
        # measured on 1706.03762, 21,673 of 43,180 chars delivered with
        # truncated=false and next_offset=null. An agent stops there, then
        # reports that a cited work "does not report" a number that was in the
        # half it never saw. That is worse than an empty result — it is a
        # fabricated finding.
        if _is_paged_text(payload):
            return _recut_paged_text(payload, limit)

        # Any other record: shrink the largest string and keep the rest, so the
        # metadata an agent needs to cite still arrives.
        biggest = max(
            (k for k, v in payload.items() if isinstance(v, str)),
            key=lambda k: len(payload[k]), default=None)
        if biggest is not None:
            out = dict(payload)
            original = len(out[biggest])
            over = _size(payload) - limit
            keep = max(0, len(out[biggest]) - over - 800)
            out[biggest] = out[biggest][:keep]
            out.update(_marker(keep, original, "field", field=biggest))
            return out

    return _marker(0, 0, "opaque")


_PAGED_KEYS = {"text", "offset", "returned_chars", "total_chars",
               "truncated", "next_offset"}


def _is_paged_text(rec: dict[str, Any]) -> bool:
    """Does this record carry the full-text paging contract?"""
    return _PAGED_KEYS <= set(rec) and isinstance(rec.get("text"), str)


def _recut_paged_text(rec: dict[str, Any], limit: int) -> dict[str, Any]:
    """Cut a full-text window down, and keep its own contract true.

    `providers.window` guarantees that `offset + returned_chars` chains
    exactly, and the tool's docstring tells the agent to keep calling while
    `next_offset` is not null. So a shorter window is fine — a shorter window
    that still claims the old length is not.

    The same snapping rule is reused rather than reimplemented: the cut moves
    back to a paragraph, line or space boundary, because a blind cut between
    "26.3" and "0" leaves a reader a plausible, wrong number.
    """
    out = dict(rec)
    text = rec["text"]
    total = int(rec.get("total_chars") or len(text))
    start = int(rec.get("offset") or 0)

    over = _size(rec) - limit
    budget = max(200, len(text) - over - 900)   # room for the marker itself
    if budget >= len(text):
        return out

    from providers import window as _window   # pure, no third-party imports
    snapped = _window(text, budget, 0)["text"]
    end = start + len(snapped)

    out["text"] = snapped
    out["returned_chars"] = len(snapped)
    out["truncated"] = end < total
    out["next_offset"] = end if end < total else None
    out.update(_marker(len(snapped), total, "paged"))
    return out


def _marker(returned: int, total: int, kind: str, field: str = "") -> dict[str, Any]:
    """The record that says a result was cut. Loud on purpose."""
    if kind == "list":
        how = ("Re-run with a smaller max_results, or raise --max-bytes. "
               "The records above are complete; the rest were not returned.")
    elif kind == "paged":
        how = ("This window was shortened to fit. `next_offset` has been "
               "corrected, so keep calling with `offset` set to it until it is "
               "null — the document is complete only when it is.")
    elif kind == "field":
        how = (f"The {field!r} field was cut. If this tool takes max_chars and "
               f"offset, page through it; otherwise raise --max-bytes.")
    else:
        how = "Raise --max-bytes."
    return {
        "osp_truncated": True,
        "osp_returned": returned,
        "osp_total": total,
        "osp_note": ("This result was cut to fit the output limit. It is NOT "
                     "an empty result and NOT a complete one. Say so in "
                     "Provenance rather than treating it as the whole corpus."),
        "osp_how_to_get_the_rest": how,
    }


def _emit(payload: Any) -> None:
    json.dump(payload, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def _registered() -> dict[str, Any]:
    """The tools this project is serving, name -> core.Tool.

    Read from `core`, not from the MCP server. The set is the same — both
    surfaces gate on the same OSP_SOURCES — but reading it here through FastMCP
    would mean the command-line fallback could not answer whenever `mcp` was
    broken, which is the situation it exists for.
    """
    return core.enabled_tools()


def _is_gated_off(name: str) -> bool:
    """True when `name` is a real tool that this project switched off.

    Registry membership, not module identity. The version this replaces
    compared `fn.__module__` against the importing module's name, which worked
    only while the tools lived in the server file. Once they moved to `core`
    every tool reported `core`, so the predicate returned False for all of
    them and "this database is switched off — edit OSP_SOURCES" silently
    became "no tool named X", sending a user to hunt a typo. Both exit 2, so
    nothing that checked only the exit code would have noticed.
    """
    return core.is_gated_off(name)


def _required(spec: Any) -> list[str]:
    return core.required_args(spec.fn)


def _is_error(result: Any) -> bool:
    """Is this result an error envelope, however the tool chose to wrap it?

    This is the whole contract, so it is worth being exact. A *search* tool
    declares `list[dict]` and therefore returns its failure as `[_err(...)]` —
    a one-element list — while a lookup tool declares `dict` and returns
    `_err(...)` bare. Measured in `core.py`: 14 of the 22 tools take the
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
        # Name, first line, required. NOT the full schemas or descriptions.
        # Measured: the full form is 37,463 bytes, of which descriptions are
        # 21,536 (69.8%) and schemas 7,118 (23.1%) — so dropping schemas alone
        # would not have been enough. This form is about 4 KB, and
        # `schema <tool>` still gives everything for the one tool in hand.
        _emit([
            {
                "name": name,
                "summary": ((t.doc or "").strip().splitlines() or [""])[0],
                "required": _required(t),
            }
            for name, t in sorted(tools.items())
        ])
        return 0

    print(f"{len(tools)} search tools are enabled in this project.")
    print("Call one with:  osp_cli.py call <tool> '<json arguments>'")
    print()
    for name, t in sorted(tools.items()):
        summary = (t.doc or "").strip().splitlines()
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
    _emit(core.input_schema(tools[name].fn))
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


def _read_args(raw: str | None, expect: str = "object") -> tuple[Any, int]:
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
        return ([] if expect == "array" else {}), 0
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        _emit(_envelope(f"arguments are not valid JSON: {exc}", "bad_request"))
        return None, 2
    if expect == "array":
        return parsed, 0
    if not isinstance(parsed, dict):
        _emit(_envelope(
            f"arguments must be a JSON object naming each one, not a "
            f"{type(parsed).__name__}. Example: '{{\"query\": \"...\"}}'",
            "bad_request",
        ))
        return None, 2
    return parsed, 0


def cmd_call(name: str, raw_args: str | None, deadline: float) -> int:
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

    fn = tools[name].fn
    import asyncio  # 37 ms, and `list` and `schema` never reach this line

    core.CALL_TIMEOUT.set(float(deadline))
    asyncio.run(_dispatch(name, fn, kwargs, float(deadline)))
    raise AssertionError("unreachable: _dispatch always exits")  # pragma: no cover


def _shaped(name: str, fn: Any, envelope: dict[str, Any]) -> Any:
    """Return an error in the shape this tool would have used itself.

    A search tool declares `list[dict]` and returns its own failures as
    `[_err(...)]`. When the CLI catches something ABOVE the tool — an outer
    timeout, a cancellation — returning a bare dict would hand the agent a
    different shape on the error path than on every other path, and an agent
    doing `for paper in result` would silently iterate the dict's keys.
    """
    try:
        return [envelope] if core.returns_list(fn) else envelope
    except Exception:  # noqa: BLE001 - shape detection must never be fatal
        return envelope


async def _dispatch(name: str, fn: Any, kwargs: dict[str, Any],
                    deadline: float) -> None:
    """Run the tool, write exactly one JSON document, and leave.

    All of it inside the event loop, deliberately. `asyncio.wait_for` cancels
    the *wait*, not the worker thread, and `asyncio.run()` then joins the
    executor on the way out: measured, a 1 s timeout against a 6 s call raised
    at 1.00 s and the process did not return until 6.01 s. Returning normally
    would therefore hold the answer hostage to the thing that already timed out.
    """
    import asyncio

    try:
        # The backstop. Normally the inner _run timeout fires first and the
        # tool returns its own envelope naming the provider; this catches the
        # case where it does not.
        result = await asyncio.wait_for(fn(**kwargs), timeout=deadline + _GRACE)
    except TypeError as exc:
        # Wrong argument names reach us as a TypeError from the call itself.
        _emit_and_exit(_envelope(
            f"{name} rejected those arguments: {exc}. "
            f"Run `osp_cli.py schema {name}`.",
            "bad_request",
        ), code=2)
    except (asyncio.TimeoutError, TimeoutError):
        _emit_and_exit(_shaped(name, fn, core._err(name, TimeoutError(
            f"{name} passed the {deadline}s limit set by --timeout and was "
            f"abandoned. Nothing was searched — this is not an empty result."))))
    except asyncio.CancelledError:
        # CancelledError is a BaseException, so the tools' own `except
        # Exception` does not swallow it and mislabel it as `failed`.
        _emit_and_exit(_shaped(name, fn,
                               core._err(name, TimeoutError(f"{name} was cancelled"))))
    except Exception as exc:  # noqa: BLE001 — mirror the server's own catch-all
        _emit_and_exit(_shaped(name, fn, core._err(name, exc)))

    # The exit code is read off the UNCAPPED result. Capping can delete a
    # one-element error envelope that does not fit, and then nothing downstream
    # can tell a blocked provider from a large one: measured, a Google Scholar
    # block with a 30 KB message came back as exit 0 with no `error` and no
    # `reason`, presented as a size problem with advice to ask for fewer
    # results. That is the M11 defect, reintroduced through the cap.
    _emit_and_exit(_cap(result), code=1 if _is_error(result) else 0)


def _emit_and_exit(result: Any, code: int | None = None) -> None:
    """Write the one JSON document and end the process. Never returns.

    os._exit skips every buffer Python owns, so stdout is flushed explicitly
    first. Getting that order wrong loses the envelope exactly when it matters
    most — on the timeout path, where there is a stuck thread and nothing else
    to tell the agent what happened.

    It also skips atexit and the executor join, which is the point. Nothing
    here needs a polite shutdown: the CLI holds no file handles, and the arXiv
    lock is an fcntl.flock the kernel releases when the process dies.
    """
    import os

    # The tools return their own envelope rather than raising, so the exit code
    # has to be read back off the result.
    if code is None:
        code = 1 if _is_error(result) else 0
    try:
        _emit(result)
        sys.stdout.flush()
    except BrokenPipeError:
        os._exit(1)  # nobody is reading; there is nowhere to report to
    except Exception:  # noqa: BLE001
        code = 1
    try:
        sys.stderr.flush()
    except Exception:  # noqa: BLE001
        pass
    os._exit(code)


MAX_BATCH = 32


def cmd_batch(raw: str | None, deadline: float) -> int:
    """Run several calls in ONE process.

    The process boundary is the only real difference between this surface and
    MCP. One MCP server is one process, so the arXiv lock, the three-second
    gap, the eight-entry parsed-text cache and the in-flight de-duplication all
    work. Every separate CLI call throws that away and pays a fresh start-up:
    measured, a three-round literature phase is ~18 calls at ~0.44s of start-up
    each, plus an enforced 3s between arXiv calls — over a minute of pure
    overhead per phase, against roughly nothing here.

    It needs no change to the prompts. The literature skill says "fire
    everything you chose in the same dispatch batch", which stays true on both
    surfaces — which is the point.

    Four rules, and each one exists to keep a failure attributable:
      * a deadline PER ITEM, never one for the whole batch;
      * one envelope per item, so a failure names its own call;
      * a failing item never stops the others;
      * the output cap applies per item AND to the whole response.
    """
    import asyncio

    payload, code = _read_args(raw, expect="array")
    if payload is None:
        return code
    if not isinstance(payload, list):
        _emit(_envelope(
            "batch takes a JSON array of calls, each "
            '{"tool": "...", "arguments": {...}}.', "bad_request"))
        return 2
    if not payload:
        _emit(_envelope("the batch is empty — nothing to run.", "bad_request"))
        return 2
    if len(payload) > MAX_BATCH:
        _emit(_envelope(
            f"a batch is limited to {MAX_BATCH} calls and this one has "
            f"{len(payload)}. Split it: a batch that is too long is more likely "
            f"to meet a rate limit part-way through, and a partial answer is "
            f"harder to reason about than two whole ones.", "bad_request"))
        return 2

    tools = _registered()
    plans: list[dict[str, Any]] = []
    for i, item in enumerate(payload):
        if not isinstance(item, dict) or "tool" not in item:
            _emit(_envelope(
                f"call {i} is not an object naming a tool. Each call is "
                '{"tool": "...", "arguments": {...}}.', "bad_request"))
            return 2
        name = item["tool"]
        # Read it before defaulting. `or {}` would turn a falsy wrong type —
        # [], "", 0 — into an empty dict, so the check below never saw it and
        # the call failed later as a missing argument instead of a bad one.
        kwargs = item.get("arguments")
        if kwargs is None:
            kwargs = {}
        if not isinstance(kwargs, dict):
            _emit(_envelope(
                f"call {i} ({name}): arguments must be a JSON object.",
                "bad_request"))
            return 2
        plans.append({"tool": name, "arguments": kwargs})

    async def run_one(plan: dict[str, Any]) -> dict[str, Any]:
        name, kwargs = plan["tool"], plan["arguments"]
        if name not in tools:
            if core.is_gated_off(name):
                why = _envelope(
                    f"{name} is a real tool, but its database is switched off "
                    f"for this project. Nothing was searched — this is not an "
                    f"empty result.", "unavailable")
            else:
                why = _envelope(
                    f"No tool named {name}. Run `osp_cli.py list`.",
                    "bad_request")
            return {"tool": name, "ok": False, "result": why}
        missing = [k for k in _required(tools[name]) if k not in kwargs]
        if missing:
            return {"tool": name, "ok": False, "result": _envelope(
                f"{name} needs {', '.join(missing)}. "
                f"Run `osp_cli.py schema {name}`.", "bad_request")}
        try:
            result = await asyncio.wait_for(tools[name].fn(**kwargs),
                                            timeout=deadline + _GRACE)
        except TypeError as exc:
            # Same mistake, same reason as `call`. A wrong argument NAME
            # arrives as a TypeError from the call itself, and reporting it as
            # a generic failure would send the agent looking at the provider
            # instead of at its own arguments.
            result = _envelope(
                f"{name} rejected those arguments: {exc}. "
                f"Run `osp_cli.py schema {name}`.", "bad_request")
        except (asyncio.TimeoutError, TimeoutError):
            result = _shaped(name, tools[name].fn, core._err(name, TimeoutError(
                f"{name} passed the {deadline}s per-call limit and was "
                f"abandoned. Nothing was searched — not an empty result.")))
        except asyncio.CancelledError:
            result = _shaped(name, tools[name].fn,
                             core._err(name, TimeoutError(f"{name} was cancelled")))
        except Exception as exc:  # noqa: BLE001
            result = _shaped(name, tools[name].fn, core._err(name, exc))
        return {"tool": name, "ok": not _is_error(result), "result": result}

    async def run_all() -> None:
        core.CALL_TIMEOUT.set(float(deadline))
        # Providers load lazily, and LazyLoader takes no lock: two threads
        # reaching a cold provider at the same moment is a race. A single
        # `call` cannot race itself, but a batch dispatches together — so warm
        # exactly the sources this batch will touch, before anything runs.
        core.warm_providers({tools[p["tool"]].source
                             for p in plans if p["tool"] in tools})
        # Together, not one after the other — the same instruction the skill
        # gives. arXiv calls still serialise on its own lock; everything else
        # overlaps. gather with return_exceptions so one failure cannot take
        # the batch down, which is the whole promise.
        done = await asyncio.gather(*(run_one(p) for p in plans),
                                    return_exceptions=True)
        out: list[Any] = []
        for plan, item in zip(plans, done):
            if isinstance(item, BaseException):
                item = {"tool": plan["tool"], "ok": False,
                        "result": core._err(plan["tool"], item)
                        if isinstance(item, Exception)
                        else _envelope(f"{item!r}", "failed")}
            # Per item first, so one huge result cannot crowd out the others.
            item["result"] = _cap(item["result"], max(2_000, MAX_BYTES // len(plans)))
            out.append(item)
        failed = sum(1 for i in out if not i["ok"])
        # And the whole response, in case many small results still overflow.
        _emit_and_exit(_cap(out), code=1 if failed else 0)

    asyncio.run(run_all())
    raise AssertionError("unreachable")  # pragma: no cover


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
    global core, MAX_BYTES

    parser = _JsonArgumentParser(
        prog="osp_cli.py",
        description="Open ScholarPeer search tools over the command line, "
                    "for agents without an MCP client.",
    )
    # --verbose is accepted BEFORE or AFTER the subcommand. argparse only
    # offers the first, and every example in the guide reads the second way —
    # `call <tool> ... --verbose` — so it is declared in both places rather
    # than telling agents the flag order matters.
    def _verbose_flag(pp: argparse.ArgumentParser) -> None:
        pp.add_argument("--verbose", action="store_true", default=False,
                        help="let the search layer log to stderr; off by "
                             "default so `2>&1` still parses as JSON")

    _verbose_flag(parser)
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="show every enabled search tool")
    p_list.add_argument("--json", action="store_true", dest="as_json",
                        help="machine-readable, with full input schemas")
    _verbose_flag(p_list)

    p_schema = sub.add_parser("schema", help="show one tool's arguments")
    p_schema.add_argument("tool")
    _verbose_flag(p_schema)

    p_call = sub.add_parser("call", help="run one tool")
    p_call.add_argument("tool")
    p_call.add_argument("arguments", nargs="?", default=None,
                        help="JSON object; omit or pass '-' to read stdin")
    p_call.add_argument("--timeout", type=float, default=None,
                        help="seconds to wait before abandoning the call "
                             "(default: OSP_CALL_TIMEOUT, or 90)")
    p_call.add_argument("--max-bytes", type=int, default=None, dest="max_bytes",
                        help=f"cut the result to fit this many bytes "
                             f"(default {MAX_BYTES}; 0 means no limit)")
    _verbose_flag(p_call)

    p_batch = sub.add_parser(
        "batch", help="run several tools in ONE process — prefer this")
    p_batch.add_argument("calls", nargs="?", default=None,
                         help='JSON array of {"tool": ..., "arguments": {...}}; '
                              "omit or pass '-' to read stdin")
    p_batch.add_argument("--timeout", type=float, default=None,
                         help="seconds allowed for EACH call, not the batch")
    p_batch.add_argument("--max-bytes", type=int, default=None, dest="max_bytes",
                         help=f"cut the whole response to fit this many bytes "
                              f"(default {MAX_BYTES}; 0 means no limit)")
    _verbose_flag(p_batch)

    args = parser.parse_args()
    _configure_io(getattr(args, "verbose", False))

    # Imported here, not at module level: an ImportError above main() escapes
    # before the guard at the bottom of this file exists, and the process then
    # exits 1 with zero bytes of stdout.
    import core as _core

    core = _core

    if args.command == "list":
        return cmd_list(args.as_json)
    if args.command == "schema":
        return cmd_schema(args.tool)
    if args.command == "call":
        if args.max_bytes is not None:
            MAX_BYTES = args.max_bytes
        deadline = (args.timeout if args.timeout is not None
                    else core.CALL_TIMEOUT.get())
        if deadline <= 0:
            _emit(_envelope("--timeout must be greater than zero.",
                            "bad_request"))
            return 2
        return cmd_call(args.tool, args.arguments, deadline)
    if args.command == "batch":
        if args.max_bytes is not None:
            MAX_BYTES = args.max_bytes
        deadline = (args.timeout if args.timeout is not None
                    else core.CALL_TIMEOUT.get())
        if deadline <= 0:
            _emit(_envelope("--timeout must be greater than zero.",
                            "bad_request"))
            return 2
        return cmd_batch(args.calls, deadline)

    _emit(_envelope(
        "no command given. Use `list`, `schema <tool>`, "
        "`call <tool> '<json>'`, or `batch '<json array>'` to run several "
        "calls in one process, which is the preferred form.",
        "bad_request",
    ))
    return 2


if __name__ == "__main__":
    try:
        _configure_io()
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
