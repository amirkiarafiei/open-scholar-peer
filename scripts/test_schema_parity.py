#!/usr/bin/env python3
"""
test_schema_parity.py — the two derivers must describe the same tools.

One source of truth: the decorated function's signature. Two readers of it —
FastMCP through pydantic, and `core.input_schema` through `inspect.signature`.
Neither owns a schema, so a human edits one function and both surfaces follow.
This file is what stops them drifting while nobody is looking.

It is the ONE place allowed to import both `core` and `osp_mcp`. Everywhere
else the point of the split is that the CLI never loads `mcp` at all.

Why it compares what it compares:

  * Argument names and required sets already agree 22/22 today, so a test that
    checked only those could never fail. It would look like coverage and be
    none. Types and defaults are compared as well, field by field, so a failure
    names the parameter and the facet.
  * Then the whole document, byte for byte. That is what pins `anyOf` ordering
    and pydantic's per-field `title`, which the field-by-field checks ignore.
  * Then the annotation census, frozen. Adding a 23rd tool with an eighth
    annotation form fails here with a one-line diff, before anyone runs the CLI.

Exit codes:  0 all checks pass · 1 a check failed · 2 the suite could not run.
"""
from __future__ import annotations

import asyncio
import collections
import inspect
import json
import sys
import typing
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "mcp-server"))

_FAILURES: list[str] = []
_CHECKS = 0


def check(label: str, got: object, want: object) -> None:
    global _CHECKS
    _CHECKS += 1
    if got != want:
        _FAILURES.append(f"  - {label}\n      expected: {want!r}\n      got:      {got!r}")


_ABSENT = object()

# The seven forms the 22 tools use, and how many parameters use each. Frozen on
# purpose: the count is what makes an accidental eighth form loud.
_EXPECTED_CENSUS = {
    "str": 23, "int": 17, "str | None": 9, "int | None": 5,
    "bool": 4, "list[str] | None": 4, "list[str]": 1,
}


def _render(ann: object) -> str:
    """Spell an annotation the way a human writes it, for the census."""
    args = typing.get_args(ann)
    if type(None) in args:
        inner = [a for a in args if a is not type(None)]
        if len(inner) == 1:
            return f"{_render(inner[0])} | None"
        return " | ".join(_render(a) for a in args)
    origin = typing.get_origin(ann)
    if origin is not None and args:
        # list[str] renders as "list[str]", not as "list" — the parameter is
        # the whole point, and dropping it would make two different forms look
        # like one in the census.
        inner = ", ".join(_render(a) for a in args)
        return f"{getattr(origin, '__name__', str(origin))}[{inner}]"
    name = getattr(ann, "__name__", None)
    return name if name else str(ann).replace("typing.", "")


def _type_facet(prop: dict) -> object:
    """The type of a property, with pydantic's two spellings normalised.

    An optional is `anyOf: [T, null]`; a plain one carries `type` (and `items`
    for an array). Comparing this rather than the whole property means a type
    mismatch is reported as a type mismatch, not as a whole-document diff.
    """
    if "anyOf" in prop:
        return ("optional",
                tuple(sorted(json.dumps(b, sort_keys=True) for b in prop["anyOf"])))
    return ("plain", json.dumps({k: v for k, v in prop.items()
                                 if k in ("type", "items")}, sort_keys=True))


def main() -> int:
    try:
        import core
        import osp_mcp  # only here, and only to read what FastMCP derived
    except Exception as exc:  # noqa: BLE001
        print(f"❌ cannot import the search layer: {type(exc).__name__}: {exc}")
        return 2

    fastmcp = {t.name: t for t in asyncio.run(osp_mcp.mcp.list_tools())}
    ours = core.enabled_tools()

    check("both surfaces expose the same tool names",
          sorted(fastmcp), sorted(ours))

    for name in sorted(set(fastmcp) & set(ours)):
        spec = ours[name]
        theirs = fastmcp[name].inputSchema
        try:
            mine = core.input_schema(spec.fn)
        except core.UnknownAnnotation as exc:
            _FAILURES.append(f"  - {name}: the CLI cannot describe this tool\n"
                             f"      {exc}")
            continue

        check(f"{name}: argument names",
              list(mine["properties"]), list(theirs["properties"]))
        check(f"{name}: required set",
              sorted(mine.get("required", [])), sorted(theirs.get("required", [])))

        for param in theirs["properties"]:
            t = theirs["properties"][param]
            m = mine["properties"].get(param, {})
            check(f"{name}.{param}: type", _type_facet(m), _type_facet(t))
            check(f"{name}.{param}: default",
                  m.get("default", _ABSENT), t.get("default", _ABSENT))

        # The whole document. This is what catches anyOf ordering and titles.
        check(f"{name}: schema byte-identical",
              json.dumps(mine, indent=2), json.dumps(theirs, indent=2))

        # The description an agent reads to choose a tool is the same string.
        check(f"{name}: description",
              (spec.doc or "").strip(), (fastmcp[name].description or "").strip())

    # The annotation space is closed. Walk REGISTRY, not enabled_tools: gating
    # must not be able to hide a form from this census.
    census: collections.Counter = collections.Counter()
    for spec in core.REGISTRY.values():
        hints = typing.get_type_hints(spec.fn)
        for param in inspect.signature(spec.fn).parameters:
            census[_render(hints[param])] += 1
    check("no annotation form outside the closed set",
          sorted(set(census) - set(_EXPECTED_CENSUS)), [])
    check("the annotation census is unchanged", dict(census), _EXPECTED_CENSUS)

    # And the count the docs point at.
    check("core.py registers 22 tools", len(core.REGISTRY), 22)

    if _FAILURES:
        print(f"\n❌ {len(_FAILURES)} of {_CHECKS} schema-parity checks failed:\n")
        print("\n".join(_FAILURES))
        print("\nThe two derivers disagree. Do NOT hand-write a schema to make "
              "this pass — that creates the second source of truth this test "
              "exists to prevent. Fix the deriver, or teach both about the new "
              "annotation form in the same change.")
        return 1

    print(f"  ✓ {len(ours)} tools, schemas and descriptions byte-identical")
    print(f"  ✓ annotation space closed: {len(_EXPECTED_CENSUS)} forms, "
          f"{sum(_EXPECTED_CENSUS.values())} parameters")
    print(f"\n  ✅ All {_CHECKS} schema-parity checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
