# `osp_mcp` — Open ScholarPeer MCP Server

Single FastMCP server exposing academic-search and full-text tools across four providers.

## Tools

19 tools. The authority is the source: `grep -c '^@mcp.tool()' osp_mcp.py`.
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

## Errors are never an empty list

A tool returns either records, or an error record. The error carries a
`reason` so the caller can act on it without reading the prose:

| `reason` | Meaning |
|---|---|
| `blocked` | Google Scholar refused — a 429, 403, or captcha page |
| `rate_limited` | Semantic Scholar answered 429 |
| `busy` | another arXiv call held the one allowed connection |
| `not_found` | no such paper, so no fallback worth suggesting |
| `timeout` | the call ran past `OSP_CALL_TIMEOUT` |
| `bad_request` | the arguments were wrong |
| `failed` | anything else |

An empty list `[]` means one thing only: the search ran and matched nothing.

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

## Getting a Semantic Scholar API key

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
2. Import it at the top of `osp_mcp.py` and add `@mcp.tool()`-decorated wrappers.
3. Document each tool with a rich docstring (the MCP host shows it to the LLM).
4. Add the new dependencies to `requirements.txt`, **with an upper bound**.
5. Give failures their own exception type and never return `[]` for one.
6. Add offline checks to `scripts/test_providers_unit.py` and a live check to
   `scripts/test_providers.py`. Nothing else in the repository loads this
   package.
7. (Optional) Document API-key env vars in this README.

The framework principle is **dumb tools only** — no agentic logic in the server. Cognitive decisions about *what* to search and *when* to stop belong to the OSP agents in the calling tool.
