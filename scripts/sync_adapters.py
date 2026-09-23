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
    qa_mode: str  # "subagent" | "prefer-subagent" | "self-reflection"
    command_dir: str
    command_ext: str  # "md" | "toml"
    skill_dir: str
    rule_dir: str | None  # None means rule lives at tool root or as a flat file
    extra_files: list[tuple[str, str]]  # (relpath, source_content_id) -- e.g. AGENTS.md, GEMINI.md

    # --- Added for the 2026-09 tool wave. Defaults keep the first 14 unchanged.

    # Some tools have no file-based slash commands at all: every skill simply
    # becomes a command (Hermes, OpenClaw), or the command mechanism has been
    # retired in favour of skills (Cline). For those, the 8 commands ship as
    # skill directories instead of as files under `command_dir`.
    commands_as_skills: bool = False

    # Where a tool keeps *subagent definitions*, when those are a different
    # thing from skills. Oh My Pi, Grok Build and Kilo Code all delegate to an
    # agent file and cannot dispatch a skill directly, so the personas have to
    # exist in both shapes for delegation to reach them.
    agent_dir: str | None = None

    # How the search layer reaches this tool. "mcp" is the norm; "cli" is for
    # a tool with no MCP client, which calls `osp_cli.py` through its shell.
    search_mode: str = "mcp"

    # The directory the INSTALLER copies this adapter into, as the user will
    # see it from their project root. Usually the adapter directory's own name,
    # but OpenClaw installs into the shared `.agents/`. Used to turn the
    # canonical `defaults/x.md` references into a path that actually resolves.
    # Set explicitly on every tool: it is NOT `root.name`, because `--check`
    # clones each tool with a temporary root, and OpenClaw installs into the
    # shared `.agents/` rather than its own adapter directory.
    install_dir: str | None = None

