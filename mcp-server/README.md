# `osp_mcp` — Open ScholarPeer MCP Server

Single FastMCP server exposing academic-search and full-text tools across six
databases.

**Not every tool is always registered.** The installer asks which databases to
use and writes the answer to `.env` as `OSP_SOURCES`; only those sources have
their tools registered. An unset `OSP_SOURCES` means all of them. This keeps
the agent's tool list short — six databases is 22 tools, three is 17.

The picker starts with **arXiv and Semantic Scholar** ticked, the two that
cover every field. The rest are one keypress away.

## Tools

22 tools with every database on. The authority is the source:
`grep -c '^@tool_for(' core.py` — the tools live in `core.py`, which knows nothing
about MCP. `osp_mcp.py` serves them over MCP and `osp_cli.py` serves the same
function objects over argv; neither names a tool, so neither can drift from the
other. For what THIS project has switched on:
`osp_cli.py list --json | python3 -c 'import json,sys;print(len(json.load(sys.stdin)))'`.
Each tool's own docstring gives the full parameter list and return keys —
that is what the agent reads, so keep it richer than this table.

### arXiv — free, no key (3)
- `search_arxiv(query, max_results=10, sort_by="relevance", date_from=None, date_to=None, categories=None)`
  Dates and categories are filtered by arXiv itself, inside the query.
- `get_arxiv_paper_details(arxiv_id)`
  Takes new-style `2305.14314`, old-style `hep-th/9901001`, or a pinned
  version `1706.03762v5`.
- `read_arxiv_paper(arxiv_id, max_chars=50000, offset=0)`
  The paper's **full text**, from its LaTeX source. Nothing written to disk.
  Returned in windows; follow `truncated` and `offset`.

### Europe PMC — free, no key (2)
Biomedical, health and life sciences, which arXiv barely covers. The only
provider here that serves whole articles over a plain request.
- `search_europe_pmc(query, limit=10, open_access_only=True, sort=None)`
- `get_europe_pmc_full_text(pmcid, max_chars=50000, offset=0)`

### Semantic Scholar — free, optional key for a dedicated rate limit (11)
- `search_semantic_scholar(query, limit=10, year=, publication_date_or_year=, venue=, fields_of_study=, publication_types=, open_access_pdf=, min_citation_count=, sort=)`
- `match_semantic_scholar_title(title)` — one best-matching paper, with a `matchScore`
- `get_semantic_scholar_paper(paper_id)`
- `get_semantic_scholar_papers_batch(paper_ids)` — up to 500 in one request
- `get_semantic_scholar_paper_references(paper_id, limit=50)`
- `get_semantic_scholar_paper_citations(paper_id, limit=50)`
- `get_semantic_scholar_paper_recommendations(paper_id, limit=10)`
- `get_semantic_scholar_author(author_id)`
- `search_semantic_scholar_authors(query, limit=10)`
- `get_semantic_scholar_author_papers(author_id, limit=50)`
- `search_semantic_scholar_snippets(query, limit=10)` — excerpts from paper text

### Google Scholar — free, best-effort HTML scraping (3)
- `search_google_scholar(query, num_results=5)`
- `search_google_scholar_advanced(query, author=None, year_start=None, year_end=None, num_results=5)`
- `get_google_scholar_author_info(author_name)`

### OpenAlex — free, optional key (2)
~327 million works across every field. Two things nothing else here gives:
a retraction flag on every record, and `fwci`, which normalises citations
against a work's own field and year.
- `search_openalex(query, limit=10, from_year=, to_year=, open_access_only=, exclude_retracted=, work_type=, sort=)`
- `get_openalex_work(identifier)` — **the retraction check.** Give it a DOI,
  read `isRetracted`.

### Zenodo — free, no key (1)
Not a paper search. It answers *"did the authors release their code and
data?"*, which most review forms ask and nothing else here can check.
- `search_zenodo(query, limit=10, resource_type="software")`

## Errors are never an empty list

A tool returns either records, or an error record. The error carries a
`reason` so the caller can act on it without reading the prose:

| `reason` | Meaning |
|---|---|
| `blocked` | Google Scholar refused — a 429, 403, or captcha page |
| `rate_limited` | Semantic Scholar answered 429 |
| `busy` | another arXiv call held the one allowed connection |
| `not_found` | no such paper or article; the provider is fine |
| `timeout` | the call ran past its deadline and was abandoned |
| `unavailable` | the source cannot serve this — it is switched off for this project by `OSP_SOURCES`, or the provider is down |
| `bad_request` | the arguments were wrong |
| `failed` | anything else |

