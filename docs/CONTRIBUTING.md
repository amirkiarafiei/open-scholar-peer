# Contributing — Open ScholarPeer

Thanks for your interest. OSP is designed to be community-extensible. This guide covers the four most common contribution paths.

---

## The Golden Rule

**`extensions/_shared/` is the only place humans edit canonical content.** Per-tool adapter directories (`extensions/.claude/`, `.cursor/`, `.gemini/`, `.agent/`, `.agents/`, `.github/`, `.junie/`, `.kiro/`, `.codex/`, `.kimi/`, `.qwen/`, `.vibe/`, `.opencode/`, `.openhands/`) are **generated** by `scripts/sync_adapters.py`. If you edit them directly, your changes will be wiped on the next sync.

Workflow for any change to commands, skills, rules, or defaults:

```bash
# 1. Edit in _shared/
$EDITOR extensions/_shared/skills/osp-summary-agent/SKILL.md

# 2. Regenerate adapters
python3 scripts/sync_adapters.py

# 3. Verify parity
python3 scripts/test_parity.py

# 4. Smoke-test installers
bash scripts/test_install.sh
```

---

## Path 1: Modify or add a slash command

Slash commands live in `extensions/_shared/commands/<name>.md` with frontmatter:

```yaml
---
description: "One-line summary shown in command palettes"
reads: [".brain/session.json", ".brain/raw/01_structured_summary.md"]
writes: [".brain/raw/03_domain_narrative.md", ".brain/session.json"]
---
```

The `reads:` and `writes:` fields are part of the contract documented in `docs/ARTIFACT_CONTRACTS.md`. Update the contract doc when you change them.

### Adding a new numbered phase

1. Pick the next number (e.g. `7-osp-followup`) — be careful not to break existing ordering.
2. Create `commands/7-osp-followup.md` with full I/O contract.
3. Create the persona skill at `skills/osp-followup-agent/SKILL.md`.
4. Update `MANIFEST.md` and `docs/ARTIFACT_CONTRACTS.md`.
5. Update the orchestrator's routing table in `skills/osp-orchestrator/SKILL.md`.
6. Sync, parity-test, smoke-test.

---

## Path 2: Modify a persona skill

Persona skills live in `extensions/_shared/skills/<name>/SKILL.md` with frontmatter declaring `name:` and `description:` (the description is the trigger phrase for skill activation).

A persona skill must:

- State its single responsibility in 1-2 sentences at the top.
- List inputs (artifacts the calling command provides via `reads:`) and outputs (the single artifact the persona writes).
- Use the universal artifact structure for outputs: `## Method` / `## Output` / `## Provenance`.
- End with a "Pitfalls" section so future maintainers know what NOT to do.

When refining prompts, prefer adding to the Pitfalls section over expanding the "what to do" section. Prohibitions are easier for LLMs to follow than long affirmative instructions.

---

## Path 3: Add an MCP provider (e.g. PubMed, OpenAlex)

The MCP server at `mcp-server/osp_mcp.py` is intentionally modular. To add a new provider:

1. **Create the module** at `mcp-server/providers/<provider>.py` with plain Python functions:

   ```python
   # providers/pubmed.py
   def search(query: str, max_results: int = 10) -> list[dict]:
       """Search PubMed and return a list of paper records."""
       ...

   def get_paper(pmid: str) -> dict:
       """Fetch full record for a PMID."""
       ...
   ```

2. **Register the FastMCP wrappers** in `osp_mcp.py`:

   ```python
   from providers import pubmed as pubmed_provider

   @mcp.tool()
   async def search_pubmed(query: str, max_results: int = 10) -> list[dict[str, Any]]:
       """Search PubMed for biomedical literature.

       <Rich docstring — agents read this to decide when to call your tool.
        Include args, return shape, and use cases.>
       """
       try:
           return await asyncio.to_thread(pubmed_provider.search, query, max_results)
       except Exception as e:
           return [{"error": f"search_pubmed failed: {e}"}]
   ```

3. **Register it behind `@tool_for("<source>")`, not `@mcp.tool()`**, and add the source name to `_ALL_SOURCES` in `osp_mcp.py` and to the `DB_*` arrays in `install.sh`. A tool that cannot be switched off is a cost the agent pays on every request, whether or not the user wanted that database.

4. **Update `requirements.txt`** with any new dependencies, **with an upper bound**. An unbounded pin has broken this project twice: `arxiv>=2.1.0` resolved two majors up, and `mcp>=1.2.0` resolved to a version that had removed the import the server needs.

5. **Give failures their own exception type**, and never return `[]` for one. Map it to a `reason` in `_err()`.

