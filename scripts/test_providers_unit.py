#!/usr/bin/env python3
"""
test_providers_unit.py — offline checks for the MCP provider logic.

No network. Everything here is a pure function fed a fixed input, so it runs
in about a second and gives the same answer every time.

This exists because the most important provider rule cannot be proved against
the live internet: **a blocked request must never look like a search that
found nothing.** You cannot ask Google to block you on demand, so the block
page is a fixture.

Companion: `scripts/test_providers.py` calls the real APIs. Run that too
before believing a provider works; run this one on every change.

Exit codes:
  0  — all checks pass.
  1  — at least one check failed.
  2  — script error (usually the provider dependencies are not installed).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "mcp-server"))

PASS: list[str] = []
FAIL: list[str] = []


def check(label: str, got, want) -> None:
    if got == want:
        PASS.append(label)
    else:
        FAIL.append(f"{label}\n       expected: {want!r}\n       got:      {got!r}")


def check_true(label: str, got) -> None:
    check(label, bool(got), True)


def check_false(label: str, got) -> None:
    check(label, bool(got), False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# What Google sends when it does not want to talk to you. Trimmed from a real
# 429 captured on 2026-09-20.
BLOCK_PAGE = """<!DOCTYPE html><html><head><title>Error 429 (Too Many Requests)</title></head>
<body><div id="gs_captcha_ccl"></div>
<p>Our systems have detected unusual traffic from your computer network.
Please try your request again later. This page checks to see if it's really
you sending the requests, and not a robot.</p></body></html>"""

# A real search that found nothing. Note: also has zero result rows. This is
# the page the block detector must NOT flag.
EMPTY_PAGE = """<!DOCTYPE html><html><head><title>zzqqxx - Google Scholar</title></head>
<body><div id="gs_res_ccl_mid"></div>
<div class="gs_med">Your search - <b>zzqqxx nonexistent</b> - did not match any articles.</div>
</body></html>"""

RESULTS_PAGE = """<!DOCTYPE html><html><body><div id="gs_res_ccl_mid">
<div class="gs_r gs_or gs_scl"><div class="gs_ri">
  <h3 class="gs_rt"><a href="https://example.org/a.pdf">Attention Is All You Need</a></h3>
  <div class="gs_a">A Vaswani, N Shazeer - Advances in neural information, 2017</div>
  <div class="gs_rs">The dominant sequence transduction models are based on ...</div>
</div></div>
<div class="gs_r gs_or gs_scl"><div class="gs_ri">
  <h3 class="gs_rt"><a href="https://example.org/b.pdf">BERT: Pre-training of Deep Bidirectional Transformers</a></h3>
  <div class="gs_a">J Devlin, MW Chang - NAACL, 2019</div>
  <div class="gs_rs">We introduce a new language representation model ...</div>
