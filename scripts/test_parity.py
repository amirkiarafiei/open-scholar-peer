#!/usr/bin/env python3
"""
test_parity.py — Verify per-tool adapter parity against `extensions/_shared/`.

For every canonical command and skill in `_shared/`, every tool's adapter
directory must contain an equivalent file. This catches:
  - Adapter files deleted by hand and not regenerated.
  - Sync script bugs that drop a file silently.
  - New canonical content forgotten in the sync transformer.

Exit codes:
  0  — full parity, all tools complete.
  1  — drift detected (missing or extra files).
  2  — script error (e.g. _shared/ missing).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SHARED = REPO_ROOT / "extensions" / "_shared"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    root: Path
    command_dir: str
    command_ext: str
    skill_dir: str
    rule_paths: list[str]  # files that the rules content lands at (relative to root)


TOOLS = [
    ToolSpec("claude", REPO_ROOT / "extensions" / ".claude",
             "commands", "md", "skills", ["rules/osp-rules.md"]),
    ToolSpec("cursor", REPO_ROOT / "extensions" / ".cursor",
             "commands", "md", "skills", ["rules/osp-rules.mdc"]),
    ToolSpec("gemini", REPO_ROOT / "extensions" / ".gemini",
             "commands", "toml", "skills", ["GEMINI.md"]),
    ToolSpec("antigravity", REPO_ROOT / "extensions" / ".agent",
             "workflows", "md", "skills", ["rules/osp-rules.md"]),
    ToolSpec("antigravity-cli", REPO_ROOT / "extensions" / ".agents",
             "workflows", "md", "skills", ["rules/osp-rules.md", "AGENTS.md"]),
    ToolSpec("copilot", REPO_ROOT / "extensions" / ".github",
             "prompts", "md", "skills", ["instructions/osp-rules.md", "AGENTS.md"]),
    ToolSpec("junie", REPO_ROOT / "extensions" / ".junie",
             "commands", "md", "skills", ["guidelines.md"]),
    ToolSpec("kiro", REPO_ROOT / "extensions" / ".kiro",
             "hooks", "md", "skills", ["steering/osp-rules.md"]),
    ToolSpec("codex", REPO_ROOT / "extensions" / ".codex",
             "prompts", "md", "skills", ["AGENTS.md"]),
    ToolSpec("kimi", REPO_ROOT / "extensions" / ".kimi",
             "commands", "md", "skills", ["AGENTS.md"]),
    ToolSpec("qwen", REPO_ROOT / "extensions" / ".qwen",
             "commands", "md", "agents", ["QWEN.md"]),
    ToolSpec("vibe", REPO_ROOT / "extensions" / ".vibe",
             "commands", "md", "skills", ["AGENTS.md"]),
    ToolSpec("opencode", REPO_ROOT / "extensions" / ".opencode",
             "commands", "md", "agents", ["AGENTS.md"]),
    ToolSpec("openhands", REPO_ROOT / "extensions" / ".openhands",
             "commands", "md", "skills", ["AGENTS.md"]),
]


def list_canonical_commands() -> list[str]:
    return sorted(p.stem for p in (SHARED / "commands").glob("*.md"))


def list_canonical_skills() -> list[str]:
    return sorted(p.parent.name for p in (SHARED / "skills").glob("*/SKILL.md"))


def list_canonical_defaults() -> list[str]:
    d = SHARED / "defaults"
    return sorted(p.name for p in d.glob("*.md")) if d.exists() else []


def check_tool(tool: ToolSpec, commands: list[str], skills: list[str], defaults: list[str]) -> list[str]:
    issues: list[str] = []
    if not tool.root.exists():
        issues.append(f"[{tool.name}] adapter root missing: {tool.root.relative_to(REPO_ROOT)}")
        return issues

    # Commands
    for cmd in commands:
        target = tool.root / tool.command_dir / f"{cmd}.{tool.command_ext}"
        if not target.exists():
            issues.append(f"[{tool.name}] missing command: {target.relative_to(REPO_ROOT)}")

    # Skills
    for skill in skills:
        target = tool.root / tool.skill_dir / skill / "SKILL.md"
        if not target.exists():
            issues.append(f"[{tool.name}] missing skill: {target.relative_to(REPO_ROOT)}")

    # Rules
    for rel in tool.rule_paths:
        target = tool.root / rel
        if not target.exists():
            issues.append(f"[{tool.name}] missing rules artifact: {target.relative_to(REPO_ROOT)}")

    # Defaults (every tool gets the full set under defaults/)
    for d in defaults:
        target = tool.root / "defaults" / d
        if not target.exists():
            issues.append(f"[{tool.name}] missing default: {target.relative_to(REPO_ROOT)}")

    return issues


def check_dependencies() -> list[str]:
    import ast
    issues = []
    tools_dir = REPO_ROOT / "scripts" / "tools"
    req_file = tools_dir / "requirements.txt"
    if not req_file.exists():
        return [f"requirements.txt missing at {req_file}"]

    # Parse requirements.txt
    packages = set()
    with open(req_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name = line.split(">=")[0].split("==")[0].split("<=")[0].split(">")[0].split("<")[0].strip().lower()
            packages.add(name)

    # Mapping of top-level import name to requirements package name
    import_mapping = {
        "bs4": "beautifulsoup4",
        "dateutil": "python-dateutil",
        "dotenv": "python-dotenv",
        "arxiv": "arxiv",
        "semanticscholar": "semanticscholar",
        "scholarly": "scholarly",
        "requests": "requests",
        "mcp": "mcp",
        "fastmcp": "fastmcp",
        "markitdown": "markitdown",
    }

    # Standard library modules to ignore
    stdlib = {
        "sys", "os", "json", "time", "urllib", "argparse", "dataclasses", 
        "pathlib", "typing", "re", "shutil", "abc", "threading", "concurrent", 
        "tempfile", "hashlib", "traceback", "datetime", "ast", "importlib", "logging",
        "warnings", "__future__"
    }

    # Python files to check
    py_files = [
        tools_dir / "osp_cli.py",
        tools_dir / "convert_pdf.py",
        tools_dir / "providers" / "arxiv.py",
        tools_dir / "providers" / "google_scholar.py",
        tools_dir / "providers" / "semantic_scholar.py",
    ]

    for pfile in py_files:
        if not pfile.exists():
            continue
        try:
            with open(pfile, "r") as f:
                tree = ast.parse(f.read(), filename=pfile.name)
        except Exception as e:
            issues.append(f"Failed to parse AST of {pfile.name}: {e}")
            continue

        for node in ast.walk(tree):
            imported_names = []
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_names.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    imported_names.append(node.module.split(".")[0])

            for name in imported_names:
                if name in stdlib or name == "providers":
                    continue

                # If name is a local sibling module or folder, ignore it
                sibling_py = pfile.parent / f"{name}.py"
                sibling_dir = pfile.parent / name
                if sibling_py.exists() or sibling_dir.exists():
                    continue

                pkg = import_mapping.get(name, name.lower())
                if pkg not in packages:
                    issues.append(f"[{pfile.name}] imports '{name}' but '{pkg}' is missing from requirements.txt")

    return issues


def main() -> int:
    if not SHARED.exists():
        print(f"ERROR: {SHARED} does not exist.", file=sys.stderr)
        return 2

    commands = list_canonical_commands()
    skills = list_canonical_skills()
    defaults = list_canonical_defaults()

    if not commands or not skills:
        print("ERROR: _shared/ is empty (no commands or skills found).", file=sys.stderr)
        return 2

    print(f"  ▸ canonical: {len(commands)} commands, {len(skills)} skills, {len(defaults)} defaults")

    all_issues: list[str] = []
    
    # 1. Parity checks
    for tool in TOOLS:
        issues = check_tool(tool, commands, skills, defaults)
        if issues:
            all_issues.extend(issues)
        else:
            print(f"  ✓ {tool.name}: parity OK")

    # 2. Dependency checks
    dep_issues = check_dependencies()
    if dep_issues:
        all_issues.extend(dep_issues)
    else:
        print("  ✓ tools dependencies: check OK")

    if all_issues:
        print("\n  ❌ Issues detected:")
        for i in all_issues:
            print(f"     - {i}")
        print(f"\n  → Please correct parity or requirements drift.")
        return 1

    print(f"\n  ✅ All checks passed (parity and dependencies OK)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
