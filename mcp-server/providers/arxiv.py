"""arXiv provider — uses the official `arxiv` Python package.

The package handles HTTPS, request spacing and pagination, avoiding the 429
errors produced by raw HTTP calls to the Atom API.

Filtering is done by arXiv, not by us. An earlier version fetched by relevance
and then dropped out-of-range papers in Python, which made a narrow date window
return almost nothing.
"""
from __future__ import annotations

import calendar as _calendar
import errno
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

from . import window as _window  # the function in providers/__init__.py

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

# The package makes num_retries + 1 attempts, not num_retries: _parse_feed
# starts at _try_index 0 and recurses while _try_index < num_retries, so the
# default of 3 means FOUR requests. At 20 s each plus the 3 s spacing that is
# 89 s inside results() alone, and _LOCK_WAIT on top took the worst case to
# 104 s — past the 90 s ceiling, on a thread that cannot be cancelled and
# that goes on holding the lock after the caller has given up.
#
# Pinned here rather than left to the default. Worst case now:
# 3 attempts x 15 s + 2 x 3 s spacing + _LOCK_WAIT 15 = 66 s.
_HTTP_TIMEOUT = 15
_ARXIV_RETRIES = 2          # => 3 attempts
_LOCK_WAIT = 15

_CLIENT = arxiv.Client(num_retries=_ARXIV_RETRIES)
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


def _lock_path() -> "pathlib.Path":
    """Where the cross-process arXiv lock lives.

    Keyed to this install and this user, so two projects on one machine do not
    serialise against each other and two users cannot collide on permissions.

    **That is the decision, and it is narrower than arXiv's terms.** The note at
    the top of this file quotes those terms as applying to every machine under
    your control as a whole; this lock is per project. Two OSP projects open at
    once can therefore each hold a turn, halving the gap. Accepted: serialising
    every project on a shared machine would make one review wait on another's
    unrelated search, and arXiv tolerates the occasional overlap from one user.
    The gap is strict within a project and best-effort across them.
    In the temp directory rather than beside the code, because an install can
    sit on a read-only path and a lock that cannot be created must degrade
    rather than fail.
    """
    import getpass
    import hashlib
    import os
    import pathlib
    import tempfile
    here = str(pathlib.Path(__file__).resolve().parent)
    try:
        who = getpass.getuser()
    except Exception:  # noqa: BLE001 - no passwd entry in some containers
        who = str(os.getuid()) if hasattr(os, "getuid") else "nouser"
    tag = hashlib.sha256(f"{here}:{who}".encode()).hexdigest()[:16]

    # In a directory of our own, mode 0700, rather than loose in a shared /tmp.
    # The file name is derivable by anyone with a shell on the box — it is a
    # hash of the install path and the username — and `_throttle` truncates
    # whatever it opens. A symlink planted at that name therefore truncates the
    # target: demonstrated by a reviewer against a 140-byte file. Modern Linux
    # (fs.protected_symlinks) and macOS's per-user TMPDIR both prevent it, but
    # that is the kernel's mitigation and not ours.
    uid = os.getuid() if hasattr(os, "getuid") else 0
    home = pathlib.Path(tempfile.gettempdir()) / f"osp-{uid}"
    try:
        home.mkdir(mode=0o700, exist_ok=True)
    except OSError:
        return pathlib.Path(tempfile.gettempdir()) / f"osp-arxiv-{tag}.lock"
    return home / f"arxiv-{tag}.lock"