All eight are listed here on purpose: a `reason` an agent has never been told
about is one it cannot act on, and the whole point of the field is that it can.

An empty list `[]` means one thing only: the search ran and matched nothing.

## Choosing databases

The installer asks. To change it afterwards, edit `OSP_SOURCES` in `.env`:

```bash
OSP_SOURCES=arxiv,semantic_scholar,google_scholar,europepmc,zenodo,openalex
```

Remove the line to enable everything. An unknown name is warned about and
ignored; a line naming nothing known falls back to all sources rather than
leaving the agent with no tools. `europe_pmc`, `epmc`, `s2` and `scholar` are
understood as aliases.

| Database | Key | Covers |
|---|---|---|
| `arxiv` | free | preprints: CS, physics, maths. Full text from LaTeX. |
| `semantic_scholar` | optional | all fields, citation graph |
| `google_scholar` | free | broad, best-effort scraping |
| `europepmc` | free | biomedical, and full text over REST |
| `zenodo` | free | code, data and software releases |
| `openalex` | optional | all fields, retraction flags |

No database here requires a key. A key only lifts a rate limit.

## Setup

The installer (`bash install.sh`) copies this server into `<your-project>/.open-scholar-peer/mcp/` and creates a Python virtualenv with all dependencies. You don't need to manage it manually.

To run it standalone for testing, build the virtualenv at the **repository
root**, never inside `mcp-server/`.
`scripts/init_mcp.sh` copies `mcp-server/.` into every user's project, so a
venv left here is copied along with it.

```bash
# from the repository root
python3 -m venv .venv
.venv/bin/pip install -r mcp-server/requirements.txt

# Optional: a Semantic Scholar API key gives you a dedicated rate limit
export SEMANTIC_SCHOLAR_API_KEY=sk-...

cd mcp-server && PYTHONPATH=. ../.venv/bin/python osp_mcp.py
```

Check the providers without starting the server:

```bash
.venv/bin/python scripts/test_providers_unit.py   # offline, ~1s
.venv/bin/python scripts/test_providers.py        # live APIs, opt-in
```

The server runs on stdio and is meant to be spawned by an MCP-aware host (Claude Code, Cursor, Gemini CLI, etc.) — not invoked directly by users.

## API keys

All optional. Set them in `.env`, or let the installer prompt you.

| Variable | For |
|---|---|
| `SEMANTIC_SCHOLAR_API_KEY` | a dedicated Semantic Scholar rate limit |
| `OPENALEX_API_KEY` | a much larger OpenAlex daily budget |
| `OPENALEX_MAILTO` | OpenAlex's faster lane for callers who identify themselves |
| `GOOGLE_SCHOLAR_PROXY_URL` | the only thing that helps when Google blocks your address |
| `ZENODO_API_TOKEN` | a higher Zenodo rate limit |

### Getting a Semantic Scholar API key

Free at: https://www.semanticscholar.org/product/api#api-key.

Anonymous access is a single pool shared by every unauthenticated caller
everywhere, so it is throttled unpredictably — during testing on 2026-09-20 it
refused connections outright for long stretches. A key gives you your own
limit, documented as 1 request per second. The server works without one.

Set it at install time or later via env var:
```bash
export SEMANTIC_SCHOLAR_API_KEY=sk-...
```

## Extending — adding a new provider

1. Create `providers/<name>.py` with plain Python functions for search/get-detail.
2. Add it to `core.py` — a lazy alias with `_lazy("providers.<name>")`, then a
   wrapper decorated `@tool_for("<source>")` that calls `await _run(...)` and
   returns `_err(...)` on failure. Do **not** touch `osp_mcp.py`: it names no
   tool, and one registration serves both the MCP and the CLI surfaces.
3. Document each tool with a rich docstring (the MCP host shows it to the LLM).
4. Add the new dependencies to `requirements.txt`, **with an upper bound**.
5. Give failures their own exception type and never return `[]` for one.
6. Add offline checks to `scripts/test_providers_unit.py` and a live check to
   `scripts/test_providers.py`. Nothing else in the repository loads this
   package.
7. (Optional) Document API-key env vars in this README.

The framework principle is **dumb tools only** — no agentic logic in the server. Cognitive decisions about *what* to search and *when* to stop belong to the OSP agents in the calling tool.
