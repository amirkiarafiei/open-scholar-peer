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
  OSP_CALL_TIMEOUT         — per-call timeout in seconds (default: 90).
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
from providers import europe_pmc as epmc_provider
from providers import zenodo as zenodo_provider
from providers import openalex as openalex_provider


def _err(tool: str, exc: Exception) -> dict[str, Any]:
    """Build the error record, tagged with a reason the agent can branch on.

    Prose alone makes the agent guess. `reason` separates "the provider would
    not talk to us" from "the call was wrong", because only the first means
    "record the provider as unavailable and carry on with the others".
    """
    reason = "failed"
    if isinstance(exc, gs_provider.GoogleScholarBlocked):
        reason = "blocked"
    elif isinstance(exc, gs_provider.GoogleScholarUnavailable):
        reason = "unavailable"
    elif isinstance(exc, (ss_provider.SemanticScholarRateLimited,
                          openalex_provider.OpenAlexRateLimited,
                          zenodo_provider.ZenodoRateLimited)):
        reason = "rate_limited"
    elif isinstance(exc, arxiv_provider.ArxivBusy):
        reason = "busy"
    elif isinstance(exc, (arxiv_provider.ArxivNotFound,
                          epmc_provider.EuropePmcNotFound,
                          openalex_provider.OpenAlexNotFound,
                          zenodo_provider.ZenodoNotFound,
                          gs_provider.GoogleScholarNotFound)):
        reason = "not_found"
    elif isinstance(exc, (arxiv_provider.ArxivFullTextError,
                          epmc_provider.EuropePmcError,
                          zenodo_provider.ZenodoError,
                          openalex_provider.OpenAlexError)):
        reason = "unavailable"
    elif isinstance(exc, TimeoutError):
        reason = "timeout"
    elif isinstance(exc, ValueError):
        reason = "bad_request"
    else:
        # The semanticscholar package raises its own types. Matched by name
        # so a missing optional dependency cannot break error reporting.
        name = type(exc).__name__
        if name == "ObjectNotFoundException":
            reason = "not_found"
        elif name == "BadQueryParametersException":
            reason = "bad_request"
    return {"error": f"{tool} failed: {exc}", "reason": reason}

try:
    from dotenv import load_dotenv
    load_dotenv()  # loads .env from CWD (project root) at server startup
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("osp_mcp")

mcp = FastMCP("osp_mcp")

_TIMEOUT = int(os.environ.get("OSP_CALL_TIMEOUT", "90"))

# ---------- Which databases this project uses -------------------------------
#
# The installer asks, and writes the answer to .env as OSP_SOURCES. Only the
# chosen sources have their tools registered, so a user reviewing CS papers is
# not carrying eleven biomedical and repository tools in every request. That
# is the whole reason the picker exists (D21): "always on" was rejected
# because a longer tool list costs the agent on every single call.
#
# UNSET MEANS ALL. Installs made before this existed, and anyone running a
# per-tool installer directly, keep every tool.

_ALL_SOURCES = (
    "arxiv", "semantic_scholar", "google_scholar",
    "europepmc", "zenodo", "openalex",
)

# Spellings a human might reasonably type into .env by hand.
_SOURCE_ALIASES = {
    "europe_pmc": "europepmc", "epmc": "europepmc", "pmc": "europepmc",
    "s2": "semantic_scholar", "semanticscholar": "semantic_scholar",
    "gscholar": "google_scholar", "scholar": "google_scholar",
    "openalex_works": "openalex", "open_alex": "openalex",
}


