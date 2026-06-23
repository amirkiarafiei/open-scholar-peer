"""Semantic Scholar provider.

Wraps the official `semanticscholar` Python client. All blocking calls are
executed via asyncio.to_thread so the event loop stays responsive. Timeouts
are applied at the osp_mcp.py layer via asyncio.wait_for.

Reads the optional SEMANTIC_SCHOLAR_API_KEY env var for higher rate limits.
"""
from __future__ import annotations

import os
from typing import Any

from semanticscholar import SemanticScholar

_client: SemanticScholar | None = None


def _get_client() -> SemanticScholar:
    global _client
    if _client is None:
        api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
        _client = SemanticScholar(api_key=api_key) if api_key else SemanticScholar()
    return _client


# ---------- Serializers ----------------------------------------------------

def _paper_to_dict(paper: Any) -> dict[str, Any]:
    return {
        "paperId": getattr(paper, "paperId", None),
        "title": getattr(paper, "title", None),
        "abstract": getattr(paper, "abstract", None),
        "year": getattr(paper, "year", None),
        "authors": [
            {"name": getattr(a, "name", None), "authorId": getattr(a, "authorId", None)}
            for a in (getattr(paper, "authors", None) or [])
        ],
        "url": getattr(paper, "url", None),
        "venue": getattr(paper, "venue", None),
        "publicationTypes": getattr(paper, "publicationTypes", None),
        "citationCount": getattr(paper, "citationCount", None),
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
        "authors": [
            {"name": getattr(a, "name", None), "authorId": getattr(a, "authorId", None)}
            for a in (getattr(paper, "authors", None) or [])
        ],
    }


# ---------- Provider functions (all synchronous — called via asyncio.to_thread) --

def search_papers(query: str, limit: int = 10) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    results = _get_client().search_paper(query, limit=limit)
    return [_paper_to_dict(p) for p in results]


def get_paper(paper_id: str) -> dict[str, Any]:
    paper = _get_client().get_paper(paper_id)
    return _paper_to_dict(paper)


def get_paper_references(paper_id: str, limit: int = 50) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    results = _get_client().get_paper_references(paper_id, limit=limit)
    return [_slim_paper(r.paper) for r in results if r.paper]


def get_paper_citations(paper_id: str, limit: int = 50) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    results = _get_client().get_paper_citations(paper_id, limit=limit)
    return [_slim_paper(c.paper) for c in results if c.paper]


def get_papers_batch(paper_ids: list[str]) -> list[dict[str, Any]]:
    if not paper_ids:
        return []
    papers = _get_client().get_papers(paper_ids[:500])
    return [_paper_to_dict(p) for p in papers if p]


def get_author(author_id: str) -> dict[str, Any]:
    author = _get_client().get_author(author_id)
    return _author_to_dict(author)


def search_authors(query: str, limit: int = 10) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    results = _get_client().search_author(query, limit=limit)
    return [_author_to_dict(a) for a in results]


def get_author_papers(author_id: str, limit: int = 50) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    results = _get_client().get_author_papers(author_id, limit=limit)
    return [_slim_paper(p) for p in results]


def get_paper_recommendations(paper_id: str, limit: int = 10) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    results = _get_client().get_recommended_papers(paper_id, limit=limit)
    return [_slim_paper(p) for p in results]


def search_snippets(query: str, limit: int = 10) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 20))
    results = _get_client().search_snippet(query, limit=limit)
    return [
        {
            "snippetId": getattr(s, "snippetId", None),
            "text": getattr(s, "text", None),
            "paper": _slim_paper(s.paper) if hasattr(s, "paper") and s.paper else None,
        }
        for s in results
    ]
