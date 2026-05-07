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
  4. Extensible — community can add a new provider by appending a new tools module
     and decorating its functions with @mcp.tool().

Environment variables:
  SEMANTIC_SCHOLAR_API_KEY — optional; provides higher rate limits if set.
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

# ---------- arXiv ----------------------------------------------------------

@mcp.tool()
async def search_arxiv(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Search arXiv for pre-prints and published papers.

    arXiv is the primary repository for pre-prints in CS, math, physics, and ML.
    Use this tool when you need to find recent unpublished work, including
    concurrent submissions and workshop papers that may not yet be indexed by
    Semantic Scholar.

    Args:
        query: Free-form search query (matches title, abstract, authors).
            Examples: "transformer attention scaling laws", "Vaswani 2017".
        max_results: Maximum number of results to return (1-50, default 10).

    Returns:
        List of dicts, each with keys: title, authors, summary, published, link,
        arxiv_id, primary_category. Returns [{"error": "..."}] on failure.
    """
    log.info("search_arxiv(query=%r, max_results=%d)", query, max_results)
    try:
        return await asyncio.to_thread(arxiv_provider.search, query, max_results)
    except Exception as e:
        return [{"error": f"search_arxiv failed: {e}"}]


@mcp.tool()
async def get_arxiv_paper_details(arxiv_id: str) -> dict[str, Any]:
    """Fetch detailed metadata for a specific arXiv paper by its ID.

    Use this when you have a specific arXiv ID (e.g. "2305.14314" or
    "cs.CL/0306050") and want the full record with abstract, authors,
    publication date, and any updated version info.

    Args:
        arxiv_id: The arXiv identifier (e.g. "2305.14314" or "1706.03762").

    Returns:
        Dict with keys: title, authors, summary, published, updated, link,
        arxiv_id, primary_category, comment. Returns {"error": "..."} on failure.
    """
    log.info("get_arxiv_paper_details(arxiv_id=%r)", arxiv_id)
    try:
        return await asyncio.to_thread(arxiv_provider.get_details, arxiv_id)
    except Exception as e:
        return {"error": f"get_arxiv_paper_details failed: {e}"}


# ---------- Semantic Scholar ----------------------------------------------

@mcp.tool()
async def search_semantic_scholar(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search Semantic Scholar for academic papers across all fields.

    Semantic Scholar provides high-quality citation-graph data, abstracts, and
    venue metadata. Use this when you need citation counts, author IDs for
    follow-up queries, or normalized venue names. Works well for established
    publications; less reliable for very recent pre-prints (use arXiv for those).

    Args:
        query: Free-form search query.
        limit: Maximum number of results to return (1-100, default 10).

    Returns:
        List of dicts with keys: paperId, title, abstract, year, authors, url,
        venue, publicationTypes, citationCount. Returns [{"error": "..."}] on failure.
    """
    log.info("search_semantic_scholar(query=%r, limit=%d)", query, limit)
    try:
        return await asyncio.to_thread(ss_provider.search_papers, query, limit)
    except Exception as e:
        return [{"error": f"search_semantic_scholar failed: {e}"}]


@mcp.tool()
async def get_semantic_scholar_paper_details(paper_id: str) -> dict[str, Any]:
    """Fetch full metadata for a specific Semantic Scholar paper.

    Use after `search_semantic_scholar` to get richer information about a
    specific result, or when you have a known paperId / DOI.

    Args:
        paper_id: Semantic Scholar paperId (e.g. "0796f6cd7f0403a854d67d525e9b32af3b277331")
            or DOI (e.g. "10.1038/nature14539").

    Returns:
        Dict with keys: paperId, title, abstract, year, authors, url, venue,
        publicationTypes, citationCount. Returns {"error": "..."} on failure.
    """
    log.info("get_semantic_scholar_paper_details(paper_id=%r)", paper_id)
    try:
        return await asyncio.to_thread(ss_provider.get_paper, paper_id)
    except Exception as e:
        return {"error": f"get_semantic_scholar_paper_details failed: {e}"}


@mcp.tool()
async def get_semantic_scholar_author_details(author_id: str) -> dict[str, Any]:
    """Fetch metadata for a specific Semantic Scholar author.

    Use this to get author profile information including affiliations, paper
    count, citation count, and h-index. Useful when assessing whether a paper's
    authors have prior expertise in the claimed sub-field.

    Args:
        author_id: Semantic Scholar authorId (e.g. "1741101").

    Returns:
        Dict with keys: authorId, name, url, affiliations, paperCount,
        citationCount, hIndex. Returns {"error": "..."} on failure.
    """
    log.info("get_semantic_scholar_author_details(author_id=%r)", author_id)
    try:
        return await asyncio.to_thread(ss_provider.get_author, author_id)
    except Exception as e:
        return {"error": f"get_semantic_scholar_author_details failed: {e}"}


@mcp.tool()
async def get_semantic_scholar_citations_and_references(paper_id: str) -> dict[str, Any]:
    """Fetch the citation graph for a specific paper.

    Returns both the papers that cite this paper (citations) and the papers
    this paper cites (references). Use this to expand the literature corpus
    around a known seed paper, or to verify whether a paper actually cites
    work it claims to compare against.

    Args:
        paper_id: Semantic Scholar paperId or DOI.

    Returns:
        Dict with keys: citations (list), references (list). Each entry has
        paperId, title, year, authors. Returns {"error": "..."} on failure.
    """
    log.info("get_semantic_scholar_citations_and_references(paper_id=%r)", paper_id)
    try:
        return await asyncio.to_thread(ss_provider.get_citations_and_references, paper_id)
    except Exception as e:
        return {"error": f"get_semantic_scholar_citations_and_references failed: {e}"}


# ---------- Google Scholar -------------------------------------------------

@mcp.tool()
async def search_google_scholar(query: str, num_results: int = 5) -> list[dict[str, Any]]:
    """Search Google Scholar for broader academic coverage.

    Google Scholar indexes content beyond standard publications: blog posts,
    workshop papers, theses, technical reports, and pre-prints from sources
    other than arXiv. Use this as a third retrieval source to catch what
    arXiv and Semantic Scholar miss.

    Note: Google Scholar uses HTML scraping; results may vary and rate limits
    may apply. Treat results as best-effort.

    Args:
        query: Free-form search query.
        num_results: Maximum number of results to return (1-20, default 5).

    Returns:
        List of dicts with keys: title, authors, abstract, url. Returns
        [{"error": "..."}] on failure.
    """
    log.info("search_google_scholar(query=%r, num_results=%d)", query, num_results)
    try:
        return await asyncio.to_thread(gs_provider.search, query, num_results)
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
    months" for the temporal-expansion round of literature review) or
    constrain to a specific author's body of work.

    Args:
        query: Free-form search query.
        author: Optional author-name filter.
        year_start: Optional inclusive start year (e.g. 2024).
        year_end: Optional inclusive end year (e.g. 2026).
        num_results: Maximum number of results to return (1-20, default 5).

    Returns:
        List of dicts with keys: title, authors, abstract, url. Returns
        [{"error": "..."}] on failure.
    """
    log.info(
        "search_google_scholar_advanced(query=%r, author=%r, year_start=%r, year_end=%r, num_results=%d)",
        query, author, year_start, year_end, num_results,
    )
    year_range = (year_start, year_end) if (year_start or year_end) else None
    try:
        return await asyncio.to_thread(gs_provider.search_advanced, query, author, year_range, num_results)
    except Exception as e:
        return [{"error": f"search_google_scholar_advanced failed: {e}"}]


@mcp.tool()
async def get_google_scholar_author_info(author_name: str) -> dict[str, Any]:
    """Fetch a Google Scholar author profile.

    Returns affiliation, research interests, total citation count, and the
    author's top publications. Use to verify expertise claims or find an
    author's other work.

    Note: Uses the `scholarly` library which scrapes Google Scholar; may be
    rate-limited.

    Args:
        author_name: The author's name to look up (e.g. "Ian Goodfellow").

    Returns:
        Dict with keys: name, affiliation, interests, citedby, publications
        (list of top 5 with title, year, citations). Returns {"error": "..."}
        on failure.
    """
    log.info("get_google_scholar_author_info(author_name=%r)", author_name)
    try:
        return await asyncio.to_thread(gs_provider.get_author_info, author_name)
    except Exception as e:
        return {"error": f"get_google_scholar_author_info failed: {e}"}


# ---------- Server entrypoint ----------------------------------------------

if __name__ == "__main__":
    if os.environ.get("SEMANTIC_SCHOLAR_API_KEY"):
        log.info("Semantic Scholar API key detected — higher rate limits enabled.")
    else:
        log.info("No SEMANTIC_SCHOLAR_API_KEY in env — Semantic Scholar will use anonymous limits.")
    log.info("Starting Open ScholarPeer MCP server (osp_mcp)")
    mcp.run(transport="stdio")
