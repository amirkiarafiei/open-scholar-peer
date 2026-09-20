#!/usr/bin/env python3
"""
test_providers.py — call every MCP provider against the real API.

Opt-in, because it needs the network and the provider dependencies. It is the
only thing in the repo that proves a provider still works: the adapter tests
(`test_parity.py`, `sync_adapters.py --check`) and the installer smoke test
never load `mcp-server/providers/` at all.

Run the offline checks first — they are faster and catch more:

    .venv/bin/python scripts/test_providers_unit.py

Then, with a virtualenv that has the server's dependencies:

    python3 -m venv .venv
    .venv/bin/pip install -r mcp-server/requirements.txt
    .venv/bin/python scripts/test_providers.py

Options:
    --only arxiv,semantic_scholar     run just these providers
    --list                            show provider names and exit

What "pass" means here is weaker than in a unit test, because the answer comes
from someone else's server and changes daily. Each check states what it
measured so a human can judge it. Two rules are absolute, and they do fail the
run:
  * a provider must never return an empty list to report a failure;
  * a blocked scrape must raise, not come back as "no results".

Google Scholar being blocked is NOT a failure of this script. From most
addresses it will be. The script checks that the block is *reported* properly,
which is the thing that was broken.

Exit codes:
  0  — everything that could be checked passed.
  1  — a real failure.
  2  — script error (usually missing dependencies).
"""
from __future__ import annotations

import argparse
import signal
import sys
import time
import traceback
from contextlib import contextmanager
from pathlib import Path

# A provider that has stopped answering must not hold the whole run. Semantic
# Scholar under anonymous limits can sit for ten minutes before giving up.
PROVIDER_BUDGET_S = 180


