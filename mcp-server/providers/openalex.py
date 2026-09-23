"""OpenAlex provider — the whole scholarly record, and retraction flags.

About 327 million works. The thing nothing else here can do is tell the agent
that a cited paper was **retracted**: `is_retracted` flagged 135,737 works when
last measured (2026-09-20). Recommending "accept" on a paper that leans on
retracted work is exactly the failure that catches.

Key handling: OpenAlex answers without a key, but a keyless caller gets a small
daily budget and a list call costs several credits, which is roughly ten
searches a day. A free key raises it far above anything this project needs. So
the key is optional, and the installer must label it that way.

Docs: https://help.openalex.org/api/ · filters:
https://help.openalex.org/api/filtering/
"""
from __future__ import annotations

import os
import re
from typing import Any

import requests

BASE = "https://api.openalex.org"
UA = "open-scholar-peer/1.0 (https://github.com/amirkiarafiei/open-scholar-peer)"
# Same budget discipline as the other providers: `timeout` is spent on the
# connect AND again on each read, so a single 60 here could outlast the 90 s
# OSP_CALL_TIMEOUT on its own and leave the agent a bare "timed out".
# Worst case: connect 10 + read 20 = 30 s.
_CONNECT_TIMEOUT = 10
_READ_TIMEOUT = 20


class OpenAlexError(RuntimeError):
    """OpenAlex could not answer. Never reported as an empty result."""


class OpenAlexRateLimited(OpenAlexError):
    """OpenAlex answered 429 or 403. Temporary, and a key lifts it — telling
    the agent the provider is unavailable would retire it for the review."""


class OpenAlexNotFound(OpenAlexError):
    """No such work. OpenAlex is fine; it has simply not indexed this one.

    Kept separate because the headline use of this provider is feeding it
    every DOI in a bibliography. Reporting the first un-indexed one as
    "provider unavailable" would stop the agent checking the rest.
    """


def _params(extra: dict[str, Any]) -> dict[str, Any]:
    params = dict(extra)
    key = os.environ.get("OPENALEX_API_KEY")
    if key:
        params["api_key"] = key
    # The polite pool. OpenAlex asks callers to identify themselves and gives
    # them a faster lane for doing it.
    mail = os.environ.get("OPENALEX_MAILTO")
    if mail:
        params["mailto"] = mail
    return params


def _get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        resp = requests.get(f"{BASE}/{path}", params=_params(params),
                            headers={"User-Agent": UA}, timeout=(_CONNECT_TIMEOUT, _READ_TIMEOUT))
    except requests.RequestException as e:
        raise OpenAlexError(f"OpenAlex request failed: {e}") from e

    if resp.status_code == 403:
        raise OpenAlexRateLimited(
            "OpenAlex refused the request (HTTP 403). The keyless daily budget "
            "is small — set OPENALEX_API_KEY in .env to raise it.")
    if resp.status_code == 429:
        raise OpenAlexRateLimited(
            "OpenAlex rate limit reached (HTTP 429). Set OPENALEX_API_KEY in "
            ".env for a much larger budget.")
    if resp.status_code == 404:
        raise OpenAlexNotFound(
            f"OpenAlex has not indexed {path.split(':')[-1]!r}. That is about "
            "this one work, not the provider — carry on with the others.")
    if resp.status_code != 200:
        raise OpenAlexError(f"OpenAlex returned HTTP {resp.status_code}")

    try:
        return resp.json()
    except ValueError as e:
        raise OpenAlexError(f"OpenAlex sent something that is not JSON: {e}") from e


def invert_abstract(index: dict[str, list[int]] | None) -> str | None:
    """Rebuild an abstract from OpenAlex's inverted index.

    OpenAlex stores abstracts as {word: [positions]} rather than as text.
    Handed straight to an agent it is unreadable, so it is put back in order
    here. Pure, unit tested offline.
    """
    if not index:
        return None
    slots: list[tuple[int, str]] = []
    for word, positions in index.items():
        for pos in positions or []:
            slots.append((pos, word))
    if not slots:
        return None
    slots.sort(key=lambda p: p[0])
    return " ".join(word for _, word in slots)


