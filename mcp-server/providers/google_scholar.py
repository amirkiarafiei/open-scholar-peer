"""Google Scholar provider.

Two retrieval paths:
  • Direct HTML scraping (via requests + BeautifulSoup) — used for keyword and
    advanced search. Fast but subject to Google's rate limits.
  • `scholarly` library — used for richer author profile lookups.

Note: Google Scholar has no public API. Treat results as best-effort.
"""
from __future__ import annotations

from typing import Any

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _parse_results(html: str, num_results: int) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict[str, Any]] = []
    for item in soup.find_all("div", class_="gs_ri"):
        if len(out) >= num_results:
            break
        title_tag = item.find("h3", class_="gs_rt")
        title = title_tag.get_text() if title_tag else ""
        link_anchor = title_tag.find("a") if title_tag else None
        link = link_anchor["href"] if link_anchor and link_anchor.has_attr("href") else ""
        authors_tag = item.find("div", class_="gs_a")
        authors = authors_tag.get_text() if authors_tag else ""
        abstract_tag = item.find("div", class_="gs_rs")
        abstract = abstract_tag.get_text() if abstract_tag else ""
        out.append({"title": title, "authors": authors, "abstract": abstract, "url": link})
    return out


def search(query: str, num_results: int = 5) -> list[dict[str, Any]]:
    num_results = max(1, min(int(num_results), 20))
    url = f"https://scholar.google.com/scholar?q={requests.utils.quote(query)}"
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    resp.raise_for_status()
    return _parse_results(resp.text, num_results)


def search_advanced(
    query: str,
    author: str | None = None,
    year_range: tuple[int | None, int | None] | None = None,
    num_results: int = 5,
) -> list[dict[str, Any]]:
    num_results = max(1, min(int(num_results), 20))
    params: dict[str, str] = {"q": query}
    if author:
        params["as_auth"] = author
    if year_range:
        ys, ye = year_range
        if ys:
            params["as_ylo"] = str(ys)
        if ye:
            params["as_yhi"] = str(ye)
    url = "https://scholar.google.com/scholar?" + "&".join(
        f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()
    )
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    resp.raise_for_status()
    return _parse_results(resp.text, num_results)


def get_author_info(author_name: str) -> dict[str, Any]:
    """Use the `scholarly` library to fetch an author profile."""
    from scholarly import scholarly  # imported lazily — heavier dependency

    search_query = scholarly.search_author(author_name)
    author = next(search_query)
    filled = scholarly.fill(author)
    return {
        "name": filled.get("name", ""),
        "affiliation": filled.get("affiliation", ""),
        "interests": filled.get("interests", []),
        "citedby": filled.get("citedby", 0),
        "publications": [
            {
                "title": p.get("bib", {}).get("title", ""),
                "year": p.get("bib", {}).get("pub_year", ""),
                "citations": p.get("num_citations", 0),
            }
            for p in (filled.get("publications", []) or [])[:5]
        ],
    }
