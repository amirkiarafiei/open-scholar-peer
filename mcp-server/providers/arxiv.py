"""arXiv provider — uses the official `arxiv` Python package.

The package handles HTTPS, request spacing and pagination, avoiding the 429
errors produced by raw HTTP calls to the Atom API.

Filtering is done by arXiv, not by us. An earlier version fetched by relevance
and then dropped out-of-range papers in Python, which made a narrow date window
return almost nothing.
"""
from __future__ import annotations

import calendar as _calendar
import gzip
import io
import re
import tarfile
import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import Any

import arxiv
import requests
from dateutil import parser as _dp

from . import window as _window

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


# ---------- Full text -------------------------------------------------------
#
# Full text is fetched by plain HTTP: arxiv 4.x removed Result.download_pdf
# and download_source. These downloads go through the same single connection
# as search, because arXiv's terms count every request we make, not every
# request one library makes.
#
# The archive is held in memory and never written to disk, so every size is
# bounded. Nothing here extracts to a path, so a crafted member name cannot
# escape anywhere; the risk is decompression size, which is what these caps
# are for.

_MAX_DOWNLOAD = 40 * 1024 * 1024      # compressed bytes off the wire
_MAX_UNPACKED = 60 * 1024 * 1024      # total decompressed bytes
_MAX_MEMBERS = 2000                   # files inside the archive
_MAX_MEMBER_BYTES = 12 * 1024 * 1024  # one file inside the archive

# The whole call must fit inside OSP_CALL_TIMEOUT (90 s), or the agent gets a
# bare "timed out" instead of an error it can act on. Worst case:
# _LOCK_WAIT (25) + _MIN_GAP (3) + _DOWNLOAD_BUDGET (45) = 73 s.
# requests' `timeout` applies per socket operation, not to the whole transfer,
# so a slow trickle would otherwise run for as long as it liked. The streaming
# loop enforces the wall-clock budget itself.
_DOWNLOAD_TIMEOUT = 20      # per socket operation
_DOWNLOAD_BUDGET = 45       # whole transfer
_MIN_GAP = 3.0
_last_raw_request = 0.0

UA = "open-scholar-peer (https://github.com/amirkiarafiei/open-scholar-peer)"


# Reading a long paper takes several windows, and without this each one
# re-downloaded and re-parsed the whole tarball: six fetches for a 300k-char
# paper, each paying the three-second gap. That is slower for the caller and
# ruder to arXiv than it needs to be.
#
# This changes WHEN an answer arrives, never WHAT it is — the same argument
# that allows the shared client under D3. Two entries, newest kept, dropped
# when the process ends. Nothing is written to disk.
# Provider functions run in worker threads (asyncio.to_thread), so the cache
# needs its own lock: a move_to_end followed by a popitem is not one atomic
# step, and two readers could otherwise race on eviction.
_TEXT_CACHE: "OrderedDict[str, str]" = OrderedDict()
_TEXT_CACHE_MAX = 2
_TEXT_CACHE_LOCK = threading.Lock()


def _cache_get(key: str) -> str | None:
    with _TEXT_CACHE_LOCK:
        text = _TEXT_CACHE.get(key)
        if text is not None:
            _TEXT_CACHE.move_to_end(key)
        return text


def _cache_put(key: str, text: str) -> None:
    with _TEXT_CACHE_LOCK:
        _TEXT_CACHE[key] = text
        while len(_TEXT_CACHE) > _TEXT_CACHE_MAX:
            _TEXT_CACHE.popitem(last=False)


class ArxivFullTextError(RuntimeError):
    """Full text could not be produced. Never reported as empty text."""


class ArxivNotFound(ArxivFullTextError):
    """No source archive at that id. Suggesting a PDF here would be wrong."""


def _throttle() -> None:
    """Keep arXiv's three seconds between our own raw downloads.

    The `arxiv` package keeps this gap for the search API using a timestamp on
    the client; these downloads bypass that code path, so they need their own.
    """
    global _last_raw_request
    gap = time.time() - _last_raw_request
    if gap < _MIN_GAP:
        time.sleep(_MIN_GAP - gap)
    _last_raw_request = time.time()


