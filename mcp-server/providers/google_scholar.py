"""Google Scholar provider.

Google Scholar has no public API, so this scrapes the HTML. Treat results as
best-effort.

**The rule this module exists to keep: a block is never reported as "no
results".** A blocked request and a search with no matches used to produce the
same empty list, so the agent wrote "no papers found" when the truth was "we
were shut out". That breaks MANIFESTO rule 8 and hides the failure from the
Provenance block of the literature artifact.

Block detection is by marker, never by "the page had no results", because a
genuine zero-hit search also has no result rows.

What was measured on 2026-09-20, from one ordinary residential IP, five
requests about eight seconds apart:

  * Google answered **HTTP 429** to every one of them.
  * Four different User-Agent strings — Chrome 124 on Windows, Chrome 131 on
    macOS, Firefox 133 on Linux, and no User-Agent at all — produced byte-for-
    byte identical 429 bodies. **Rotating the User-Agent changed nothing.**
    The block is on the address, not the client string.
  * So retrying a 429 inside one tool call only spends the caller's 90-second
    budget and pushes harder on a host that has already said no. This module
    therefore **does not retry a 429**. It fails at once and says why, which
    leaves the time for arXiv, Semantic Scholar and the other providers.

Retries are kept only for faults that really are transient: a dropped
connection, a timeout, or a 5xx.

Block-page markers and the proxy environment variable follow
`openags/paper-search-mcp` (`academic_platforms/google_scholar.py`), MIT
licence, used with attribution.
"""
from __future__ import annotations

import os
import random
import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://scholar.google.com/scholar"

# Kept current, and rotated per request. Measured as no help against an
# address-level block, but it costs nothing and does no harm.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:133.0) "
    "Gecko/20100101 Firefox/133.0",
]

# Structure, not prose.
#
# The first version of this matched phrases: "unusual traffic", "not a robot",
# "our systems have detected". Google echoes your query into the page title
# and into every result, so a genuine results page for a paper called
# "I'm not a robot: (Deep) Learning to Break Semantic Image CAPTCHAs" was
# reported as a block. That is the B9 bug inverted — telling the agent the
# provider is down when it answered perfectly well — and it would have hit
# exactly the reviews most likely to search for those words.
#
# These are HTML element ids and classes from the interstitial itself. They
# are matched only in attribute position, so a paper that merely discusses
# reCAPTCHA cannot trip them.
_BLOCK_ATTR_VALUES = (
    "gs_captcha_ccl",
    "g-recaptcha",
    "recaptcha",
    "rc-doscaptcha-body",
    "captcha-form",
)
_BLOCK_ATTR_RE = re.compile(
    r"""(?:id|class|name)\s*=\s*["']?[^"'>]*(?:"""
    + "|".join(re.escape(v) for v in _BLOCK_ATTR_VALUES)
    + r""")""",
    re.IGNORECASE,
)
# Google's own redirect target, and the form it posts back to.
_SORRY_RE = re.compile(r"""/sorry/(?:index|image)|CaptchaRedirect""", re.IGNORECASE)

# The whole retry budget must fit inside OSP_CALL_TIMEOUT (90 s by default),
# or the tool layer times out first and the caller gets a bare "timed out"
# instead of the message explaining that the provider was blocked.
# Worst case here: 3 x 20 s of request time + 1 s + 2 s of backoff = 63 s.
_TIMEOUT = 20
_MAX_ATTEMPTS = 3
_RETRYABLE_STATUS = (500, 502, 503, 504)


class GoogleScholarUnavailable(RuntimeError):
    """Google Scholar could not be read. NEVER an empty result.

    Every failure here — a block, a timeout, a dropped connection — means
    "we did not get to look", not "there is nothing there". The caller must
    record the provider as unavailable rather than writing "no papers found".
    """


class GoogleScholarBlocked(GoogleScholarUnavailable):
    """Google actively refused: a 429, a 403, or a captcha interstitial."""


class GoogleScholarNotFound(RuntimeError):
    """No such profile. Google answered; nobody by that name is listed.

    Deliberately NOT a subclass of GoogleScholarUnavailable: the provider
    worked, so it must not be recorded as unavailable."""


def _proxies() -> dict[str, str] | None:
    url = os.environ.get("GOOGLE_SCHOLAR_PROXY_URL")
    return {"http": url, "https": url} if url else None


def is_block_page(status_code: int, html: str, final_url: str = "") -> bool:
    """True when the response is an interstitial rather than search results.

    Pure, so it is unit tested offline against saved pages. Two rules it must
    keep, and they pull in opposite directions:

    * Never key off the absence of result rows. A real search with no matches
      also has none.
    * Never key off words that could appear in a paper. Google puts the query
      and the results into the page, so any phrase a researcher might search
      for will eventually show up on a perfectly good page.

    So: the HTTP status, the redirect target, and element ids belonging to
    the interstitial's own markup.
    """
    if status_code in (429, 403, 503):
        return True
    if _SORRY_RE.search(final_url or ""):
        return True
    text = html or ""
    return bool(_BLOCK_ATTR_RE.search(text) or _SORRY_RE.search(text))


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


