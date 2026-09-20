"""Europe PMC provider — open biomedical literature, and full text over REST.

No API key, no registration. Europe PMC is the cheapest full-text path that
exists for this project: for open-access articles it serves the whole article
as JATS XML from a plain GET, so there is no PDF to parse.

It matters here because arXiv covers almost no health or biology, and a real
share of the papers this project reviews are exactly that.

Docs: https://europepmc.org/RestfulWebService
"""
from __future__ import annotations

import re
import threading
import time
import xml.etree.ElementTree as ET
from typing import Any

import requests

from . import window as _window

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
UA = "open-scholar-peer/1.0 (https://github.com/amirkiarafiei/open-scholar-peer)"
# Same arithmetic as arxiv.py: requests spends `timeout` on the connect AND
# again on each read, and an in-loop deadline check overshoots by one read.
# Worst case: connect 10 + budget 35 + one overshooting read 15 = 60 s.
_CONNECT_TIMEOUT = 10
_READ_TIMEOUT = 15
_BUDGET = 35

# Hard ceiling on a single download. Full articles run to a few hundred KB;
# anything past this is not an article we want to hold in memory.
_MAX_BYTES = 12 * 1024 * 1024


class _Deadline(threading.local):
    """Per-thread transfer deadline, set by _get and read by _read_capped."""
    value: float = 0.0


_deadline = _Deadline()


class EuropePmcError(RuntimeError):
    """Europe PMC could not answer. Never reported as an empty result."""


class EuropePmcNotFound(EuropePmcError):
    """No such article. The provider is fine; the identifier is not."""


def _get(path: str, params: dict[str, Any] | None = None,
         missing_is_not_found: bool = False) -> requests.Response:
    # Started before the request so a slow connect counts against it too.
    _deadline.value = time.time() + _BUDGET
    try:
        resp = requests.get(
            f"{BASE}/{path}", params=params,
            headers={"User-Agent": UA},
            timeout=(_CONNECT_TIMEOUT, _READ_TIMEOUT), stream=True,
        )
    except requests.RequestException as e:
        raise EuropePmcError(f"Europe PMC request failed: {e}") from e

    # Europe PMC answers an unusable PMCID with 500, not 404 — measured on
    # 2026-09-20 for PMC99999999, PMCNONE and PMC0. Reported as a plain
    # server error it reads as "the provider is down", and one mistyped id
    # would have the agent write Europe PMC off for the rest of the review.
    if resp.status_code in (404, 500) and missing_is_not_found:
        raise EuropePmcNotFound(
            f"Europe PMC has no full text for {path.split('/')[0]!r}. The "
            "identifier may be wrong, or the article may not be open access "
            "here. This is about that one article, not the provider.")
    if resp.status_code == 404:
        raise EuropePmcError(f"Europe PMC has nothing at {path!r} (HTTP 404)")
    if resp.status_code != 200:
        raise EuropePmcError(
            f"Europe PMC returned HTTP {resp.status_code} for {path!r}")

    length = resp.headers.get("Content-Length")
    if length and int(length) > _MAX_BYTES:
        raise EuropePmcError(
            f"Europe PMC response is {int(length)} bytes, over the "
            f"{_MAX_BYTES} byte cap")
    return resp


def _read_capped(resp: requests.Response) -> str:
    """Read a response body, stopping at the cap.

    Content-Length is absent on chunked replies, so the cap is also applied
    while reading.
    """
    deadline = _deadline.value or (time.time() + _BUDGET)
    chunks, total = [], 0
    for chunk in resp.iter_content(chunk_size=65536):
        total += len(chunk)
        if total > _MAX_BYTES:
            raise EuropePmcError(
                f"Europe PMC response exceeded the {_MAX_BYTES} byte cap")
        if time.time() > deadline:
            raise EuropePmcError(
                f"Europe PMC response did not finish within {_BUDGET}s "
                f"(got {total} bytes)")
        chunks.append(chunk)
    return b"".join(chunks).decode(resp.encoding or "utf-8", errors="replace")