def _work_to_dict(w: dict[str, Any]) -> dict[str, Any]:
    oa = w.get("open_access") or {}
    best = w.get("best_oa_location") or {}
    primary = w.get("primary_location") or {}
    source = (primary.get("source") or {}) if primary else {}
    return {
        "id": w.get("id"),
        "doi": w.get("doi"),
        "title": w.get("display_name"),
        "year": w.get("publication_year"),
        "publicationDate": w.get("publication_date"),
        "type": w.get("type"),
        "venue": source.get("display_name"),
        "authors": [
            {
                "name": (a.get("author") or {}).get("display_name"),
                "id": (a.get("author") or {}).get("id"),
                "institutions": [
                    i.get("display_name") for i in (a.get("institutions") or [])
                ],
            }
            for a in (w.get("authorships") or [])
        ],
        "abstract": invert_abstract(w.get("abstract_inverted_index")),
        "citedByCount": w.get("cited_by_count"),
        # Field-weighted citation impact: citations against the average for
        # the same field, year and type. Above 1 is above average.
        "fwci": w.get("fwci"),
        "topics": [t.get("display_name") for t in (w.get("topics") or [])],
        "isOpenAccess": oa.get("is_oa"),
        "oaUrl": best.get("pdf_url") or best.get("landing_page_url"),
        # The reason this provider is here.
        "isRetracted": w.get("is_retracted"),
        "referencedWorksCount": len(w.get("referenced_works") or []),
        "referencedWorks": w.get("referenced_works") or [],
    }


_SELECT = (
    "id,doi,display_name,publication_year,publication_date,type,"
    "primary_location,authorships,abstract_inverted_index,cited_by_count,"
    "fwci,topics,open_access,best_oa_location,is_retracted,referenced_works"
)


def search(
    query: str,
    limit: int = 10,
    from_year: int | None = None,
    to_year: int | None = None,
    open_access_only: bool = False,
    exclude_retracted: bool = False,
    work_type: str | None = None,
    sort: str | None = None,
) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 50))

    filters: list[str] = []
    if from_year:
        filters.append(f"from_publication_date:{int(from_year)}-01-01")
    if to_year:
        filters.append(f"to_publication_date:{int(to_year)}-12-31")
    if open_access_only:
        filters.append("open_access.is_oa:true")
    if exclude_retracted:
        filters.append("is_retracted:false")
    if work_type:
        filters.append(f"type:{work_type}")

    params: dict[str, Any] = {"per-page": limit, "select": _SELECT}
    if query and query.strip():
        params["search"] = query.strip()
    if filters:
        params["filter"] = ",".join(filters)
    if sort:
        params["sort"] = sort

    data = _get("works", params)
    return [_work_to_dict(w) for w in (data.get("results") or [])[:limit]]


def get_work(identifier: str) -> dict[str, Any]:
    """Look up one work by DOI, OpenAlex id or PMID.

    **Not an arXiv id** — OpenAlex has no arXiv namespace, so one returns 404.

    This is the retraction check: give it the DOI from a bibliography line and
    read `isRetracted`.
    """
    ident = (identifier or "").strip()
    if not ident:
        raise ValueError(
            "get_openalex_work needs a DOI or an OpenAlex id")

    # Strip a doi.org prefix in any case, with or without the dx. The old
    # code lower-cased to test but split on the original, so an upper-case
    # URL raised IndexError and surfaced as "failed: list index out of range".
    stripped = re.sub(r"(?i)^https?://(?:dx\.)?doi\.org/", "", ident)
    if stripped != ident:
        path = f"works/doi:{stripped}"
    elif ident.lower().startswith("10."):
        path = f"works/doi:{ident}"
    elif re.fullmatch(r"\d+", ident):
        # A bare run of digits is a PMID. OpenAlex needs the namespace;
        # without it the lookup simply misses.
        path = f"works/pmid:{ident}"
    elif ident.lower().startswith(("http://openalex.org/", "https://openalex.org/")):
        path = f"works/{ident.rstrip('/').rsplit('/', 1)[1]}"
    else:
        path = f"works/{ident}"

    return _work_to_dict(_get(path, {"select": _SELECT}))