def _fetch(params: dict[str, str], max_attempts: int = _MAX_ATTEMPTS) -> str:
    """Fetch a results page, or raise GoogleScholarUnavailable.

    Never returns an empty list or empty text to signal a problem. Retries
    only faults that can pass on their own — a dropped connection, a timeout,
    a 5xx. A block is not retried: it was measured to persist, and spending
    the caller's time budget on it helps nobody.
    """
    last_error: Exception | None = None

    for attempt in range(max_attempts):
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            resp = requests.get(
                BASE_URL, params=params, headers=headers,
                proxies=_proxies(), timeout=_TIMEOUT,
            )
        except requests.RequestException as e:
            last_error = e
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
                continue
            raise GoogleScholarUnavailable(
                f"Google Scholar could not be reached after {max_attempts}"
                f" attempts ({type(e).__name__}: {e}). This is a failure to"
                " reach the provider, not an empty result — record Google"
                " Scholar as unavailable in Provenance and use the other"
                " providers."
            ) from e

        if is_block_page(resp.status_code, resp.text, str(resp.url)):
            retry_after = resp.headers.get("Retry-After")
            wait = f" Retry-After: {retry_after}." if retry_after else ""
            proxy_hint = (
                "" if _proxies() else
                " Set GOOGLE_SCHOLAR_PROXY_URL to route through a proxy."
            )
            raise GoogleScholarBlocked(
                f"Google Scholar refused the request (HTTP {resp.status_code}).{wait}"
                " This is a block, not an empty result — do not record it as"
                " 'no papers found'. Record Google Scholar as unavailable in"
                f" Provenance and use the other providers.{proxy_hint}"
            )

        if resp.status_code in _RETRYABLE_STATUS and attempt < max_attempts - 1:
            time.sleep(2 ** attempt)
            continue

        if resp.status_code >= 400:
            raise GoogleScholarUnavailable(
                f"Google Scholar returned HTTP {resp.status_code}. Not an"
                " empty result — record the provider as unavailable.")
        return resp.text

    raise GoogleScholarUnavailable(
        f"Google Scholar could not be reached: {last_error}. Not an empty"
        " result — record the provider as unavailable.")


def search(query: str, num_results: int = 5) -> list[dict[str, Any]]:
    num_results = max(1, min(int(num_results), 20))
    # `num` was never sent, so Google returned its default page of 10 and a
    # request for 20 could not be satisfied.
    html = _fetch({"q": query, "num": str(num_results)})
    return _parse_results(html, num_results)


def search_advanced(
    query: str,
    author: str | None = None,
    year_range: tuple[int | None, int | None] | None = None,
    num_results: int = 5,
) -> list[dict[str, Any]]:
    num_results = max(1, min(int(num_results), 20))
    params: dict[str, str] = {"q": query, "num": str(num_results)}
    if author:
        params["as_auth"] = author
    if year_range:
        ys, ye = year_range
        if ys:
            params["as_ylo"] = str(ys)
        if ye:
            params["as_yhi"] = str(ye)
    html = _fetch(params)
    return _parse_results(html, num_results)


def get_author_info(author_name: str) -> dict[str, Any]:
    """Use the `scholarly` library to fetch an author profile.

    `scholarly` scrapes the same host, so it meets the same block. It reports
    that as its own exception type, which is turned into ours so the caller
    sees one consistent message.
    """
    from scholarly import scholarly  # imported lazily — heavier dependency

    try:
        search_query = scholarly.search_author(author_name)
        author = next(search_query)
        filled = scholarly.fill(author)
    except StopIteration as e:
        # Raised, not returned: a dict here bypasses _err and carries no
        # `reason`, which is the field the agent branches on.
        raise GoogleScholarNotFound(
            f"No Google Scholar profile found for {author_name!r}") from e
    except Exception as e:
        name = type(e).__name__
        if "MaxTries" in name or "Captcha" in name or "Blocked" in name:
            raise GoogleScholarBlocked(
                "Google Scholar refused the profile request (blocked by"
                f" {name}). This is a block, not a missing profile."
            ) from e
        # Anything else out of scholarly is still a failure to reach the
        # provider. Left bare, a ConnectionError arrived as reason "failed"
        # rather than "unavailable".
        raise GoogleScholarUnavailable(
            f"Google Scholar profile lookup failed ({name}: {e}). Not an "
            "empty result — record the provider as unavailable."
        ) from e

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
