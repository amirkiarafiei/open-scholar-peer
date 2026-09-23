#!/usr/bin/env python3
"""
migrate_session.py — bring an existing .brain/session.json up to the current shape.

`init_brain.sh` never touches an existing `.brain/`, which is the right default:
it holds a review in progress. But the file's shape grows between releases, and a
session written by an older version is then missing fields the newer prompts
describe — a skip with nowhere to be recorded, an interface decided every phase
instead of once.

**Strictly additive.** It adds keys that are absent and never reads, changes or
removes a value that is already there, so it cannot lose work. A list is a value:
`qa_criteria` is the user's, and an existing one is left exactly as found.

  --check   report what is missing; exit 1 if anything is, 0 if nothing
  --apply   add the missing keys, then report what was added

Exit codes:  0 nothing to do, or done · 1 fields are missing (--check) · 2 error.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


def _missing(template: object, actual: object, path: str = "") -> list[str]:
    """Key paths present in the template and absent from the session."""
    out: list[str] = []
    if not isinstance(template, dict) or not isinstance(actual, dict):
        return out
    for key, tval in template.items():
        here = f"{path}.{key}" if path else key
        if key not in actual:
            out.append(here)
        else:
            out.extend(_missing(tval, actual[key], here))
    return out


def _add_missing(template: object, actual: object) -> None:
    """Copy absent keys in. Never touches a key that already exists."""
    if not isinstance(template, dict) or not isinstance(actual, dict):
        return
    for key, tval in template.items():
        if key not in actual:
            actual[key] = json.loads(json.dumps(tval))  # deep copy
        else:
            _add_missing(tval, actual[key])


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    if mode not in ("--check", "--apply"):
        print(f"usage: {Path(sys.argv[0]).name} [--check|--apply]", file=sys.stderr)
        return 2

    session = Path(".brain/session.json")
    template = Path(__file__).resolve().parent.parent / ".brain-template" / "session.json"
    if not session.exists() or not template.exists():
        return 0

    try:
        actual = json.loads(session.read_text(encoding="utf-8"))
        wanted = json.loads(template.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  could not read the session file: {exc}", file=sys.stderr)
        return 2

    gaps = _missing(wanted, actual)
    if not gaps:
        return 0

    if mode == "--check":
        for g in gaps:
            print(g)
        return 1

    # Back the file up before writing. It is a review in progress.
    backup = session.with_suffix(".json.before-upgrade")
    try:
        shutil.copy2(session, backup)
        _add_missing(wanted, actual)
        session.write_text(json.dumps(actual, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"  could not write the session file: {exc}", file=sys.stderr)
        return 2

    for g in gaps:
        print(g)
    print(f"__backup__ {backup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
