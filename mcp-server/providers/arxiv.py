"""arXiv provider — uses the official `arxiv` Python package.

The package handles HTTPS, request spacing and pagination, avoiding the 429
errors produced by raw HTTP calls to the Atom API.

Filtering is done by arXiv, not by us. An earlier version fetched by relevance
and then dropped out-of-range papers in Python, which made a narrow date window
return almost nothing.
"""
from __future__ import annotations

import calendar as _calendar
import re
import threading
from contextlib import contextmanager
from typing import Any

import arxiv
from dateutil import parser as _dp

# One client for the whole process, and one request at a time.
#
# arXiv's Terms of Use ask for "no more than one request every three seconds"
# and "a single connection at a time", and say this applies "to all of the
# machines under your control as a whole". The package spaces its requests
# using a timestamp stored on the client instance, so building a new client per
# call silently removes the gap. Provider functions run in worker threads
# (asyncio.to_thread) and the Literature skill dispatches providers at the same
# time, so the shared client is locked as well as shared.
#
# Sharing a lock means one stuck request could block every other arXiv call,
# and `asyncio.to_thread` cannot cancel the thread holding it. Two bounds stop
# that: the HTTP session gets a timeout the package does not set, and waiters
# give up instead of queueing forever. Without both, a single hung socket
# would wedge the provider for the life of the process.

# arxiv.Client retries num_retries (3) times, so 3 x 20 s plus the 3 s spacing
# stays inside the 90 s OSP_CALL_TIMEOUT.
_HTTP_TIMEOUT = 20
_LOCK_WAIT = 25

_CLIENT = arxiv.Client()
_CLIENT_LOCK = threading.Lock()


def _add_session_timeout(client: arxiv.Client, seconds: int) -> None:
    """Give the package's session a request timeout.

    arxiv 4.0.1 calls `self._session.get(url, headers=...)` with no timeout,
    and requests then waits forever by default. Patching the bound method
    keeps whatever adapters the package mounted.
    """
    session = getattr(client, "_session", None)
    if session is None:
        return
    original = session.request

    def request(*args, **kwargs):
        kwargs.setdefault("timeout", seconds)
        return original(*args, **kwargs)

    session.request = request


_add_session_timeout(_CLIENT, _HTTP_TIMEOUT)


class ArxivBusy(RuntimeError):
    """Another arXiv call is still running. Not an empty result."""


@contextmanager
def _arxiv_turn():
    """Take the single arXiv connection, or give up rather than queue."""
    if not _CLIENT_LOCK.acquire(timeout=_LOCK_WAIT):
        raise ArxivBusy(
            f"another arXiv request has held the single allowed connection "
            f"for more than {_LOCK_WAIT}s. arXiv's terms allow one request at "
            "a time, so this call was not sent. This is a busy provider, not "
            "an empty result — try again, or use the other providers."
        )
    try:
        yield
    finally:
        _CLIENT_LOCK.release()

# arXiv ranges need both ends, so an open-ended request gets a wide default.
_STAMP_MIN = "190001010000"
_STAMP_MAX = "299912312359"


def _paper_to_dict(paper: arxiv.Result) -> dict[str, Any]:
    return {
        "arxiv_id": paper.get_short_id(),
        "title": paper.title,
        "authors": [a.name for a in paper.authors],
        "summary": paper.summary,
        "published": paper.published.isoformat() if paper.published else None,
        "updated": paper.updated.isoformat() if paper.updated else None,
        "link": paper.entry_id,
        "pdf_url": paper.pdf_url,
        "primary_category": paper.primary_category,
        "categories": list(paper.categories),
        "comment": paper.comment or "",
        "doi": paper.doi,
        "journal_ref": paper.journal_ref,
    }


