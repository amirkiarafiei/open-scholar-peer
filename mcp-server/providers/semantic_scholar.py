"""Semantic Scholar provider.

Wraps the official `semanticscholar` Python client. Reads the optional
SEMANTIC_SCHOLAR_API_KEY env var for higher rate limits.
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


def search_papers(query: str, limit: int = 10) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    client = _get_client()
    results = client.search_paper(query, limit=limit)
    return [_paper_to_dict(p) for p in results]


def get_paper(paper_id: str) -> dict[str, Any]:
    client = _get_client()
    paper = client.get_paper(paper_id)
    return _paper_to_dict(paper)


def get_author(author_id: str) -> dict[str, Any]:
    client = _get_client()
    author = client.get_author(author_id)
    return _author_to_dict(author)


def get_citations_and_references(paper_id: str) -> dict[str, Any]:
    client = _get_client()
    paper = client.get_paper(paper_id)

    def _ref_to_dict(p: Any) -> dict[str, Any]:
        return {
            "paperId": getattr(p, "paperId", None),
            "title": getattr(p, "title", None),
            "year": getattr(p, "year", None),
            "authors": [
                {"name": getattr(a, "name", None), "authorId": getattr(a, "authorId", None)}
                for a in (getattr(p, "authors", None) or [])
            ],
        }

    return {
        "citations": [_ref_to_dict(c) for c in (getattr(paper, "citations", None) or [])],
        "references": [_ref_to_dict(r) for r in (getattr(paper, "references", None) or [])],
    }
