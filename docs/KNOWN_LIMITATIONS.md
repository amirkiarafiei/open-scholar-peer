# Known Limitations — Open ScholarPeer v2

These are limitations users should know about going in. None block normal operation, but each affects the quality or smoothness of specific phases. Workarounds are listed.

---

## 1. Some tools fall back to self-reflection for the Q&A engine

**What:** The Multi-Aspect Q&A Engine (`/5-osp-qa`) is designed around true subagent isolation: the Query Agent (main thread) delegates each question to a fresh Answer Generator subagent so the verification cannot be biased by the question's reasoning trace.

**Limitation:** Three of the supported tools — **Antigravity** (legacy desktop app), **Mistral Vibe**, and **OpenHands** — either do not support subagents or have only profile-style independence (no documented subagent delegation). On these, the Q&A engine falls back to **self-reflection mode**: both Query and Answer Generator personas run in the same context window, separated by strict turn markers (`=== Query Agent === ... === END === === Answer Generator === ...`).

**Impact:** Reviews on the Q&A axis from these tools are likely lower in independent-verification depth than reviews from Claude Code, Cursor, Gemini CLI, Antigravity CLI, Copilot CLI, Codex CLI, Qwen Code, OpenCode, Junie, Kiro, or Kimi Code. The other downstream phases (literature, historian, baseline scout, reviewer) are unaffected.

**Workaround:** If you need full subagent isolation for a paper, use one of the subagent-capable tools listed above.

---

## 2. Semantic Scholar anonymous rate limits are aggressive

**What:** The `osp search-semantic-scholar` and related CLI subcommands use the official Semantic Scholar API. Without an API key, anonymous limits apply (~100 requests / 5 min, frequently bursty 429s).

**Impact:** During the 3-round literature retrieval (`/2-osp-literature`), an anonymous user may hit rate limits mid-round, causing partial corpora.

**Workaround:** Get a free API key at https://www.semanticscholar.org/product/api#api-key and add it to your `.env` file at the project root:

```env
SEMANTIC_SCHOLAR_API_KEY=sk-...
```

The CLI shim loads the env var on every execution.

---

## 3. PDF parsing depends on the host tool's environment or convert_pdf.py script

**What:** OSP needs a readable text version of the paper at `.brain/input/paper.md` for the Summary Agent. The `convert_pdf.py` script wrapper is configured for this purpose.

**Limitation:** If `markitdown` is not installed in the environment (or `uv` cannot run it), and the paper is supplied as a PDF/DOCX, conversion will fail.

**Impact:** `/0-osp-onboarding` will refuse to advance until either (a) dependencies are installed, or (b) the user manually provides `.brain/input/paper.md`. This is intentional fail-fast behavior to avoid silent downstream errors.

**Workaround:** Install markitdown:
```bash
pip install markitdown          # if not already installed
```
or convert manually:
```bash
markitdown paper.pdf > .brain/input/paper.md
```

---

## 4. CLI shim execution permissions and environment paths

**What:** OSP executes scripts locally through the `.open-scholar-peer/osp` Unix shim (or `.open-scholar-peer\osp.cmd` Windows shim).

**Limitation:** If Python 3.10+ is missing, or the sandbox environment has locked down local script executions (blocking subprocesses), the shim will fail to run.

**Impact:** Downstream agents will print a warning asking the user to run setup or check executions, and exit.

**Workaround:** Ensure Python is in your PATH and the project folder has correct read/write/execute permissions. Run the installer again if necessary.

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

**What:** Google Scholar has no public API. The `osp search-google-scholar` CLI command scrapes HTML.

**Limitation:** Subject to Google's rate limits and HTML structure changes. Results may be empty or stale during heavy usage.

**Impact:** The Literature Agent and Baseline Scout still have arXiv and Semantic Scholar as primary sources; Google Scholar adds breadth (blog posts, theses, workshop papers) but isn't load-bearing.

**Workaround:** None needed unless Google Scholar is your primary source, in which case consider running searches at off-peak times.

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