def _full_text_routes(record: dict[str, Any]) -> list[dict[str, str]]:
    urls = (record.get("fullTextUrlList") or {}).get("fullTextUrl") or []
    return [
        {
            "url": u.get("url"),
            "style": u.get("documentStyle"),
            "availability": u.get("availability"),
        }
        for u in urls
    ]


def _record_to_dict(r: dict[str, Any]) -> dict[str, Any]:
    journal = (r.get("journalInfo") or {}).get("journal") or {}
    return {
        "id": r.get("id"),
        "source": r.get("source"),
        "pmid": r.get("pmid"),
        # The id the full-text tool needs. Null means no full text here.
        "pmcid": r.get("pmcid"),
        "doi": r.get("doi"),
        "title": r.get("title"),
        "authors": r.get("authorString"),
        "journal": journal.get("title"),
        "year": r.get("pubYear"),
        "abstract": r.get("abstractText"),
        "citedByCount": r.get("citedByCount"),
        "isOpenAccess": r.get("isOpenAccess") == "Y",
        "inEPMC": r.get("inEPMC") == "Y",
        "hasFullTextXML": r.get("inEPMC") == "Y" and r.get("isOpenAccess") == "Y",
        "fullTextUrls": _full_text_routes(r),
    }


def build_query(query: str, open_access_only: bool = False) -> str:
    """Add the open-access clause when the caller wants readable full text.

    Pure, so it is unit tested offline. OPEN_ACCESS:Y alone is not enough:
    a record can be open access somewhere else and still not be held by
    Europe PMC, and only IN_EPMC:Y records have a fullTextXML route.
    """
    q = (query or "").strip()
    if open_access_only:
        return f"({q}) AND OPEN_ACCESS:Y AND IN_EPMC:Y" if q else "OPEN_ACCESS:Y AND IN_EPMC:Y"
    return q


def search(
    query: str,
    limit: int = 10,
    open_access_only: bool = False,
    sort: str | None = None,
) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    full_query = build_query(query, open_access_only)
    if not full_query:
        raise ValueError("search_europe_pmc needs a query")

    params = {
        "query": full_query,
        "format": "json",
        "pageSize": limit,
        # `core` is what returns abstractText and fullTextUrlList; `lite`
        # leaves both out.
        "resultType": "core",
    }
    if sort:
        params["sort"] = sort

    resp = _get("search", params)
    # Read through the cap rather than calling resp.json() on the stream, so a
    # runaway response cannot be pulled into memory whole.
    import json
    try:
        data = json.loads(_read_capped(resp))
    except ValueError as e:
        raise EuropePmcError(f"Europe PMC sent something that is not JSON: {e}") from e

    results = (data.get("resultList") or {}).get("result") or []
    return [_record_to_dict(r) for r in results[:limit]]


# ---------- Full text --------------------------------------------------------

# Dropped before the text is assembled: the bibliography is long, adds no
# argument, and would crowd out the article itself. Its absence is reported
# rather than left for the reader to infer.
_DROP_TAGS = {"ref-list", "fn-group", "table-wrap-foot"}

_BLOCK_TAGS = ("p", "caption", "list-item", "statement", "disp-quote")

# Sections nest, and Python's recursion limit is about 1000 frames. 500 levels
# of <sec> raised RecursionError, which surfaced as an unactionable "failed".
# No real article is anywhere near this.
_MAX_DEPTH = 100


def _local(tag: str) -> str:
    """Strip the namespace: ElementTree gives '{uri}sec' for namespaced XML."""
    return tag.rsplit("}", 1)[-1]