def _enabled_sources() -> set[str]:
    raw = os.environ.get("OSP_SOURCES", "").strip()
    # Someone hand-editing .env may well write OSP_SOURCES='arxiv, openalex'.
    # python-dotenv strips the quotes, a plain environment variable does not.
    raw = raw.strip("\"'").strip()
    if not raw:
        return set(_ALL_SOURCES)

    # Commas are the documented separator; whitespace is accepted because it
    # is the other thing a person types.
    asked = {
        _SOURCE_ALIASES.get(part, part)
        for part in (
            token.strip().lower().replace("-", "_")
            for token in raw.replace(",", " ").split()
        )
        if part
    }
    unknown = sorted(asked - set(_ALL_SOURCES))
    known = asked & set(_ALL_SOURCES)

    if unknown:
        log.warning("OSP_SOURCES names %s, which is not a source I know. "
                    "Known sources: %s", ", ".join(unknown), ", ".join(_ALL_SOURCES))
    if not known:
        # Better to be noisy and complete than silently useless.
        log.warning("OSP_SOURCES enabled no known source, so all of them are "
                    "on. Fix the value in .env or remove the line.")
        return set(_ALL_SOURCES)
    return known


_ENABLED = _enabled_sources()


def tool_for(source: str):
    """Register this tool only when its database is switched on."""
    def decorate(fn):
        if source in _ENABLED:
            return mcp.tool()(fn)
        return fn
    return decorate


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