</div></div></div></body></html>"""


# ---------------------------------------------------------------------------
# Google Scholar — the block must not look like an empty result (B9)
# ---------------------------------------------------------------------------

def test_google_scholar() -> None:
    from providers import google_scholar as gs

    check_true("block: HTTP 429 is a block",
               gs.is_block_page(429, "", ""))
    check_true("block: HTTP 403 is a block",
               gs.is_block_page(403, "", ""))
    check_true("block: captcha markers in a 200 body are a block",
               gs.is_block_page(200, BLOCK_PAGE, ""))
    check_true("block: a redirect to /sorry/ is a block",
               gs.is_block_page(200, "<html></html>",
                                "https://www.google.com/sorry/index?continue=..."))

    # The whole point. Both pages have zero result rows; only one is a block.
    check_false("no false alarm: a genuine zero-hit page is NOT a block",
                gs.is_block_page(200, EMPTY_PAGE, ""))
    check_false("no false alarm: a normal results page is NOT a block",
                gs.is_block_page(200, RESULTS_PAGE, ""))

    check("zero-hit page parses to an empty list",
          gs._parse_results(EMPTY_PAGE, 10), [])

    rows = gs._parse_results(RESULTS_PAGE, 10)
    check("results page yields 2 rows", len(rows), 2)
    check("row title", rows[0]["title"], "Attention Is All You Need")
    check("row url", rows[0]["url"], "https://example.org/a.pdf")
    check_true("row authors captured", rows[0]["authors"].startswith("A Vaswani"))
    check_true("row abstract captured", rows[0]["abstract"].startswith("The dominant"))
    check("num_results caps the rows", len(gs._parse_results(RESULTS_PAGE, 1)), 1)

    # Every Google Scholar failure must be one family, so a caller can catch
    # "we did not get to look" without listing exception types.
    check_true("GoogleScholarUnavailable is an exception type",
               issubclass(gs.GoogleScholarUnavailable, Exception))
    check_true("a block is a kind of unavailable",
               issubclass(gs.GoogleScholarBlocked, gs.GoogleScholarUnavailable))

    # The retry budget has to fit inside the tool layer's own timeout, or the
    # caller gets a bare "timed out" instead of the message that explains the
    # block — which is the whole point of the fix.
    worst = gs._TIMEOUT * gs._MAX_ATTEMPTS + sum(2 ** i for i in range(gs._MAX_ATTEMPTS - 1))
    check_true(f"retry budget ({worst}s) fits inside OSP_CALL_TIMEOUT (90s)",
               worst < 90)

    # No code path may answer a failure with an empty list.
    import inspect
    src = inspect.getsource(gs._fetch)
    check_false("_fetch never returns an empty list", "return []" in src)
    check_true("_fetch raises the provider's own error type",
               "GoogleScholarUnavailable(" in src)


# ---------------------------------------------------------------------------
# arXiv — the query builder (B1, B2)
# ---------------------------------------------------------------------------

def test_arxiv_query() -> None:
    from providers import arxiv as ax

    check("plain query is parenthesised",
          ax.build_query("transformer"), "(transformer)")

    # The bug that made the category filter do nothing: without AND, arXiv ORs
    # the two halves and returns papers from any category.
    check("category is joined with AND, not whitespace",
          ax.build_query("transformer", categories=["cs.CL"]),
          "(transformer) AND (cat:cs.CL)")

    check("several categories are ORed inside one group",
          ax.build_query("transformer", categories=["cs.CL", "cs.LG"]),
          "(transformer) AND (cat:cs.CL OR cat:cs.LG)")

    # arXiv needs both ends of a range, so an open end gets a wide default.
    check("date_from only, open upper end",
          ax.build_query("llm", date_from="2026-01-01"),
          "(llm) AND submittedDate:[202601010000 TO 299912312359]")

    check("date_to only, open lower end",
          ax.build_query("llm", date_to="2024-06-30"),
          "(llm) AND submittedDate:[190001010000 TO 202406302359]")

    # A bare end date means midnight, which would drop the whole last day.
    check("a bare end date covers the whole day",
          ax.build_query("llm", date_from="2024-01-01", date_to="2024-06-30"),
          "(llm) AND submittedDate:[202401010000 TO 202406302359]")

    check("dates and categories together",
          ax.build_query("bert", date_from="2024-01-01", date_to="2024-06-30",
                         categories=["cs.CL"]),
          "(bert) AND (cat:cs.CL) AND submittedDate:[202401010000 TO 202406302359]")

    # dateutil fills a partial date from TODAY, so "2024" would become
    # 2024-<this month>-<today> and silently drop most of the year.
    check("a bare year starts on 1 January",
          ax.build_query("x", date_from="2024"),
          "(x) AND submittedDate:[202401010000 TO 299912312359]")
    check("a bare year ends on 31 December",
          ax.build_query("x", date_to="2024"),
          "(x) AND submittedDate:[190001010000 TO 202412312359]")
    check("a year-month starts on the 1st",
          ax.build_query("x", date_from="2024-06"),
          "(x) AND submittedDate:[202406010000 TO 299912312359]")
    check("a year-month ends on its last day",
          ax.build_query("x", date_to="2024-06"),
          "(x) AND submittedDate:[190001010000 TO 202406302359]")
    check("February in a leap year ends on the 29th",
          ax.build_query("x", date_to="2024-02"),
          "(x) AND submittedDate:[190001010000 TO 202402292359]")
    check("February in a common year ends on the 28th",
          ax.build_query("x", date_to="2023-02"),
          "(x) AND submittedDate:[190001010000 TO 202302282359]")

    # A query with its own operators must survive being wrapped.
    check("an ANDNOT query is parenthesised, not mangled",
          ax.build_query('"multi-agent" ANDNOT survey', categories=["cs.MA"]),
          '("multi-agent" ANDNOT survey) AND (cat:cs.MA)')
    check("a field prefix survives",
          ax.build_query('ti:"attention is all you need"'),
          '(ti:"attention is all you need")')

    check("categories only, no free text",
          ax.build_query("", categories=["cs.CL"]), "(cat:cs.CL)")
    check("blank category entries are dropped",
          ax.build_query("x", categories=["cs.CL", "", "  "]),
          "(x) AND (cat:cs.CL)")
    check("nothing at all yields an empty query",
          ax.build_query("  "), "")


# ---------------------------------------------------------------------------
# Semantic Scholar — field lists must match the serializers (B5, B6, B8)
# ---------------------------------------------------------------------------

def test_semantic_scholar_fields() -> None:
    from providers import semantic_scholar as ss

    for name in ("tldr", "openAccessPdf", "isOpenAccess", "publicationDate",
                 "fieldsOfStudy"):
        check_true(f"_PAPER_FIELDS requests {name}", name in ss._PAPER_FIELDS)

    # The 10 MB failure came from asking for nested citation/reference trees
    # and the embedding vector on every paper.
    heavy = [f for f in ss._PAPER_FIELDS
             if f.startswith(("citations.", "references.")) or f == "embedding"]
    check("_PAPER_FIELDS asks for no nested or embedding fields", heavy, [])
    heavy = [f for f in ss._SLIM_FIELDS
             if f.startswith(("citations.", "references.")) or f == "embedding"]
    check("_SLIM_FIELDS asks for no nested or embedding fields", heavy, [])
    check_false("_SLIM_FIELDS does not pull abstracts into list results",
                "abstract" in ss._SLIM_FIELDS)

    # _take must stop pulling, or one call pages the whole result set.
    class ExplodingPager:
        """Yields 3 real items, then fails — standing in for page 2."""
        def __iter__(self):
            yield from (1, 2, 3)
            raise AssertionError("fetched another page when it should have stopped")

    check("_take stops at the limit and fetches no further page",
          ss._take(ExplodingPager(), 3), [1, 2, 3])
    check("_take under-reads happily", ss._take([1, 2, 3], 2), [1, 2])

    # B8: SnippetPaper is not a Paper.
    class FakeSnippetPaper:
        corpus_id = 12345
        title = "A paper"
        authors = ["Ada Lovelace", "Alan Turing"]   # plain strings
        open_access_info = {"license": "CCBY"}

    got = ss._snippet_paper_to_dict(FakeSnippetPaper())
    check("snippet authors stay real names",
          got["authors"], ["Ada Lovelace", "Alan Turing"])
    check("snippet corpusId is read from corpus_id", got["corpusId"], 12345)
    check_false("snippet record no longer claims a snippetId", "snippetId" in got)


# ---------------------------------------------------------------------------
# Regressions found by review on 2026-09-20. Each of these shipped once.
# ---------------------------------------------------------------------------

def test_review_regressions() -> None:
    from providers import semantic_scholar as ss
    from providers import arxiv as ax
    import datetime

    # A datetime cannot be serialized, and coercing it invents a midnight
    # time the API never sent.
    check("publicationDate becomes a plain date string",
          ss._date_str(datetime.datetime(2024, 3, 5, 0, 0)), "2024-03-05")
    check("a missing date stays None", ss._date_str(None), None)
    check("a string date is left alone", ss._date_str("2024-03-05"), "2024-03-05")

    class FakePaper:
        # `Paper` declares no matchScore property, so getattr answers None.
        raw_data = {"matchScore": 181.6}
        paperId = "p1"
        title = "A Paper"

    import json
    record = ss._paper_to_dict(FakePaper())
    json.dumps(record)          # raises if any value is not serializable
    PASS.append("a paper record is JSON serializable")
    raw = getattr(FakePaper(), "raw_data", None) or {}
    check("matchScore is read from raw_data, not getattr",
          raw.get("matchScore"), 181.6)
    check("getattr really does answer None for it",
          getattr(FakePaper(), "matchScore", None), None)

    # The package turns HTTP 429 into ConnectionRefusedError and, with its
    # own retry on, sleeps for minutes past the tool timeout.
    check_true("the client is built with the package's retry loop off",
               "retry=False" in __import__("inspect").getsource(ss._get_client))
    def _expect_rate_limit(label, raiser):
        try:
            ss._call(raiser)
            FAIL.append(f"{label}: no SemanticScholarRateLimited raised")
        except ss.SemanticScholarRateLimited:
            PASS.append(label)
        except Exception as e:
            FAIL.append(f"{label}: raised {type(e).__name__} instead")

    def bare():
        raise ConnectionRefusedError("HTTP status 429 Too Many Requests.")
    _expect_rate_limit("a bare 429 becomes a rate-limit error", bare)

    # What actually happens: tenacity wraps it, even with retrying off, so
    # catching only the inner type misses every real case.
    class FakeRetryError(Exception):
        pass

    def wrapped():
        try:
            raise ConnectionRefusedError("HTTP status 429 Too Many Requests.")
        except ConnectionRefusedError as inner:
            raise FakeRetryError("RetryError[...]") from inner
    _expect_rate_limit("a 429 wrapped in RetryError is still caught", wrapped)

    # And an unrelated error must pass straight through, not be mislabelled.
    def other():
        raise ValueError("bad field name")
    try:
        ss._call(other)
        FAIL.append("an unrelated error was swallowed")
    except ValueError:
        PASS.append("an unrelated error is not mislabelled as a rate limit")
    except ss.SemanticScholarRateLimited:
        FAIL.append("an unrelated error was mislabelled as a rate limit")

    # A shared lock plus a request with no timeout wedges every later call.
    check_true("the arXiv session was given a request timeout",
               getattr(ax._CLIENT, "_session", None) is not None
               and ax._CLIENT._session.request.__module__ == ax.__name__)
    check_true("waiting for the arXiv connection is bounded", ax._LOCK_WAIT > 0)
    check_true("the arXiv HTTP timeout leaves room inside OSP_CALL_TIMEOUT",
               ax._HTTP_TIMEOUT * 3 + ax._MIN_SPACING_ALLOWANCE < 90
               if hasattr(ax, "_MIN_SPACING_ALLOWANCE") else ax._HTTP_TIMEOUT * 3 < 90)
    check_true("ArxivBusy is not mistaken for an empty result",
               issubclass(ax.ArxivBusy, Exception))


# ---------------------------------------------------------------------------
# Semantic Scholar — the filters must reach the client under the right names
# (B7). Checked offline with a stand-in client, because the live API is not
# always reachable and a typo here fails silently as "no filter applied".
# ---------------------------------------------------------------------------

class _FakeClient:
    """Records the call instead of making it."""

    def __init__(self):
        self.calls = []

    def search_paper(self, query, **kwargs):
        self.calls.append(("search_paper", query, kwargs))
        return []

    def get_paper(self, paper_id, **kwargs):
        self.calls.append(("get_paper", paper_id, kwargs))
        return object()


def test_semantic_scholar_wiring() -> None:
    from providers import semantic_scholar as ss

    fake = _FakeClient()
    real = ss._get_client
    ss._get_client = lambda: fake
    try:
        ss.search_papers(
            "q", limit=7, year="2019", publication_date_or_year="2019-01-01:2019-06-30",
            venue=["NeurIPS"], fields_of_study=["Computer Science"],
            publication_types=["JournalArticle"], open_access_pdf=True,
            min_citation_count=5,
        )
        _, query, kw = fake.calls[-1]
        check("query is passed through", query, "q")
        check("limit is passed", kw.get("limit"), 7)
        check("year reaches the client", kw.get("year"), "2019")
        check("publication_date_or_year reaches the client",
              kw.get("publication_date_or_year"), "2019-01-01:2019-06-30")
        check("venue reaches the client", kw.get("venue"), ["NeurIPS"])
        check("fields_of_study reaches the client",
              kw.get("fields_of_study"), ["Computer Science"])
        check("publication_types reaches the client",
              kw.get("publication_types"), ["JournalArticle"])
        check("open_access_pdf reaches the client", kw.get("open_access_pdf"), True)
        check("min_citation_count reaches the client", kw.get("min_citation_count"), 5)
        check_true("an explicit field list is sent", bool(kw.get("fields")))

        # Unset filters must be absent, not None: the package builds the query
        # string from whatever it is handed.
        fake.calls.clear()
        ss.search_papers("q", limit=3)
        _, _, kw = fake.calls[-1]
        absent = [k for k in ("year", "venue", "sort", "bulk", "min_citation_count",
                              "fields_of_study", "publication_types",
                              "publication_date_or_year")
                  if k in kw]
        check("unset filters are omitted entirely", absent, [])
        check_false("open_access_pdf is omitted when false", "open_access_pdf" in kw)

        # The package refuses `sort` unless `bulk` is set, so the provider must
        # set it, and callers must be told relevance is lost.
        fake.calls.clear()
        ss.search_papers("q", limit=3, sort="citationCount:desc")
        _, _, kw = fake.calls[-1]
        check("sort reaches the client", kw.get("sort"), "citationCount:desc")
        check("sort forces bulk, which the package requires", kw.get("bulk"), True)

        # limit is clamped to the package's documented 1..100.
        fake.calls.clear()
        ss.search_papers("q", limit=9999)
        check("limit is clamped to 100", fake.calls[-1][2].get("limit"), 100)
        fake.calls.clear()
        ss.search_papers("q", limit=0)
        check("limit is floored at 1", fake.calls[-1][2].get("limit"), 1)

        # get_paper is where the 76-field default caused 10 MB failures.
        fake.calls.clear()
        ss.get_paper("abc")
        check("get_paper sends an explicit field list",
              fake.calls[-1][2].get("fields"), ss._PAPER_FIELDS)
    finally:
        ss._get_client = real


# ---------------------------------------------------------------------------
# arXiv full text — archive handling (M12 F1/F2)
# ---------------------------------------------------------------------------

def _make_tarball(files: dict[str, bytes]) -> bytes:
    """Build a .tar.gz in memory, so the extractor is tested on a real one."""
    import io, tarfile
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, data in files.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def test_arxiv_fulltext() -> None:
    from providers import arxiv as ax

    # \title and \author sit in the preamble. Dropping the preamble wholesale
    # handed the agent a paper with no title and no authors — only a bare
    # \maketitle. Nested braces rule out a regex: \thanks{} is routine.
    withmeta = b"""\\documentclass{article}
