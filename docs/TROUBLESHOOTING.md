# Troubleshooting — Open ScholarPeer

Common issues and how to fix them, organized by symptom.

---

## Install issues

### `python3: command not found`

OSP's MCP runtime needs Python 3.10+. Install via your OS package manager:
```bash
# Ubuntu/Debian
sudo apt install python3 python3-venv

# macOS (Homebrew)
brew install python@3.12
```

### `pip install` fails inside `.open-scholar-peer/mcp/`

Inspect the log:
```bash
.open-scholar-peer/mcp/.venv/bin/pip install -r .open-scholar-peer/mcp/requirements.txt
```
Common causes: outdated pip (`pip install --upgrade pip` in the venv), missing system libs for `lxml` or `cryptography` (on Ubuntu: `sudo apt install build-essential libxml2-dev libxslt1-dev libssl-dev`).

### Installer wrote files but the AI tool doesn't see commands

Reload the tool:
- **Claude Code:** restart or run `/help` to confirm commands appear.
- **Cursor:** reload window (Cmd+R / Ctrl+R).
- **Gemini CLI:** run `/commands reload`.
- **Copilot CLI:** restart the CLI session.
- **Antigravity:** type `/` in Agent chat to refresh.

If commands still don't appear, verify the adapter directory is in the right location:
```bash
ls .claude/commands/      # Claude
ls .cursor/commands/      # Cursor
ls .gemini/commands/      # Gemini (TOML)
ls .agents/workflows/     # Antigravity
ls .github/prompts/       # Copilot CLI
```

### Re-running the installer didn't pick up `_shared/` changes

The installer copies from `extensions/.{tool}/` (the synced adapter), not `_shared/`. Run the sync first:
```bash
python3 scripts/sync_adapters.py
bash install.sh   # or scripts/install_<tool>.sh
```

---

## CLI runtime issues

### `osp` CLI shim appears unreachable in the AI tool

Verify that the CLI shim exists and is runnable:
```bash
./.open-scholar-peer/osp --capabilities
```
If it prints a capabilities JSON manifest, the runner is correctly configured. If it exits with an error or a Python traceback, check:
- Is Python 3.10+ installed? Run `python3 --version`.
- Is there a virtualenv? Run `ls .open-scholar-peer/venv/bin/python`.
- If the traceback is about missing dependencies, try running the installer again: `bash install.sh`.

### PDF conversion fails with "binary format and conversion failed"

The conversion utilizes `uvx markitdown` or `python3 .open-scholar-peer/convert_pdf.py`. Verify `uvx` or `pip install markitdown` is functioning:
```bash
uvx --version          # uv 0.4+ required
uvx markitdown <pdf>   # should output markdown content
```
If `uv` is not installed, install it:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Alternatively, convert the paper manually to Markdown and place the text at `.brain/input/paper.md`.

### Semantic Scholar returns 429 Too Many Requests

Anonymous rate limits are tight. Get a free API key (https://www.semanticscholar.org/product/api#api-key) and add it to your `.env` file at the project root:
```env
SEMANTIC_SCHOLAR_API_KEY=sk-...
```
The CLI shim loads the `.env` file automatically on every search execution.

### CLI starts but returns errors

Look for JSON error envelopes in your tool's terminal logs. The CLI provides a structured error return value:
```json
{
  "error": "provider_error",
  "provider": "google_scholar",
  "message": "...",
  "guidance": "..."
}
```
Read the `"guidance"` field for actionable troubleshooting advice.

---

## Workflow issues

### `/0-osp-onboarding` says it can't find the paper

Run `/open-scholar-peer` — the orchestrator will detect you're at the onboarding step and ask you for the paper's path. You can provide any path; it will copy the file into `.brain/input/` for you.

### `/1-osp-summary` refuses with "binary format and conversion failed"

This is the hard input guard working correctly. Either:
1. Fix or install markitdown dependencies (see above).
2. Provide a markdown version manually:
   ```bash
   markitdown paper.pdf > .brain/input/paper.md   # if you have it CLI-locally
   ```

### `/2-osp-literature` produces only 1-2 round files instead of 3

The agent stopped early. Re-run `/2-osp-literature` — the structural file requirement (`02a/02b/02c_literature_round*.md`) is enforced, so missing files block consolidation. Check `.brain/raw/` to see how far it got.

### Q&A phase produces fewer than 10 pairs per criterion

The file template at `defaults/qa_pair_template.md` declares 10 placeholder slots. If the agent stopped early, re-run `/5-osp-qa`. On Antigravity (self-reflection mode), pair generation is sequential and slower — be patient.

### `/open-scholar-peer` says "No `.brain/session.json`"

Run the brain initializer:
```bash
bash scripts/init_brain.sh
```
This creates the v2 schema. Then re-run `/0-osp-onboarding`.

### Re-ran `/1-osp-summary` and now my final review feels stale

OSP does not auto-invalidate downstream artifacts (see `KNOWN_LIMITATIONS.md` §8). Re-run `/2-osp-literature` … `/6-osp-review` in order, or use `/open-scholar-peer` and follow its dispatcher.

---

## Sync / development issues

### `python3 scripts/sync_adapters.py` reports drift

Run with no arguments to regenerate:
```bash
python3 scripts/sync_adapters.py
python3 scripts/test_parity.py   # confirm
```

### My edits to `extensions/.claude/...` keep disappearing

Adapter directories are **generated**. Edit `extensions/_shared/` instead, then run the sync script. See `docs/CONTRIBUTING.md`.

### `bash scripts/test_install.sh` fails on one tool

Inspect the log:
```bash
cat /tmp/osp_install_<tool>.log
```
Most failures are missing `python3` or the smoke test running with stale adapters. Re-sync first:
```bash
python3 scripts/sync_adapters.py
bash scripts/test_install.sh
```

---

## Still stuck?

Open an issue at https://github.com/amirkiarafiei/open-scholar-peer/issues with:
- The slash command you ran
- The exact error message
- Your `.brain/session.json` (with any sensitive paper content redacted)
- The output of `python3 scripts/test_parity.py`
