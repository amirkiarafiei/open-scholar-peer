#!/usr/bin/env python3
"""
merge_mcp_config.py — Safely merge OSP MCP server entries into a tool's MCP config.

Each MCP-aware tool (Claude, Cursor, Gemini, Copilot CLI) stores its server list
in a JSON file with `mcpServers` (or similar) at root or under a settings key.
This script reads the existing file (creating it if missing), merges in the OSP
entries, and writes it back — preserving any unrelated user keys.

Usage:
    python3 merge_mcp_config.py <config_path> <python_path> <server_path> [--key mcpServers]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError as e:
        print(f"ERROR: {path} is not valid JSON: {e}", file=sys.stderr)
        sys.exit(2)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config_path")
    parser.add_argument("python_path", help="absolute path to .scholar-peer/mcp/.venv/bin/python")
    parser.add_argument("server_path", help="absolute path to .scholar-peer/mcp/osp_mcp.py")
    parser.add_argument("--key", default="mcpServers", help="root key under which servers live")
    args = parser.parse_args()

    cfg_path = Path(args.config_path)
    cfg = load_json(cfg_path)
    cfg.setdefault(args.key, {})

    cfg[args.key]["osp"] = {
        "command": args.python_path,
        "args": [args.server_path],
        "env": {
            # If user has SEMANTIC_SCHOLAR_API_KEY in env at runtime, the server
            # will pick it up; we don't bake it into config to avoid leaking.
        },
    }

    cfg[args.key]["markitdown"] = {
        "command": "uvx",
        "args": ["markitdown-mcp"],
    }

    write_json(cfg_path, cfg)
    print(f"  ✅ Merged osp + markitdown into {cfg_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
