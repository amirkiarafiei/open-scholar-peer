#!/usr/bin/env python3
"""
merge_mcp_config.py — Safely merge OSP MCP server entries into a tool's MCP config.

Each MCP-aware tool (Claude, Cursor, Gemini, Copilot CLI) stores its server list
in a JSON file with `mcpServers` (or similar) at root or under a settings key.
This script reads the existing file (creating it if missing), merges in the OSP
entries, and writes it back — preserving any unrelated user keys *and* any
hand-customized osp/markitdown entries the user may have added themselves.

Managed-entry tracking: which entries we wrote is recorded in
`.open-scholar-peer/osp-managed-entries.json` alongside the project, NOT inside the
tool's own JSON (which would break strict validators like Gemini CLI).

Usage:
    python3 merge_mcp_config.py <config_path> <python_path> <server_path> [--key mcpServers]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Sidecar file that tracks which server entries in each config file were written
# by OSP.  Lives in .open-scholar-peer/ in the user's project (CWD at install time).
SIDECAR = Path(".open-scholar-peer/osp-managed-entries.json")


def load_json(path: Path) -> dict:
    """Load a JSON object from disk. Treats missing or whitespace-only files as `{}`.

    Hard-errors only on a file that is non-empty after stripping AND not valid JSON.
    """
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(
            f"ERROR: {path} is non-empty but not valid JSON: {e}\n"
            f"       Refusing to overwrite. Inspect the file, or back it up and retry.",
            file=sys.stderr,
        )
        sys.exit(2)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


# ---------- Sidecar helpers -------------------------------------------------

def _load_sidecar() -> dict:
    if not SIDECAR.exists():
        return {}
    raw = SIDECAR.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _save_sidecar(data: dict) -> None:
    SIDECAR.parent.mkdir(parents=True, exist_ok=True)
    SIDECAR.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _sidecar_key(config_path: Path) -> str:
    """Resolve the config path to its absolute, symlink-resolved form so the
    sidecar key is stable regardless of how the path was passed in (relative
    vs absolute, with or without `~`)."""
    try:
        return str(config_path.expanduser().resolve())
    except (OSError, RuntimeError):
        # resolve() can fail on broken symlinks; fall back to absolute form.
        return str(config_path.expanduser().absolute())


def _is_osp_managed(config_path: Path, key: str, entry_name: str) -> bool:
    """True if this entry was previously written by OSP (recorded in sidecar)."""
    sidecar = _load_sidecar()
    return entry_name in sidecar.get(_sidecar_key(config_path), {}).get(key, [])


def _mark_osp_managed(config_path: Path, key: str, entry_name: str) -> None:
    sidecar = _load_sidecar()
    cfg_str = _sidecar_key(config_path)
    sidecar.setdefault(cfg_str, {}).setdefault(key, [])
    if entry_name not in sidecar[cfg_str][key]:
        sidecar[cfg_str][key].append(entry_name)
    _save_sidecar(sidecar)


def _looks_like_osp_entry(entry: dict | None) -> bool:
    """Heuristic recognizer for entries written by an *earlier* OSP install,
    even one in a different project whose sidecar we cannot see.

    Without this, when User installs OSP in Project B after Project A, the
    global config (~/.kimi/mcp.json, ~/.copilot/mcp-config.json, etc.) still
    points at Project A's venv — and Project B's empty sidecar makes us
    "preserve" that stale entry. Then Project B's tool tries to launch
    Project A's interpreter, which may not exist anymore.

    The fix: if the existing entry's command or first arg points inside any
    `.open-scholar-peer/mcp/` directory, treat it as OSP-managed regardless
    of sidecar state, and replace with the current project's paths.
    """
    if not isinstance(entry, dict):
        return False
    needle = ".open-scholar-peer/mcp"
    cmd = entry.get("command", "")
    args = entry.get("args", []) or []
    if needle in str(cmd):
        return True
    return any(needle in str(a) for a in args)


# ---------- Merge logic -----------------------------------------------------

def merge_entry(
    servers: dict,
    name: str,
    new_entry: dict,
    config_path: Path,
    key: str,
) -> str:
    """Insert `new_entry` at `servers[name]`, but never clobber a user-customized
    entry sharing that key. Returns one of {"created", "updated", "preserved"}.
    """
    existing = servers.get(name)
    if existing is None:
        servers[name] = new_entry
        _mark_osp_managed(config_path, key, name)
        return "created"
    if _is_osp_managed(config_path, key, name) or _looks_like_osp_entry(existing):
        servers[name] = new_entry
        _mark_osp_managed(config_path, key, name)  # refresh sidecar in case it was lost
        return "updated"
    # Foreign entry under our preferred name — do NOT overwrite.
    return "preserved"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config_path")
    parser.add_argument("python_path", help="absolute path to .open-scholar-peer/mcp/.venv/bin/python")
    parser.add_argument("server_path", help="absolute path to .open-scholar-peer/mcp/osp_mcp.py")
    parser.add_argument("--key", default="mcpServers", help="root key under which servers live")
    args = parser.parse_args()

    cfg_path = Path(args.config_path)
    cfg = load_json(cfg_path)

    # Type-validate before mutating — we cannot safely merge into a non-dict shape.
    if not isinstance(cfg, dict):
        print(
            f"ERROR: {cfg_path} top-level is {type(cfg).__name__}, expected object/dict.\n"
            f"       Refusing to mutate. Back up and retry, or remove the file.",
            file=sys.stderr,
        )
        return 2

    cfg.setdefault(args.key, {})
    if not isinstance(cfg[args.key], dict):
        print(
            f"ERROR: {cfg_path} key '{args.key}' is {type(cfg[args.key]).__name__}, expected object/dict.\n"
            f"       Refusing to mutate. Inspect the file by hand.",
            file=sys.stderr,
        )
        return 2

    # Clean entries — no extra keys that strict JSON validators (e.g. Gemini) reject.
    # Both entries are kept structurally consistent (no dangling empty `env`).
    osp_entry = {
        "command": args.python_path,
        "args": [args.server_path],
    }
    markitdown_entry = {
        "command": "uvx",
        "args": ["markitdown-mcp"],
    }

    actions = {
        "osp": merge_entry(cfg[args.key], "osp", osp_entry, cfg_path, args.key),
        "markitdown": merge_entry(cfg[args.key], "markitdown", markitdown_entry, cfg_path, args.key),
    }

    write_json(cfg_path, cfg)

    summary = ", ".join(f"{k}: {v}" for k, v in actions.items())
    print(f"  ✅ Wrote {cfg_path} ({summary})")
    if "preserved" in actions.values():
        print(
            "  ℹ️  One or more entries were left untouched because they were not OSP-managed.\n"
            "     If you want OSP to manage them, remove or rename them and re-run."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
