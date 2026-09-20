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


def _display_width(s: str) -> int:
    """Columns a terminal gives this string. `─` and `●` are one column, three bytes."""
    import unicodedata
    return sum(
        0 if (unicodedata.combining(c) or c == "\ufe0f")
        else (2 if unicodedata.east_asian_width(c) in "WF" else 1)
        for c in s
    )


def check_phase_blocks() -> list[str]:
    """The phase block has exactly one definition. Guard its shape so it cannot drift back.

    M16 replaced seven hand-written closing blocks with one template. The thing that let them
    drift in the first place was that nothing checked them, so this does.
    """
    import re

    tmpl = SHARED / "defaults" / "phase_block_template.md"
    if not tmpl.exists():
        return ["defaults/phase_block_template.md is missing — the phase block has no definition"]

    issues: list[str] = []
    text = tmpl.read_text(encoding="utf-8")

    # Only the template may carry a rendered rail; everywhere else supplies values.
    rail_re = re.compile(r"──\s*[●◐○]")
    for f in sorted(SHARED.rglob("*.md")):
        if f == tmpl:
            continue
        if rail_re.search(f.read_text(encoding="utf-8")):
            issues.append(
                f"{f.relative_to(SHARED)} renders a rail. Only defaults/phase_block_template.md may — "
                f"everything else gives values, or the design drifts again."
            )

    # Inside the template: rules exactly 60 columns, nothing past 72, 7 markers, value column at 12.
    inside, block, start = False, [], 0
    blocks = 0
    for n, line in enumerate(text.split("\n"), 1):
        if line.strip().startswith("```"):
            if inside and block and block[0].startswith("──"):
                blocks += 1
                top, bottom = block[0], block[-1]
                if _display_width(top) != 60:
                    issues.append(f"phase_block_template.md:{start}: top rule is {_display_width(top)} columns, not 60")
                if _display_width(bottom) != 60:
                    issues.append(f"phase_block_template.md:{start}: bottom rule is {_display_width(bottom)} columns, not 60")
                marks = [c for c in top if c in "●◐○"]
                if len(marks) != 7:
                    issues.append(f"phase_block_template.md:{start}: rail has {len(marks)} markers, not 7 (one per phase)")
                for k, b in enumerate(block):
                    if _display_width(b) > 72:
                        issues.append(f"phase_block_template.md:{start + k}: {_display_width(b)} columns, over the 72 cap")
                    if b.startswith("  ") and not b.startswith("   ") and len(b) > 11 and b[10] != " ":
                        issues.append(f"phase_block_template.md:{start + k}: value column is not at 12")
            block, inside, start = [], not inside, n + 1
            continue
        if inside:
            block.append(line)

    if blocks < 2:
        issues.append(f"phase_block_template.md shows {blocks} example block(s); it needs an opening and a closing one")
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
    for tool in TOOLS:
        issues = check_tool(tool, commands, skills, defaults)
        if issues:
            all_issues.extend(issues)
        else:
            print(f"  ✓ {tool.name}: parity OK")

    block_issues = check_phase_blocks()
    if block_issues:
        all_issues.extend(block_issues)
    else:
        print("  ✓ phase block: one definition, 60-column rules, 7 markers")

    if all_issues:
        print("\n  ❌ Drift detected:")
        for i in all_issues:
            print(f"     - {i}")
        print(f"\n  → Run `python3 scripts/sync_adapters.py` to regenerate.")
        return 1

    print(f"\n  ✅ All {len(TOOLS)} tools have full parity with _shared/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
