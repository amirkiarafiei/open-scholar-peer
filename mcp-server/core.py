"""
core.py — the Open ScholarPeer search tools, with no transport attached.

`osp_mcp.py` serves these over MCP; `osp_cli.py` serves the same function
objects over argv. Neither front end owns anything the other needs, which is
the whole point: the command-line fallback must not fail when the thing it is
a fallback for is broken.

Three properties here are load-bearing and easy to undo by accident:

  1. Providers are imported LAZILY. `osp_cli.py list` must answer when `arxiv`,
     `bs4`, `requests` or `semanticscholar` is broken, and it must answer in
     tens of milliseconds. Touching a provider at import time costs both.
  2. `asyncio` is imported inside `_run`, not at module level. It costs 37 ms,
     and the `list` and `schema` paths never reach it.
  3. `logging.basicConfig()` is NOT called here. It configures the ROOT logger,
     and each front end wants a different answer: the MCP server logs INFO to
     stderr, the CLI stays silent unless asked. A library does not decide that.

Design principles, unchanged from the server this was extracted from:
  1. Dumb tools only — no agentic logic. Each tool is atomic, stateless.
  2. Rich docstrings — agents read these to decide when to call which tool.
  3. Consistent error envelope — every tool returns records or an error record,
     never raises, and never reports a failure as an empty list.
  4. Per-call timeout — every blocking call goes through `_run`.

Environment variables:
  SEMANTIC_SCHOLAR_API_KEY — optional; provides higher rate limits if set.
  OSP_CALL_TIMEOUT         — per-call timeout in seconds (default: 90).
  OSP_SOURCES              — which databases this project switched on.
"""
from __future__ import annotations

import importlib.util
import logging
import os
import sys
from contextvars import ContextVar
from typing import Any, Callable, NamedTuple

# ---------- Environment ----------------------------------------------------
# Order is load-bearing: the .env file has to be read before anything else
# looks at os.environ, or OSP_CALL_TIMEOUT and OSP_SOURCES are read as unset.
try:
    from dotenv import load_dotenv
    load_dotenv()  # loads .env from CWD (project root)
except ImportError:
    pass

_DEFAULT_TIMEOUT = float(os.environ.get("OSP_CALL_TIMEOUT", "90"))

# A ContextVar rather than a module global, because the CLI takes --timeout and
# _run reads the value at 22 call sites. It propagates into asyncio.to_thread.
CALL_TIMEOUT: ContextVar[float] = ContextVar("osp_call_timeout",
                                             default=_DEFAULT_TIMEOUT)

log = logging.getLogger("osp_mcp")  # name kept: existing guidance greps for it


# ---------- Providers, imported only when touched --------------------------

