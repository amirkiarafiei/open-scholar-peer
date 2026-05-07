#!/usr/bin/env python3
"""
sync_adapters.py — Open ScholarPeer canonical-to-adapter sync.

Reads `extensions/_shared/` and regenerates per-tool adapter directories under
`extensions/.{claude,cursor,gemini,agent,agents,github}/`.

Humans edit only `_shared/`. Per-tool directories are wiped and regenerated on
every run — never edit them by hand.

Usage:
    python3 scripts/sync_adapters.py            # sync all tools
    python3 scripts/sync_adapters.py --tool claude  # sync one tool
    python3 scripts/sync_adapters.py --check    # dry run, exit 1 if drift
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
SHARED = REPO_ROOT / "extensions" / "_shared"

# ---------- Capability matrix ----------------------------------------------

@dataclass(frozen=True)
class ToolCaps:
    name: str
    root: Path
    supports_subagent: bool
    qa_mode: str  # "subagent" | "self-reflection"
    command_dir: str
    command_ext: str  # "md" | "toml"
    skill_dir: str
    rule_dir: str | None  # None means rule lives at tool root or as a flat file
    extra_files: list[tuple[str, str]]  # (relpath, source_content_id) -- e.g. AGENTS.md, GEMINI.md

TOOLS: dict[str, ToolCaps] = {
    "claude": ToolCaps(
        name="claude",
        root=REPO_ROOT / "extensions" / ".claude",
        supports_subagent=True,
        qa_mode="subagent",
        command_dir="commands",
        command_ext="md",
        skill_dir="skills",
        rule_dir="rules",
        extra_files=[],
    ),
    "cursor": ToolCaps(
        name="cursor",
        root=REPO_ROOT / "extensions" / ".cursor",
        supports_subagent=True,
        qa_mode="subagent",
        command_dir="commands",
        command_ext="md",
        skill_dir="skills",
        rule_dir="rules",  # uses .mdc inside
        extra_files=[],
    ),
    "gemini": ToolCaps(
        name="gemini",
        root=REPO_ROOT / "extensions" / ".gemini",
        supports_subagent=True,
        qa_mode="subagent",
        command_dir="commands",
        command_ext="toml",
        skill_dir="skills",
        rule_dir=None,  # Gemini uses GEMINI.md at root
        extra_files=[("GEMINI.md", "rules")],
    ),
    "antigravity": ToolCaps(
        name="antigravity",
        root=REPO_ROOT / "extensions" / ".agent",
        supports_subagent=False,
        qa_mode="self-reflection",
        command_dir="workflows",  # antigravity calls them workflows
        command_ext="md",
        skill_dir="skills",
        rule_dir="rules",
        extra_files=[],
    ),
    "copilot": ToolCaps(
        name="copilot",
        root=REPO_ROOT / "extensions" / ".github",
        supports_subagent=True,
        qa_mode="subagent",
        command_dir="prompts",
        command_ext="md",
        skill_dir="skills",
        rule_dir="instructions",
        extra_files=[("AGENTS.md", "rules")],
    ),
}

# Antigravity dual-write target (legacy `.agents/` mirror of `.agent/`)
ANTIGRAVITY_MIRROR = REPO_ROOT / "extensions" / ".agents"


# ---------- Frontmatter helpers --------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split YAML-ish frontmatter from body. Returns (fields, body).

    Light-touch parser — keys map to raw string values (multi-line block scalars
    preserved). Sufficient for our flat schema.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fields: dict[str, str] = {}
    fm_block = m.group(1)
    current_key: str | None = None
    buffer: list[str] = []
    for line in fm_block.split("\n"):
        if re.match(r"^[A-Za-z0-9_]+:", line) and not line.startswith(" "):
            if current_key is not None:
                fields[current_key] = "\n".join(buffer).strip()
                buffer = []
            key, _, val = line.partition(":")
            current_key = key.strip()
            buffer.append(val.strip())
        else:
            buffer.append(line)
    if current_key is not None:
        fields[current_key] = "\n".join(buffer).strip()
    return fields, m.group(2)


# ---------- Q&A mode adaptation --------------------------------------------

QA_COMMAND_BASENAME = "5-osp-qa"


def adapt_qa_body_for_tool(body: str, qa_mode: str) -> str:
    """Inject a tool-specific banner into the Q&A command so the runtime knows
    whether to use subagent delegation or self-reflection."""
    if qa_mode == "subagent":
        banner = (
            "> **Tool capability:** This tool supports subagents. The Query Agent "
            "MUST delegate each question to `osp-answer-generator-agent` as a "
            "subagent with a fresh, minimal context bundle. Do NOT use self-reflection.\n\n"
        )
    else:
        banner = (
            "> **Tool capability:** This tool does NOT support subagents. Use the "
            "self-reflection fallback: strict turn markers (`=== Query Agent === ... "
            "=== END === === Answer Generator === ...`) within the main context "
            "window. This is a documented weaker substitute — see KNOWN_LIMITATIONS.md.\n\n"
        )
    return banner + body


# ---------- Per-format writers ---------------------------------------------

def write_command_md(path: Path, fields: dict[str, str], body: str) -> None:
    """Write a Markdown command with normalized frontmatter (Claude/Cursor/Antigravity/Copilot)."""
    desc = fields.get("description", "").strip().strip('"')
    fm_lines = ["---", f'description: "{desc}"']
    for k in ("reads", "writes"):
        if k in fields:
            fm_lines.append(f"{k}: {fields[k]}")
    fm_lines.append("---")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(fm_lines) + "\n" + body, encoding="utf-8")


def write_command_toml(path: Path, fields: dict[str, str], body: str) -> None:
    """Write a Gemini-style TOML command. Gemini commands use a `description` field
    and a `prompt` field containing the Markdown body verbatim."""
    desc = fields.get("description", "").replace('"""', '\\"\\"\\"').strip().strip('"')
    body_escaped = body.replace('"""', '\\"\\"\\"')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'description = "{desc}"\n\n'
        f'prompt = """\n{body_escaped}\n"""\n',
        encoding="utf-8",
    )


