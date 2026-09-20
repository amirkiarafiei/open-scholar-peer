"""Zenodo provider — did the authors actually release their code and data?

Zenodo does not find papers, and must not be used in the literature rounds.
It holds software releases, datasets and other artifacts, each with a DOI.

That answers a question the review forms ask and this project could not check
at all: the paper says "code is available" — is it? This belongs to the
Baseline Scout.

Docs: https://developers.zenodo.org/
"""
from __future__ import annotations

import os
from typing import Any

import requests

BASE = "https://zenodo.org/api"
UA = "open-scholar-peer/1.0 (https://github.com/amirkiarafiei/open-scholar-peer)"
# Same budget discipline as the other providers: `timeout` is spent on the
# connect AND again on each read, so a single 60 here could outlast the 90 s
# OSP_CALL_TIMEOUT on its own and leave the agent a bare "timed out".
# Worst case: connect 10 + read 20 = 30 s.
_CONNECT_TIMEOUT = 10
_READ_TIMEOUT = 20

# What Zenodo calls the things it stores. Passed straight through as `type`.
RESOURCE_TYPES = (
    "software", "dataset", "publication", "poster", "presentation",
    "image", "video", "lesson", "physicalobject", "other",
)


class ZenodoError(RuntimeError):
    """Zenodo could not answer. Never reported as an empty result."""


class ZenodoNotFound(ZenodoError):
    """No such record. Zenodo is fine."""


def _get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    # Zenodo works without a token; one only raises the rate limit.
    token = os.environ.get("ZENODO_API_TOKEN")
    if token:
        params = dict(params, access_token=token)
    try:
        resp = requests.get(f"{BASE}/{path}", params=params,
                            headers={"User-Agent": UA}, timeout=(_CONNECT_TIMEOUT, _READ_TIMEOUT))
    except requests.RequestException as e:
        raise ZenodoError(f"Zenodo request failed: {e}") from e

    if resp.status_code == 429:
        # The docs say 60/minute for guests; the live API reports
        # x-ratelimit-limit: 30 on an anonymous GET. The cap a long review
        # actually reaches is the hourly one.
        retry = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
        wait = f" Retry-After: {retry}s." if retry else ""
        raise ZenodoError(
            f"Zenodo rate limit reached (HTTP 429).{wait} Anonymous callers "
            "get roughly 30-60 requests a minute and 2,000 an hour. Set "
            "ZENODO_API_TOKEN in .env to raise it.")
    if resp.status_code == 404:
        raise ZenodoNotFound(f"Zenodo has no record at {path!r}")
    if resp.status_code != 200:
        raise ZenodoError(f"Zenodo returned HTTP {resp.status_code}")
    try:
        return resp.json()
    except ValueError as e:
        raise ZenodoError(f"Zenodo sent something that is not JSON: {e}") from e


def _record_to_dict(h: dict[str, Any]) -> dict[str, Any]:
    meta = h.get("metadata") or {}
    rtype = meta.get("resource_type") or {}
    return {
        "id": h.get("id"),
        "doi": h.get("doi") or meta.get("doi"),
        "title": meta.get("title"),
        "type": rtype.get("type"),
        "subtype": rtype.get("subtype"),
        "publicationDate": meta.get("publication_date"),
        "description": meta.get("description"),
        "creators": [c.get("name") for c in (meta.get("creators") or [])],
        "license": ((meta.get("license") or {}).get("id")
                    if isinstance(meta.get("license"), dict)
                    else meta.get("license")),
        "version": meta.get("version"),
        "url": (h.get("links") or {}).get("self_html") or h.get("doi_url"),
        # Where the code or data actually is.
        "relatedIdentifiers": [
            {"identifier": r.get("identifier"), "relation": r.get("relation")}
            for r in (meta.get("related_identifiers") or [])
        ],
        "fileCount": len(h.get("files") or []),
    }


def search(
    query: str,
    limit: int = 10,
    resource_type: str | None = "software",
    all_versions: bool = False,
) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 50))
    if not (query or "").strip():
        raise ValueError("search_zenodo needs a query")

    params: dict[str, Any] = {"q": query.strip(), "size": limit}
    if resource_type:
        rt = resource_type.strip().lower()
        if rt not in RESOURCE_TYPES:
            raise ValueError(
                f"unknown resource_type {resource_type!r}; use one of "
                f"{', '.join(RESOURCE_TYPES)}")
        params["type"] = rt
    if all_versions:
        params["all_versions"] = "true"

    data = _get("records", params)
    hits = ((data.get("hits") or {}).get("hits")) or []
    return [_record_to_dict(h) for h in hits[:limit]]
