#!/usr/bin/env python3
"""
test_upgrade.py — installing over an older project must be safe and legible.

Two things are being protected. **Nothing the user has written may change**: the
session file holds a review in progress, and the migration is additive or it is
nothing. And **the installer must say what it did** — a re-install that reads
exactly like a first install leaves the user unable to tell whether anything
happened.

The end-to-end flow needs a real venv and is exercised by hand; this covers the
logic underneath it, which is where a silent regression would live.

Exit codes:  0 all checks pass · 1 a check failed · 2 the suite could not run.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PY = REPO / ".venv" / "bin" / "python"
if not PY.exists():
    PY = Path(sys.executable)

_FAILURES: list[str] = []
_CHECKS = 0


def check(label: str, got: object, want: object) -> None:
    global _CHECKS
    _CHECKS += 1
    if got != want:
        _FAILURES.append(f"  - {label}\n      expected: {want!r}\n      got:      {got!r}")


def check_true(label: str, got: object) -> None:
    check(label, bool(got), True)


def _version_cmp(a: str, b: str) -> str:
    out = subprocess.run(
        ["bash", "-c", f'. "{REPO}/scripts/_version.sh"; osp_version_cmp "{a}" "{b}"'],
        capture_output=True, text=True)
    return out.stdout.strip()


def test_version_comparison() -> None:
    """The installer decides what to say from this, so it must not guess."""
    check("an older version is older", _version_cmp("1.2.0", "2.0.0"), "older")
    check("the same version is the same", _version_cmp("2.0.0", "2.0.0"), "same")
    check("a newer version is newer", _version_cmp("2.1.0", "2.0.0"), "newer")
    check("a much older version is older", _version_cmp("1.0.0", "2.0.0"), "older")
    check("a patch bump is older", _version_cmp("2.0.0", "2.0.1"), "older")

    v = (REPO / "VERSION").read_text().strip()
    check_true(f"VERSION is a dotted release number ({v})",
               v.count(".") == 2 and all(p.isdigit() for p in v.split(".")))


def _run_migrate(project: Path, mode: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(PY), str(REPO / "scripts" / "migrate_session.py"), mode],
                          capture_output=True, text=True, cwd=project)


def test_migration_is_additive() -> None:
    """The one rule: it may add, and it may not touch."""
    tmp = Path(tempfile.mkdtemp(prefix="osp-upgrade-"))
    try:
        brain = tmp / ".brain"
        brain.mkdir()
        # A session from an older release: real values, missing newer fields.
        old = {
            "protocol": "OpenScholarPeer", "version": "2.0",
            "venue": {"name": "ICLR 2026", "year": "2026"},
            "paper": {"title": "A paper", "path": "paper.md"},
            "qa_criteria": [{"slug": "novelty", "label": "Novelty"}],
            "phases": {"onboarding": {"status": "completed", "notes": "done"},
                       "literature": {"status": "in_progress"}},
            # A real v1 session HAS an mcp block — it just lacks `interface`.
            # Omitting the parent entirely would exercise a different, easier
            # path, and the nested one is what upgraders actually hit.
            "mcp": {"semantic_scholar_api_key_present": False},
            "resume_from": "literature",
        }
        (brain / "session.json").write_text(json.dumps(old, indent=2))

        r = _run_migrate(tmp, "--check")
        check("--check reports missing fields with exit 1", r.returncode, 1)
        check_true("--check names mcp.interface", "mcp.interface" in r.stdout)

        r = _run_migrate(tmp, "--apply")
        check("--apply succeeds", r.returncode, 0)
        new = json.loads((brain / "session.json").read_text())

        # Every value that existed must be byte-identical.
        def same(a: object, b: object, path: str = "") -> list[str]:
            bad: list[str] = []
            if isinstance(a, dict):
                for k, v in a.items():
                    bad += same(v, (b or {}).get(k), f"{path}.{k}" if path else k)
            elif a != b:
                bad.append(f"{path}: {a!r} -> {b!r}")
            return bad

        check("no pre-existing value was changed", same(old, new), [])
        check("the user's venue survived", new["venue"]["name"], "ICLR 2026")
        check("the user's criteria survived", len(new["qa_criteria"]), 1)
        check("a completed phase stayed completed",
              new["phases"]["onboarding"]["status"], "completed")
        check_true("the new interface field was added", "interface" in new.get("mcp", {}))
        check_true("a backup was written",
                   (brain / "session.json.before-upgrade").exists())

        r = _run_migrate(tmp, "--check")
        check("running it again finds nothing to do", r.returncode, 0)

        r = _run_migrate(tmp, "--apply")
        check("a second apply is a no-op", r.returncode, 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_a_current_session_is_left_alone() -> None:
    """The common case — installing over the same version — must touch nothing."""
    tmp = Path(tempfile.mkdtemp(prefix="osp-upgrade-"))
    try:
        brain = tmp / ".brain"
        brain.mkdir()
        template = (REPO / ".brain-template" / "session.json").read_text()
        (brain / "session.json").write_text(template)
        r = _run_migrate(tmp, "--check")
        check("a current session needs no migration", r.returncode, 0)
        check("and nothing is printed about it", r.stdout.strip(), "")
        check("the file is untouched", (brain / "session.json").read_text(), template)
        check_true("and no backup was made",
                   not (brain / "session.json.before-upgrade").exists())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_broken_session_is_not_destroyed() -> None:
    """An unreadable session must be reported, never overwritten."""
    tmp = Path(tempfile.mkdtemp(prefix="osp-upgrade-"))
    try:
        brain = tmp / ".brain"
        brain.mkdir()
        (brain / "session.json").write_text("{ this is not json")
        r = _run_migrate(tmp, "--apply")
        check("a corrupt session exits 2 rather than rewriting", r.returncode, 2)
        check("and is left exactly as it was",
              (brain / "session.json").read_text(), "{ this is not json")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


TESTS = [
    ("version comparison", test_version_comparison),
    ("migration is additive", test_migration_is_additive),
    ("a current session is left alone", test_a_current_session_is_left_alone),
    ("a broken session is not destroyed", test_broken_session_is_not_destroyed),
]


def main() -> int:
    print("  ▸ installing over an older project\n")
    for name, fn in TESTS:
        try:
            fn()
            print(f"  ✓ {name}")
        except Exception as exc:  # noqa: BLE001
            _FAILURES.append(f"  - {name}: {type(exc).__name__}: {exc}")
            print(f"  ❌ {name}: {type(exc).__name__}: {exc}")
    if _FAILURES:
        print(f"\n❌ {len(_FAILURES)} of {_CHECKS} upgrade checks failed:\n")
        print("\n".join(_FAILURES))
        return 1
    print(f"\n  ✅ All {_CHECKS} upgrade checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