@contextmanager
def _cross_process_turn(deadline: float):
    """Hold arXiv's single connection against OTHER PROCESSES as well.

    The in-process lock below is enough for the MCP server, which is one long
    process. It is worth nothing to the CLI, where every call is a new process:
    measured, a fresh process reads `_last_raw_request = 0.0`, computes a gap of
    about 1.79 billion seconds against `_MIN_GAP`, and never sleeps. The three
    seconds arXiv's terms ask for were not degraded in CLI mode — they were
    absent, and so was the one-request-at-a-time rule.

    flock, not a lock file we create and delete: the kernel releases it when the
    process dies, so a killed call cannot wedge every later one. If the lock
    cannot be made at all — an odd filesystem, no temp directory — this degrades
    to in-process only rather than refusing to search.
    """
    try:
        import fcntl
        import os
    except ImportError:          # not a Unix; in-process locking only
        yield None
        return
    try:
        # O_NOFOLLOW so a symlink planted at this name is refused rather than
        # followed and then truncated. 0o600 so nobody else can read or write
        # it even if they reach the directory.
        path = _lock_path()
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        handle = os.fdopen(fd, "r+")
    except OSError:
        # Includes ELOOP — something is already there and is a symlink. Not
        # ours to fix, and not a reason to refuse to search: degrade to the
        # in-process lock.
        yield None
        return
    # Two different OSErrors come out of flock and they mean opposite things.
    # EWOULDBLOCK is "someone else holds it" — wait and retry. ENOLCK and
    # friends mean this filesystem cannot lock at all, and retrying can never
    # succeed: NFS without lockd, Lustre or GPFS mounted without `flock`, WSL1
    # on a DrvFs path. Treating those as contention burns the whole 15 s
    # deadline and then reports a concurrent process that does not exist —
    # arXiv would appear permanently down, minutes at a time, for a reason that
    # names the wrong cause.
    _CONTENDED = {errno.EWOULDBLOCK, errno.EAGAIN, errno.EACCES, errno.EDEADLK}
    locked = False
    try:
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
                break
            except OSError as exc:
                if exc.errno not in _CONTENDED:
                    # No locking here. Degrade to the in-process lock and the
                    # on-disk timestamp, which is what the docstring promises:
                    # the three-second gap still applies, only the guarantee of
                    # one-at-a-time across processes is lost.
                    break
                if time.time() >= deadline:
                    raise ArxivBusy(
                        f"another Open ScholarPeer process has held the single "
                        f"allowed arXiv connection for more than {_LOCK_WAIT}s. "
                        "arXiv's terms allow one request at a time, so this "
                        "call was not sent. This is a busy provider, not an "
                        "empty result — try again, or use the other providers."
                    )
                time.sleep(0.05)
        yield handle
    finally:
        try:
            if locked:
                fcntl.flock(handle, fcntl.LOCK_UN)
        except OSError:
            # The kernel releases the lock when the handle closes, so this call
            # can only ever lose information. Unguarded, an OSError here
            # REPLACES whatever exception was unwinding — an ArxivBusy and its
            # whole explanation became a bare "[Errno 37] No locks available".
            pass
        finally:
            handle.close()


@contextmanager
def _arxiv_turn():
    """Take the single arXiv connection, or give up rather than queue.

    Both locks share ONE deadline. Giving each its own would double the worst
    case, and the time budget this provider promises is pinned by a test.
    """
    deadline = time.time() + _LOCK_WAIT
    if not _CLIENT_LOCK.acquire(timeout=_LOCK_WAIT):
        raise ArxivBusy(
            f"another arXiv request has held the single allowed connection "
            f"for more than {_LOCK_WAIT}s. arXiv's terms allow one request at "
            "a time, so this call was not sent. This is a busy provider, not "
            "an empty result — try again, or use the other providers."
        )
    try:
        with _cross_process_turn(deadline) as handle:
            # Every arXiv turn, not only the raw downloads. The `arxiv` package
            # keeps its own gap for the search API, but only within one process,
            # so in CLI mode consecutive searches had no gap at all. In the
            # server this costs nothing: the package has already waited, so the
            # recorded timestamp is old enough and this does not sleep.
            _throttle(handle)
            yield
    finally:
        _CLIENT_LOCK.release()

# arXiv ranges need both ends, so an open-ended request gets a wide default.
_CATEGORY_RE = re.compile(r"[A-Za-z-]+(?:\.[A-Za-z-]+)?")

_STAMP_MIN = "190001010000"
_STAMP_MAX = "299912312359"


class ArxivFullTextError(RuntimeError):
    """Full text could not be produced. Never reported as empty text."""


class ArxivNotFound(ArxivFullTextError):
    """No such paper, or no source archive for it. arXiv is fine; the id
    is not, so suggesting a PDF fallback here would be wrong."""


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
        # Validated, not just trimmed. A category of
        # "cs.CL) OR (cat:quant-ph" would close the group early and leave the
        # AND binding nothing — recreating the exact bug B2 existed to fix.
        cats = []
        for c in categories:
            c = (c or "").strip()
            if not c:
                continue
            if not _CATEGORY_RE.fullmatch(c):
                raise ValueError(
                    f"{c!r} is not an arXiv category. They look like "
                    "'cs.CL', 'math.AG' or 'hep-th'.")
            cats.append(c)
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
        # Raised, not returned: a dict here bypasses _err and arrives with
        # no `reason`, which is the one field the agent branches on.
        raise ArxivNotFound(f"No paper found for arxiv_id={arxiv_id!r}.{hint}")
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
_PARSE_BUDGET = 20                    # seconds spent walking the archive
_BRACE_TRIES = 8                      # \title{ occurrences worth trying
_BRACE_SCAN = 64 * 1024               # how far to look for its closing brace

