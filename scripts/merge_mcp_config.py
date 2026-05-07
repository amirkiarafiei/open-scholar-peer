#!/usr/bin/env python3
"""
merge_mcp_config.py — Safely merge OSP MCP server entries into a tool's MCP config.

Each MCP-aware tool (Claude, Cursor, Gemini, Copilot CLI) stores its server list
in a JSON file with `mcpServers` (or similar) at root or under a settings key.
This script reads the existing file (creating it if missing), merges in the OSP
entries, and writes it back — preserving any unrelated user keys *and* any
hand-customized osp/markitdown entries the user may have added themselves.

Usage:
    python3 merge_mcp_config.py <config_path> <python_path> <server_path> [--key mcpServers]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Marker baked into our managed entries so we can recognize a prior OSP-managed
# write versus a user-customized entry sharing the same key. If a user removes
# this marker (e.g. by hand-editing), we leave their version alone.
MANAGED_MARKER = "_osp_managed"


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


def is_osp_managed(entry: object) -> bool:
    """True if this entry was previously written by us (carries our marker)."""
    return isinstance(entry, dict) and entry.get(MANAGED_MARKER) is True


def merge_entry(servers: dict, name: str, new_entry: dict) -> str:
    """Insert `new_entry` at `servers[name]`, but never clobber a user-customized
    entry sharing that key. Returns one of {"created", "updated", "preserved"}.
    """
    existing = servers.get(name)
    if existing is None:
        servers[name] = new_entry
        return "created"
    if is_osp_managed(existing):
        servers[name] = new_entry
        return "updated"
    # Foreign entry under our preferred name — do NOT overwrite.
    return "preserved"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config_path")
    parser.add_argument("python_path", help="absolute path to .scholar-peer/mcp/.venv/bin/python")
    parser.add_argument("server_path", help="absolute path to .scholar-peer/mcp/osp_mcp.py")
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

    osp_entry = {
        MANAGED_MARKER: True,
        "command": args.python_path,
        "args": [args.server_path],
        "env": {
            # If user has SEMANTIC_SCHOLAR_API_KEY in env at runtime, the server
            # picks it up; we don't bake it into config to avoid secret leakage.
        },
    }
    markitdown_entry = {
        MANAGED_MARKER: True,
        "command": "uvx",
        "args": ["markitdown-mcp"],
    }

    actions = {
        "osp": merge_entry(cfg[args.key], "osp", osp_entry),
        "markitdown": merge_entry(cfg[args.key], "markitdown", markitdown_entry),
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