TOOLS: dict[str, ToolCaps] = {
    "claude": ToolCaps(
        name="claude",
        install_dir=".claude",
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
        install_dir=".cursor",
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
        install_dir=".gemini",
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
        install_dir=".agent",
        root=REPO_ROOT / "extensions" / ".agent",
        # Antigravity 2.0 ships an asynchronous subagent framework
        # (invoke_subagent, custom subagents under .agents/agents/<name>.md).
        # Unverified whether a persona *skill* is reachable through it, so the
        # Q&A banner asks it to try and degrade rather than insist. O11.
        supports_subagent=True,
        qa_mode="prefer-subagent",
        command_dir="workflows",  # antigravity calls them workflows
        command_ext="md",
        skill_dir="skills",
        rule_dir="rules",
        extra_files=[],
    ),
    "antigravity-cli": ToolCaps(
        name="antigravity-cli",
        install_dir=".agents",
        # Workflows are DEPRECATED and are no longer indexed as slash commands.
        # Verified against agy 1.2.9: eight files in `.agents/workflows/` gave a
        # `/skills` catalog of 8 — the personas only — and typing the command
        # name fell through to raw text, with the agent trying to run a shell
        # command by that name. The same eight emitted as skill directories give
        # a catalog of 16 and `/open-scholar-peer` activates. The binary's own
        # bundled `migrate-workflows` skill says so: skills provide everything
        # workflows did "plus first-class slash command support".
        commands_as_skills=True,
        root=REPO_ROOT / "extensions" / ".agents",
        supports_subagent=True,
        qa_mode="subagent",
        command_dir="workflows",
        command_ext="md",
        skill_dir="skills",
        rule_dir="rules",
        extra_files=[("AGENTS.md", "rules")],
    ),
    "copilot": ToolCaps(
        name="copilot",
        install_dir=".github",
        root=REPO_ROOT / "extensions" / ".github",
        supports_subagent=True,
        qa_mode="subagent",
        command_dir="prompts",
        command_ext="md",
        skill_dir="skills",
        rule_dir="instructions",
        extra_files=[("AGENTS.md", "rules")],
    ),
    "junie": ToolCaps(
        name="junie",
        install_dir=".junie",
        root=REPO_ROOT / "extensions" / ".junie",
        supports_subagent=True,
        qa_mode="subagent",
        command_dir="commands",
        command_ext="md",
        skill_dir="skills",
        rule_dir=None,
        extra_files=[("guidelines.md", "rules")],
    ),
    "kiro": ToolCaps(
        name="kiro",
        install_dir=".kiro",
        root=REPO_ROOT / "extensions" / ".kiro",
        supports_subagent=True,
        qa_mode="subagent",
        command_dir="hooks",
        command_ext="md",
        skill_dir="skills",
        rule_dir="steering",
        extra_files=[],
    ),
    "codex": ToolCaps(
        name="codex",
        install_dir=".codex",
        root=REPO_ROOT / "extensions" / ".codex",
        supports_subagent=True,
        qa_mode="subagent",
        command_dir="prompts",
        command_ext="md",
        skill_dir="skills",
        rule_dir=None,
        extra_files=[("AGENTS.md", "rules")],
    ),
    "kimi": ToolCaps(
        name="kimi",
        install_dir=".kimi",
        root=REPO_ROOT / "extensions" / ".kimi",
        supports_subagent=True,
        qa_mode="subagent",
        command_dir="commands",
        command_ext="md",
        skill_dir="skills",
        rule_dir=None,
        extra_files=[("AGENTS.md", "rules")],
    ),
    "qwen": ToolCaps(
        name="qwen",
        install_dir=".qwen",
        root=REPO_ROOT / "extensions" / ".qwen",
        supports_subagent=True,
        qa_mode="subagent",
        command_dir="commands",
        command_ext="md",
        skill_dir="agents",
        rule_dir=None,
        extra_files=[("QWEN.md", "rules")],
    ),
    "vibe": ToolCaps(
        name="vibe",
        install_dir=".vibe",
        root=REPO_ROOT / "extensions" / ".vibe",
        supports_subagent=False,
        qa_mode="self-reflection",
        command_dir="commands",
        command_ext="md",
        skill_dir="skills",
        rule_dir=None,
        extra_files=[("AGENTS.md", "rules")],
    ),
    "opencode": ToolCaps(
        name="opencode",
        install_dir=".opencode",
        root=REPO_ROOT / "extensions" / ".opencode",
        supports_subagent=True,
        qa_mode="subagent",
        command_dir="commands",
        command_ext="md",
        skill_dir="agents",
        rule_dir=None,
        extra_files=[("AGENTS.md", "rules")],
    ),
    "openhands": ToolCaps(
        name="openhands",
        install_dir=".openhands",
        root=REPO_ROOT / "extensions" / ".openhands",
        supports_subagent=False,
        qa_mode="self-reflection",
        command_dir="commands",
        command_ext="md",
        skill_dir="skills",
        rule_dir=None,
        extra_files=[("AGENTS.md", "rules")],
    ),
    "pi": ToolCaps(
        name="pi",
        install_dir=".pi",
        root=REPO_ROOT / "extensions" / ".pi",
        # "No sub-agents." and "No MCP." are both stated non-features, not gaps
        # waiting to be filled. Pi's answer to each is a CLI tool plus a skill,
        # so the search layer reaches it through osp_cli.py over bash.
        supports_subagent=False,
        qa_mode="self-reflection",
        command_dir="prompts",
        command_ext="md",
        skill_dir="skills",
        rule_dir=None,
        # AGENTS.md is the one thing Pi loads regardless of project trust, so
        # it is also the only place a rule is certain to arrive.
        extra_files=[("AGENTS.md", "rules")],
        search_mode="cli",
    ),
    "ohmypi": ToolCaps(
        name="ohmypi",
        install_dir=".omp",
        root=REPO_ROOT / "extensions" / ".omp",
        supports_subagent=True,
        qa_mode="subagent",
        command_dir="commands",
        command_ext="md",
        skill_dir="skills",
        rule_dir=None,
        # RULES.md is omp's sticky rule: carried in full on every request and
        # never demoted. A conditional rule under rules/ would not be.
        extra_files=[("RULES.md", "rules")],
        agent_dir="agents",
    ),
    "grok": ToolCaps(
        name="grok",
        install_dir=".grok",
        root=REPO_ROOT / "extensions" / ".grok",
        supports_subagent=True,
        qa_mode="subagent",
        command_dir="commands",
        command_ext="md",
        skill_dir="skills",
        # .grok/rules/*.md is always scanned — unlike the .claude and .cursor
        # compatibility directories, which a user can switch off.
        rule_dir="rules",
        extra_files=[],
        agent_dir="agents",
    ),
    "hermes": ToolCaps(
        name="hermes",
        install_dir=".hermes",
        root=REPO_ROOT / "extensions" / ".hermes",
        # delegate_task gives a child its own context, but cannot be pointed at
        # a skill — the persona has to travel in the delegation message. So the
        # Q&A engine is told to try delegation and fall back, not to insist.
        supports_subagent=True,
        qa_mode="prefer-subagent",
        command_dir="skills",
        command_ext="md",
        skill_dir="skills",
        rule_dir=None,
        # Hermes loads exactly ONE project context file, first match wins:
        # .hermes.md > AGENTS.override.md > AGENTS.md. Writing .hermes.md would
        # silently suppress the user's own AGENTS.md, so we merge into theirs.
        extra_files=[("AGENTS.md", "rules")],
        commands_as_skills=True,
    ),
    "cline": ToolCaps(
        name="cline",
        install_dir=".cline",
        root=REPO_ROOT / "extensions" / ".cline",
        # use_subagents is model-triggered, experimental, and explicitly cannot
        # reach MCP servers — which is most of what an OSP answer needs.
        # new_task resets the same thread rather than starting a second agent.
        supports_subagent=False,
        qa_mode="self-reflection",
        command_dir="skills",
        command_ext="md",
        skill_dir="skills",
        rule_dir="rules",
        extra_files=[],
        # Workflows still resolve in code but have been dropped from the docs,
        # and slash-command duty moved to skills. Build on the supported one.
        commands_as_skills=True,
    ),
    "kilo": ToolCaps(
        name="kilo",
        install_dir=".kilo",
        root=REPO_ROOT / "extensions" / ".kilo",
        supports_subagent=True,
        qa_mode="subagent",
        command_dir="commands",
        command_ext="md",
        skill_dir="skills",
        # .kilo/rules/ is NOT read unless it is listed in an `instructions`
        # key, so a rules file dropped there is a silent no-op. AGENTS.md is
        # read automatically and cannot be switched off.
        rule_dir=None,
        extra_files=[("AGENTS.md", "rules")],
        agent_dir="agents",
    ),
    "openclaw": ToolCaps(
        name="openclaw",
        install_dir=".agents",
        root=REPO_ROOT / "extensions" / ".openclaw",
        # Sub-agents are documented and user-invocable (sessions_spawn), but
        # whether a skill is reachable from one is not stated, so this gets the
        # same try-then-degrade treatment as Antigravity. O11.
        supports_subagent=True,
        qa_mode="prefer-subagent",
        command_dir="skills",
        command_ext="md",
        skill_dir="skills",
        rule_dir=None,
        extra_files=[("AGENTS.md", "rules")],
        commands_as_skills=True,
    ),
}




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