@tool_for("arxiv")
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
        date_from: Optional start date (YYYY-MM-DD). Filtered by arXiv via
            submittedDate, so a narrow window still returns a full page.
        date_to: Optional end date (YYYY-MM-DD), inclusive of that whole day.
        categories: Optional list of arXiv category codes. Matches papers in
            any of them, including cross-listed ones.

    Returns:
        List of dicts with keys: arxiv_id, title, authors, summary, published,
        updated, link, pdf_url, primary_category, categories, comment, doi,
        journal_ref.
        Returns [{"error": "..."}] on failure.
    """
    log.info("search_arxiv(query=%r, max=%s, sort=%s, from=%s, to=%s, cats=%s)",
             query, max_results, sort_by, date_from, date_to, categories)
    try:
        return await _run(arxiv_provider.search, query, max_results, sort_by,
                          date_from, date_to, categories)
    except Exception as e:
        return [_err("search_arxiv", e)]


@tool_for("arxiv")
async def get_arxiv_paper_details(arxiv_id: str) -> dict[str, Any]:
    """Fetch detailed metadata for a specific arXiv paper by its ID.

    Use when you have a specific arXiv ID (e.g. "2305.14314" or "1706.03762")
    and want the full record with abstract, authors, dates, and categories.

    Args:
        arxiv_id: The arXiv identifier. New style "2305.14314", old style
            "hep-th/9901001", or pinned to a version "1706.03762v5".
            Without a version you get the latest one.

    Returns:
        Dict with keys: arxiv_id, title, authors, summary, published, updated,
        link, pdf_url, primary_category, categories, comment, doi, journal_ref.
        This is metadata only — for the body, the methods, the tables and the
        numbers, use read_arxiv_paper.
        Returns {"error": "..."} on failure.
    """
    log.info("get_arxiv_paper_details(arxiv_id=%r)", arxiv_id)
    try:
        return await _run(arxiv_provider.get_details, arxiv_id)
    except Exception as e:
        return _err("get_arxiv_paper_details", e)


@tool_for("arxiv")
async def read_arxiv_paper(
    arxiv_id: str, max_chars: int = 50000, offset: int = 0
) -> dict[str, Any]:
    """Read the FULL TEXT of an arXiv paper, not just its abstract.

    Use this when the abstract is not enough: to check whether a cited paper
    really reports the number the paper under review attributes to it, to read
    an experimental setup, or to find what a method section actually says.

    It returns the LaTeX source: the author's own text, with equations, table
    cells and section headings intact. For reading NUMBERS this beats a PDF
    conversion, which flattens a table into loose columns and can align a
    value to the wrong row.

    What it cannot do: **citations do not resolve.** The source carries
    `\citep{key}` markers, not the printed numbers, and the reference list is
    not in it. To turn a citation into a paper, use
    get_semantic_scholar_paper_references on the same paper. The title and
    author list ARE included. Nothing is written to disk.

    Long papers run past 100,000 characters, so the text comes in windows.
    Read the first, and while `next_offset` is not null call again with
    `offset` set to it. Windows end at a paragraph break, never mid-number.

    If the paper was submitted as a PDF with no source, this returns an error
    naming the PDF URL. The markitdown MCP server registered alongside this
    one reads it with convert_to_markdown — which is also the better route
    when you want the printed reference list.

    Args:
        arxiv_id: "2305.14314", "hep-th/9901001", or "1706.03762v5".
        max_chars: Characters per window (100-200000, default 50000).
        offset: Where to start reading (default 0).

    Returns:
        Dict with keys: arxiv_id, format, text, offset, returned_chars,
        next_offset (None at the end), total_chars, truncated, source,
        bibliography.
        Returns {"error": "...", "reason": "..."} on failure.
    """
    log.info("read_arxiv_paper(arxiv_id=%r, max_chars=%s, offset=%s)",
             arxiv_id, max_chars, offset)
    try:
        return await _run(arxiv_provider.read_paper, arxiv_id, max_chars, offset)
    except Exception as e:
        return _err("read_arxiv_paper", e)


# ---------- Europe PMC ------------------------------------------------------

@tool_for("europepmc")
async def search_europe_pmc(
    query: str,
    limit: int = 10,
    open_access_only: bool = True,
    sort: str | None = None,
) -> list[dict[str, Any]]:
    """Search Europe PMC — biomedical, health and life-science literature.

    Use this whenever the paper under review touches medicine, biology, public
    health, psychology or clinical work. arXiv covers almost none of that, and
    Europe PMC is the source that does. No API key is needed.

    Its other job is full text: for open-access articles it hands over the
    whole article as text through get_europe_pmc_full_text. Keep
    `open_access_only` true when you intend to read the paper — records
    without a `pmcid` have no full-text route, and they are the majority.

    Query syntax accepts field tags, for example:
      AUTH:"Smith"            author
      TITLE:"fatigue"         title
      PUB_YEAR:2024           year
      JOURNAL:"Lancet"        journal
      DOI:"10.1234/abc"       a specific DOI

    Args:
        query: Free-form query, or one using the field tags above.
        limit: Maximum results (1-100, default 10).
        open_access_only: Restrict to articles whose full text is readable
            here (default true).
        sort: e.g. "CITED desc" or "P_PDATE_D desc". Relevance if unset.

    Returns:
        List of dicts with keys: id, source, pmid, pmcid, doi, title, authors,
        journal, year, abstract, citedByCount, isOpenAccess, inEPMC,
        hasFullTextXML, fullTextUrls.
        Pass `pmcid` to get_europe_pmc_full_text to read the article, when
        `hasFullTextXML` is true. When it is false the `pmcid` is usually
        null and there is nothing to read here — use `fullTextUrls`.
        Returns [{"error": "...", "reason": "..."}] on failure.
    """
    log.info("search_europe_pmc(query=%r, limit=%s, oa=%s)",
             query, limit, open_access_only)
    try:
        return await _run(epmc_provider.search, query, limit,
                          open_access_only, sort)
    except Exception as e:
        return [_err("search_europe_pmc", e)]


@tool_for("europepmc")
async def get_europe_pmc_full_text(
    pmcid: str, max_chars: int = 50000, offset: int = 0
) -> dict[str, Any]:
    """Read the FULL TEXT of an open-access Europe PMC article.

    The cheapest full text there is: Europe PMC serves the whole article over
    a plain request, so there is no PDF to parse and no key to hold. Section
    headings are kept, and funding, competing-interest and data-availability
    statements survive — useful for a reproducibility check. Nothing is
    written to disk.

    **Table contents are NOT included — only the caption.** A number reported
    only inside a table will not be here; follow `fullTextUrls` for it. The
    reference list is replaced by a count.

    Get the `pmcid` from search_europe_pmc. Records where `hasFullTextXML` is
    false are not readable here — use the links in `fullTextUrls` instead.

    Long articles come in windows. While `next_offset` is not null, call again
    with `offset` set to it. Windows end at a paragraph break.

    Args:
        pmcid: The PMC identifier, e.g. "PMC12798607". A bare number works.
        max_chars: Characters per window (100-200000, default 50000).
        offset: Where to start reading (default 0).

    Returns:
        Dict with keys: pmcid, text, offset, returned_chars, next_offset
        (None at the end), total_chars, truncated, source.
        Returns {"error": "...", "reason": "..."} on failure.
    """
    log.info("get_europe_pmc_full_text(pmcid=%r, max_chars=%s, offset=%s)",
             pmcid, max_chars, offset)
    try:
        return await _run(epmc_provider.get_full_text, pmcid, max_chars, offset)
    except Exception as e:
        return _err("get_europe_pmc_full_text", e)


# ---------- Semantic Scholar -----------------------------------------------

@tool_for("semantic_scholar")
async def search_semantic_scholar(
    query: str,
    limit: int = 10,
    year: str | None = None,
    publication_date_or_year: str | None = None,
    venue: list[str] | None = None,
    fields_of_study: list[str] | None = None,
    publication_types: list[str] | None = None,
    open_access_pdf: bool = False,
    min_citation_count: int | None = None,
    sort: str | None = None,
) -> list[dict[str, Any]]:
    """Search Semantic Scholar for academic papers across all fields.

    Semantic Scholar provides high-quality citation-graph data, abstracts, and
    venue metadata. Use for established publications; for very recent pre-prints,
    prefer search_arxiv. Returns citation counts and author IDs for follow-up.

    It returns no full text. For biomedical work you may need to read rather
    than skim, search_europe_pmc does.

    Filters (all optional) let you narrow a round without post-filtering:
      year="2024"            → one year
      year="2020-2024"       → a range; "2020-" and "-2024" also work
      publication_date_or_year="2024-01-01:2024-06-30"  → a date window
      venue=["NeurIPS", "ICML"]
      fields_of_study=["Computer Science", "Medicine"]
      publication_types=["JournalArticle", "Review", "Conference"]
      open_access_pdf=True   → only papers with a free, legal PDF
      min_citation_count=50  → drop thinly-cited work

    Args:
        query: Free-form search query.
        limit: Maximum number of results (1-100, default 10).
        year: Publication year or range.
        publication_date_or_year: Date or date range, finer than `year`.
        venue: Restrict to these venues.
        fields_of_study: Restrict to these fields.
        publication_types: Restrict to these publication types.
        open_access_pdf: If true, only return papers with a free PDF.
        min_citation_count: Minimum citation count.
        sort: e.g. "citationCount:desc" or "publicationDate:desc". Sorting
            switches to the bulk endpoint, which does NOT rank by search
            relevance — leave it unset for ordinary relevance search.

    Returns:
        List of dicts with keys: paperId, title, abstract, tldr, year,
        publicationDate, authors, url, venue, publicationTypes, fieldsOfStudy,
        citationCount, influentialCitationCount, referenceCount, isOpenAccess,
        openAccessPdf, externalIds.
        Returns [{"error": "..."}] on failure.
    """
    log.info("search_semantic_scholar(query=%r, limit=%s, year=%s, sort=%s)",
             query, limit, year, sort)
    try:
        return await _run(
            ss_provider.search_papers, query, limit,
            year=year,
            publication_date_or_year=publication_date_or_year,
            venue=venue,
            fields_of_study=fields_of_study,
            publication_types=publication_types,
            open_access_pdf=open_access_pdf,
            min_citation_count=min_citation_count,
            sort=sort,
        )
    except Exception as e:
        return [_err("search_semantic_scholar", e)]


@tool_for("semantic_scholar")
async def match_semantic_scholar_title(title: str) -> dict[str, Any]:
    """Find the ONE paper whose title best matches the text you give.

    Use this to turn a line from a bibliography, or a title mentioned in the
    paper under review, into a real paperId. Ordinary search returns a ranked
    list and leaves you to guess; this returns a single record with a
    `matchScore`, which is the right way to resolve a reference.

    Args:
        title: The paper title, or the closest text you have to one.

    Returns:
        Dict with the usual paper keys plus matchScore (higher is a closer
        title match). Returns {"error": "..."} when nothing matches.
    """
    log.info("match_semantic_scholar_title(title=%r)", title)
    try:
        return await _run(ss_provider.match_paper_title, title)
    except Exception as e:
        return _err("match_semantic_scholar_title", e)


@tool_for("semantic_scholar")
async def get_semantic_scholar_paper(paper_id: str) -> dict[str, Any]:
    """Fetch full metadata for a specific Semantic Scholar paper.

    Use after search_semantic_scholar to get richer information, or when you
    have a known paperId, DOI, ArXiv ID, or ACL ID.

    Args:
        paper_id: Semantic Scholar paperId, DOI (e.g. "10.1038/nature14539"),
            ArXiv ID (e.g. "arXiv:1706.03762"), or ACL ID.

    Returns:
        Dict with keys: paperId, title, abstract, tldr, year, publicationDate,
        authors, url, venue, publicationTypes, fieldsOfStudy, citationCount,
        influentialCitationCount, referenceCount, isOpenAccess, openAccessPdf,
        externalIds.
        Returns {"error": "..."} on failure.
    """
    log.info("get_semantic_scholar_paper(paper_id=%r)", paper_id)
    try:
        return await _run(ss_provider.get_paper, paper_id)
    except Exception as e:
        return _err("get_semantic_scholar_paper", e)


@tool_for("semantic_scholar")
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
        List of dicts with keys: paperId, title, year, citationCount,
        isOpenAccess, openAccessPdf, externalIds, authors.
        Returns [{"error": "..."}] on failure.
    """
    log.info("get_semantic_scholar_paper_references(paper_id=%r, limit=%s)", paper_id, limit)
    try:
        return await _run(ss_provider.get_paper_references, paper_id, limit)
    except Exception as e:
        return [_err("get_semantic_scholar_paper_references", e)]


