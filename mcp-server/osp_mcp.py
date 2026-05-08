"""
osp_mcp.py — Open ScholarPeer consolidated MCP server.

Exposes academic-search tools across three providers:
  • arXiv          — pre-prints, no API key needed
  • Semantic Scholar — citation graph, abstracts; API key recommended for higher rate limits
  • Google Scholar — broad coverage including blog posts, theses, workshop papers

Design principles:
  1. Dumb tools only — no agentic logic. Each tool is atomic, stateless.
  2. Rich docstrings — agents read these to decide when to call which tool.
  3. Consistent error envelope — all tools return either a list of records or
     [{"error": "..."}] (search-style) or {"error": "..."} (single-record style).
  4. Per-call timeout — every blocking call is wrapped with asyncio.wait_for
     so a hanging API call cannot block the server indefinitely.

Environment variables:
  SEMANTIC_SCHOLAR_API_KEY — optional; provides higher rate limits if set.
  OSP_CALL_TIMEOUT         — per-call timeout in seconds (default: 30).
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from providers import arxiv as arxiv_provider
from providers import semantic_scholar as ss_provider
from providers import google_scholar as gs_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("osp_mcp")

mcp = FastMCP("osp_mcp")

_TIMEOUT = int(os.environ.get("OSP_CALL_TIMEOUT", "30"))


async def _run(fn, *args, **kwargs) -> Any:
    """Run a synchronous provider function in a thread with a timeout."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(fn, *args, **kwargs),
            timeout=_TIMEOUT,
        )
    except asyncio.TimeoutError:
        raise TimeoutError(f"{fn.__name__} timed out after {_TIMEOUT}s")


# ---------- arXiv ----------------------------------------------------------