# The whole call must fit inside OSP_CALL_TIMEOUT (90 s), or the agent gets a
# bare "timed out" instead of an error it can act on.
#
# The arithmetic has to account for two things that are easy to miss, and a
# measurement against a deliberately slow server caught both: requests' single
# `timeout` value applies to the connect AND to each read separately, so a
# server that stalls twice spends it twice; and an in-loop deadline check only
# runs after a blocking read returns, so it can overshoot by one read timeout.
#
# Worst case now: _LOCK_WAIT 15 + _MIN_GAP 3 + connect 10 + budget 35 +
# one overshooting read 15 = 78 s. The deadline is started before the request,
# not after it returns.
_CONNECT_TIMEOUT = 10
_READ_TIMEOUT = 15
_DOWNLOAD_BUDGET = 35       # whole transfer, from before the connect
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
# Sized for a working set, not a single paper. At 2 entries a phase reading
# three papers in turn missed on every single read — measured 41/41/40
# downloads over 200 reads, a 0% hit rate, which is worse than no cache
# because each miss also pays the three-second gap.
_TEXT_CACHE: "OrderedDict[str, str]" = OrderedDict()
_TEXT_CACHE_MAX = 8
_TEXT_CACHE_LOCK = threading.Lock()

# One download per paper, however many callers ask at once.
#
# Without this, concurrent first-touches of the same id all miss the cache and
# all queue up behind the single arXiv connection. Measured with nine threads
# on one cold id: six separate downloads, and the last three were refused with
# ArxivBusy after waiting out _LOCK_WAIT — for a paper that was already being
# fetched. The Q&A engine runs subagents in parallel and they read the same
# paper, so this is the normal case, not a corner.
_INFLIGHT: dict[str, threading.Lock] = {}
_INFLIGHT_GUARD = threading.Lock()
_INFLIGHT_MAX = 64


def _inflight_lock(key: str) -> threading.Lock:
    with _INFLIGHT_GUARD:
        lock = _INFLIGHT.get(key)
        if lock is None:
            if len(_INFLIGHT) >= _INFLIGHT_MAX:
                # Drop the ones nobody is holding; the rest are in use.
                for k in [k for k, v in _INFLIGHT.items() if not v.locked()]:
                    del _INFLIGHT[k]
            lock = _INFLIGHT[key] = threading.Lock()
        return lock


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


def _throttle(handle=None) -> None:
    """Keep arXiv's three seconds between requests, across processes too.

    The timestamp lives in the lock file when there is one, so a brand-new
    process inherits it instead of starting from zero. The in-process value is
    still kept and the later of the two wins, so the gap holds whichever way
    the calls arrive.
    """
    global _last_raw_request
    last = _last_raw_request
    if handle is not None:
        try:
            handle.seek(0)
            raw = handle.read().strip()
            if raw:
                last = max(last, float(raw))
        except (OSError, ValueError):
            pass  # unreadable stamp: fall back to the in-process one
    gap = time.time() - last
    if gap < _MIN_GAP:
        time.sleep(_MIN_GAP - gap)
    _last_raw_request = time.time()
    if handle is not None:
        try:
            handle.seek(0)
            handle.truncate()
            handle.write(str(_last_raw_request))
            handle.flush()
        except OSError:
            pass  # cannot record it; the in-process gap still applies