# ---------- Default-file references ----------------------------------------

_DEFAULTS_REF_RE = re.compile(r"`defaults/([A-Za-z0-9_\-]+\.md)`")


def resolve_defaults_refs(text: str, tool: "ToolCaps") -> str:
    """Point `defaults/x.md` at where the file will actually be.

    The canonical files under `_shared/` say `defaults/phase_block_template.md`,
    which is correct there and wrong everywhere else: the installer copies the
    adapter into `.claude/`, `.codex/`, `.agents/` and so on, so nothing ever
    lands at `<project>/defaults/`. An agent resolving that path from the
    project root finds nothing, and the file it was sent to read is the only
    definition of the phase block.

    Measured 2026-09-21: 26 such references across the canonical commands,
    skills and rules, dead on all 21 tools. The canonical source keeps the
    short form so it stays tool-agnostic; each adapter gets its own real path.
    """
    if not tool.install_dir:
        raise ValueError(
            f"{tool.name} has no install_dir, so `defaults/...` cannot be resolved. "
            "It must name the directory the installer writes into — deriving it from "
            "`root` is wrong, because --check clones tools with a temporary root."
        )
    return _DEFAULTS_REF_RE.sub(rf"`{tool.install_dir}/defaults/\1`", text)


# ---------- Q&A mode adaptation --------------------------------------------

QA_COMMAND_BASENAME = "5-osp-qa"