6. **Add tests.** Offline checks for the pure logic in `scripts/test_providers_unit.py`, and a live check in `scripts/test_providers.py`. Nothing else in the repository loads `mcp-server/providers/`, so an untested provider is an unchecked one.

7. **Document the new tool** in `mcp-server/README.md`, and keep the tool list honest — it was once listing three tools that did not exist. If the provider takes an API key, document the env var and where to get one. **A key must never be required**; every source here answers without one (MANIFESTO rule 1).

8. **Update `osp-literature-review-agent` and related skills** to mention the new tool if it should be used in the 3-round retrieval. Re-sync. A tool nobody is told about changes nothing — and put it in the output *template*, not only the prose, because an agent fills the template it is given.

### Design constraints for new providers

- **Dumb tools only.** Each tool is atomic and stateless. No orchestration logic, no retries that hide failures. A transport-level cache (an HTTP client, parsed text for paging) is allowed, because it changes *when* an answer arrives and never *what* it is — anything that changes the answer is not.
- **Rich docstrings.** The MCP host shows the docstring to the LLM. Vague descriptions cause the agent to call the wrong tool.
- **Consistent error envelope.** Search-style tools return `[{"error": "...", "reason": "..."}]` on failure; single-record tools return `{"error": "...", "reason": "..."}`. **An empty list means the search ran and matched nothing — never use it to report a failure.** Getting this wrong is not cosmetic: a Google Scholar block returned `[]` for months, so the agent reported "no papers found" when the truth was "we were shut out".
- **No secrets in the registered config.** API keys are read from env vars at runtime, never written into `.mcp.json`. They belong in `.env`, which is gitignored and chmod 600.
- **Bound your own time.** `OSP_CALL_TIMEOUT` (90 s) cannot cancel a running thread, so a provider that hangs keeps working after the caller has given up. Cap your retries and your transfers from the inside, and pin the budget with a test.

---

## Path 4: Improve a tool transformer in the sync script

`scripts/sync_adapters.py` has a per-tool capability matrix. To improve a tool's adapter:

1. Edit the relevant `ToolCaps` entry at the top of the script. Note the existing fields:
   - `command_dir` — directory name where slash commands land.
   - `command_ext` — `md` or `toml` (Gemini uses TOML).
   - `skill_dir` — usually `skills/`.
   - `rule_dir` — None means rules go to a top-level file (e.g. Gemini's `GEMINI.md`).
   - `extra_files` — additional generated files (e.g. Copilot's `AGENTS.md`).

2. If your tool has unusual quirks (different file format, frontmatter), add a transformer function and wire it into `sync_tool()`.

3. Update `extensions/_shared/MANIFEST.md`'s "What gets generated where" table.

4. Update `scripts/test_parity.py` with the new tool spec so parity is enforced.

5. Sync, parity-test, smoke-test.

---

## Code style

- **Python:** Follow PEP 8. Type hints encouraged but not required for small helpers.
- **Bash:** Always `set -e`. Use `[[ ... ]]` (not `[ ... ]`). Quote all variable expansions.
- **Markdown:** No HTML. Use fenced code blocks with language tags.
- **Frontmatter:** Keep YAML frontmatter shallow (no nested objects); the sync script's parser is intentionally simple.

---

## Pull request checklist

Before submitting:

- [ ] Changes are made in `_shared/` (or `mcp-server/`, `scripts/`, `docs/`), never in per-tool adapter dirs.
- [ ] `python3 scripts/sync_adapters.py` runs cleanly.
- [ ] `python3 scripts/test_parity.py` passes.
- [ ] `bash scripts/test_install.sh` passes.
- [ ] If you added a command, skill, or default — `MANIFEST.md` and `ARTIFACT_CONTRACTS.md` are updated.
- [ ] If you added an MCP provider — `mcp-server/README.md` documents the new tool with rich docstrings.
- [ ] If user-visible behavior changed — `docs/KNOWN_LIMITATIONS.md` and/or `docs/TROUBLESHOOTING.md` are updated.
- [ ] PR description explains the WHY, not just the WHAT.

---

## Out of scope (please don't open PRs for these)

- **Plugin marketplace integrations** — the project's design philosophy is plain-files-and-installers, no marketplace dependency.
- **Hyperparameter exposure** (temperature, k, N_QA as runtime flags) — host tools don't expose these; structural file enforcement is the deliberate alternative.
- **Single-monolithic-server "do everything" MCP tools** — keep providers atomic.
- **Removing the `_shared/` → adapter sync pattern** — this is the project's drift mitigation strategy and is non-negotiable.

If you're not sure whether a contribution fits, open an issue first.