def _download(url: str) -> bytes:
    # Same turn as search: arXiv asks for a single connection at a time across
    # everything under our control, not one per library.
    with _arxiv_turn():
        _throttle()
        try:
            resp = requests.get(url, headers={"User-Agent": UA},
                                timeout=_DOWNLOAD_TIMEOUT, stream=True)
        except requests.RequestException as e:
            raise ArxivFullTextError(f"arXiv download failed: {e}") from e

        if resp.status_code == 404:
            raise ArxivNotFound(
                f"arXiv has no source at {url}. Either the id is wrong, or "
                "this submission has no source archive. Check the id with "
                "get_arxiv_paper_details first.")
        if resp.status_code != 200:
            raise ArxivFullTextError(
                f"arXiv returned HTTP {resp.status_code} for {url}")

        deadline = time.time() + _DOWNLOAD_BUDGET
        chunks, total = [], 0
        for chunk in resp.iter_content(chunk_size=262144):
            total += len(chunk)
            if total > _MAX_DOWNLOAD:
                raise ArxivFullTextError(
                    f"arXiv source is larger than the {_MAX_DOWNLOAD} byte cap")
            if time.time() > deadline:
                raise ArxivFullTextError(
                    f"arXiv source did not finish downloading within "
                    f"{_DOWNLOAD_BUDGET}s (got {total} bytes)")
            chunks.append(chunk)
        return b"".join(chunks)


def _tex_members(raw: bytes) -> dict[str, str]:
    """Pull the .tex files out of an arXiv e-print archive, in memory.

    An e-print is a gzip stream. Usually it is a tarball; for a single-file
    submission it is just the one gzipped file.
    """
    try:
        tf = tarfile.open(fileobj=io.BytesIO(raw))
    except tarfile.ReadError:
        try:
            text = gzip.decompress(raw).decode("utf-8", errors="replace")
        except OSError as e:
            raise ArxivFullTextError(
                f"arXiv source is neither a tarball nor a gzipped file: {e}") from e
        if "\\documentclass" not in text and "\\begin{document}" not in text:
            raise ArxivFullTextError(
                "arXiv source holds no LaTeX — the submission is probably "
                "PDF-only")
        return {"main.tex": text}

    out: dict[str, str] = {}
    unpacked = 0
    tex_seen = 0        # .tex members present, whether or not we took them
    skipped_big = 0
    hit_cap = ""

    for i, member in enumerate(tf.getmembers()):
        if i >= _MAX_MEMBERS:
            hit_cap = f"stopped after {_MAX_MEMBERS} files in the archive"
            break
        if not member.isfile():
            continue
        name = member.name.lstrip("./")
        if not name.lower().endswith((".tex", ".bbl")):
            continue
        tex_seen += 1
        # Checked before reading, so an over-sized member is never allocated.
        if member.size > _MAX_MEMBER_BYTES:
            skipped_big += 1
            continue
        if unpacked + member.size > _MAX_UNPACKED:
            hit_cap = (f"stopped at the {_MAX_UNPACKED} byte limit on total "
                       f"unpacked size")
            break
        unpacked += member.size
        handle = tf.extractfile(member)
        if handle is None:
            continue
        out[name] = handle.read().decode("utf-8", errors="replace")

    if not out:
        # Say which of these it actually was. Reporting "probably PDF-only"
        # for an archive whose .tex files were all too large sends the reader
        # off to a PDF that will not help.
        if skipped_big:
            raise ArxivFullTextError(
                f"every .tex file in the arXiv source is larger than the "
                f"{_MAX_MEMBER_BYTES} byte per-file limit "
                f"({skipped_big} skipped), so none was read")
        if hit_cap:
            raise ArxivFullTextError(f"arXiv source could not be read: {hit_cap}")
        raise ArxivFullTextError(
            "arXiv source archive holds no .tex files — the submission is "
            "probably PDF-only")

    # Partial is fine, silently partial is not.
    if skipped_big or hit_cap:
        notes = []
        if skipped_big:
            notes.append(f"{skipped_big} .tex file(s) over the per-file limit "
                         f"were skipped")
        if hit_cap:
            notes.append(hit_cap)
        out["__truncation_note__"] = "; ".join(notes)
    return out


def _strip_comments(tex: str) -> str:
    # A % starts a comment unless it is escaped. \% is a literal percent.
    return re.sub(r"(?<!\\)%.*$", "", tex, flags=re.MULTILINE)


def _main_file(files: dict[str, str]) -> str:
    for name, text in files.items():
        if "\\documentclass" in text:
            return name
    for name, text in files.items():
        if "\\begin{document}" in text:
            return name
    return sorted(files)[0]


def _inline(name: str, files: dict[str, str], seen: set[str], depth: int = 0) -> str:
    """Splice \\input and \\include children in, so the text reads in order."""
    if depth > 8 or name in seen:
        return ""
    seen.add(name)
    text = _strip_comments(files.get(name, ""))

    def repl(m: re.Match) -> str:
        child = m.group(1).strip()
        for candidate in (child, f"{child}.tex", child.lstrip("./"),
                          f"{child.lstrip('./')}.tex"):
            if candidate in files:
                return "\n" + _inline(candidate, files, seen, depth + 1) + "\n"
        return ""

    return re.sub(r"\\(?:input|include)\s*\{([^}]+)\}", repl, text)