@contextmanager
def time_budget(seconds: int):
    """Interrupt the block if it runs past `seconds`. No-op where unsupported."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def _expire(signum, frame):
        raise TimeoutError(
            f"provider checks ran past the {seconds}s budget")

    previous = signal.signal(signal.SIGALRM, _expire)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "mcp-server"))

FAILURES: list[str] = []
NOTES: list[str] = []
UNVERIFIED: list[str] = []


def _rate_limited() -> tuple:
    """Provider exception types that mean "throttled", not "broken"."""
    types: list[type] = []
    try:
        from providers.semantic_scholar import SemanticScholarRateLimited
        types.append(SemanticScholarRateLimited)
    except Exception:
        pass
    try:
        from providers.google_scholar import GoogleScholarUnavailable
        types.append(GoogleScholarUnavailable)
    except Exception:
        pass
    try:
        from providers.arxiv import ArxivBusy
        types.append(ArxivBusy)
    except Exception:
        pass
    return tuple(types) or (RuntimeError,)


def unreachable(exc: BaseException) -> str | None:
    """Name the network fault, if this exception is one.

    An API that will not talk to us is not a defect in our code, and must not
    be reported as one. Semantic Scholar in particular starts refusing
    connections outright after enough anonymous traffic.
    """
    seen, node = set(), exc
    while node is not None and id(node) not in seen:
        seen.add(id(node))
        name = type(node).__name__
        if name in ("ConnectionRefusedError", "ConnectionError", "ConnectTimeout",
                    "ConnectError", "ReadTimeout", "Timeout", "TimeoutError",
                    "gaierror", "SSLError", "RemoteDisconnected",
                    "ProtocolError", "ChunkedEncodingError"):
            return name
        node = node.__cause__ or node.__context__
    return None


def fail(msg: str) -> None:
    FAILURES.append(msg)
    print(f"      ✗ {msg}")


def ok(msg: str) -> None:
    print(f"      ✓ {msg}")


def note(msg: str) -> None:
    NOTES.append(msg)
    print(f"      · {msg}")


def cannot_verify(msg: str) -> None:
    UNVERIFIED.append(msg)
    print(f"      ⚠ could not verify — {msg}")


def is_error_envelope(result) -> bool:
    """True when the provider reported a failure the agreed way."""
    if isinstance(result, dict):
        return "error" in result
    if isinstance(result, list) and len(result) == 1 and isinstance(result[0], dict):
        return "error" in result[0]
    return False


# ---------------------------------------------------------------------------

def check_arxiv() -> None:
    from providers import arxiv as ax

    # B1 — a narrow window used to return one paper, because the filtering
    # happened in Python after a relevance fetch.
    rows = ax.search("large language model", max_results=5, date_from="2026-01-01")
    inside = [r for r in rows if (r.get("published") or "") >= "2026-01-01"]
    if len(rows) == 5 and len(inside) == 5:
        ok(f"date window: {len(rows)} results, {len(inside)} inside it (was 1 before the fix)")
    else:
        fail(f"date window returned {len(rows)} results, {len(inside)} inside it; expected 5 and 5")

    time.sleep(3)

    # B2 — `cat:` matches any category on the paper, primary or cross-listed,
    # so measure membership, not the primary field.
    rows = ax.search("transformer", max_results=25, categories=["cs.CL"])
    member = [r for r in rows if "cs.CL" in (r.get("categories") or [])]
    primary = [r for r in rows if r.get("primary_category") == "cs.CL"]
    pct = 100 * len(member) // max(len(rows), 1)
    if pct >= 95:
        ok(f"category filter: {len(member)}/{len(rows)} are in cs.CL ({pct}%), "
           f"{len(primary)} of them primary")
    else:
        fail(f"category filter: only {len(member)}/{len(rows)} in cs.CL")

    time.sleep(3)

    # B3 — a shared, locked client keeps arXiv's 3-second spacing.
    # Time the gaps between call COMPLETIONS, not between call starts. The
    # client sleeps out the delay inside the next call, so a start-to-start
    # gap just measures how long the previous call took and reads as ~0.
    ends = []
    for _ in range(3):
        ax.search("attention", max_results=1)
        ends.append(time.time())
    gaps = [ends[i + 1] - ends[i] for i in range(len(ends) - 1)]
    if gaps and min(gaps) >= 2.9:
        ok(f"request spacing: gaps of {', '.join(f'{g:.1f}s' for g in gaps)} "
           f"(arXiv asks for 3s)")
    else:
        fail(f"request spacing too short: {[round(g, 1) for g in gaps]} "
             f"— the client is not being shared")

    time.sleep(3)

    d = ax.get_details("1207.7214")   # a paper that really was published
    if d.get("doi") and d.get("journal_ref"):
        ok(f"doi and journal_ref present: {d['doi']}")
    else:
        fail(f"doi/journal_ref missing on a published paper: {d.get('doi')!r}")

    time.sleep(3)

    # Both id shapes the docstring promises. Measured 2026-09-20: a version
    # that was never published returns an empty feed, so pick one that exists.
    d = ax.get_details("1706.03762v5")
    if d.get("arxiv_id") == "1706.03762v5":
        ok("versioned id resolves to that exact version")
    else:
        fail(f"versioned id failed: {d.get('arxiv_id') or d}")

    time.sleep(3)

    d = ax.get_details("hep-th/9901001")
    if (d.get("arxiv_id") or "").startswith("hep-th/9901001"):
        ok("old-style id resolves")
    else:
        fail(f"old-style id failed: {d.get('arxiv_id') or d}")


def check_semantic_scholar() -> None:
    from providers import semantic_scholar as ss

    rows = ss.search_papers("retrieval augmented generation", limit=5)
    if is_error_envelope(rows):
        fail(f"search returned an error: {rows[0]['error']}")
        return
    if len(rows) == 5:
        ok(f"search returned {len(rows)} papers")
    else:
        fail(f"search returned {len(rows)} papers, expected 5")

    # B6 — the fields the old serializer threw away.
    have_tldr = sum(1 for r in rows if r.get("tldr"))
    have_pdf = sum(1 for r in rows if r.get("openAccessPdf"))
    note(f"tldr on {have_tldr}/{len(rows)}, openAccessPdf on {have_pdf}/{len(rows)}")
    # `key in r` is always true — the serializer is a dict literal — so it
    # would pass even if every value were None. Check for a real value.
    for key in ("publicationDate", "fieldsOfStudy", "isOpenAccess"):
        filled = sum(1 for r in rows if r.get(key) is not None)
        if filled:
            ok(f"{key} carries a real value on {filled}/{len(rows)}")
        else:
            fail(f"{key} is None on every record — the field is not arriving")

    # publicationDate must be a plain string; a datetime will not serialize.
    bad = [r["publicationDate"] for r in rows
           if r.get("publicationDate") is not None
           and not isinstance(r["publicationDate"], str)]
    if bad:
        fail(f"publicationDate is not a string: {bad[:2]}")
    else:
        ok("publicationDate is a plain date string")

    # B7 — a filter that is easy to verify.
    rows = ss.search_papers("neural machine translation", limit=5, year="2019")
    years = {r.get("year") for r in rows}
    if rows and years <= {2019}:
        ok(f"year filter works: every result is {years}")
    else:
        fail(f"year filter leaked other years: {years}")

    # B5 — the 10 MB failure: a very heavily cited paper.
    paper = ss.get_paper("10.1038/nature14539")   # LeCun/Bengio/Hinton, Deep Learning
    if is_error_envelope(paper):
        fail(f"get_paper on a heavily-cited paper errored: {paper['error']}")
    else:
        ok(f"get_paper on a {paper.get('citationCount')}-citation paper returned fine")

    # B7 — title matching, the right way to resolve a reference.
    m = ss.match_paper_title("Attention is all you need")
    if m.get("paperId") and m.get("matchScore") is not None:
        ok(f"title match resolved to {m['title'][:40]!r} (score {m['matchScore']:.0f})")
    else:
        fail(f"title match returned no paperId/matchScore: {m}")

    # B8 — snippets used to return null ids and null author names.
    snips = ss.search_snippets("chain of thought prompting", limit=3)
    if is_error_envelope(snips):
        note(f"snippet search unavailable: {snips[0]['error'][:70]}")
    elif not snips:
        note("snippet search returned nothing")
    else:
        s = snips[0]
        if s.get("text"):
            ok(f"snippet text present ({len(s['text'])} chars)")
        else:
            fail("snippet text is empty")
        authors = (s.get("paper") or {}).get("authors") or []
        if authors and all(isinstance(a, str) and a for a in authors):
            ok(f"snippet authors are real names: {authors[:2]}")
        elif not authors:
            note("snippet record carried no authors")
        else:
            fail(f"snippet authors are not plain names: {authors[:2]}")
        if "snippetId" in s:
            fail("snippet record still carries the non-existent snippetId")


def check_google_scholar() -> None:
    from providers import google_scholar as gs

    try:
        rows = gs.search("mental fatigue detection", num_results=3)
    except gs.GoogleScholarBlocked as e:
        # The expected outcome from most addresses, and the behaviour B9 was
        # about. Reporting the block IS the pass.
        ok("blocked, and reported as an error rather than an empty list")
        note(f"block message: {str(e)[:90]}...")
        return
    except gs.GoogleScholarUnavailable as e:
        # A timeout or dropped connection. Still the right shape of answer:
        # an error, never [].
        ok("unreachable, and reported as an error rather than an empty list")
        cannot_verify(f"google_scholar could not be reached, so parsing a real "
                      f"results page was not exercised ({str(e)[:60]}...)")
        return
    except Exception as e:
        fail(f"failed with {type(e).__name__}, which is not one of the "
             f"provider's own exception types: {e}")
        return

    if rows and rows[0].get("title"):
        ok(f"returned {len(rows)} results, first: {rows[0]['title'][:45]!r}")
    elif rows == []:
        note("returned an empty list — not blocked, so this really is zero hits")
    else:
        fail(f"returned something unexpected: {rows[:1]}")


PROVIDERS = {
    "arxiv": check_arxiv,
    "semantic_scholar": check_semantic_scholar,
    "google_scholar": check_google_scholar,
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help="comma-separated provider names")
    ap.add_argument("--list", action="store_true", help="list providers and exit")
    ap.add_argument("--budget", type=int, default=PROVIDER_BUDGET_S,
                    help=f"seconds allowed per provider (default {PROVIDER_BUDGET_S})")
    args = ap.parse_args()
    budget = max(10, args.budget)

    if args.list:
        for name in PROVIDERS:
            print(name)
        return 0

    chosen = list(PROVIDERS)
    if args.only:
        chosen = [n.strip() for n in args.only.split(",") if n.strip()]
        unknown = [n for n in chosen if n not in PROVIDERS]
        if unknown:
            print(f"  ❌ unknown provider(s): {', '.join(unknown)}")
            print(f"     known: {', '.join(PROVIDERS)}")
            return 2

    print("  ▸ live provider checks — these call the real APIs\n")
    for name in chosen:
        print(f"  ── {name} " + "─" * (56 - len(name)))
        try:
            with time_budget(budget):
                PROVIDERS[name]()
        except _rate_limited() as e:
            cannot_verify(f"{name} rate-limited us ({str(e)[:60]}...). The "
                          f"error path worked; the data path is unproved.")
        except ImportError as e:
            print(f"      ❌ cannot import provider — {e}")
            print("         → .venv/bin/pip install -r mcp-server/requirements.txt")
            return 2
        except Exception as e:
            fault = unreachable(e)
            if fault:
                cannot_verify(
                    f"{name} is unreachable from here ({fault}). Nothing is "
                    f"proved either way; re-run when the API answers again.")
            else:
                fail(f"{name} raised:\n{traceback.format_exc()}")
        print()

    if FAILURES:
        print(f"  ❌ {len(FAILURES)} check(s) failed:")
        for f in FAILURES:
            print(f"     - {f}")
        return 1

    if UNVERIFIED:
        print(f"  ⚠  {len(UNVERIFIED)} provider(s) could not be reached, so "
              f"they are neither proved nor disproved:")
        for u in UNVERIFIED:
            print(f"     - {u}")
        print()
    print(f"  ✅ every check that could run passed "
          f"({len(NOTES)} note(s) above)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