def _find(root: ET.Element, name: str) -> ET.Element | None:
    """First descendant with this local name, namespace or not.

    `root.find(".//article-title")` matches nothing when the document carries
    a default namespace, because the real tag is
    `{http://jats.nlm.nih.gov/...}article-title`. JATS is served both ways,
    and the namespaced version was losing the whole article — and then
    reporting it as "probably not open access", which is worse than losing it.
    """
    if _local(root.tag) == name:
        return root
    for node in root.iter():
        if _local(node.tag) == name:
            return node
    return None


def _child(node: ET.Element, name: str) -> ET.Element | None:
    for child in node:
        if _local(child.tag) == name:
            return child
    return None


def _node_text(node: ET.Element) -> str:
    return re.sub(r"\s+", " ", "".join(node.itertext())).strip()


def _placeholder(node: ET.Element, kind: str) -> str:
    """Render a table or figure as one labelled line.

    JATS <label> already reads "Table 1", so prefixing the word again gave
    "[Table Table 1: ...]".
    """
    label_el = _child(node, "label")
    label = (label_el.text or "" if label_el is not None else "").strip().rstrip(".")
    cap = _child(node, "caption")
    caption = _node_text(cap) if cap is not None else ""
    if not label:
        label = kind
    elif not label.lower().startswith(kind.lower()):
        label = f"{kind} {label}"
    return f"[{label}: {caption}]".replace(": ]", "]")


def _render(node: ET.Element, depth: int) -> list[str]:
    """Blocks of text for this node's children. Empty list means nothing here.

    Returning nothing for an empty branch is what stops a heading appearing
    with no body under it — the reference list is dropped, and its enclosing
    section's title used to survive as a bare "## References", which reads as
    "this article has no bibliography".
    """
    if depth > _MAX_DEPTH:
        return ["[section nesting too deep to render]"]
    out: list[str] = []
    for child in node:
        tag = _local(child.tag)
        if tag in _DROP_TAGS:
            if tag == "ref-list":
                n = sum(1 for _ in child.iter() if _local(_.tag) == "ref")
                if n:
                    out.append(f"[Reference list omitted — {n} entries]")
            continue
        if tag == "sec":
            out.extend(_render_sec(child, depth + 1))
        elif tag in _BLOCK_TAGS:
            text = _node_text(child)
            if text:
                out.append(text)
        elif tag == "table-wrap":
            out.append(_placeholder(child, "Table"))
        elif tag in ("fig", "graphic"):
            out.append(_placeholder(child, "Figure"))
        elif tag in ("title", "label"):
            continue
        else:
            out.extend(_render(child, depth))
    return out


def _render_sec(sec: ET.Element, depth: int) -> list[str]:
    """A section, with its heading only if it actually has content."""
    if depth > _MAX_DEPTH:
        # Say so. Returning nothing made the caller conclude the article had
        # no body, and report it as "probably not open access" — the wrong
        # reason, sent to someone who would then go looking in the wrong place.
        return ["[section nesting too deep to render]"]
    title_el = None
    rest: list[str] = []
    for child in sec:
        tag = _local(child.tag)
        if tag == "title" and title_el is None:
            title_el = child
            continue
        rest.extend(_render(_wrap(child), depth))
    if not rest:
        return []
    heading: list[str] = []
    if title_el is not None:
        text = _node_text(title_el)
        if text:
            heading = [f"{'#' * min(depth + 1, 6)} {text}"]
    return heading + rest


def _wrap(child: ET.Element) -> ET.Element:
    """Put one element inside a throwaway parent so _render can walk it."""
    holder = ET.Element("holder")
    holder.append(child)
    return holder


class _EntityDeclared(Exception):
    """An entity declaration reached the parser. Refuse the document."""


def _safe_parser() -> ET.XMLParser:
    """An XMLParser that refuses to define entities at all.

    The textual scan above can be defeated by anything that hides the
    declaration from a substring search. expat cannot be: this handler fires
    on the declaration itself, before any expansion happens.
    """
    parser = ET.XMLParser()
    try:
        def _refuse(*_args, **_kwargs):
            raise _EntityDeclared()
        parser.parser.EntityDeclHandler = _refuse
    except AttributeError:
        # Non-expat backend; the textual scan is the only guard there.
        pass
    return parser