def _braced(tex: str, command: str) -> str | None:
    """Read the balanced {...} argument of \\command, or None.

    A regex cannot do this: titles and author lists routinely contain nested
    braces (\\thanks{}, \\textbf{}, footnote markers), and a non-greedy match
    stops at the first closing brace.
    """
    at = tex.find("\\" + command)
    while at != -1:
        i = at + len(command) + 1
        while i < len(tex) and tex[i] in " \t\n":
            i += 1
        if i < len(tex) and tex[i] == "{":
            depth, j = 0, i
            while j < len(tex):
                if tex[j] == "{" and (j == 0 or tex[j - 1] != "\\"):
                    depth += 1
                elif tex[j] == "}" and tex[j - 1] != "\\":
                    depth -= 1
                    if depth == 0:
                        return tex[i + 1:j].strip()
                j += 1
        at = tex.find("\\" + command, at + 1)
    return None


def _body_only(tex: str) -> str:
    """Drop the preamble and the bibliography, but keep who wrote what.

    Everything before \\begin{document} is \\usepackage lines, which tell a
    reviewer nothing and would fill the first page of any capped read. But
    \\title and \\author almost always sit up there too, and dropping the
    preamble wholesale handed the agent a paper with no title and no authors —
    only a \\maketitle that means nothing on its own. They are carried over.
    """
    start = tex.find("\\begin{document}")
    carried = ""
    if start != -1:
        preamble = tex[:start]
        title = _braced(preamble, "title")
        author = _braced(preamble, "author")
        if title:
            carried += f"\\title{{{title}}}\n"
        if author:
            carried += f"\\author{{{author}}}\n"
        tex = tex[start + len("\\begin{document}"):]
        if carried:
            tex = carried + tex
    end = tex.find("\\end{document}")
    if end != -1:
        tex = tex[:end]
    # An inlined bibliography is long and carries no argument.
    tex = re.sub(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}",
                 "", tex, flags=re.S)
    return tex


def _tidy(tex: str) -> str:
    # \label is deliberately KEPT. \ref survives into the output, so removing
    # the labels turned every "see Table~\ref{tab:wmt}" into a pointer at
    # nothing — 21 \ref against 0 \label on 1706.03762.
    tex = re.sub(r"[ \t]+", " ", tex)
    tex = re.sub(r"\n{3,}", "\n\n", tex)
    return tex.strip()


def latex_from_archive(raw: bytes) -> str:
    """Archive bytes -> one ordered LaTeX document. Pure, unit testable."""
    files = _tex_members(raw)
    note = files.pop("__truncation_note__", "")
    main = _main_file(files)

    # `_inline` fills `used` as it walks, so one pass answers both questions:
    # what the document says, and which files it reached.
    used: set[str] = set()
    body = _body_only(_inline(main, files, used))

    # Anything the main file never included is appended AFTER the body has
    # been trimmed. Appending first dropped it silently: `_body_only` cuts at
    # \end{document}, and the orphan text was sitting past that point.
    orphans = [n for n in sorted(files) if n not in used]
    for name in orphans:
        text = _strip_comments(files[name]).strip()
        if text:
            body += f"\n\n% --- {name} (not included by the main file) ---\n{text}"

    if note:
        body = f"% INCOMPLETE: {note}\n\n{body}"
    return _tidy(body)


def read_paper(arxiv_id: str, max_chars: int = 50000, offset: int = 0) -> dict[str, Any]:
    arxiv_id = (arxiv_id or "").strip()
    if not arxiv_id:
        return {"error": "read_arxiv_paper needs an arXiv id"}
    url = f"https://arxiv.org/e-print/{arxiv_id}"

    cached = _cache_get(arxiv_id)
    if cached is not None:
        out = _window(cached, max_chars, offset)
        out["arxiv_id"] = arxiv_id
        out["format"] = "latex"
        out["source"] = url
        out["bibliography"] = ("not included — resolve citations with "
                               "get_semantic_scholar_paper_references")
        return out

    try:
        text = latex_from_archive(_download(url))
    except ArxivNotFound:
        # The paper is not there at all; a PDF suggestion would be nonsense.
        raise
    except ArxivFullTextError as e:
        # The paper exists but carries no LaTeX, so it was submitted as PDF.
        raise ArxivFullTextError(
            f"{e} Read the PDF instead: https://arxiv.org/pdf/{arxiv_id} — "
            "the markitdown MCP server installed alongside this one converts "
            "it with convert_to_markdown."
        ) from e

    _cache_put(arxiv_id, text)

    out = _window(text, max_chars, offset)
    out["arxiv_id"] = arxiv_id
    out["format"] = "latex"
    out["source"] = url
    # Said outright, because the source carries \citep{key} markers and no
    # printed reference numbers, and the reference list is not in it.
    out["bibliography"] = ("not included — resolve citations with "
                           "get_semantic_scholar_paper_references")
    return out