@mcp.tool()
async def search_arxiv(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance",
    date_from: str | None = None,
    date_to: str | None = None,
    categories: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Search arXiv for pre-prints and published papers.

    arXiv is the primary repository for pre-prints in CS, math, physics, and ML.
    Use when you need recent unpublished work, concurrent submissions, or workshop
    papers that may not yet be indexed by Semantic Scholar.

    Query tips — use quoted phrases for precision:
      ti:"transformer attention"         → title search
      au:"Vaswani"                       → author search
      abs:"scaling laws"                 → abstract search
      "multi-agent" ANDNOT "survey"      → exclude surveys

    Category codes (pass in `categories`):
      cs.AI, cs.LG, cs.CL, cs.CV, cs.MA, cs.RO, cs.CR, cs.HC

    Args:
        query: Free-form or field-specific query string.
        max_results: Number of results (1-50, default 10).
        sort_by: "relevance" (default) or "date" (newest first).
        date_from: Optional start date filter (YYYY-MM-DD).
        date_to: Optional end date filter (YYYY-MM-DD).
        categories: Optional list of arXiv category codes.

    Returns:
        List of dicts with keys: arxiv_id, title, authors, summary, published,
        updated, link, pdf_url, primary_category, categories, comment.
        Returns [{"error": "..."}] on failure.
    """
    log.info("search_arxiv(query=%r, max=%d, sort=%s, from=%s, to=%s, cats=%s)",
             query, max_results, sort_by, date_from, date_to, categories)
    try:
        return await _run(arxiv_provider.search, query, max_results, sort_by,
                          date_from, date_to, categories)
    except Exception as e:
        return [{"error": f"search_arxiv failed: {e}"}]


@mcp.tool()
async def get_arxiv_paper_details(arxiv_id: str) -> dict[str, Any]:
    """Fetch detailed metadata for a specific arXiv paper by its ID.

    Use when you have a specific arXiv ID (e.g. "2305.14314" or "1706.03762")
    and want the full record with abstract, authors, dates, and categories.

    Args:
        arxiv_id: The arXiv identifier (e.g. "2305.14314" or "cs.CL/0306050").

    Returns:
        Dict with keys: arxiv_id, title, authors, summary, published, updated,
        link, pdf_url, primary_category, categories, comment.
        Returns {"error": "..."} on failure.
    """
    log.info("get_arxiv_paper_details(arxiv_id=%r)", arxiv_id)
    try:
        return await _run(arxiv_provider.get_details, arxiv_id)
    except Exception as e:
        return {"error": f"get_arxiv_paper_details failed: {e}"}


# ---------- Semantic Scholar -----------------------------------------------

@mcp.tool()
async def search_semantic_scholar(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search Semantic Scholar for academic papers across all fields.

    Semantic Scholar provides high-quality citation-graph data, abstracts, and
    venue metadata. Use for established publications; for very recent pre-prints,
    prefer search_arxiv. Returns citation counts and author IDs for follow-up.

    Args:
        query: Free-form search query.
        limit: Maximum number of results (1-100, default 10).

    Returns:
        List of dicts with keys: paperId, title, abstract, year, authors, url,
        venue, publicationTypes, citationCount, externalIds.
        Returns [{"error": "..."}] on failure.
    """
    log.info("search_semantic_scholar(query=%r, limit=%d)", query, limit)
    try:
        return await _run(ss_provider.search_papers, query, limit)
    except Exception as e:
        return [{"error": f"search_semantic_scholar failed: {e}"}]


@mcp.tool()
async def get_semantic_scholar_paper(paper_id: str) -> dict[str, Any]:
    """Fetch full metadata for a specific Semantic Scholar paper.

    Use after search_semantic_scholar to get richer information, or when you
    have a known paperId, DOI, ArXiv ID, or ACL ID.

    Args:
        paper_id: Semantic Scholar paperId, DOI (e.g. "10.1038/nature14539"),
            ArXiv ID (e.g. "arXiv:1706.03762"), or ACL ID.

    Returns:
        Dict with keys: paperId, title, abstract, year, authors, url, venue,
        publicationTypes, citationCount, externalIds.
        Returns {"error": "..."} on failure.
    """
    log.info("get_semantic_scholar_paper(paper_id=%r)", paper_id)
    try:
        return await _run(ss_provider.get_paper, paper_id)
    except Exception as e:
        return {"error": f"get_semantic_scholar_paper failed: {e}"}


@mcp.tool()
async def get_semantic_scholar_paper_references(
    paper_id: str, limit: int = 50
) -> list[dict[str, Any]]:
    """Fetch the reference list (bibliography) for a specific paper.

    Returns the papers cited BY this paper. Use to verify whether a paper
    actually cites work it claims to compare against, or to find papers this
    paper builds on.

    Args:
        paper_id: Semantic Scholar paperId, DOI, ArXiv ID, or ACL ID.
        limit: Max references to return (1-100, default 50).

    Returns:
        List of dicts with keys: paperId, title, year, citationCount, authors.
        Returns [{"error": "..."}] on failure.
    """
    log.info("get_semantic_scholar_paper_references(paper_id=%r, limit=%d)", paper_id, limit)
    try:
        return await _run(ss_provider.get_paper_references, paper_id, limit)
    except Exception as e:
        return [{"error": f"get_semantic_scholar_paper_references failed: {e}"}]


@mcp.tool()
async def get_semantic_scholar_paper_citations(
    paper_id: str, limit: int = 50
) -> list[dict[str, Any]]:
    """Fetch the papers that cite a specific paper.

    Use to find downstream work that builds on a paper, or to assess how
    widely cited a baseline or method is.

    Args:
        paper_id: Semantic Scholar paperId, DOI, ArXiv ID, or ACL ID.
        limit: Max citations to return (1-100, default 50).

    Returns:
        List of dicts with keys: paperId, title, year, citationCount, authors.
        Returns [{"error": "..."}] on failure.
    """
    log.info("get_semantic_scholar_paper_citations(paper_id=%r, limit=%d)", paper_id, limit)
    try:
        return await _run(ss_provider.get_paper_citations, paper_id, limit)
    except Exception as e:
        return [{"error": f"get_semantic_scholar_paper_citations failed: {e}"}]


@mcp.tool()
async def get_semantic_scholar_papers_batch(
    paper_ids: list[str],
) -> list[dict[str, Any]]:
    """Fetch metadata for multiple papers in a single request (up to 500).

    More efficient than calling get_semantic_scholar_paper in a loop when you
    have many IDs from a prior search or reference list.

    Args:
        paper_ids: List of paper IDs (paperId, DOI, ArXiv ID, ACL ID, etc.).

    Returns:
        List of paper dicts. Returns [{"error": "..."}] on failure.
    """
    log.info("get_semantic_scholar_papers_batch(n=%d)", len(paper_ids))
    try:
        return await _run(ss_provider.get_papers_batch, paper_ids)
    except Exception as e:
        return [{"error": f"get_semantic_scholar_papers_batch failed: {e}"}]


@mcp.tool()
async def get_semantic_scholar_author(author_id: str) -> dict[str, Any]:
    """Fetch metadata for a specific Semantic Scholar author by ID.

    Returns profile information including affiliations, paper count, citation
    count, and h-index. Use to assess whether a paper's authors have prior
    expertise in the claimed sub-field.

    Args:
        author_id: Semantic Scholar authorId (e.g. "1741101").

    Returns:
        Dict with keys: authorId, name, url, affiliations, paperCount,
        citationCount, hIndex. Returns {"error": "..."} on failure.
    """
    log.info("get_semantic_scholar_author(author_id=%r)", author_id)
    try:
        return await _run(ss_provider.get_author, author_id)
    except Exception as e:
        return {"error": f"get_semantic_scholar_author failed: {e}"}


@mcp.tool()
async def search_semantic_scholar_authors(
    query: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Search Semantic Scholar for authors by name.

    Use when you have an author name from a paper and need their authorId for
    follow-up queries (e.g. get_semantic_scholar_author_papers).

    Args:
        query: Author name or partial name (e.g. "Yann LeCun").
        limit: Max results (1-100, default 10).

    Returns:
        List of dicts with keys: authorId, name, url, affiliations, paperCount,
        citationCount, hIndex. Returns [{"error": "..."}] on failure.
    """
    log.info("search_semantic_scholar_authors(query=%r, limit=%d)", query, limit)
    try:
        return await _run(ss_provider.search_authors, query, limit)
    except Exception as e:
        return [{"error": f"search_semantic_scholar_authors failed: {e}"}]


@mcp.tool()
async def get_semantic_scholar_author_papers(
    author_id: str, limit: int = 50
) -> list[dict[str, Any]]:
    """Fetch the publication list for a specific author.

    Use to find an author's other work, or to determine whether the paper's
    claimed contribution is novel compared to the authors' prior work.

    Args:
        author_id: Semantic Scholar authorId.
        limit: Max papers to return (1-100, default 50).

    Returns:
        List of paper dicts. Returns [{"error": "..."}] on failure.
    """
    log.info("get_semantic_scholar_author_papers(author_id=%r, limit=%d)", author_id, limit)
    try:
        return await _run(ss_provider.get_author_papers, author_id, limit)
    except Exception as e:
        return [{"error": f"get_semantic_scholar_author_papers failed: {e}"}]


@mcp.tool()
async def get_semantic_scholar_paper_recommendations(
    paper_id: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Get papers recommended by Semantic Scholar as similar to a given paper.

    Useful for discovering related work the paper may not have cited, or for
    expanding the literature corpus during the temporal expansion round.

    Args:
        paper_id: Semantic Scholar paperId, DOI, ArXiv ID, or ACL ID.
        limit: Max recommendations (1-100, default 10).

    Returns:
        List of slim paper dicts. Returns [{"error": "..."}] on failure.
    """
    log.info("get_semantic_scholar_paper_recommendations(paper_id=%r, limit=%d)", paper_id, limit)
    try:
        return await _run(ss_provider.get_paper_recommendations, paper_id, limit)
    except Exception as e:
        return [{"error": f"get_semantic_scholar_paper_recommendations failed: {e}"}]


@mcp.tool()
async def search_semantic_scholar_snippets(
    query: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Search for text snippets from paper abstracts/bodies matching a query.

    Unlike search_semantic_scholar (which matches metadata), this returns actual
    ~500-word excerpts from the paper text. Use when you need to verify that a
    paper actually discusses a specific concept, or to find papers containing
    specific technical claims.

    Args:
        query: Free-form query describing the content to find.
        limit: Max snippets (1-20, default 10).

    Returns:
        List of dicts with keys: snippetId, text, paper (slim paper record).
        Returns [{"error": "..."}] on failure.
    """
    log.info("search_semantic_scholar_snippets(query=%r, limit=%d)", query, limit)
    try:
        return await _run(ss_provider.search_snippets, query, limit)
    except Exception as e:
        return [{"error": f"search_semantic_scholar_snippets failed: {e}"}]


# ---------- Google Scholar -------------------------------------------------

@mcp.tool()
async def search_google_scholar(query: str, num_results: int = 5) -> list[dict[str, Any]]:
    """Search Google Scholar for broader academic coverage.

    Google Scholar indexes content beyond standard publications: blog posts,
    workshop papers, theses, technical reports, and pre-prints from sources
    other than arXiv. Use as a third retrieval source to catch what arXiv
    and Semantic Scholar miss.

    Note: Uses HTML scraping; results may vary and rate limits may apply.

    Args:
        query: Free-form search query.
        num_results: Maximum number of results (1-20, default 5).

    Returns:
        List of dicts with keys: title, authors, abstract, url.
        Returns [{"error": "..."}] on failure.
    """
    log.info("search_google_scholar(query=%r, num_results=%d)", query, num_results)
    try:
        return await _run(gs_provider.search, query, num_results)
    except Exception as e:
        return [{"error": f"search_google_scholar failed: {e}"}]


@mcp.tool()
async def search_google_scholar_advanced(
    query: str,
    author: str | None = None,
    year_start: int | None = None,
    year_end: int | None = None,
    num_results: int = 5,
) -> list[dict[str, Any]]:
    """Search Google Scholar with author and year-range filters.

    Use when you need to search within a specific time window (e.g. "last 12
    months" for the temporal-expansion round) or constrain to a specific
    author's body of work.

    Args:
        query: Free-form search query.
        author: Optional author-name filter.
        year_start: Optional inclusive start year (e.g. 2024).
        year_end: Optional inclusive end year (e.g. 2026).
        num_results: Maximum number of results (1-20, default 5).

    Returns:
        List of dicts with keys: title, authors, abstract, url.
        Returns [{"error": "..."}] on failure.
    """
    log.info(
        "search_google_scholar_advanced(query=%r, author=%r, yr=%s-%s, n=%d)",
        query, author, year_start, year_end, num_results,
    )
    year_range = (year_start, year_end) if (year_start or year_end) else None
    try:
        return await _run(gs_provider.search_advanced, query, author, year_range, num_results)
    except Exception as e:
        return [{"error": f"search_google_scholar_advanced failed: {e}"}]


@mcp.tool()
async def get_google_scholar_author_info(author_name: str) -> dict[str, Any]:
    """Fetch a Google Scholar author profile.

    Returns affiliation, research interests, total citation count, and the
    author's top publications. Use to verify expertise claims or find an
    author's other work.

    Note: Uses the `scholarly` library; may be rate-limited by Google.

    Args:
        author_name: The author's name to look up (e.g. "Ian Goodfellow").

    Returns:
        Dict with keys: name, affiliation, interests, citedby, publications
        (list of top 5 with title, year, citations). Returns {"error": "..."}
        on failure.
    """
    log.info("get_google_scholar_author_info(author_name=%r)", author_name)
    try:
        return await _run(gs_provider.get_author_info, author_name)
    except Exception as e:
        return {"error": f"get_google_scholar_author_info failed: {e}"}


# ---------- Server entrypoint ----------------------------------------------

if __name__ == "__main__":
    if os.environ.get("SEMANTIC_SCHOLAR_API_KEY"):
        log.info("Semantic Scholar API key detected — higher rate limits enabled.")
    else:
        log.info("No SEMANTIC_SCHOLAR_API_KEY in env — Semantic Scholar will use anonymous limits.")
    log.info("Starting Open ScholarPeer MCP server (osp_mcp), timeout=%ds", _TIMEOUT)
    mcp.run(transport="stdio")