def _download(url: str) -> bytes:
    # Same turn as search: arXiv asks for a single connection at a time across
    # everything under our control, not one per library.
    with _arxiv_turn():
        # Started before the request, so a slow connect and a slow first read
        # both count against it.
        deadline = time.time() + _DOWNLOAD_BUDGET
        try:
            resp = requests.get(url, headers={"User-Agent": UA},
                                timeout=(_CONNECT_TIMEOUT, _READ_TIMEOUT),
                                stream=True)
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
        # gzip.decompress() has no ceiling, and gzip reaches about 1030:1.
        # Measured: a 4.7 MB e-print expanded to 1,073,741,864 characters and
        # 3.1 GB of RSS before returning happily. Read through the cap instead.
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz:
                blob = gz.read(_MAX_UNPACKED + 1)
            if len(blob) > _MAX_UNPACKED:
                raise ArxivFullTextError(
                    f"arXiv source expands past the {_MAX_UNPACKED} byte "
                    "limit on unpacked size")
            text = blob.decode("utf-8", errors="replace")
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

    # Iterating the TarFile yields headers lazily. `getmembers()` walked the
    # whole index first, so an archive of 9 million empty members cost 4 GB
    # and 157 s before `_MAX_MEMBERS` was ever consulted — well past the call
    # timeout, on a thread that cannot be cancelled.
    parse_deadline = time.time() + _PARSE_BUDGET
    for i, member in enumerate(tf):
        if time.time() > parse_deadline:
            hit_cap = (f"stopped after {_PARSE_BUDGET}s spent reading the "
                       "archive index")
            break
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
    # Bounded on both axes. An unclosed `\title{` repeated through the file
    # made this quadratic: 22 s on 64 KB, and the archive compressed to 2.5 KB.
    # A real document has one or two of these, near the top.
    tries = 0
    at = tex.find("\\" + command)
    while at != -1 and tries < _BRACE_TRIES:
        tries += 1
        i = at + len(command) + 1
        while i < len(tex) and tex[i] in " \t\n":
            i += 1
        if i < len(tex) and tex[i] == "{":
            depth, j = 0, i
            stop = min(len(tex), i + _BRACE_SCAN)
            while j < stop:
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
    # An inlined bibliography is long and carries no argument. Done with
    # find() rather than a regex: `\begin{...}.*?\end{...}` with re.S rescans
    # to end-of-file for every unmatched opener, which is quadratic. Measured
    # 10.6 s on 508 KB, and hours at the per-file cap.
    open_tag, close_tag = "\\begin{thebibliography}", "\\end{thebibliography}"
    while True:
        b = tex.find(open_tag)
        if b == -1:
            break
        e = tex.find(close_tag, b)
        if e == -1:
            # Unterminated: a bibliography runs to the end of the document.
            tex = tex[:b]
            break
        tex = tex[:b] + tex[e + len(close_tag):]
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
        raise ValueError("read_arxiv_paper needs an arXiv id")
    url = f"https://arxiv.org/e-print/{arxiv_id}"

    def _bibliography_note(body: str) -> str:
        """Say honestly whether the reference list came through.

        Most arXiv archives ship a compiled `.bbl`, which is collected and
        appended as an orphan. When it is there the printed entries ARE
        present, and claiming otherwise was simply wrong.
        """
        if "bibitem" in body:
            return ("the compiled .bbl is appended at the end, so the "
                    "reference entries are present — but \\citep{key} markers "
                    "still do not map to their printed numbers")
        return ("not included — resolve citations with "
                "get_semantic_scholar_paper_references")

    def _serve(body: str) -> dict[str, Any]:
        out = _window(body, max_chars, offset)
        out["arxiv_id"] = arxiv_id
        out["format"] = "latex"
        out["source"] = url
        out["bibliography"] = _bibliography_note(body)
        return out

    cached = _cache_get(arxiv_id)
    if cached is not None:
        return _serve(cached)

    with _inflight_lock(arxiv_id):
        # Another caller may have finished the download while we waited.
        cached = _cache_get(arxiv_id)
        if cached is not None:
            return _serve(cached)
        return _serve(_fetch_text(arxiv_id, url))


def _fetch_text(arxiv_id: str, url: str) -> str:
    """Download and parse one paper. Callers hold its in-flight lock."""
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

    if not text.strip():
        # A record saying total_chars: 0 with no error reads as "this paper is
        # empty". It means we could not get the text out.
        raise ArxivFullTextError(
            f"no readable text came out of the source for {arxiv_id}. The "
            "body may be entirely comments or non-TeX includes. Read the PDF "
            f"instead: https://arxiv.org/pdf/{arxiv_id} — the markitdown MCP "
            "server registered alongside this one converts it.")

    _cache_put(arxiv_id, text)
    return text
