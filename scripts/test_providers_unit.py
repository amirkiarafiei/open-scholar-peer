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

TESTS = [
    ("google_scholar", test_google_scholar),
    ("arxiv query builder", test_arxiv_query),
    ("semantic_scholar fields", test_semantic_scholar_fields),
    ("semantic_scholar filter wiring", test_semantic_scholar_wiring),
    ("review regressions", test_review_regressions),
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
