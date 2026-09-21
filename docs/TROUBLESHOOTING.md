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

## MCP server issues

### `osp` MCP server appears "disconnected" in the AI tool

Try running it manually to surface errors:
```bash
.open-scholar-peer/mcp/.venv/bin/python .open-scholar-peer/mcp/osp_mcp.py
```
The server runs on stdio and stays open waiting for MCP protocol messages. If it exits immediately with a Python traceback, that's the bug.

### `markitdown` MCP not converting PDFs

`markitdown-mcp` is registered as `{"command": "uvx", "args": ["markitdown-mcp"]}`. Verify `uvx` works:
```bash
uvx --version          # uv 0.4+ required
uvx markitdown-mcp --help   # should print usage. Without --help it starts the MCP
                            # server and waits silently — that is not a hang, Ctrl-C it.
```
If `uvx` is not installed:
```bash
pipx install uv
# or
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Semantic Scholar returns 429 Too Many Requests

Anonymous access is one pool shared by every unauthenticated caller everywhere, so it is throttled unpredictably. Get a free API key (https://www.semanticscholar.org/product/api#api-key) and put it in `.env` at your project root:
```bash
SEMANTIC_SCHOLAR_API_KEY=sk-...
```
The MCP server reads `.env` on startup, so restart your AI tool to pick it up. The tool reports this failure with `reason: rate_limited` — it is not an empty result, and should not be recorded as "no papers found".

### `osp` server starts but tools return errors

Each tool has a consistent error envelope carrying a `reason`, which tells you what to do:

| `reason` | What it means | What to do |
|---|---|---|
| `blocked` | Google refused — 429, 403 or a captcha page | Set `GOOGLE_SCHOLAR_PROXY_URL`, or drop Google Scholar. Waiting rarely helps; the block is on your address. |
| `rate_limited` | Semantic Scholar answered 429 | Set `SEMANTIC_SCHOLAR_API_KEY` in `.env`. |
| `busy` | another arXiv call held the one connection its terms allow | Transient. Retry. |
| `timeout` | the call ran past `OSP_CALL_TIMEOUT` | Raise it in `.env`, or check the network. |
| `not_found` | no such paper or article | Check the identifier. The provider is fine. |
| `bad_request` | the arguments were wrong | Read the tool's docstring. |

An empty list `[]` is not an error. It means the search ran and matched nothing.

Also check network connectivity: `curl https://api.semanticscholar.org/graph/v1/paper/search?query=test`

### A tool I expected is missing

Tools are registered per database, and the installer asked which you wanted. Check `OSP_SOURCES` in `.env` at your project root — remove the line to enable all six databases, or add the one you want:

```bash
OSP_SOURCES=arxiv,semantic_scholar,google_scholar,europepmc,zenodo,openalex
```

Restart your AI tool afterwards. The server logs which databases are on at startup.

---

## Workflow issues

### `/0-osp-onboarding` cannot find the paper

Tell it where the paper is — any path will do, and it copies the file into `.brain/input/` for you. It
also looks in the project root on its own, so putting the paper beside `.brain/` is enough.

### `/1-osp-summary` stops with "binary format and markitdown unavailable"

Working as intended. A readable paper is the one input the protocol cannot work around, and this is one
of only two places in OSP that stop. Either install markitdown (see above), or convert the paper
yourself and save it as `.brain/input/paper.md`.

### Fewer than three literature rounds

Normal, and probably your own choice. `/2-osp-literature` runs one round per invocation and asks after
each whether to continue. Stopping at one or two completes the phase with a smaller corpus — the
consolidated `02_retrieved_literature.md` is still written. Run `/2-osp-literature` again for the next
round; it never repeats one you already have. Check `phases.literature.rounds_completed` in
`.brain/session.json` to see where you stopped.

### Fewer than ten Q&A pairs per criterion

Also normal. The default is **two**, and `/5-osp-qa` asks before it starts. The paper this implements
used ten probing questions in total across a whole review, not ten per criterion. Your answer is stored
in `session.json` as `qa_pairs_per_criterion`.

On Mistral Vibe and OpenHands, pair generation runs in self-reflection mode — sequential and slower.

### A phase ran but the result looks thin

Check the closing block for a `BLOCKED` line: that means a search provider failed and nothing was
searched, which is not the same as finding nothing. Check `NOTE` for phases you skipped. Both also
appear in the artifact's `## Provenance`, and `/6-osp-review` collects them under
`## What this review did not have`.

### `/open-scholar-peer` says "No `.brain/session.json`"

OSP is not initialised in this directory. Re-run the installer from here — it merges with your existing
config rather than replacing it:

```bash
curl -sSL https://raw.githubusercontent.com/amirkiarafiei/open-scholar-peer/main/install.sh | bash
```

If `.brain/` exists but `session.json` does not, ask your agent to recreate it from the v2 schema in
`docs/BRAIN_LAYOUT.md` and carry on.

### Re-ran an early phase and the final review feels stale

OSP does not invalidate downstream artifacts (`KNOWN_LIMITATIONS.md` §8). Re-run the phases after it in
order, or run `/open-scholar-peer` and follow what it recommends.

### I want to change which databases are searched

Edit `OSP_SOURCES` in `.env` at your project root, then restart your agent. Remove the line entirely to
enable every installed source. Pick by your paper's field, not by speed: Europe PMC for life sciences,
arXiv for CS, physics and maths.

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
