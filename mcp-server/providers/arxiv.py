"""arXiv provider — uses the public arXiv Atom API. No API key required."""
from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def _parse_entry(entry: ET.Element) -> dict[str, Any]:
    def text(path: str, ns: dict[str, str] = ATOM_NS) -> str:
        el = entry.find(path, ns)
        return el.text.strip().replace("\n", " ") if el is not None and el.text else ""

    authors = [
        a.text.strip() for a in entry.findall("atom:author/atom:name", ATOM_NS) if a.text
    ]
    arxiv_id = text("atom:id").rsplit("/", 1)[-1]
    primary_cat_el = entry.find("arxiv:primary_category", ATOM_NS)
    primary_category = primary_cat_el.attrib.get("term", "") if primary_cat_el is not None else ""
    return {
        "title": text("atom:title"),
        "authors": authors,
        "summary": text("atom:summary"),
        "published": text("atom:published"),
        "updated": text("atom:updated"),
        "link": text("atom:id"),
        "arxiv_id": arxiv_id,
        "primary_category": primary_category,
        "comment": text("arxiv:comment", ATOM_NS),
    }


def search(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    max_results = max(1, min(int(max_results), 50))
    url = (
        "http://export.arxiv.org/api/query?"
        f"search_query=all:{urllib.parse.quote(query)}&start=0&max_results={max_results}"
    )
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    return [_parse_entry(e) for e in root.findall("atom:entry", ATOM_NS)]


def get_details(arxiv_id: str) -> dict[str, Any]:
    url = f"http://export.arxiv.org/api/query?id_list={urllib.parse.quote(arxiv_id)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    entries = root.findall("atom:entry", ATOM_NS)
    if not entries:
        return {"error": f"No paper found for arxiv_id={arxiv_id}"}
    return _parse_entry(entries[0])