@tool_for("semantic_scholar")
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
        List of dicts with keys: paperId, title, year, citationCount,
        isOpenAccess, openAccessPdf, externalIds, authors.
        Returns [{"error": "..."}] on failure.
    """
    log.info("get_semantic_scholar_paper_citations(paper_id=%r, limit=%s)", paper_id, limit)
    try:
        return await _run(ss_provider.get_paper_citations, paper_id, limit)
    except Exception as e:
        return [_err("get_semantic_scholar_paper_citations", e)]


@tool_for("semantic_scholar")
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
    log.info("get_semantic_scholar_papers_batch(n=%s)", len(paper_ids))
    try:
        return await _run(ss_provider.get_papers_batch, paper_ids)
    except Exception as e:
        return [_err("get_semantic_scholar_papers_batch", e)]


@tool_for("semantic_scholar")
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
        return _err("get_semantic_scholar_author", e)


@tool_for("semantic_scholar")
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
    log.info("search_semantic_scholar_authors(query=%r, limit=%s)", query, limit)
    try:
        return await _run(ss_provider.search_authors, query, limit)
    except Exception as e:
        return [_err("search_semantic_scholar_authors", e)]


@tool_for("semantic_scholar")
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
    log.info("get_semantic_scholar_author_papers(author_id=%r, limit=%s)", author_id, limit)
    try:
        return await _run(ss_provider.get_author_papers, author_id, limit)
    except Exception as e:
        return [_err("get_semantic_scholar_author_papers", e)]


@tool_for("semantic_scholar")
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
    log.info("get_semantic_scholar_paper_recommendations(paper_id=%r, limit=%s)", paper_id, limit)
    try:
        return await _run(ss_provider.get_paper_recommendations, paper_id, limit)
    except Exception as e:
        return [_err("get_semantic_scholar_paper_recommendations", e)]


@tool_for("semantic_scholar")
async def search_semantic_scholar_snippets(
    query: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Search for text snippets from paper abstracts/bodies matching a query.

    Unlike search_semantic_scholar (which matches metadata), this returns
    actual ~500-word excerpts from paper text.

    Use it to DISCOVER which papers contain a claim, when you do not yet know
    which paper to read. It searches the whole corpus and CANNOT be limited to
    one paper. To check what a specific paper says, read that paper:
    read_arxiv_paper or get_europe_pmc_full_text.

    Args:
        query: Free-form query describing the content to find.
        limit: Max snippets (1-50, default 10). Each is about 500 words, so
            50 already puts roughly 25,000 words in front of you.

    Returns:
        List of dicts with keys: text, section, snippetKind, score, and paper
        (corpusId, title, authors as plain names, openAccessInfo). A snippet
        record carries no paperId — use match_semantic_scholar_title on the
        title if you need one.
        Returns [{"error": "..."}] on failure.
    """
    log.info("search_semantic_scholar_snippets(query=%r, limit=%s)", query, limit)
    try:
        return await _run(ss_provider.search_snippets, query, limit)
    except Exception as e:
        return [_err("search_semantic_scholar_snippets", e)]


