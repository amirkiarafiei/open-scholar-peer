"""Semantic Scholar provider.

Wraps the official `semanticscholar` Python client. All calls here are
synchronous and are run in a worker thread by osp_mcp.py, which also applies
the per-call timeout.

Two things this module is careful about, both of which cost real time when they
were missing:

1. **It never lets a result set page itself to exhaustion.** `PaginatedResults`
   iterates with `yield from self._items` and then keeps fetching pages while
   `_has_next_page()` is true. A plain list comprehension therefore walks the
   whole result set. `search_paper` allows up to 1000 results and the citation
   endpoints default to 10000, so one `limit=10` call could issue ~100 HTTP
   requests. With an API key the limit is 1 request per second, so that alone
   would exceed the 90 s call timeout. `_take` stops at the requested count.

2. **It asks for the fields it actually serializes.** `get_paper` defaults to
   all 76 `Paper.FIELDS`, which includes `embedding` plus 21 nested
   `citations.*` and 21 nested `references.*` fields, each carrying its own
   abstract. Responses are capped at 10 MB by the API, so a heavily-cited paper
   returns an error instead of a paper.

Reads the optional SEMANTIC_SCHOLAR_API_KEY env var for a keyed rate limit.
"""
from __future__ import annotations

import itertools
import os
import threading
from typing import Any

from semanticscholar import SemanticScholar


class SemanticScholarRateLimited(RuntimeError):
    """Semantic Scholar answered 429. Not an empty result."""


_client: SemanticScholar | None = None
_client_lock = threading.Lock()


def _get_client() -> SemanticScholar:
    """One client, with the package's own retry loop switched OFF.

    `retry=True` is the package default and it is the wrong default for us.
    ApiRequester turns an HTTP 429 into ConnectionRefusedError and retries it
    ten times with exponential backoff (min 5 s, max 60 s), so a single
    rate-limited call can sit there for roughly six minutes. The tool layer
    gives up at 90 s, but the worker thread cannot be cancelled, so it keeps
    hammering Semantic Scholar for minutes after the tool already returned a
    timeout — which makes the next call likelier to be throttled too.

    Failing in one round trip and saying "set an API key" is more useful than
    a six-minute stall the caller never sees the end of.
    """
    global _client
    with _client_lock:
        if _client is None:
            api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
            _client = SemanticScholar(api_key=api_key, retry=False)
    return _client


def _is_rate_limit(exc: BaseException) -> bool:
    """Is a 429 hiding anywhere in this exception chain?

    The package raises ConnectionRefusedError for HTTP 429, then tenacity
    wraps it in a RetryError even when retrying is off. Catching only the
    inner type misses every real case, so walk the chain.
    """
    seen, node = set(), exc
    while node is not None and id(node) not in seen:
        seen.add(id(node))
        if isinstance(node, ConnectionRefusedError):
            return True
        if "429" in str(node):
            return True
        node = node.__cause__ or node.__context__
    return False


