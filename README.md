# Open ScholarPeer (OSP)

A community implementation of [**ScholarPeer**: A Context-Aware Multi-Agent Framework for Automated Peer Review](https://arxiv.org/abs/2601.22638) — runnable inside the AI coding tools you already use.

<div align="center">
  <figure>
    <img src="assets/support.png" alt="Open ScholarPeer" width="360" />
  </figure>
</div>

OSP turns the paper's 7-agent pipeline into a portable set of Skills, Slash Commands, and MCP tools that install into your project directory. Use your favorite AI tool to review papers.

---

## 🚀 Quickstart

**1. In your terminal**, from the directory holding the paper you want to review:

```bash
curl -sSL https://raw.githubusercontent.com/amirkiarafiei/open-scholar-peer/main/install.sh | bash
```

**2. Open your code agent** in that directory, and in its interactive chat run:

```text
/open-scholar-peer
```

The orchestrator reads your session state and tells you which step to run next.

## How it works


Given an academic paper, OSP runs a 7-step protocol to produce a venue-formatted peer review:

<figure>
  <img src="docs/paper/agents.png" alt="ScholarPeer architecture diagram" width="720" />
  <figcaption>ScholarPeer architecture diagram. Source: Google paper, <a href="https://arxiv.org/abs/2601.22638">https://arxiv.org/abs/2601.22638</a>.</figcaption>
</figure>

---

First, you can invoke `/open-scholar-peer` and it guides you towards the steps.

| Step | Persona | Command | What it produces |
| --- | --- | --- | --- |
| 0 | Onboarding | `/0-osp-onboarding` | Detects venue, scrapes review guidelines, scaffolds the working directory |
| 1 | Summary Agent | `/1-osp-summary` | Structured summary (claims, method, evidence) |
| 2 | Literature Review Agent | `/2-osp-literature` | 3-round live retrieval (sub-domain anchor, method anchor, temporal expansion) |
| 3 | Historian Agent | `/3-osp-historian` | Chronological domain narrative |
| 4 | Baseline Scout | `/4-osp-baseline-scout` | Adversarial audit of missing baselines and datasets |
| 5 | Q&A Engine | `/5-osp-qa` | Configurable Q&A pairs per criterion, default 2 (subagent-isolated where possible) |
| 6 | Reviewer Agent | `/6-osp-review` | Final consolidated review formatted to the venue's guidelines |

### How to View Artifcats

Every artifact is saved as auditable markdown in `.brain/raw/` and `.brain/review/`. No black box.

---

## 🛠️ Installation

From your project directory (the directory containing the paper you want to review):

```bash
# One-liner installer

curl -sSL https://raw.githubusercontent.com/amirkiarafiei/open-scholar-peer/main/install.sh | bash
```

Or clone and run locally:

```bash
git clone https://github.com/amirkiarafiei/open-scholar-peer
cd open-scholar-peer
bash install.sh   # interactive — pick your AI tool
```

Prefer no prompts? `bash install.sh --tool claude,cursor` installs directly, and
`bash install.sh --help` lists every option and tool slug.

Then open your code agent in that directory, and in its interactive chat run:

```text
/open-scholar-peer        ← guides towards steps
/0-osp-onboarding         ← venue + paper detection
/1-osp-summary
/2-osp-literature
/3-osp-historian
/4-osp-baseline-scout
/5-osp-qa
/6-osp-review
```

Or just run `/open-scholar-peer` at any point — it reads your session state and tells you which command comes next.

---

## Literature Databases

Six open databases. **None of them requires a paid subscription, and none
requires a key to work** — a key only lifts a rate limit. The installer asks
which ones you want and enables just those, so your agent carries a short tool
list instead of all 22. It starts with **arXiv and Semantic Scholar** ticked;
tick the others if your papers need them.

| Database | Key | What it is for |
| --- | --- | --- |
| arXiv | Not required | Preprints in CS, physics and maths. Also serves **full text**, from the LaTeX source. |
| Semantic Scholar | Optional | Citation graph, references, recommendations, title matching. |
| Google Scholar | Not required | Broadest coverage — theses, workshop papers, blogs. Best-effort scraping. |
| Europe PMC | Not required | Biomedical and life sciences, with **full text** over a plain request. |
| Zenodo | Not required | Code, datasets and software releases — *did the authors release their code?* |
| OpenAlex | Optional | ~327 million works, with **retraction flags** and field-normalised citation impact. |

Deliberately not included: ACM DL, IEEE Xplore, Web of Science, Scopus,
Springer and ScienceDirect all need a subscription or a paid key, which is the
one thing this project will not require of you. DBLP was dropped after four
probes in September 2026 hit a bot wall. bioRxiv and medRxiv are a feed rather
than a search engine — they have no keyword search — and Semantic Scholar
already indexes both.

The search layer lives in [mcp-server/](mcp-server/), and
[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) has the recipe for adding a
source of your own.

### 🔑 API keys

The installer creates a `.env` file at your project root and offers to take
your keys during setup. You can skip that and add them later:

```bash
# .env  (gitignored — never committed)
SEMANTIC_SCHOLAR_API_KEY=sk-...    # a dedicated rate limit
OPENALEX_API_KEY=...               # a much larger daily budget
OPENALEX_MAILTO=you@example.org    # OpenAlex's faster lane

# which databases the agent may search; remove the line for all of them
OSP_SOURCES=arxiv,semantic_scholar,google_scholar,europepmc,zenodo,openalex
```

Anonymous Semantic Scholar access is one pool shared by every unauthenticated
caller everywhere, so it is throttled unpredictably. A free key at
https://www.semanticscholar.org/product/api#api-key gives you your own limit.
The MCP server loads `.env` automatically on startup.

---

## 🔌 Supported AI tools

| Tool | Subagent isolation | MCP auto-config |
| --- | --- | --- |
| [Claude Code](https://claude.com/claude-code) | ✓ | ✓ (`.mcp.json`) |
| [Cursor](https://cursor.com) | ✓ | ✓ (`.cursor/mcp.json`) |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | ✓ | ✓ (`.gemini/settings.json`) |
| [Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/) | ✓ | ✓ (`~/.copilot/mcp-config.json`) |
| [Codex CLI](https://github.com/openai/codex) | ✓ | via `codex mcp add` (TOML) |
| [Qwen Code](https://github.com/QwenLM/qwen-code) | ✓ | ✓ (`.qwen/settings.json`) |
| [OpenCode](https://opencode.ai) | ✓ | via `opencode mcp add` (or `opencode.json`) |
| [Junie](https://www.jetbrains.com/junie/) | ✓ | ✓ (`.junie/mcp/mcp.json`) |
| [Kiro](https://kiro.dev) | ✓ | ✓ (`.kiro/settings/mcp.json`) |
| [Kimi Code](https://moonshotai.github.io/kimi-cli/) | ✓ | ✓ (`~/.kimi/mcp.json`) |
| [Mistral Vibe](https://docs.mistral.ai/mistral-vibe/) | ✗ (self-reflection fallback) | manual snippet (TOML) |
| [OpenHands](https://docs.openhands.dev) | ✗ (self-reflection fallback) | via OpenHands UI / `config.toml` |
| [Antigravity](https://antigravity.google/) | ✓ (falls back if unavailable) | ✓ (`~/.gemini/antigravity/` + `~/.gemini/config/`) |
| [Antigravity CLI](https://antigravity.google/cli/) | ✓ | ✓ (`.agents/mcp_config.json` + `~/.gemini/antigravity-cli/`) |

See [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md) for self-reflection caveats and per-tool MCP wiring details.

---

## Documentation

- **[`docs/BRAIN_LAYOUT.md`](docs/BRAIN_LAYOUT.md)** — `.brain/` filesystem contract.
- **[`docs/ARTIFACT_CONTRACTS.md`](docs/ARTIFACT_CONTRACTS.md)** — Per-step I/O contract.
- **[`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md)** — What to expect, what won't work, workarounds.
- **[`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)** — Common issues, by symptom.
- **[`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md)** — How to extend OSP (commands, skills, MCP providers).
- **[`docs/paper/SUMMARY.md`](docs/paper/SUMMARY.md)** — Paper essence (architecture and protocol).

### Why it is the way it is

`kia-context/` is the project's own memory — why decisions were made, what was rejected, and what must
stay true. Start at [`kia-context/INDEX.md`](kia-context/INDEX.md).

- **[`kia-context/specs/MANIFESTO.md`](kia-context/specs/MANIFESTO.md)** — The product boundary and the rules that do not move.
- **[`kia-context/specs/ARCHITECTURE.md`](kia-context/specs/ARCHITECTURE.md)** — How the protocol, the state machine and the 14-tool sync pipeline actually work.
- **[`kia-context/logs/BRAINSTORM.md`](kia-context/logs/BRAINSTORM.md)** — Decisions and the alternatives they beat.
- **[`kia-context/logs/PROGRESS.md`](kia-context/logs/PROGRESS.md)** — Milestones, and what is being built now.
- **[`kia-context/genesis/`](kia-context/genesis/)** — Why the project exists, and the original design document.

---

## License

MIT.

## Citation

If you use OSP in research, please cite the upstream ScholarPeer paper. The implementation here is community-built and is not affiliated with the paper's authors or Google.

```bibtex
@article{goyal2026scholarpeer,
  title={ScholarPeer: A Context-Aware Multi-Agent Framework for Automated Peer Review},
  author={Goyal, Palash and Parmar, Mihir and Song, Yiwen and Palangi, Hamid and Pfister, Tomas and Yoon, Jinsung},
  journal={arXiv preprint arXiv:2601.22638},
  year={2026},
  doi={10.48550/arXiv.2601.22638},
  url={https://arxiv.org/abs/2601.22638}
}
```

---

## Community

- [Contributing](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [License](LICENSE)