# ---------- Google Scholar -------------------------------------------------

@tool_for("google_scholar")
async def search_google_scholar(query: str, num_results: int = 5) -> list[dict[str, Any]]:
    """Search Google Scholar for broader academic coverage.

    Google Scholar indexes content beyond standard publications: blog posts,
    workshop papers, theses, technical reports, and pre-prints from sources
    other than arXiv. Use as a third retrieval source to catch what arXiv
    and Semantic Scholar miss.

    Note: Uses HTML scraping. If Google blocks the request this returns an
    error, NOT an empty list. An empty list means the search genuinely found
    nothing. Record a block as "provider unavailable" in Provenance — never as
    "no papers found".

    Args:
        query: Free-form search query.
        num_results: Maximum number of results (1-20, default 5).

    Returns:
        List of dicts with keys: title, authors, abstract, url.
        Returns [{"error": "..."}] on failure.
    """
    log.info("search_google_scholar(query=%r, num_results=%s)", query, num_results)
    try:
        return await _run(gs_provider.search, query, num_results)
    except Exception as e:
        return [_err("search_google_scholar", e)]


@tool_for("google_scholar")
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

    Note: Uses HTML scraping. If Google blocks the request this returns an
    error, NOT an empty list. An empty list means the search genuinely found
    nothing. Record a block as "provider unavailable" in Provenance — never as
    "no papers found".

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
        return [_err("search_google_scholar_advanced", e)]