def _call(fn, *args, **kwargs):
    """Run a client call and turn a 429 into something the agent can read."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        if not _is_rate_limit(e):
            raise
        raise SemanticScholarRateLimited(
            "Semantic Scholar rate-limited the request (HTTP 429). This is a "
            "rate limit, not an empty result — record the provider as "
            "unavailable rather than 'no papers found'. Anonymous access is "
            "shared across every unauthenticated caller; set "
            "SEMANTIC_SCHOLAR_API_KEY in .env for a dedicated limit."
        ) from e


def _take(results: Any, limit: int) -> list[Any]:
    """Take at most `limit` items and fetch no further pages.

    islice stops pulling once it has enough, which leaves the generator
    suspended inside `yield from self._items` and never reaches the
    page-fetching loop.
    """
    return list(itertools.islice(results, limit))


# ---------- Field lists ----------------------------------------------------
# Explicit, because every default is either too wide or missing something we
# serialize. Keep each list in step with the matching serializer below.

# For full paper records. This is Paper.SEARCH_FIELDS minus the parts we drop
# on the floor (citationStyles, s2FieldsOfStudy, corpusId, journal,
# publicationVenue) plus `tldr`, which no default list includes.
_PAPER_FIELDS = [
    "paperId", "title", "abstract", "year", "publicationDate", "venue",
    "publicationTypes", "citationCount", "influentialCitationCount",
    "referenceCount", "externalIds", "url", "isOpenAccess", "openAccessPdf",
    "fieldsOfStudy", "tldr", "authors",
]

# For citation/reference/recommendation lists, where hundreds of records may
# come back and only a summary of each is useful.
_SLIM_FIELDS = [
    "paperId", "title", "year", "citationCount", "externalIds",
    "isOpenAccess", "openAccessPdf", "authors",
]

_AUTHOR_FIELDS = [
    "authorId", "name", "url", "affiliations", "paperCount", "citationCount",
    "hIndex",
]


# ---------- Serializers ----------------------------------------------------

def _authors(obj: Any) -> list[dict[str, Any]]:
    return [
        {"name": getattr(a, "name", None), "authorId": getattr(a, "authorId", None)}
        for a in (getattr(obj, "authors", None) or [])
    ]


def _date_str(value: Any) -> str | None:
    """Render publicationDate as a plain date.

    The package parses it into a datetime, which json cannot serialize at all
    and which, once coerced, grows a midnight time component that was never in
    the API response.
    """
    if value is None:
        return None
    strftime = getattr(value, "strftime", None)
    return strftime("%Y-%m-%d") if strftime else str(value)


def _paper_to_dict(paper: Any) -> dict[str, Any]:
    tldr = getattr(paper, "tldr", None)
    return {
        "paperId": getattr(paper, "paperId", None),
        "title": getattr(paper, "title", None),
        "abstract": getattr(paper, "abstract", None),
        # A one-line auto-written summary. Useful for triage when the abstract
        # is long or missing.
        "tldr": getattr(tldr, "text", None) if tldr else None,
        "year": getattr(paper, "year", None),
        "publicationDate": _date_str(getattr(paper, "publicationDate", None)),
        "authors": _authors(paper),
        "url": getattr(paper, "url", None),
        "venue": getattr(paper, "venue", None),
        "publicationTypes": getattr(paper, "publicationTypes", None),
        "fieldsOfStudy": getattr(paper, "fieldsOfStudy", None),
        "citationCount": getattr(paper, "citationCount", None),
        "influentialCitationCount": getattr(paper, "influentialCitationCount", None),
        "referenceCount": getattr(paper, "referenceCount", None),
        "isOpenAccess": getattr(paper, "isOpenAccess", None),
        # The direct link to a legal PDF, when one exists. This is the input to
        # the full-text tools.
        "openAccessPdf": getattr(paper, "openAccessPdf", None),
        "externalIds": getattr(paper, "externalIds", None),
    }


def _author_to_dict(author: Any) -> dict[str, Any]:
    return {
        "authorId": getattr(author, "authorId", None),
        "name": getattr(author, "name", None),
        "url": getattr(author, "url", None),
        "affiliations": getattr(author, "affiliations", None),
        "paperCount": getattr(author, "paperCount", None),
        "citationCount": getattr(author, "citationCount", None),
        "hIndex": getattr(author, "hIndex", None),
    }


def _slim_paper(paper: Any) -> dict[str, Any]:
    """Minimal paper record for citation/reference/recommendation lists."""
    return {
        "paperId": getattr(paper, "paperId", None),
        "title": getattr(paper, "title", None),
        "year": getattr(paper, "year", None),
        "citationCount": getattr(paper, "citationCount", None),
        "isOpenAccess": getattr(paper, "isOpenAccess", None),
        "openAccessPdf": getattr(paper, "openAccessPdf", None),
        "externalIds": getattr(paper, "externalIds", None),
        "authors": _authors(paper),
    }


def _snippet_paper_to_dict(paper: Any) -> dict[str, Any]:
    """Serializer for SnippetPaper, which is not a Paper.

    It carries only corpus_id, title, authors and open_access_info, and its
    authors are plain strings rather than author objects. Passing it through
    the normal paper serializer produced null ids, null years and a list of
    {"name": null, "authorId": null}.
    """
    return {
        "corpusId": getattr(paper, "corpus_id", None),
        "title": getattr(paper, "title", None),
        "authors": list(getattr(paper, "authors", None) or []),
        "openAccessInfo": getattr(paper, "open_access_info", None),
    }


# ---------- Provider functions ---------------------------------------------

def search_papers(
    query: str,
    limit: int = 10,
    year: str | None = None,
    publication_date_or_year: str | None = None,
    venue: list[str] | None = None,
    fields_of_study: list[str] | None = None,
    publication_types: list[str] | None = None,
    open_access_pdf: bool | None = None,
    min_citation_count: int | None = None,
    sort: str | None = None,
) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))

    kwargs: dict[str, Any] = {"limit": limit, "fields": _PAPER_FIELDS}
    if year:
        kwargs["year"] = year
    if publication_date_or_year:
        kwargs["publication_date_or_year"] = publication_date_or_year
    if venue:
        kwargs["venue"] = venue
    if fields_of_study:
        kwargs["fields_of_study"] = fields_of_study
    if publication_types:
        kwargs["publication_types"] = publication_types
    if open_access_pdf:
        kwargs["open_access_pdf"] = True
    if min_citation_count is not None:
        kwargs["min_citation_count"] = int(min_citation_count)
    if sort:
        # The package refuses `sort` unless `bulk` is set: sorting is only
        # offered by the bulk endpoint, which does not rank by search
        # relevance.
        kwargs["sort"] = sort
        kwargs["bulk"] = True

    results = _call(_get_client().search_paper, query, **kwargs)
    return [_paper_to_dict(p) for p in _take(results, limit)]


def match_paper_title(title: str) -> dict[str, Any]:
    """Resolve a title to the single closest paper, with a match score."""
    paper = _call(
        _get_client().search_paper, title, match_title=True,
        fields=_PAPER_FIELDS,
    )
    record = _paper_to_dict(paper)
    # `Paper` declares no matchScore property and never assigns one, so
    # getattr always answers None. The value is only in the raw payload.
    # Same shape of mistake as the snippetId bug this milestone fixed.
    raw = getattr(paper, "raw_data", None) or {}
    record["matchScore"] = raw.get("matchScore")
    return record


def get_paper(paper_id: str) -> dict[str, Any]:
    paper = _call(_get_client().get_paper, paper_id, fields=_PAPER_FIELDS)
    return _paper_to_dict(paper)


def get_paper_references(paper_id: str, limit: int = 50) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    results = _call(_get_client().get_paper_references,
                    paper_id, limit=limit, fields=_SLIM_FIELDS)
    return [_slim_paper(r.paper) for r in _take(results, limit) if r.paper]


def get_paper_citations(paper_id: str, limit: int = 50) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    results = _call(_get_client().get_paper_citations,
                    paper_id, limit=limit, fields=_SLIM_FIELDS)
    return [_slim_paper(c.paper) for c in _take(results, limit) if c.paper]


def get_papers_batch(paper_ids: list[str]) -> list[dict[str, Any]]:
    if not paper_ids:
        return []
    asked = paper_ids[:500]
    papers = _call(_get_client().get_papers, asked, fields=_PAPER_FIELDS)
    found = [_paper_to_dict(p) for p in papers if p]
    # Silently returning 47 records for 50 ids hides which three failed.
    if len(found) < len(asked):
        resolved = {r.get("paperId") for r in found}
        resolved |= {
            v for r in found
            for v in (r.get("externalIds") or {}).values() if isinstance(v, str)
        }
        missing = [i for i in asked if i not in resolved]
        if missing:
            found.append({
                "warning": f"{len(missing)} of {len(asked)} ids did not "
                           f"resolve to a paper",
                "unresolved": missing[:50],
            })
    return found


def get_author(author_id: str) -> dict[str, Any]:
    author = _call(_get_client().get_author, author_id, fields=_AUTHOR_FIELDS)
    return _author_to_dict(author)


def search_authors(query: str, limit: int = 10) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    results = _call(_get_client().search_author, query, limit=limit, fields=_AUTHOR_FIELDS)
    return [_author_to_dict(a) for a in _take(results, limit)]


def get_author_papers(author_id: str, limit: int = 50) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    results = _call(_get_client().get_author_papers,
                    author_id, limit=limit, fields=_SLIM_FIELDS)
    return [_slim_paper(p) for p in _take(results, limit)]


def get_paper_recommendations(paper_id: str, limit: int = 10) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    results = _call(_get_client().get_recommended_papers,
                    paper_id, limit=limit, fields=_SLIM_FIELDS)
    return [_slim_paper(p) for p in _take(results, limit)]


def search_snippets(query: str, limit: int = 10) -> list[dict[str, Any]]:
    # The endpoint allows up to 1000, but each snippet is about 500 words, so
    # 50 already puts roughly 25,000 words in front of the agent. The cost is
    # paid in context, which nothing here meters.
    limit = max(1, min(int(limit), 50))
    results = _call(_get_client().search_snippet, query, limit=limit)
    out: list[dict[str, Any]] = []
    for s in _take(results, limit):
        inner = getattr(s, "snippet", None)
        out.append({
            "text": getattr(s, "text", None),
            "section": getattr(inner, "section", None) if inner else None,
            "snippetKind": getattr(inner, "snippet_kind", None) if inner else None,
            "score": getattr(s, "score", None),
            "paper": _snippet_paper_to_dict(s.paper) if getattr(s, "paper", None) else None,
        })
    return out