def _lazy(dotted: str):
    """A real module object that does not execute until something touches it.

    Not a proxy. importlib swaps the module's __class__ on first attribute
    access, so afterwards it is indistinguishable from a normal import and the
    tool bodies below can keep saying `arxiv_provider.search` unchanged.

    A module __getattr__ (PEP 562) would NOT work here: it is not consulted for
    a LOAD_GLOBAL inside a function defined in this module, so the tool bodies
    would raise NameError. Measured: six lazy stubs cost 0.3 ms against 149 ms
    to import all six providers eagerly.
    """
    if dotted in sys.modules:
        return sys.modules[dotted]
    spec = importlib.util.find_spec(dotted)
    spec.loader = importlib.util.LazyLoader(spec.loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[dotted] = module
    spec.loader.exec_module(module)
    return module


arxiv_provider = _lazy("providers.arxiv")
ss_provider = _lazy("providers.semantic_scholar")
gs_provider = _lazy("providers.google_scholar")
epmc_provider = _lazy("providers.europe_pmc")
zenodo_provider = _lazy("providers.zenodo")
openalex_provider = _lazy("providers.openalex")


def warm_providers() -> None:
    """Import every enabled provider now, instead of on first call.

    For the MCP server only. It is one long-lived process, so paying 149 ms once
    at start-up is free, and it removes any question about two concurrent calls
    racing to be the first to touch the same lazy module. The CLI never calls
    this: one process serves one call, and start cost is the thing being saved.
    """
    by_source = {
        "arxiv": arxiv_provider, "semantic_scholar": ss_provider,
        "google_scholar": gs_provider, "europepmc": epmc_provider,
        "zenodo": zenodo_provider, "openalex": openalex_provider,
    }
    for source in enabled_sources():
        getattr(by_source[source], "__name__", None)  # forces the exec


# ---------- The error envelope ---------------------------------------------

# Matched by exception class NAME along the MRO, not by isinstance. Importing
# six provider modules to report an error means a broken dependency breaks the
# report of itself — and the report is the only thing standing between "the
# provider failed" and "there are no papers". The file already matched the
# semanticscholar package's exceptions by name; this generalises that.
#
# Order within the table does not matter. Precedence comes from the MRO, which
# puts the more specific class first — the same precedence the hand-ordered
# isinstance chain encoded (GoogleScholarBlocked before GoogleScholarUnavailable,
# ArxivNotFound before ArxivFullTextError, ZenodoRateLimited before ZenodoError).
_REASON_BY_EXCEPTION: dict[str, str] = {
    # Google Scholar: Blocked is a subclass of Unavailable.
    "GoogleScholarBlocked": "blocked",
    "GoogleScholarUnavailable": "unavailable",
    "GoogleScholarNotFound": "not_found",
    # Rate limits.
    "SemanticScholarRateLimited": "rate_limited",
    "OpenAlexRateLimited": "rate_limited",
    "ZenodoRateLimited": "rate_limited",
    # arXiv.
    "ArxivBusy": "busy",
    "ArxivNotFound": "not_found",
    "ArxivFullTextError": "unavailable",
    # Europe PMC, Zenodo, OpenAlex.
    "EuropePmcNotFound": "not_found",
    "EuropePmcError": "unavailable",
    "ZenodoNotFound": "not_found",
    "ZenodoError": "unavailable",
    "OpenAlexNotFound": "not_found",
    "OpenAlexError": "unavailable",
    # The semanticscholar package raises its own types. Matched by name since
    # before this change, so a missing optional dependency cannot break error
    # reporting.
    "ObjectNotFoundException": "not_found",
    "BadQueryParametersException": "bad_request",
    # Builtins.
    "TimeoutError": "timeout",
    "ValueError": "bad_request",
}


def _err(tool: str, exc: Exception) -> dict[str, Any]:
    """Build the error record, tagged with a reason the agent can branch on.

    Prose alone makes the agent guess. `reason` separates "the provider would
    not talk to us" from "the call was wrong", because only the first means
    "record the provider as unavailable and carry on with the others".
    """
    for cls in type(exc).__mro__:
        reason = _REASON_BY_EXCEPTION.get(cls.__name__)
        if reason is not None:
            break
    else:
        reason = "failed"

    detail = f"{tool} failed: {exc}"
    if isinstance(exc, ImportError):
        # Providers are imported lazily, so a missing package now surfaces on
        # the first call rather than at start-up. Without this sentence an
        # agent sees several tools fail in a row and concludes the databases
        # are down, when the truth is that this install is incomplete.
        detail += (" — this is a missing dependency in the install, not a "
                   "problem with the database. Re-run the OSP installer to "
                   "rebuild .open-scholar-peer/mcp/.venv.")
    return {"error": detail, "reason": reason}


# ---------- Which databases this project switched on ------------------------

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


def enabled_sources() -> set[str]:
    """The databases OSP_SOURCES switches on, read from the environment NOW.

    Deliberately a function, not a module constant computed at import. A
    constant is wrong twice: a test that re-executes a front end with a
    different OSP_SOURCES gets a cached answer from the first run, and the
    value is fixed before any front end has configured logging, so the
    warnings below are formatted by Python's handler of last resort.
    """
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


# ---------- The tool registry ----------------------------------------------

class Tool(NamedTuple):
    """One search tool: what it is called, whose database it reads, and the
    function itself. `doc` is fn.__doc__ verbatim — the same string FastMCP
    publishes as the tool description, so both surfaces show one text."""
    name: str
    source: str
    fn: Callable[..., Any]
    doc: str


REGISTRY: dict[str, Tool] = {}


def tool_for(source: str):
    """Record this tool under the database it reads.

    Registration only. Unlike the decorator this replaces, it does NOT gate:
    a switched-off tool stays in REGISTRY, because "present but not enabled" is
    exactly the set the CLI has to describe when an agent asks for a database
    this project turned off. Telling that apart from "no such tool" is the
    difference between sending someone to .env and sending them to hunt a typo.

    The spelling is kept so `grep -c '^@tool_for(' core.py` is still the count.
    """
    if source not in _ALL_SOURCES:
        raise ValueError(f"{source!r} is not one of {_ALL_SOURCES}")

    def decorate(fn):
        REGISTRY[fn.__name__] = Tool(fn.__name__, source, fn, fn.__doc__ or "")
        return fn  # returned unchanged; nothing wraps a tool
    return decorate


def enabled_tools() -> dict[str, Tool]:
    """The tools this project serves, computed from the environment now."""
    on = enabled_sources()
    return {name: t for name, t in REGISTRY.items() if t.source in on}


def is_gated_off(name: str) -> bool:
    """True when `name` is a real tool whose database this project switched off.

    Registry membership, not module identity. The predicate this replaces
    compared fn.__module__ against the importing module's name, which worked
    only while the tools lived in the same file as the server — and would
    silently return False for every tool once they moved here, turning "this
    database is switched off" into "no such tool".
    """
    return name in REGISTRY and name not in enabled_tools()


# ---------- Describing a tool's arguments ----------------------------------

# The seven annotation forms the 22 tools use. This is the whole set, and a
# test freezes the census so an eighth cannot arrive unnoticed.
_LEAF_SCHEMA: dict[Any, dict[str, Any]] = {
    str: {"type": "string"},
    bool: {"type": "boolean"},
    int: {"type": "integer"},
    list[str]: {"items": {"type": "string"}, "type": "array"},
}


class UnknownAnnotation(TypeError):
    """An annotation the two derivers have not been shown to describe alike."""


def _leaf_schema(ann: Any, tool: str, param: str) -> dict[str, Any]:
    try:
        return dict(_LEAF_SCHEMA[ann])
    except (KeyError, TypeError):
        raise UnknownAnnotation(
            f"{tool}({param}): annotation {ann!r} is not one of the seven forms "
            f"this project has shown FastMCP and the CLI to describe "
            f"identically. Add it to _LEAF_SCHEMA and to the parity test in the "
            f"same change, or the two surfaces will disagree in silence."
        ) from None


def input_schema(fn: Callable[..., Any]) -> dict[str, Any]:
    """The JSON Schema for a tool's arguments, derived from its signature.

    **Neither surface owns a schema.** FastMCP derives one through pydantic;
    this derives the same one through `inspect.signature`. A human edits one
    decorated function and both follow — so this is not the "two artifacts a
    human keeps in step" drift this project has paid for elsewhere. Saying
    otherwise would invite someone to hand-write 22 schemas and create the
    second source that does not exist today.

    It exists because the CLI must describe its tools without importing `mcp`.
    `scripts/test_schema_parity.py` pins the two derivers against each other,
    byte for byte, so they cannot drift.

    Two rules make the output byte-identical to pydantic's rather than merely
    equivalent: keys are sorted alphabetically at both levels, and each field
    carries the title pydantic generates, `name.replace("_", " ").title()`.
    """
    import inspect
    import typing

    hints = typing.get_type_hints(fn)
    props: dict[str, Any] = {}
    required: list[str] = []
    for name, param in inspect.signature(fn).parameters.items():
        ann = hints[name]
        args = typing.get_args(ann)
        if type(None) in args:  # X | None
            inner = [a for a in args if a is not type(None)]
            if len(inner) != 1:
                raise UnknownAnnotation(
                    f"{fn.__name__}({name}): a union of {len(inner)} types; "
                    f"pydantic emits a different anyOf and this does not model it."
                )
            body: dict[str, Any] = {
                "anyOf": [_leaf_schema(inner[0], fn.__name__, name),
                          {"type": "null"}]
            }
        else:
            body = _leaf_schema(ann, fn.__name__, name)

        if param.default is inspect.Parameter.empty:
            required.append(name)
        else:
            body["default"] = param.default
        body["title"] = name.replace("_", " ").title()
        props[name] = dict(sorted(body.items()))

    out: dict[str, Any] = {
        "properties": props,
        "title": f"{fn.__name__}Arguments",
        "type": "object",
    }
    if required:
        out["required"] = required
    return dict(sorted(out.items()))


def required_args(fn: Callable[..., Any]) -> list[str]:
    """Which arguments have no default.

    Deliberately does not look at an annotation, so a tool with an annotation
    neither deriver understands still appears correctly in `osp_cli.py list`.
    One bad annotation must not take the other 21 tools off the list.
    """
    import inspect
    return [n for n, p in inspect.signature(fn).parameters.items()
            if p.default is inspect.Parameter.empty]


async def _run(fn, *args, **kwargs) -> Any:
    """Run a synchronous provider function in a thread with a timeout."""
    import asyncio  # 37 ms; `list` and `schema` never reach this line

    timeout = CALL_TIMEOUT.get()
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(fn, *args, **kwargs),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        raise TimeoutError(f"{fn.__name__} timed out after {timeout}s")


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