def _stamp(value: str, *, end: bool) -> str:
    """Turn a date string into arXiv's YYYYMMDDHHMM stamp.

    Partial dates are widened to the whole period they name, and this is the
    reason the function exists rather than calling dateutil directly:
    `dateutil.parser.parse("2024")` fills the gaps from *today*, returning
    2024-09-20 on the day this was written. A caller asking for "everything
    from 2024" would silently lose January to September, and nothing would
    look wrong. Same trap with "2024-06", which becomes the 20th.

      "2024"       -> 2024-01-01 00:00 as a start, 2024-12-31 23:59 as an end
      "2024-06"    -> 2024-06-01 00:00 as a start, 2024-06-30 23:59 as an end
      "2024-06-15" -> that day, from 00:00 or up to 23:59

    A date that already carries a time is used exactly as given.
    """
    value = (value or "").strip()

    if re.fullmatch(r"\d{4}", value):
        year = int(value)
        return f"{year}1231" "2359" if end else f"{year}0101" "0000"

    if re.fullmatch(r"\d{4}-\d{1,2}", value):
        year, month = (int(x) for x in value.split("-"))
        if not end:
            return f"{year:04d}{month:02d}01" "0000"
        last = _calendar.monthrange(year, month)[1]
        return f"{year:04d}{month:02d}{last:02d}" "2359"

    dt = _dp.parse(value)
    if end and dt.hour == 0 and dt.minute == 0:
        dt = dt.replace(hour=23, minute=59)
    return dt.strftime("%Y%m%d%H%M")


def build_query(
    query: str,
    date_from: str | None = None,
    date_to: str | None = None,
    categories: list[str] | None = None,
) -> str:
    """Build one arXiv `search_query` string. Pure — unit tested offline.

    Every part is joined with AND. Leaving the operator out makes arXiv OR the
    parts instead, which is why a category filter used to do nothing.
    """
    parts: list[str] = []

    text = (query or "").strip()
    if text:
        parts.append(f"({text})")

    if categories:
        cats = [c.strip() for c in categories if c and c.strip()]
        if cats:
            parts.append("(" + " OR ".join(f"cat:{c}" for c in cats) + ")")

    if date_from or date_to:
        low = _stamp(date_from, end=False) if date_from else _STAMP_MIN
        high = _stamp(date_to, end=True) if date_to else _STAMP_MAX
        parts.append(f"submittedDate:[{low} TO {high}]")

    return " AND ".join(parts)


def search(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance",
    date_from: str | None = None,
    date_to: str | None = None,
    categories: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Search arXiv papers. Returns a list of paper dicts."""
    max_results = max(1, min(int(max_results), 50))

    full_query = build_query(query, date_from, date_to, categories)
    if not full_query:
        raise ValueError("need a query, a category, or a date range")

    sort_criterion = (
        arxiv.SortCriterion.Relevance
        if sort_by == "relevance"
        else arxiv.SortCriterion.SubmittedDate
    )

    search_obj = arxiv.Search(
        query=full_query, max_results=max_results, sort_by=sort_criterion
    )

    with _arxiv_turn():
        return [_paper_to_dict(p) for p in _CLIENT.results(search_obj)]


def get_details(arxiv_id: str) -> dict[str, Any]:
    """Fetch metadata for a specific arXiv paper by ID.

    Uses `id_list`, which the arXiv manual prefers "to properly handle article
    versions". Versioned ("2305.14314v2") and old-style ("cs.CL/0306050") IDs
    both work. Do not change this to a query.
    """
    search_obj = arxiv.Search(id_list=[arxiv_id.strip()])
    with _arxiv_turn():
        papers = list(_CLIENT.results(search_obj))
    if not papers:
        hint = ""
        if re.search(r"v\d+$", arxiv_id.strip()):
            # arXiv answers an id_list lookup for a version that was never
            # published with an empty feed, not an error.
            hint = (" That version may not exist — try the id without the"
                    " version suffix to get the latest one.")
        return {"error": f"No paper found for arxiv_id={arxiv_id!r}.{hint}"}
    return _paper_to_dict(papers[0])