def adapt_qa_body_for_tool(body: str, qa_mode: str) -> str:
    """Inject a tool-specific banner into the Q&A command so the runtime knows
    whether to use subagent delegation or self-reflection.

    Three modes, not two. `prefer-subagent` exists for tools where the vendor
    documents a subagent framework but OSP has not been able to confirm that the
    persona skill is reachable through it — the banner asks the agent to try
    delegation and to fall back rather than fail. See BRAINSTORM D17 / O11.
    """
    if qa_mode == "subagent":
        banner = (
            "> **Tool capability:** This tool supports subagents. The Query Agent "
            "MUST delegate each question to `osp-answer-generator-agent` as a "
            "subagent with a fresh, minimal context bundle. Do NOT use self-reflection.\n\n"
        )
    elif qa_mode == "prefer-subagent":
        banner = (
            "> **Tool capability:** This tool documents a subagent framework, and "
            "subagent isolation is preferred here. Try it first: delegate each "
            "question to `osp-answer-generator-agent` as a subagent with a fresh, "
            "minimal context bundle.\n"
            ">\n"
            "> If delegation is unavailable in your session — the persona is not "
            "reachable as a subagent, the call errors, or the capability is simply "
            "absent — fall back to self-reflection with strict turn markers "
            "(`=== Query Agent === ... === END === === Answer Generator === ...`) "
            "in the main context window, and carry on. Do not stop the phase over "
            "it.\n"
            ">\n"
            "> Either way, record which one you used in the `## Method` section of "
            "each `05_qa_<slug>.md` (`Mode: subagent` or `Mode: self-reflection`), "
            "so the artifact says how the answers were actually produced.\n\n"
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


def write_command_as_skill(dest_dir: Path, name: str, fields: dict[str, str], body: str) -> None:
    """Write a command as a skill directory, for tools where skills *are* the
    slash commands (Hermes, OpenClaw) or where the command mechanism was
    retired in favour of them (Cline).

    Only `name` and `description` are emitted. All three tools require exactly
    those two and say nothing about the rest, and Cline additionally requires
    `name` to equal the directory name — so the directory name is the only
    thing that decides the command, and we do not invent frontmatter that no
    vendor documents.
    """
    desc = " ".join(fields.get("description", "").split()).strip().strip('"')
    content = f'---\nname: {name}\ndescription: "{desc}"\n---\n{body}'
    target = dest_dir / name / "SKILL.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


# A subagent definition is the same persona text, in the shape the tool's
# delegation machinery reads. Only Kilo Code asks for an extra key.
AGENT_EXTRA_FRONTMATTER: dict[str, str] = {
    "kilo": "mode: subagent",
}


def write_agent_definition(dest_dir: Path, tool_name: str, name: str, content: str) -> None:
    """Write a persona as a flat subagent definition, `<agent_dir>/<name>.md`.

    Oh My Pi, Grok Build and Kilo Code can all delegate to a named agent with
    its own context window, but none of them can dispatch a *skill* that way.
    Without this the Q&A engine would fall back to self-reflection on three
    tools that are perfectly capable of the real thing.
    """
    extra = AGENT_EXTRA_FRONTMATTER.get(tool_name)
    if extra:
        fields, body = split_frontmatter(content)
        keep = [f"{k}: {v}" for k, v in fields.items()]
        content = "---\n" + "\n".join(keep + [extra]) + "\n---\n" + body
    target = dest_dir / f"{name}.md"
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


def sync_tool(tool: ToolCaps) -> list[str]:
    """Regenerate one tool's adapter directory from `_shared/`. Returns a list of
    relative paths that were written (relative to the tool's root)."""
    written: list[str] = []

    wipe(tool.root)
    tool.root.mkdir(parents=True, exist_ok=True)

    # Commands
    for cmd_path in iter_shared_commands():
        fields, body = split_frontmatter(cmd_path.read_text(encoding="utf-8"))
        if cmd_path.stem == QA_COMMAND_BASENAME:
            body = adapt_qa_body_for_tool(body, tool.qa_mode)
        body = resolve_defaults_refs(body, tool)

        if tool.commands_as_skills:
            target_dir = tool.root / tool.skill_dir
            write_command_as_skill(target_dir, cmd_path.stem, fields, body)
            written.append(str((target_dir / cmd_path.stem / "SKILL.md").relative_to(tool.root)))
            continue

        target_name = f"{cmd_path.stem}.{tool.command_ext}"
        target_path = tool.root / tool.command_dir / target_name
        if tool.command_ext == "toml":
            write_command_toml(target_path, fields, body)
        else:
            write_command_md(target_path, fields, body)
        written.append(str(target_path.relative_to(tool.root)))

    # Skills
    for skill_path in iter_shared_skills():
        skill_name = skill_path.parent.name
        target_dir = tool.root / tool.skill_dir
        content = resolve_defaults_refs(skill_path.read_text(encoding="utf-8"), tool)
        write_skill(target_dir, skill_name, content)
        written.append(str((target_dir / skill_name / "SKILL.md").relative_to(tool.root)))

        # The same persona again, as a subagent definition, where delegation
        # reads a different file than skill discovery does.
        if tool.agent_dir:
            agent_target = tool.root / tool.agent_dir
            write_agent_definition(agent_target, tool.name, skill_name, content)
            written.append(str((agent_target / f"{skill_name}.md").relative_to(tool.root)))

    # Rules
    rules_src = SHARED / "rules" / "osp-rules.md"
    if rules_src.exists():
        rules_content = rules_src.read_text(encoding="utf-8")

        # A tool with no MCP client reaches the search layer through a program
        # instead. That instruction has to arrive in the always-on file, or the
        # agent has no way to know the tools exist at all.
        if tool.search_mode == "cli":
            cli_src = SHARED / "rules" / "search_via_cli.md"
            if cli_src.exists():
                rules_content = (
                    rules_content.rstrip("\n")
                    + "\n\n"
                    + cli_src.read_text(encoding="utf-8")
                )

        # Resolved AFTER the addendum is joined on, not before. Resolving first
        # rewrote only the base file, so a `defaults/...` pointer inside the
        # appended block shipped unresolved — dead on arrival, and invisible
        # because the two are one string by the time anything looks.
        rules_content = resolve_defaults_refs(rules_content, tool)

        if tool.rule_dir is not None:
            ext = "mdc" if tool.name == "cursor" else "md"
            target = tool.root / tool.rule_dir / f"osp-rules.{ext}"
            write_rule(target, rules_content, mdc=(tool.name == "cursor"))
            written.append(str(target.relative_to(tool.root)))

        # Tools that bundle rules elsewhere (Gemini -> GEMINI.md, Copilot -> AGENTS.md)
        for relpath, source_id in tool.extra_files:
            if source_id == "rules":
                target = tool.root / relpath
                target.parent.mkdir(parents=True, exist_ok=True)
                # Strip our frontmatter for top-level always-on files
                _, body = split_frontmatter(rules_content)
                target.write_text(body, encoding="utf-8")
                written.append(str(target.relative_to(tool.root)))

    # Defaults — copy verbatim into a `defaults/` folder under each tool root
    defaults_target = tool.root / "defaults"
    defaults_target.mkdir(parents=True, exist_ok=True)
    for d in iter_shared_defaults():
        target = defaults_target / d.name
        target.write_text(
            resolve_defaults_refs(d.read_text(encoding="utf-8"), tool), encoding="utf-8")
        written.append(str(target.relative_to(tool.root)))

    return written




# ---------- Drift check ----------------------------------------------------

def trees_equal(a: Path, b: Path) -> bool:
    """Recursively compare two directory trees for identical structure and bytes."""
    if a.is_file() and b.is_file():
        return a.read_bytes() == b.read_bytes()
    if a.is_dir() and b.is_dir():
        a_kids = {p.name for p in a.iterdir()}
        b_kids = {p.name for p in b.iterdir()}
        if a_kids != b_kids:
            return False
        return all(trees_equal(a / k, b / k) for k in a_kids)
    return False


def run_drift_check(selected: list[ToolCaps]) -> int:
    """Sync each selected tool to a temp tree and compare against the live adapter
    dir. Exit 0 = in sync; exit 1 = drift detected."""
    import dataclasses
    import tempfile

    drift: list[str] = []
    with tempfile.TemporaryDirectory(prefix="osp-check-") as tmpdir:
        tmp_root = Path(tmpdir)

        # Sync each selected tool to a tmp subdir
        for tool in selected:
            tmp_tool = dataclasses.replace(tool, root=tmp_root / tool.name)
            sync_tool(tmp_tool)

        # Compare
        for tool in selected:
            tmp_path = tmp_root / tool.name
            mark = "✓" if trees_equal(tool.root, tmp_path) else "✗"
            print(f"  {mark} {tool.name} ({tool.root.relative_to(REPO_ROOT)})")
            if mark == "✗":
                drift.append(tool.name)

    if drift:
        print(f"\n  ❌ Drift detected in: {', '.join(drift)}")
        print("  → Run `python3 scripts/sync_adapters.py` to regenerate.")
        return 1
    print(f"\n  ✅ All adapters in sync with _shared/")
    return 0


# ---------- Entrypoint -----------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Sync OSP _shared/ → per-tool adapters.")
    parser.add_argument("--tool", choices=list(TOOLS.keys()) + ["all"], default="all")
    parser.add_argument("--check", action="store_true",
                        help="Compare existing adapters to what would be generated; exit 1 on drift.")
    args = parser.parse_args()

    if not SHARED.exists():
        print(f"ERROR: {SHARED} does not exist. Nothing to sync.", file=sys.stderr)
        return 2

    selected = list(TOOLS.values()) if args.tool == "all" else [TOOLS[args.tool]]

    if args.check:
        return run_drift_check(selected)

    total_written: list[str] = []
    for tool in selected:
        print(f"  ▸ syncing {tool.name} → {tool.root.relative_to(REPO_ROOT)}")
        total_written.extend(sync_tool(tool))



    print(f"\n  ✅ {len(total_written)} files written.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