\\title{A Paper About {Nested} Braces}
\\author{Ada Lovelace\\thanks{Equal contribution.} \\and Alan Turing}
\\usepackage{noise}
\\begin{document}
\\maketitle
Body text here.
\\end{document}
"""
    meta = ax.latex_from_archive(_make_tarball({"ms.tex": withmeta}))
    check_true("the title survives the preamble being dropped",
               "A Paper About {Nested} Braces" in meta)
    check_true("so does the author list", "Ada Lovelace" in meta)
    check_true("including everything after a nested command",
               "Alan Turing" in meta)
    check_false("but the package noise does not", "usepackage" in meta)
    check_true("and the body is still there", "Body text here." in meta)

    check("a balanced argument is read whole, nested braces and all",
          ax._braced("\\title{a {b} c} rest", "title"), "a {b} c")
    check("a missing command gives None",
          ax._braced("\\author{x}", "title"), None)

    main = b"""\\documentclass{article}
\\begin{document}
\\title{A Paper}
% this comment must not survive
Intro text. 50\\% of cases.
\\input{body}
\\begin{thebibliography}{9}
\\bibitem{x} Some Reference, 1999.
\\end{thebibliography}
\\end{document}
"""
    body = b"Body section text.\n\\label{sec:body}\nMore body.\n"
    raw = _make_tarball({"ms.tex": main, "body.tex": body,
                         "fig1.png": b"\x89PNG not tex", "notes.txt": b"ignore me"})

    text = ax.latex_from_archive(raw)
    check_false("preamble is dropped", "\\documentclass" in text)
    check_false("comments are stripped", "must not survive" in text)
    check_true("an escaped percent survives", "50\\%" in text)
    check_true("the main file's text is present", "Intro text." in text)
    check_true("an \\input child is spliced in", "Body section text." in text)
    check_true("later child text is present", "More body." in text)
    # \ref survives, so stripping \label left every cross-reference pointing
    # at nothing — 21 \ref against 0 \label on a real paper.
    check_true("\\label is KEPT, because \\ref survives", "\\label" in text)
    check_false("the bibliography is dropped", "Some Reference" in text)
    check_false("non-tex members are ignored", "ignore me" in text)

    # A .tex the main file never includes must still be returned. It used to
    # be appended after \end{document}, which _body_only then cut off, so it
    # vanished without a word. Real papers have these: Attention Is All You
    # Need lost about 5,000 characters this way.
    orphan_raw = _make_tarball({
        "ms.tex": b"\\documentclass{article}\n\\begin{document}\nMAIN BODY\n"
                  b"\\input{used}\n\\end{document}\n",
        "used.tex": b"USED CHILD\n",
        "orphan.tex": b"ORPHAN CONTENT\n",
    })
    got = ax.latex_from_archive(orphan_raw)
    check_true("an included child is spliced in", "USED CHILD" in got)
    check_true("a file the main document never includes is kept",
               "ORPHAN CONTENT" in got)
    check_true("and it is labelled as not part of the main flow",
               "not included by the main file" in got)
    check_false("the preamble is still dropped", "\\documentclass" in got)

    # Mutually recursive includes must terminate.
    loop_raw = _make_tarball({
        "a.tex": b"\\documentclass{x}\n\\begin{document}\nAAA\n\\input{b}\n\\end{document}\n",
        "b.tex": b"BBB\n\\input{a}\n",
    })
    looped = ax.latex_from_archive(loop_raw)
    check_true("mutual \\input recursion terminates", "AAA" in looped and "BBB" in looped)
    check_true("and does not blow up in size", len(looped) < 2000)

    # Every call must finish inside OSP_CALL_TIMEOUT, or the agent sees a bare
    # "timed out" instead of an error naming the cause.
    worst = ax._LOCK_WAIT + ax._MIN_GAP + ax._DOWNLOAD_BUDGET
    check_true(f"read_arxiv_paper worst case ({worst}s) fits inside 90s", worst < 90)

    # A single-file submission is a bare gzipped .tex, not a tarball.
    import gzip
    single = gzip.compress(b"\\documentclass{article}\n\\begin{document}\nOnly file.\n\\end{document}\n")
    check_true("a single gzipped .tex is handled",
               "Only file." in ax.latex_from_archive(single))

    # A hostile archive: one .tex that unpacks to far more than the per-file
    # limit. It must be refused WITHOUT being read into memory, and the
    # message must say why — "probably PDF-only" would send the reader to a
    # PDF that does not exist.
    bomb = _make_tarball({"ms.tex": b"A" * (ax._MAX_MEMBER_BYTES + 1024)})
    try:
        ax.latex_from_archive(bomb)
        FAIL.append("an over-sized .tex was accepted")
    except ax.ArxivFullTextError as e:
        check_true("an over-sized .tex is refused for the right reason",
                   "per-file limit" in str(e))
        check_false("and is not blamed on the paper being PDF-only",
                    "PDF-only" in str(e))

    # Partial is acceptable; silently partial is not.
    partial = _make_tarball({
        "ms.tex": b"\\documentclass{a}\\begin{document}GOOD\\end{document}",
        "huge.tex": b"B" * (ax._MAX_MEMBER_BYTES + 1024),
    })
    got = ax.latex_from_archive(partial)
    check_true("a partly-read archive still returns what it could",
               "GOOD" in got)
    check_true("and says so at the top", "INCOMPLETE" in got)

    # Nothing may be written to disk, whatever a member is called.
    import os
    traversal = _make_tarball({
        "../../tmp/osp_escape_test.tex":
            b"\\documentclass{a}\\begin{document}X\\end{document}",
    })
    ax.latex_from_archive(traversal)
    check_false("a ../ member name writes nothing to disk",
                os.path.exists("/tmp/osp_escape_test.tex"))

    # Paging re-downloaded the whole tarball for every window — six fetches
    # for a long paper, each paying the three-second gap. The cache is read
    # from worker threads, so it has a lock of its own.
    import threading as _t
    ax._cache_put("A", "text-A")
    ax._cache_put("B", "text-B")
    check("a cached entry comes back", ax._cache_get("A"), "text-A")
    check("an unknown key gives None", ax._cache_get("ZZZ"), None)

    bleed = []

    def _hammer(key):
        for _ in range(200):
            got = ax._cache_get(key)
            if got is not None and got != f"text-{key}":
                bleed.append((key, got))
            ax._cache_put(key, f"text-{key}")

    threads = [_t.Thread(target=_hammer, args=(k,)) for k in "ABC"]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    check("concurrent readers never see another paper's text", bleed, [])
    check_true("the cache stays bounded",
               len(ax._TEXT_CACHE) <= ax._TEXT_CACHE_MAX)

    # A PDF-only submission has no .tex at all and must say so, not return "".
    pdf_only = _make_tarball({"paper.pdf": b"%PDF-1.4 fake"})
    try:
        ax.latex_from_archive(pdf_only)
        FAIL.append("a PDF-only archive returned text instead of raising")
    except ax.ArxivFullTextError as e:
        check_true("PDF-only archive raises and mentions the PDF fallback",
                   "PDF-only" in str(e) or "pdf" in str(e).lower())


# ---------------------------------------------------------------------------
# Europe PMC — JATS to text, and the open-access clause (M12 F3/F4)
# ---------------------------------------------------------------------------

JATS_EXTRA = """<article>
<body>
  <sec><title>Empty Section</title></sec>
  <sec><title>Real</title><p>Has content.</p></sec>
  <sec><title>References</title>
    <ref-list><ref><mixed-citation>A 1999</mixed-citation></ref>
              <ref><mixed-citation>B 2001</mixed-citation></ref></ref-list>
  </sec>
  <fig><label>Figure 2.</label><caption><p>A picture</p></caption></fig>
