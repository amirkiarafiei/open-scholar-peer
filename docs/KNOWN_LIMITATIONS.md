# Known Limitations — Open ScholarPeer v2

These are limitations users should know about going in. None block normal operation, but each affects the quality or smoothness of specific phases. Workarounds are listed.

---

## 1. Four tools fall back to self-reflection for the Q&A engine

**What:** The Multi-Aspect Q&A Engine (`/5-osp-qa`) is designed around true subagent isolation: the Query Agent (main thread) delegates each question to a fresh Answer Generator subagent so the verification cannot be biased by the question's reasoning trace.

**Limitation:** Four of the supported tools always use **self-reflection mode** instead, running both personas in one context window separated by strict turn markers (`=== Query Agent === ... === END === === Answer Generator === ...`):

| Tool | Why |
|---|---|
| **Mistral Vibe** | no subagent support |
| **OpenHands** | only profile-style independence; no documented delegation |
| **Pi** | subagents are a stated non-feature — *"No sub-agents."* |
| **Cline** | `use_subagents` is model-triggered, experimental, and cannot reach MCP servers, which is most of what an OSP answer needs; `new_task` resets the same thread rather than starting a second agent |

**Three tools try delegation and degrade if it fails.** Antigravity, Hermes and OpenClaw all document a
real subagent framework with its own context window, but none of them documents that a persona *skill*
is reachable through it. The Q&A command therefore tells them to attempt delegation and, if it is
unavailable, to fall back and finish the phase rather than stop. Check the `Mode:` line in each
`.brain/raw/05_qa_<slug>.md` to see which was actually used.

**Three tools needed the persona shipped twice.** Oh My Pi, Grok Build and Kilo Code delegate to a named
*agent definition*, and none of them can dispatch a skill that way. Each persona is therefore generated
both as a skill and as an agent file, so delegation reaches it by name. Without that they would have
fallen back to self-reflection despite being perfectly capable of the real thing.

**Impact:** Reviews on the Q&A axis from the four tools above are likely lower in independent-verification
depth than reviews from the other seventeen. The other phases (literature, historian, baseline scout,
reviewer) are unaffected.

**Workaround:** If you need full subagent isolation for a paper, use one of the fourteen where it
is confirmed — Claude Code, Cursor, Gemini CLI, Copilot CLI, Codex CLI, Qwen Code, OpenCode, Junie,
Kiro, Kimi Code, Antigravity CLI, Oh My Pi, Grok Build or Kilo Code. The three try-and-degrade tools
above may or may not manage it on any given run, which is why they are listed separately.

---

## 2. Semantic Scholar anonymous rate limits are aggressive

**What:** The `osp_mcp.search_semantic_scholar` and related tools use the official Semantic Scholar API. Anonymous access is not a per-user allowance — it is **one pool shared by every unauthenticated caller everywhere**, so how much you get depends on what strangers are doing. During testing on 2026-09-20 it stopped answering altogether for long stretches and refused connections outright.

**Impact:** During the 3-round literature retrieval (`/2-osp-literature`), an anonymous user may hit rate limits mid-round, causing partial corpora. The tool reports this as an error with `reason: rate_limited`, not as an empty result, so the agent records Semantic Scholar as unavailable rather than writing "no papers found".

**Workaround:** Get a free API key at https://www.semanticscholar.org/product/api#api-key. The installer offers to take it, or add it to `.env` yourself:

```bash
SEMANTIC_SCHOLAR_API_KEY=sk-...
```

A key gives you a documented 1 request per second of your own. Note this used to be a bad trade — before M11, one search issued 100-200 requests through auto-pagination, so a 1 rps key was slower than the shared pool. One search is now one request.

The MCP server reads the env var at startup. Add it to your shell profile to persist.

---

## 3. PDF parsing depends on the host tool's native Read or markitdown MCP

**What:** OSP needs a readable text version of the paper at `.brain/input/paper.md` for the Summary Agent. The `markitdown` MCP server is registered by the installer for this purpose.

**Limitation:** If `markitdown-mcp` is not installed (or `uvx` is not on PATH), and the paper is supplied as a PDF/DOCX, conversion will fail.

**Impact:** `/0-osp-onboarding` will refuse to advance until either (a) markitdown is installed, or (b) the user manually provides `.brain/input/paper.md`. This is intentional fail-fast behavior to avoid silent downstream errors.

**Workaround:** Install markitdown:
```bash
pipx install uv          # if not already installed
uvx markitdown-mcp --help   # fetchable? (without --help it starts the server and waits)
```
or convert manually:
```bash
markitdown paper.pdf > .brain/input/paper.md
```