@tool_for("google_scholar")
async def get_google_scholar_author_info(author_name: str) -> dict[str, Any]:
    """Fetch a Google Scholar author profile.

    Returns affiliation, research interests, total citation count, and the
    author's top publications. Use to verify expertise claims or find an
    author's other work.

    Note: Uses the `scholarly` library, which scrapes the same host. If Google
    blocks the request this returns an error with reason "blocked", NOT an
    empty profile. Record a block as "provider unavailable" — never as "no
    profile found".

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
        return _err("get_google_scholar_author_info", e)


# ---------- Zenodo ----------------------------------------------------------

@tool_for("zenodo")
async def search_zenodo(
    query: str, limit: int = 10, resource_type: str = "software",
) -> list[dict[str, Any]]:
    """Find released code, datasets and other research artifacts on Zenodo.

    **This does not find papers. Do not use it in a literature round.**

    It answers one question the other tools cannot: *did the authors actually
    release their code and data?* Most review forms ask for that, and it can
    only be checked by looking. Search the paper's title, its method name, or
    the authors' names, and see whether anything with a DOI comes back.

    An empty result is meaningful here — it is evidence that nothing was
    deposited on Zenodo. It is not proof: code often lives only on GitHub, so
    say "nothing found on Zenodo", not "the authors released nothing".

    Args:
        query: Paper title, method name, or author names.
        limit: Maximum results (1-50, default 10).
        resource_type: One of software, dataset, publication, poster,
            presentation, image, video, lesson, physicalobject, other.
            Pass an empty string to search all types.

    Returns:
        List of dicts with keys: id, doi, title, type, subtype,
        publicationDate, description, creators, license, version, url,
        relatedIdentifiers (where the code actually lives, e.g. a GitHub
        URL), fileCount.
        Returns [{"error": "...", "reason": "..."}] on failure.
    """
    log.info("search_zenodo(query=%r, limit=%s, type=%s)",
             query, limit, resource_type)
    try:
        return await _run(zenodo_provider.search, query, limit,
                          resource_type or None)
    except Exception as e:
        return [_err("search_zenodo", e)]


# ---------- OpenAlex --------------------------------------------------------

@tool_for("openalex")
async def search_openalex(
    query: str,
    limit: int = 10,
    from_year: int | None = None,
    to_year: int | None = None,
    open_access_only: bool = False,
    exclude_retracted: bool = False,
    work_type: str | None = None,
    sort: str | None = None,
) -> list[dict[str, Any]]:
    """Search OpenAlex — an open index of roughly 327 million works.

    Broad coverage across every field, with two things the other search tools
    do not give you: a **retraction flag** on every record, and `fwci`, which
    compares a paper's citations against the average for its own field, year
    and type. Above 1 is above average, so it is a fairer measure than a raw
    citation count when comparing across fields.

    Abstracts are returned as ordinary readable text. OpenAlex stores them
    inverted, as word positions; that is rebuilt here.

    Works without a key. A key raises the daily budget a long way, and keyless
    access is small enough to run out during a heavy review — set
    OPENALEX_API_KEY in .env if you hit a rate-limit error.

    Args:
        query: Free-form search query.
        limit: Maximum results (1-50, default 10).
        from_year: Earliest publication year.
        to_year: Latest publication year.
        open_access_only: Only works with a free full text.
        exclude_retracted: Drop retracted works from the results.
        work_type: e.g. "article", "review", "preprint", "dataset".
        sort: e.g. "cited_by_count:desc", "publication_date:desc".

    Returns:
        List of dicts with keys: id, doi, title, year, publicationDate, type,
        venue, authors (with institutions), abstract, citedByCount, fwci,
        topics, isOpenAccess, oaUrl, isRetracted, referencedWorksCount,
        referencedWorks.
        Returns [{"error": "...", "reason": "..."}] on failure.
    """
    log.info("search_openalex(query=%r, limit=%s, years=%s-%s)",
             query, limit, from_year, to_year)
    try:
        return await _run(openalex_provider.search, query, limit, from_year,
                          to_year, open_access_only, exclude_retracted,
                          work_type, sort)
    except Exception as e:
        return [_err("search_openalex", e)]


@tool_for("openalex")
async def get_openalex_work(identifier: str) -> dict[str, Any]:
    """Look up one work, and find out whether it has been RETRACTED.

    This is the retraction check. Nothing else in this toolset can tell you
    that a cited paper was withdrawn, and recommending "accept" on a paper
    that leans on retracted work is exactly the failure it prevents. Give it
    the DOI from a bibliography line and read `isRetracted`.

    Worth doing for any citation the paper's argument rests on, and for any
    reference that looks unusually old, unusually central, or biomedical.

    Args:
        identifier: A DOI ("10.1038/nature14539"), a doi.org URL, an OpenAlex
            id ("W2741809807"), or a PMID (bare digits). **Not an arXiv id** —
            OpenAlex has no arXiv namespace. Get the DOI first, from
            get_arxiv_paper_details or get_semantic_scholar_paper.

    Returns:
        Dict with the same keys as search_openalex, for that one work.
        `isRetracted` is the field to read. Returns
        {"error": "...", "reason": "..."} when there is no such work.
    """
    log.info("get_openalex_work(identifier=%r)", identifier)
    try:
        return await _run(openalex_provider.get_work, identifier)
    except Exception as e:
        return _err("get_openalex_work", e)


# ---------- Server entrypoint ----------------------------------------------

if __name__ == "__main__":
    if os.environ.get("SEMANTIC_SCHOLAR_API_KEY"):
        log.info("Semantic Scholar API key detected — higher rate limits enabled.")
    else:
        log.info("No SEMANTIC_SCHOLAR_API_KEY in env — Semantic Scholar will use anonymous limits.")
    if os.environ.get("OSP_SOURCES", "").strip():
        log.info("Databases enabled by OSP_SOURCES: %s",
                 ", ".join(sorted(_ENABLED)))
    else:
        log.info("OSP_SOURCES not set — all %s databases enabled.",
                 len(_ALL_SOURCES))
    log.info("Starting Open ScholarPeer MCP server (osp_mcp), timeout=%ss", _TIMEOUT)
    mcp.run(transport="stdio")