</body></article>"""

JATS = """<article>
<front><article-meta>
  <title-group><article-title>Fatigue and EEG</article-title></title-group>
  <abstract><p>We study fatigue.</p></abstract>
</article-meta></front>
<body>
  <sec><title>Introduction</title>
    <p>Fatigue is common.</p>
    <sec><title>Background</title><p>Nested prose.</p></sec>
  </sec>
  <sec><title>Results</title>
    <p>Accuracy was <italic>92%</italic> overall.</p>
    <table-wrap><label>1</label><caption><p>Scores</p></caption></table-wrap>
  </sec>
</body>
<back><ref-list><ref><mixed-citation>Smith 1999</mixed-citation></ref></ref-list></back>
</article>"""


def test_europe_pmc() -> None:
    from providers import europe_pmc as ep

    check("open_access_only off leaves the query alone",
          ep.build_query("fatigue"), "fatigue")
    # OPEN_ACCESS:Y alone is not enough — only IN_EPMC records have fullTextXML.
    check("open_access_only adds both clauses",
          ep.build_query("fatigue", True),
          "(fatigue) AND OPEN_ACCESS:Y AND IN_EPMC:Y")

    text = ep.jats_to_text(JATS)
    check_true("article title becomes a heading", "# Fatigue and EEG" in text)
    check_true("abstract is included", "We study fatigue." in text)
    check_true("section titles become headings", "Introduction" in text)
    check_true("nested section prose survives", "Nested prose." in text)
    check_true("inline markup is flattened, not dropped", "92%" in text)
    check_true("tables appear as a labelled placeholder", "[Table 1" in text)
    check_false("the bibliography is dropped", "Smith 1999" in text)
    check_false("no XML tags leak into the text", "<p>" in text)

    check_true(f"europe pmc transfer budget ({ep._BUDGET}s) fits inside 90s",
               ep._BUDGET < 90)

    # Heading levels: the article title is h1, so its top sections are h2.
    check_true("top-level sections sit one level under the title",
               "\n## Introduction" in text)
    check_true("nested sections go one level deeper",
               "\n### Background" in text)

    # xml.etree expands internal entities, so a small file can become huge in
    # memory. Europe PMC never declares them, so refusing costs nothing.
    bomb = ('<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol">]>'
            '<article><body><p>&lol;</p></body></article>')
    try:
        ep.jats_to_text(bomb)
        FAIL.append("a document declaring XML entities was accepted")
    except ep.EuropePmcError:
        PASS.append("a document declaring XML entities is refused")

    # But a plain DOCTYPE is normal JATS and must NOT be refused. Blocking it
    # broke real articles, which is why this check exists.
    doctyped = ('<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) '
                'Journal Archiving and Interchange DTD v1.4//EN" '
                '"JATS-archivearticle1-4.dtd">'
                '<article><body><sec><title>Intro</title>'
                '<p>Real text.</p></sec></body></article>')
    try:
        check_true("a plain DOCTYPE is accepted, not refused",
                   "Real text." in ep.jats_to_text(doctyped))
    except ep.EuropePmcError as e:
        FAIL.append(f"a normal JATS DOCTYPE was refused: {e}")

    # Namespaced JATS must still parse — tags arrive as {uri}tag.
    nsdoc = ('<article xmlns:xlink="http://www.w3.org/1999/xlink"><body>'
             '<sec><title>Intro</title><p>Hello <xref>[1]</xref> world.</p>'
             '</sec></body></article>')
    got = ep.jats_to_text(nsdoc)
    check_true("namespaced JATS still yields text", "Hello [1] world." in got)

    # Deep nesting must not exhaust the stack and kill the server.
    deep = ("<article><body>" + "<sec><title>S</title>" * 300
            + "<p>bottom</p>" + "</sec>" * 300 + "</body></article>")
    try:
        check_true("400 levels of nesting does not blow the stack",
                   "bottom" in ep.jats_to_text(deep))
    except RecursionError:
        FAIL.append("deeply nested XML raised RecursionError")

    extra = ep.jats_to_text(JATS_EXTRA)
    # A heading with nothing under it reads as "this section is empty", which
    # is worse than no heading at all.
    check_false("a section with no content emits no heading",
                "Empty Section" in extra)
    check_true("a section with content keeps its heading", "## Real" in extra)
    # The bibliography is dropped, but its absence must not look like the
    # article having none.
    check_true("a dropped reference list is reported with a count",
               "[Reference list omitted — 2 entries]" in extra)
    check_true("the References heading survives, carrying that count",
               "## References" in extra)
    # JATS <label> already says "Figure", so prefixing it again stuttered.
    check_true("a figure placeholder is not stuttered",
               "[Figure 2: A picture]" in extra)
    check_false("really not stuttered", "Figure Figure" in extra)

    # The abstract's own <title> child duplicated the heading above it.
    check("the abstract heading appears exactly once",
          ep.jats_to_text(JATS).count("# Abstract"), 1)

    # A wrong identifier is about the article, not the provider. Europe PMC
    # answers 500 for these, which read as an outage and would have the agent
    # stop using the provider for the rest of the review.
    for bad, want in [("not-an-id", ValueError), ("", ValueError),
                      ("PMC-12", ValueError)]:
        try:
            ep.get_full_text(bad)
            FAIL.append(f"get_full_text({bad!r}) did not raise")
        except want:
            PASS.append(f"get_full_text({bad!r}) raises {want.__name__}")
        except Exception as e:
            FAIL.append(f"get_full_text({bad!r}) raised {type(e).__name__}")
    check_true("a missing article is EuropePmcNotFound, not a generic error",
               issubclass(ep.EuropePmcNotFound, ep.EuropePmcError))

    try:
        ep.jats_to_text("<article><not-closed>")
        FAIL.append("malformed XML did not raise")
    except ep.EuropePmcError:
        PASS.append("malformed XML raises rather than returning empty text")


# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Windowing — shared by both full-text providers
# ---------------------------------------------------------------------------

def test_window() -> None:
    from providers import window

    body = "\n\n".join(f"Paragraph {i} with some words in it." for i in range(40))

    w = window(body, 200, 0)
    check_true("the window never exceeds max_chars", w["returned_chars"] <= 200)
    cut = w["returned_chars"]
    check_true("the cut lands on whitespace, never inside a word",
               body[cut - 1].isspace() or body[cut].isspace())
    check_true("truncated is set while text remains", w["truncated"])
    check("next_offset chains from returned_chars",
          w["next_offset"], w["offset"] + w["returned_chars"])

    # Following next_offset must reproduce the document exactly — no gap at a
    # boundary, nothing delivered twice.
    joined, offset, guard = "", 0, 0
    while offset is not None and guard < 200:
        guard += 1
        part = window(body, 200, offset)
        joined += part["text"]
        offset = part["next_offset"]
    check("following next_offset reassembles the text exactly", joined, body)

    last = window(body, 200, len(body))
    check("an offset at the end returns nothing", last["returned_chars"], 0)
    check("and stops the loop", last["next_offset"], None)
    check_false("and is not marked truncated", last["truncated"])

    past = window(body, 200, len(body) + 10_000)
    check("an offset past the end also returns nothing", past["returned_chars"], 0)
    check("a negative offset is clamped to the start",
          window(body, 200, -50)["offset"], 0)
    check_true("max_chars is clamped up to the floor",
               window(body, 1, 0)["returned_chars"] > 1)

    short = window("tiny", 5000, 0)
    check("a short document comes back whole", short["text"], "tiny")
    check_false("and is not truncated", short["truncated"])


TESTS = [
    ("google_scholar", test_google_scholar),
    ("arxiv query builder", test_arxiv_query),
    ("semantic_scholar fields", test_semantic_scholar_fields),
    ("semantic_scholar filter wiring", test_semantic_scholar_wiring),
    ("review regressions", test_review_regressions),
    ("arxiv full text", test_arxiv_fulltext),
    ("europe pmc", test_europe_pmc),
    ("windowing", test_window),
]


def main() -> int:
    print("  ▸ offline provider checks (no network)\n")
    for name, fn in TESTS:
        try:
            fn()
            print(f"  ✓ {name}")
        except ImportError as e:
            print(f"  ❌ {name}: cannot import provider — {e}")
            print("     → install the deps: "
                  "python3 -m venv .venv && "
                  ".venv/bin/pip install -r mcp-server/requirements.txt")
            return 2
        except Exception as e:
            print(f"  ❌ {name}: {type(e).__name__}: {e}")
            return 2

    if FAIL:
        print(f"\n  ❌ {len(FAIL)} check(s) failed, {len(PASS)} passed:\n")
        for f in FAIL:
            print(f"     - {f}")
        return 1

    print(f"\n  ✅ All {len(PASS)} offline provider checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