---

## 4. Some MCP configs are global, not project-local

**What:** Every supported tool that has an MCP client has its server wired by the installer. Where that
config lands differs.

| | Tools | Where |
|---|---|---|
| **Project-local** | Claude Code, Cursor, Gemini CLI, Qwen Code, Junie, Kiro, OpenCode (`.opencode/opencode.json`), Mistral Vibe (`.vibe/config.toml`), Oh My Pi (`.omp/mcp.json`), Grok Build (`.grok/config.toml`), Kilo Code (`.kilo/kilo.json`) | a file inside your project |
| **Global** | Antigravity (`~/.gemini/antigravity/` **and** `~/.gemini/config/`), Antigravity CLI (`~/.gemini/antigravity-cli/`, plus a project-local copy), Copilot CLI (`~/.copilot/`), Kimi Code (`~/.kimi/`), Codex CLI (`~/.codex/config.toml`), OpenHands CLI (`~/.openhands/mcp.json`), Cline (`~/.cline/data/settings/cline_mcp_settings.json`), Hermes (`~/.hermes/config.yaml`), OpenClaw (registered with `openclaw mcp add`; OSP never writes its config file — see §10) | a file in your home directory |
| **No MCP at all** | Pi | not applicable — see §9 |

**Limitation:** The tools in the second row edit files shared by *every* project on your machine. The
installer preserves entries it did not write, but the blast radius is wider than one review.

**Impact:** For those tools the `osp` server is registered once globally rather than per project, so
installing OSP in a second directory re-points the same entry at the new directory's server copy. Both
folders still work one at a time; they just cannot be used simultaneously. Project-local tools have no
such problem.

**The OpenHands web UI is the one exception to "the installer wires it for you."** Its MCP settings
live in the application's database behind Settings → MCP, not in any file, so nothing OSP writes can
reach them. The installer leaves a ready-to-paste snippet at
`.open-scholar-peer/openhands_mcp_snippet.json` for that case. The OpenHands **CLI** is wired
automatically and needs nothing.

**Workaround:** After installing, open the file the installer named and confirm the `osp` entry points where you expect. If you have run OSP from a directory you later deleted, the global entry will point at a path that no longer exists — re-run the installer from a real project directory to repair it.

---

## 5. Single paper per `.brain/` (multi-paper sessions deferred)

**What:** v1 of OSP supports one active review per project directory.

**Limitation:** To review a second paper in the same project, you must archive or delete the existing `.brain/` and start fresh.

**Impact:** Researchers who maintain a directory of in-progress reviews must either use separate project directories or move `.brain/` aside between papers.

**Future:** Multi-paper sessions (`.brain/sessions/<paper_slug>/` with active-session pointer) are planned but deferred.

**Workaround:** Use one project directory per paper, or:
```bash
mv .brain .brain.archive-$(date +%F)
```

---

## 6. Google Scholar tools are best-effort (HTML scraping)

**What:** Google Scholar has no public API. The `osp_mcp.search_google_scholar` tools scrape HTML.

**Limitation:** Subject to Google's rate limits and HTML structure changes. Google blocks by **address**, not by client: on 2026-09-20, five requests eight seconds apart all returned HTTP 429, and four different User-Agent strings — plus none at all — produced byte-identical responses. Rotating the User-Agent achieves nothing. Later in the same session Google stopped answering entirely.

**Impact:** Small. The other five databases are unaffected, and Google Scholar adds breadth (blog posts, theses, workshop papers) rather than carrying the review. A block is now reported as an error with `reason: blocked` — it used to return an empty list, indistinguishable from a search that genuinely found nothing, which meant the agent wrote "no papers found" when the truth was "we were shut out".

**Workaround:** A proxy is the only thing that helps, because the block is on your address:

```bash
GOOGLE_SCHOLAR_PROXY_URL=http://user:pass@host:port
```

Or leave Google Scholar out at install time — the picker lets you. Retrying does not help and is not attempted: a refusal was measured to persist, and retrying it only spends the 90-second call budget that the other providers could have used.

---

## 7. Hyperparameters are structurally enforced, not numerically configurable

**What:** The paper specifies `k=3` literature rounds and `N_QA=10` probing pairs per criterion. OSP enforces `k=3` via file structure (3 separate round files). `N_QA` is **user-configurable** at the start of `/5-osp-qa` — the default is 2 pairs per criterion (lighter cost; the user can choose any N at runtime, and the template renders `### Q1`…`### QN` accordingly). The choice persists in `session.json.qa_pairs_per_criterion`.

