"""arXiv provider — uses the official `arxiv` Python package.

The package handles HTTPS, rate-limiting delays, and pagination automatically,
avoiding the 429 errors produced by raw HTTP calls to the Atom API.
"""
from __future__ import annotations

from datetime import timezone
from typing import Any

import arxiv
from dateutil import parser as _dp


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
    }


def _parse_date_utc(s: str):
    return _dp.parse(s).replace(tzinfo=timezone.utc)


def search(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance",
    date_from: str | None = None,
    date_to: str | None = None,
    categories: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Search arXiv papers. Returns list of paper dicts or [{"error": "..."}]."""
    max_results = max(1, min(int(max_results), 50))

    full_query = query
    if categories:
        cat_filter = " OR ".join(f"cat:{c}" for c in categories)
        full_query = f"({query}) ({cat_filter})"

    sort_criterion = (
        arxiv.SortCriterion.Relevance
        if sort_by == "relevance"
        else arxiv.SortCriterion.SubmittedDate
    )

    # Fetch slightly more to absorb date-filter attrition
    api_limit = min(max_results + 10, 50)
    search_obj = arxiv.Search(query=full_query, max_results=api_limit, sort_by=sort_criterion)

    date_from_dt = _parse_date_utc(date_from) if date_from else None
    date_to_dt = _parse_date_utc(date_to) if date_to else None

    client = arxiv.Client()
    results: list[dict[str, Any]] = []
    for paper in client.results(search_obj):
        if len(results) >= max_results:
            break
        if paper.published:
            pub = paper.published
            if not pub.tzinfo:
                pub = pub.replace(tzinfo=timezone.utc)
            if date_from_dt and pub < date_from_dt:
                continue
            if date_to_dt and pub > date_to_dt:
                continue
        results.append(_paper_to_dict(paper))

    return results


def get_details(arxiv_id: str) -> dict[str, Any]:
    """Fetch metadata for a specific arXiv paper by ID."""
    client = arxiv.Client()
    search_obj = arxiv.Search(id_list=[arxiv_id.strip()])
    papers = list(client.results(search_obj))
    if not papers:
        return {"error": f"No paper found for arxiv_id={arxiv_id!r}"}
    return _paper_to_dict(papers[0])