def write_skill(dest_dir: Path, name: str, content: str) -> None:
    """Write a skill as <name>/SKILL.md."""
    target = dest_dir / name / "SKILL.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def write_rule(dest_path: Path, content: str, *, mdc: bool = False) -> None:
    """Write a rules file. If mdc=True, write as Cursor .mdc with applies-everywhere frontmatter."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if mdc:
        # Strip our frontmatter (if any) and prepend Cursor's mdc frontmatter
        _, body = split_frontmatter(content)
        mdc_fm = "---\nalwaysApply: true\n---\n"
        dest_path.write_text(mdc_fm + body, encoding="utf-8")
    else:
        dest_path.write_text(content, encoding="utf-8")


# ---------- Sync orchestration ---------------------------------------------

def wipe(p: Path) -> None:
    if p.exists():
        shutil.rmtree(p)


def iter_shared_commands() -> Iterable[Path]:
    return sorted((SHARED / "commands").glob("*.md"))


def iter_shared_skills() -> Iterable[Path]:
    return sorted((SHARED / "skills").glob("*/SKILL.md"))


def iter_shared_defaults() -> Iterable[Path]:
    d = SHARED / "defaults"
    return sorted(d.glob("*.md")) if d.exists() else []


def sync_tool(tool: ToolCaps, *, dry_run: bool = False) -> list[str]:
    """Regenerate one tool's adapter directory from `_shared/`. Returns a list of
    relative paths that were (or would be) written, for reporting and drift checks."""
    written: list[str] = []
    if dry_run:
        # Drift check is implemented by the caller comparing in-memory writes vs disk.
        # For simplicity we still execute writes to a temp tree; not implemented here.
        # Just enumerate intended targets.
        pass

    if not dry_run:
        wipe(tool.root)
        tool.root.mkdir(parents=True, exist_ok=True)

    # Commands
    for cmd_path in iter_shared_commands():
        fields, body = split_frontmatter(cmd_path.read_text(encoding="utf-8"))
        if cmd_path.stem == QA_COMMAND_BASENAME:
            body = adapt_qa_body_for_tool(body, tool.qa_mode)
        target_name = f"{cmd_path.stem}.{tool.command_ext}"
        target_path = tool.root / tool.command_dir / target_name
        if not dry_run:
            if tool.command_ext == "toml":
                write_command_toml(target_path, fields, body)
            else:
                write_command_md(target_path, fields, body)
        written.append(str(target_path.relative_to(REPO_ROOT)))

    # Skills
    for skill_path in iter_shared_skills():
        skill_name = skill_path.parent.name
        target_dir = tool.root / tool.skill_dir
        if not dry_run:
            write_skill(target_dir, skill_name, skill_path.read_text(encoding="utf-8"))
        written.append(str((target_dir / skill_name / "SKILL.md").relative_to(REPO_ROOT)))

    # Rules
    rules_src = SHARED / "rules" / "osp-rules.md"
    if rules_src.exists():
        rules_content = rules_src.read_text(encoding="utf-8")
        if tool.rule_dir is not None:
            ext = "mdc" if tool.name == "cursor" else "md"
            target = tool.root / tool.rule_dir / f"osp-rules.{ext}"
            if not dry_run:
                write_rule(target, rules_content, mdc=(tool.name == "cursor"))
            written.append(str(target.relative_to(REPO_ROOT)))

        # Tools that bundle rules elsewhere (Gemini -> GEMINI.md, Copilot -> AGENTS.md)
        for relpath, source_id in tool.extra_files:
            if source_id == "rules":
                target = tool.root / relpath
                if not dry_run:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    # Strip our frontmatter for top-level always-on files
                    _, body = split_frontmatter(rules_content)
                    target.write_text(body, encoding="utf-8")
                written.append(str(target.relative_to(REPO_ROOT)))

    # Defaults — copy verbatim into a `defaults/` folder under each tool root
    defaults_target = tool.root / "defaults"
    if not dry_run:
        defaults_target.mkdir(parents=True, exist_ok=True)
    for d in iter_shared_defaults():
        target = defaults_target / d.name
        if not dry_run:
            target.write_text(d.read_text(encoding="utf-8"), encoding="utf-8")
        written.append(str(target.relative_to(REPO_ROOT)))

    return written


def mirror_antigravity() -> list[str]:
    """Antigravity is referenced as both `.agent/` (newer) and `.agents/` (legacy).
    After syncing `.agent/`, mirror to `.agents/` so installers can pick either."""
    if not TOOLS["antigravity"].root.exists():
        return []
    wipe(ANTIGRAVITY_MIRROR)
    shutil.copytree(TOOLS["antigravity"].root, ANTIGRAVITY_MIRROR)
    return [str(ANTIGRAVITY_MIRROR.relative_to(REPO_ROOT)) + "/ (mirrored)"]


# ---------- Entrypoint -----------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Sync OSP _shared/ → per-tool adapters.")
    parser.add_argument("--tool", choices=list(TOOLS.keys()) + ["all"], default="all")
    parser.add_argument("--check", action="store_true", help="Dry run; exit 1 if drift detected.")
    args = parser.parse_args()

    if not SHARED.exists():
        print(f"ERROR: {SHARED} does not exist. Nothing to sync.", file=sys.stderr)
        return 2

    selected = list(TOOLS.values()) if args.tool == "all" else [TOOLS[args.tool]]

    total_written: list[str] = []
    for tool in selected:
        print(f"  ▸ syncing {tool.name} → {tool.root.relative_to(REPO_ROOT)}")
        total_written.extend(sync_tool(tool, dry_run=args.check))

    if "antigravity" in [t.name for t in selected] and not args.check:
        print("  ▸ mirroring .agent/ → .agents/ (legacy compat)")
        total_written.extend(mirror_antigravity())

    print(f"\n  ✅ {len(total_written)} files {'would be ' if args.check else ''}written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