**Limitation:** You cannot easily run "k=5 rounds" or "5 Q&A pairs per criterion" without editing the canonical templates in `extensions/_shared/defaults/`.

**Why this design:** Host tools (Claude Code, Cursor, etc.) do not expose temperature or other LLM hyperparameters to slash commands. Structural enforcement (file templates the agent must fill) is the only reliable way to ensure the count without the LLM hallucinating compliance.

**Workaround:** If you need different counts for research purposes, fork the templates in `_shared/defaults/` and re-run the sync script.

---

## 8. Re-running an earlier phase invalidates downstream artifacts

**What:** OSP commands are idempotent (re-running overwrites their own artifact with a warning), but they do **not** automatically invalidate downstream artifacts.

**Limitation:** If you re-run `/1-osp-summary` after the Q&A phase has already produced `05_qa_*.md` files, those Q&A files now reflect a stale structured summary.

**Impact:** Reviews can become inconsistent across the artifact chain.

**Workaround:** After re-running an earlier phase, manually re-run each subsequent phase, or run `/open-scholar-peer` and follow the dispatcher's guidance.

**Future:** Cascading invalidation (e.g. re-running `/1-osp-summary` resets `phases.qa` to `pending`) is on the roadmap.

---

## 9. Pi has no MCP client, so its searches run through a bundled program

**What:** Pi ships no MCP support and no web access. Its built-in tools are `read`, `bash`, `edit`,
`write`, `grep`, `find`, `ls`. Both omissions are deliberate — the author's words are *"No MCP. Build
CLI tools with READMEs (see Skills)"* — not gaps waiting to be filled.

**Limitation:** OSP's search layer cannot be registered with Pi as an MCP server. Instead the same 22
tools are exposed as a command-line program, `.open-scholar-peer/mcp/osp_cli.py`, and Pi's always-on
rules tell the agent to call it through `bash`. The tools, arguments, results and error envelope are
identical; only the calling convention differs.

**Impact:** Two practical differences. The agent must read a JSON result from standard output rather
than receive a structured tool response, which costs a little accuracy in argument handling; and it
sees the tool list only when it runs `osp_cli.py list`, rather than having it always in context.

**Also: project trust.** Pi ignores everything under `.pi/` — prompts, skills, settings — until you
accept the trust prompt for the folder, and `/trust` does not reload the running session. If the OSP
commands do not appear, start Pi in the project, accept trust, and restart it. `AGENTS.md` is the one
file Pi loads regardless of trust, which is why OSP's rules are installed there.

**Workaround:** None needed for the protocol itself; every phase runs. If you want structured tool
calls on Pi, a third-party MCP adapter exists, but OSP does not depend on it.

---

## 10. OpenClaw is one assistant per machine, not a per-project tool

**What:** OpenClaw runs a single long-lived Gateway per host with a configured *workspace* that acts as
its home. It is a chat-channel assistant that can drive coding agents, not a project-scoped CLI.

**Limitation:** Discovery does not walk up from a nested folder to a parent repository — the docs are
explicit that installing from a repository does not make that repository's `.agents/skills/` visible.
So OSP installs into the folder, and you tell OpenClaw to work there. The installer prints the options:
run it from the folder with `openclaw agent exec --cwd .`, or set that agent's `workspace`.

**Impact:** One extra step after installing, and reviewing two papers means two workspaces (or running
from each folder in turn) rather than two directories that just work.

**Why the installer does not do it for you:** repointing the workspace moves your whole assistant's
home, which is not an installer's decision. And OSP never writes `~/.openclaw/openclaw.json` directly:
OpenClaw accepts only a config that fully matches its schema, and one unknown key makes the Gateway
refuse to start — taking your chat channels and scheduled jobs with it. MCP is registered through
`openclaw mcp add`, which is the vendor's own supported path.

**Workaround:** If sandboxing is enabled, check that `workspaceAccess` is `"rw"`; otherwise the agent
writes into a sandbox copy under `~/.openclaw/sandboxes` and `.brain/` never appears in your folder.

**If you also installed for Antigravity CLI**, both tools read `./.agents/skills/`, so Antigravity CLI
will list sixteen OSP skills rather than eight — its own persona skills plus the eight commands OpenClaw
needs as skills. Nothing is broken and nothing is overwritten; the extra eight are the same commands it
already has as workflows. Installing in either order gives the same result.