def jats_to_text(xml: str) -> str:
    """Turn a JATS article into readable text. Pure, unit tested offline."""
    # xml.etree expands *internal* entity declarations, so a kilobyte of
    # nested ones can become gigabytes in memory before any size cap sees it.
    # Only `<!ENTITY` does that. A plain DOCTYPE naming an external DTD is
    # harmless here, because ElementTree never fetches one — and refusing it
    # would be wrong: of four articles sampled on 2026-09-20, one carried a
    # JATS DTD declaration and none declared an entity.
    #
    # Two guards, because the first one alone was not enough. It used to
    # sniff only `xml[:8192]`, and 9 KB of leading comment pushed the
    # declaration past the window: the bomb parsed and expanded. The scan is
    # now over the whole document — it is capped at _MAX_BYTES anyway — and
    # expat is told to reject an entity declaration outright, which catches
    # anything a textual scan could still miss.
    if "<!ENTITY" in xml.upper():
        raise EuropePmcError(
            "Europe PMC full text declares XML entities, which this reader "
            "refuses — such a document can expand to many times its size. "
            "Use the links in fullTextUrls instead.")

    try:
        root = ET.fromstring(xml, parser=_safe_parser())
    except _EntityDeclared as e:
        raise EuropePmcError(
            "Europe PMC full text declares XML entities, which this reader "
            "refuses — such a document can expand to many times its size. "
            "Use the links in fullTextUrls instead.") from e
    except ET.ParseError as e:
        raise EuropePmcError(f"Europe PMC full text is not valid XML: {e}") from e

    parts: list[str] = []

    title = _find(root, "article-title")
    if title is not None and _node_text(title):
        parts.append(f"# {_node_text(title)}")

    abstract = _find(root, "abstract")
    if abstract is not None:
        # Its own <title> child is usually the word "Abstract" again, which
        # produced a heading directly under the one we just wrote.
        blocks = _render(abstract, 1)
        blocks = [b for b in blocks if b.strip().lstrip("#").strip().lower() != "abstract"]
        if blocks:
            parts.append("## Abstract")
            parts.extend(blocks)

    body = _find(root, "body")
    if body is not None:
        parts.extend(_render(body, 0))

    # Judge on whether there is prose, not on how many blocks came back. A
    # body with one paragraph and no article title is a real article.
    prose = [p for p in parts if p.strip() and not p.lstrip().startswith("#")]
    if not prose:
        raise EuropePmcError(
            "Europe PMC returned a record with no readable body — it is "
            "probably not open access. Try the links in fullTextUrls.")

    text = "\n\n".join(p for p in parts if p.strip())
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def get_full_text(pmcid: str, max_chars: int = 50000, offset: int = 0) -> dict[str, Any]:
    """Fetch an open-access article as text. Writes nothing to disk."""
    pmcid = (pmcid or "").strip().upper()
    if not pmcid:
        # The commonest way to reach this: a search result whose `pmcid` is
        # null because Europe PMC holds no full text for it. Say that, rather
        # than sounding like a missing argument.
        raise ValueError(
            "no PMCID given. If this came from a search result, that record "
            "has no pmcid, which means Europe PMC holds no full text for it "
            "— try the links in its fullTextUrls instead.")
    if not pmcid.startswith("PMC"):
        pmcid = f"PMC{pmcid}"
    if not re.fullmatch(r"PMC\d+", pmcid):
        raise ValueError(
            f"{pmcid!r} is not a PMCID. It must be PMC followed by digits, "
            "for example PMC12798607.")

    resp = _get(f"{pmcid}/fullTextXML", missing_is_not_found=True)
    text = jats_to_text(_read_capped(resp))

    out = _window(text, max_chars, offset)
    out["pmcid"] = pmcid
    out["source"] = f"{BASE}/{pmcid}/fullTextXML"
    return out
