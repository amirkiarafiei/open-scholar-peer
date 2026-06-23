#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "arxiv",
#     "semanticscholar",
#     "scholarly",
#     "requests",
#     "beautifulsoup4",
#     "python-dotenv",
#     "python-dateutil",
# ]
# ///
"""
osp_cli.py — Open ScholarPeer unified CLI.
Subcommands map 1:1 to previous MCP tools.
"""

import os
import sys
import json
import argparse
import time
import re
from datetime import datetime
import concurrent.futures
import logging
from typing import Any
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Anchor imports relative to script for project root execution (Fix 1)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environmental configs (Fix 3)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Direct logs to stderr so stdout remains clean JSON (Fix 4)
logging.basicConfig(
    level=logging.WARNING, 
    stream=sys.stderr, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("osp_cli")

from providers import arxiv, semantic_scholar, google_scholar

_TIMEOUT = int(os.environ.get("OSP_CALL_TIMEOUT", "120"))
SEMANTIC_SCHOLAR_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
RL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".rl")

# Exit Codes (Fix 2)
EXIT_OK = 0
EXIT_GENERAL_ERROR = 1
EXIT_RATE_LIMITED = 2
EXIT_AUTH_FAILURE = 3
EXIT_TIMEOUT = 4
EXIT_NO_RESULTS = 5

class OSPCLIError(Exception):
    def __init__(self, error_type: str, message: str, exit_code: int, provider: str = "system", guidance: str = ""):
        self.error_type = error_type
        self.message = message
        self.exit_code = exit_code
        self.provider = provider
        self.guidance = guidance
        super().__init__(message)

    def to_json(self) -> str:
        return json.dumps({
            "error": self.error_type,
            "provider": self.provider,
            "message": self.message,
            "guidance": self.guidance
        }, indent=2)


# --- Persistent Rate-Limiting (Fix 9) ---

def check_rate_limit(provider: str):
    lock_file = os.path.join(RL_DIR, f"{provider}.json")
    if os.path.exists(lock_file):
        try:
            with open(lock_file, "r") as f:
                data = json.load(f)
            blocked_until = data.get("blocked_until", 0)
            if time.time() < blocked_until:
                remaining = int(blocked_until - time.time())
                raise OSPCLIError(
                    error_type="rate_limited",
                    message="Rate limit lock active from previous run.",
                    exit_code=EXIT_RATE_LIMITED,
                    provider=provider,
                    guidance=f"Provider {provider} is locked for another {remaining}s to prevent IP block. Use alternative sources."
                )
        except OSPCLIError:
            raise
        except Exception:
            pass

def set_rate_limit(provider: str, duration: int = 60):
    os.makedirs(RL_DIR, exist_ok=True)
    lock_file = os.path.join(RL_DIR, f"{provider}.json")
    try:
        with open(lock_file, "w") as f:
            json.dump({"blocked_until": time.time() + duration}, f)
    except Exception:
        pass


# --- Utility Functions ---

def clean_title(title: str) -> str:
    if not title:
        return ""
    return re.sub(r'[^a-z0-9]', '', title.lower())

def truncate_text(text: str, limit: int) -> str:
    if not text:
        return ""
    if limit <= 0 or len(text) <= limit:
        return text
    return text[:limit] + "..."

def call_with_timeout(fn, *args, **kwargs) -> Any:
    """Invokes provider calls in a thread pool with a timeout wrapper (Fix 2)"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn, *args, **kwargs)
        try:
            return future.result(timeout=_TIMEOUT)
        except concurrent.futures.TimeoutError:
            raise OSPCLIError(
                error_type="timeout",
                message=f"Timeout limit of {_TIMEOUT}s reached.",
                exit_code=EXIT_TIMEOUT,
                guidance="The provider failed to respond. Retry, or try an alternate provider."
            )


# --- Provider Execution Wrappers ---

def execute_arxiv_search(query: str, limit: int, yr_from: int = None, yr_to: int = None) -> list[dict]:
    check_rate_limit("arxiv")
    try:
        date_from = f"{yr_from}-01-01" if yr_from else None
        date_to = f"{yr_to}-12-31" if yr_to else None
        
        raw_results = call_with_timeout(arxiv.search, query, max_results=limit, date_from=date_from, date_to=date_to)
        
        if raw_results and isinstance(raw_results, list) and len(raw_results) > 0 and "error" in raw_results[0]:
            raise Exception(raw_results[0]["error"])
            
        return [{
            "title": r["title"],
            "authors": r["authors"],
            "abstract": r["summary"],
            "year": int(r["published"][:4]) if r["published"] else None,
            "url": r["link"],
            "provider": "arxiv",
            "id": r["arxiv_id"]
        } for r in raw_results]
    except Exception as e:
        raise OSPCLIError(
            error_type="provider_error",
            message=f"ArXiv failed: {str(e)}",
            exit_code=EXIT_GENERAL_ERROR,
            provider="arxiv",
            guidance="Verify search syntax or check connectivity."
        )

def execute_semantic_scholar_search(query: str, limit: int) -> list[dict]:
    check_rate_limit("semantic_scholar")
    if SEMANTIC_SCHOLAR_KEY and not SEMANTIC_SCHOLAR_KEY.startswith("sk-"):
        raise OSPCLIError(
            error_type="auth_failed",
            message="SEMANTIC_SCHOLAR_API_KEY is formatted incorrectly.",
            exit_code=EXIT_AUTH_FAILURE,
            provider="semantic_scholar",
            guidance="Check API key in .env or unset it to use anonymous limits."
        )
        
    try:
        raw_results = call_with_timeout(semantic_scholar.search_papers, query, limit=limit)
        
        if raw_results and isinstance(raw_results, list) and len(raw_results) > 0 and "error" in raw_results[0]:
            err_msg = raw_results[0]["error"]
            if "429" in err_msg:
                set_rate_limit("semantic_scholar", 60)
                raise OSPCLIError(
                    error_type="rate_limited",
                    message="Semantic Scholar rate limit reached.",
                    exit_code=EXIT_RATE_LIMITED,
                    provider="semantic_scholar",
                    guidance="Wait 60s. Alternatively, run searches against arXiv."
                )
            elif "401" in err_msg or "403" in err_msg:
                raise OSPCLIError(
                    error_type="auth_failed",
                    message="API key rejected by Semantic Scholar.",
                    exit_code=EXIT_AUTH_FAILURE,
                    provider="semantic_scholar",
                    guidance="Verify keys at semanticscholar.org or unset key in .env."
                )
            raise Exception(err_msg)
            
        return [{
            "title": r["title"],
            "authors": [a["name"] for a in r.get("authors", [])],
            "abstract": r.get("abstract", ""),
            "year": r.get("year"),
            "url": r.get("url"),
            "provider": "semantic_scholar",
            "id": r["paperId"],
            "citations": r.get("citationCount", 0)
        } for r in raw_results]
    except OSPCLIError:
        raise
    except Exception as e:
        raise OSPCLIError(
            error_type="provider_error",
            message=f"Semantic Scholar failed: {str(e)}",
            exit_code=EXIT_GENERAL_ERROR,
            provider="semantic_scholar",
            guidance="Upstream API issue. Retry later or query alternative sources."
        )

def execute_google_scholar_search(query: str, limit: int, yr_from: int = None, yr_to: int = None) -> list[dict]:
    check_rate_limit("google_scholar")
    # Intentional sequential sleep to prevent IP Blocks (Fix 6)
    time.sleep(2)
    try:
        yr_range = (yr_from, yr_to) if (yr_from or yr_to) else None
        raw_results = call_with_timeout(
            google_scholar.search_advanced, 
            query, 
            year_range=yr_range, 
            num_results=limit
        )
        
        if raw_results and isinstance(raw_results, list) and len(raw_results) > 0 and "error" in raw_results[0]:
            raise Exception(raw_results[0]["error"])
            
        return [{
            "title": r["title"],
            "authors": r["authors"],
            "abstract": r["abstract"],
            "year": None,
            "url": r["url"],
            "provider": "google_scholar",
            "id": None
        } for r in raw_results]
    except Exception as e:
        set_rate_limit("google_scholar", 120)  # lock Google Scholar for longer if it fails
        raise OSPCLIError(
            error_type="provider_error",
            message=f"Google Scholar failed: {str(e)}",
            exit_code=EXIT_GENERAL_ERROR,
            provider="google_scholar",
            guidance="Google Scholar blocked the IP. Check if a VPN is needed or fallback to arXiv."
        )


# --- Capabilities Manifest Output ---

def output_capabilities():
    manifest = {
        "version": "2.0",
        "commands": [
            {
                "name": "search-arxiv",
                "description": "Query arXiv preprints. Best for CS/ML and recent temporal expansion.",
                "required_args": ["query"],
                "optional_args": {"--limit": "int (default 10)", "--year-from": "YYYY", "--year-to": "YYYY"},
                "rate_limits": "No key required. Fair use rules apply."
            },
            {
                "name": "search-semantic-scholar",
                "description": "Query Semantic Scholar. Yields citation counts and reference graphs.",
                "required_args": ["query"],
                "optional_args": {"--limit": "int (default 10)"},
                "rate_limits": "100 req/5min anonymous. Highly recommended to set SEMANTIC_SCHOLAR_API_KEY."
            },
            {
                "name": "search-google-scholar",
                "description": "Query Google Scholar. Broader web research coverage (theses, reports).",
                "required_args": ["query"],
                "optional_args": {"--limit": "int (default 5)", "--year-from": "YYYY", "--year-to": "YYYY"},
                "rate_limits": "Strict IP-based scraping rate limits. Sequential requests only."
            },
            {
                "name": "search-all",
                "description": "Queries all three database engines sequentially, deduplicates papers, truncates abstracts.",
                "required_args": ["query"],
                "optional_args": {"--limit": "int (default 5)", "--year-from": "YYYY", "--year-to": "YYYY"},
                "rate_limits": "Bounded by individual provider constraints."
            },
            {
                "name": "get-arxiv-details",
                "description": "Retrieve detailed metadata for a single arXiv paper ID.",
                "required_args": ["arxiv_id"],
                "optional_args": {}
            },
            {
                "name": "get-semantic-scholar-paper",
                "description": "Retrieve detailed metadata for a single Semantic Scholar paper ID or DOI.",
                "required_args": ["paper_id"],
                "optional_args": {}
            }
        ]
    }
    print(json.dumps(manifest, indent=2))
    sys.exit(EXIT_OK)


# --- Execution Router ---

def main():
    parser = argparse.ArgumentParser(description="Open ScholarPeer Search CLI")
    parser.add_argument("--capabilities", action="store_true", help="Output JSON capabilities manifest")
    
    subparsers = parser.add_subparsers(dest="subcommand")

    # Command: search-all
    all_p = subparsers.add_parser("search-all")
    all_p.add_argument("query")
    all_p.add_argument("--limit", type=int, default=5)
    all_p.add_argument("--year-from", type=int)
    all_p.add_argument("--year-to", type=int)
    all_p.add_argument("--abstract-length", type=int, default=300)

    # Command: search-arxiv
    arxiv_p = subparsers.add_parser("search-arxiv")
    arxiv_p.add_argument("query")
    arxiv_p.add_argument("--limit", type=int, default=10)
    arxiv_p.add_argument("--year-from", type=int)
    arxiv_p.add_argument("--year-to", type=int)
    arxiv_p.add_argument("--abstract-length", type=int, default=300)

    # Command: get-arxiv-details
    arxiv_d = subparsers.add_parser("get-arxiv-details")
    arxiv_d.add_argument("arxiv_id")

    # Command: search-semantic-scholar
    ss_p = subparsers.add_parser("search-semantic-scholar")
    ss_p.add_argument("query")
    ss_p.add_argument("--limit", type=int, default=10)
    ss_p.add_argument("--abstract-length", type=int, default=300)

    # Command: get-semantic-scholar-paper
    ss_d = subparsers.add_parser("get-semantic-scholar-paper")
    ss_d.add_argument("paper_id")

    # Command: get-semantic-scholar-references
    ss_ref = subparsers.add_parser("get-semantic-scholar-references")
    ss_ref.add_argument("paper_id")
    ss_ref.add_argument("--limit", type=int, default=50)

    # Command: get-semantic-scholar-citations
    ss_cit = subparsers.add_parser("get-semantic-scholar-citations")
    ss_cit.add_argument("paper_id")
    ss_cit.add_argument("--limit", type=int, default=50)

    # Command: get-semantic-scholar-papers-batch
    ss_bat = subparsers.add_parser("get-semantic-scholar-papers-batch")
    ss_bat.add_argument("paper_ids", nargs="+")

    # Command: get-semantic-scholar-author
    ss_aut = subparsers.add_parser("get-semantic-scholar-author")
    ss_aut.add_argument("author_id")

    # Command: search-semantic-scholar-authors
    ss_auts = subparsers.add_parser("search-semantic-scholar-authors")
    ss_auts.add_argument("query")
    ss_auts.add_argument("--limit", type=int, default=10)

    # Command: get-semantic-scholar-author-papers
    ss_autp = subparsers.add_parser("get-semantic-scholar-author-papers")
    ss_autp.add_argument("author_id")
    ss_autp.add_argument("--limit", type=int, default=50)

    # Command: get-semantic-scholar-paper-recommendations
    ss_rec = subparsers.add_parser("get-semantic-scholar-paper-recommendations")
    ss_rec.add_argument("paper_id")
    ss_rec.add_argument("--limit", type=int, default=10)

    # Command: search-semantic-scholar-snippets
    ss_snp = subparsers.add_parser("search-semantic-scholar-snippets")
    ss_snp.add_argument("query")
    ss_snp.add_argument("--limit", type=int, default=10)

    # Command: search-google-scholar
    gs_p = subparsers.add_parser("search-google-scholar")
    gs_p.add_argument("query")
    gs_p.add_argument("--limit", type=int, default=5)
    gs_p.add_argument("--abstract-length", type=int, default=300)

    # Command: search-google-scholar-advanced
    gs_adv = subparsers.add_parser("search-google-scholar-advanced")
    gs_adv.add_argument("query")
    gs_adv.add_argument("--author")
    gs_adv.add_argument("--year-from", type=int)
    gs_adv.add_argument("--year-to", type=int)
    gs_adv.add_argument("--limit", type=int, default=5)
    gs_adv.add_argument("--abstract-length", type=int, default=300)

    # Command: get-google-scholar-author-info
    gs_auti = subparsers.add_parser("get-google-scholar-author-info")
    gs_auti.add_argument("author_name")

    args = parser.parse_args()

    if args.capabilities:
        output_capabilities()

    if not args.subcommand:
        parser.print_help()
        sys.exit(EXIT_GENERAL_ERROR)

    results = []
    warnings = []
    failed_providers = []

    # Identify search vs. details commands for error envelopes (Fix 5)
    search_commands = ["search-all", "search-arxiv", "search-semantic-scholar", "search-google-scholar", 
                       "search-google-scholar-advanced", "search-semantic-scholar-authors", "search-semantic-scholar-snippets"]

    try:
        # Command: search-all
        if args.subcommand == "search-all":
            # ArXiv search
            try:
                results.extend(execute_arxiv_search(args.query, args.limit, args.year_from, args.year_to))
            except OSPCLIError as e:
                warnings.append({"provider": "arxiv", "error": e.error_type, "message": e.message, "guidance": e.guidance})
                failed_providers.append("arxiv")

            # Semantic Scholar search
            try:
                results.extend(execute_semantic_scholar_search(args.query, args.limit))
            except OSPCLIError as e:
                warnings.append({"provider": "semantic_scholar", "error": e.error_type, "message": e.message, "guidance": e.guidance})
                failed_providers.append("semantic_scholar")

            # Google Scholar search
            try:
                results.extend(execute_google_scholar_search(args.query, args.limit, args.year_from, args.year_to))
            except OSPCLIError as e:
                warnings.append({"provider": "google_scholar", "error": e.error_type, "message": e.message, "guidance": e.guidance})
                failed_providers.append("google_scholar")

            # Deduplication by title
            seen_keys = set()
            deduped_results = []
            for paper in results:
                title_key = clean_title(paper.get("title", ""))
                if title_key not in seen_keys:
                    seen_keys.add(title_key)
                    paper["query_used"] = args.query
                    paper["retrieved_at"] = datetime.utcnow().isoformat() + "Z"
                    paper["abstract"] = truncate_text(paper.get("abstract", ""), args.abstract_length)
                    deduped_results.append(paper)
            
            output = {
                "results": deduped_results,
                "result_count": len(deduped_results),
                "warnings": warnings,
                "failed_providers": failed_providers
            }
            print(json.dumps(output, indent=2))
            sys.exit(EXIT_OK if deduped_results else EXIT_NO_RESULTS)

        # Single provider commands
        else:
            # 1. arXiv
            if args.subcommand == "search-arxiv":
                res = execute_arxiv_search(args.query, args.limit, args.year_from, args.year_to)
                for paper in res:
                    paper["query_used"] = args.query
                    paper["retrieved_at"] = datetime.utcnow().isoformat() + "Z"
                    paper["abstract"] = truncate_text(paper.get("abstract", ""), args.abstract_length)
                
            elif args.subcommand == "get-arxiv-details":
                res = call_with_timeout(arxiv.get_details, args.arxiv_id)
                # details does not truncate abstracts

            # 2. Semantic Scholar
            elif args.subcommand == "search-semantic-scholar":
                res = execute_semantic_scholar_search(args.query, args.limit)
                for paper in res:
                    paper["query_used"] = args.query
                    paper["retrieved_at"] = datetime.utcnow().isoformat() + "Z"
                    paper["abstract"] = truncate_text(paper.get("abstract", ""), args.abstract_length)

            elif args.subcommand == "get-semantic-scholar-paper":
                res = call_with_timeout(semantic_scholar.get_paper, args.paper_id)

            elif args.subcommand == "get-semantic-scholar-references":
                res = call_with_timeout(semantic_scholar.get_paper_references, args.paper_id, limit=args.limit)

            elif args.subcommand == "get-semantic-scholar-citations":
                res = call_with_timeout(semantic_scholar.get_paper_citations, args.paper_id, limit=args.limit)

            elif args.subcommand == "get-semantic-scholar-papers-batch":
                res = call_with_timeout(semantic_scholar.get_papers_batch, args.paper_ids)

            elif args.subcommand == "get-semantic-scholar-author":
                res = call_with_timeout(semantic_scholar.get_author, args.author_id)

            elif args.subcommand == "search-semantic-scholar-authors":
                res = call_with_timeout(semantic_scholar.search_authors, args.query, limit=args.limit)

            elif args.subcommand == "get-semantic-scholar-author-papers":
                res = call_with_timeout(semantic_scholar.get_author_papers, args.author_id, limit=args.limit)

            elif args.subcommand == "get-semantic-scholar-paper-recommendations":
                res = call_with_timeout(semantic_scholar.get_paper_recommendations, args.paper_id, limit=args.limit)

            elif args.subcommand == "search-semantic-scholar-snippets":
                res = call_with_timeout(semantic_scholar.search_snippets, args.query, limit=args.limit)

            # 3. Google Scholar
            elif args.subcommand == "search-google-scholar":
                res = execute_google_scholar_search(args.query, args.limit)
                for paper in res:
                    paper["query_used"] = args.query
                    paper["retrieved_at"] = datetime.utcnow().isoformat() + "Z"
                    paper["abstract"] = truncate_text(paper.get("abstract", ""), args.abstract_length)

            elif args.subcommand == "search-google-scholar-advanced":
                # Translate flags
                yr_range = (args.year_from, args.year_to) if (args.year_from or args.year_to) else None
                check_rate_limit("google_scholar")
                time.sleep(2)
                raw_res = call_with_timeout(
                    google_scholar.search_advanced, 
                    args.query, 
                    author=args.author, 
                    year_range=yr_range, 
                    num_results=args.limit
                )
                if raw_res and isinstance(raw_res, list) and len(raw_res) > 0 and "error" in raw_res[0]:
                    raise Exception(raw_res[0]["error"])
                res = [{
                    "title": r["title"],
                    "authors": r["authors"],
                    "abstract": truncate_text(r["abstract"], args.abstract_length),
                    "year": None,
                    "url": r["url"],
                    "provider": "google_scholar",
                    "id": None,
                    "query_used": args.query,
                    "retrieved_at": datetime.utcnow().isoformat() + "Z"
                } for r in raw_res]

            elif args.subcommand == "get-google-scholar-author-info":
                res = call_with_timeout(google_scholar.get_author_info, args.author_name)

            else:
                raise Exception(f"Unknown subcommand {args.subcommand}")

            # Return exit code on empty result lists (Fix 5)
            if isinstance(res, list) and len(res) == 0:
                empty_guidance = {
                    "results": [],
                    "result_count": 0,
                    "query_used": getattr(args, "query", ""),
                    "guidance": "No results matched. Broaden search criteria."
                }
                print(json.dumps(empty_guidance, indent=2))
                sys.exit(EXIT_NO_RESULTS)

            print(json.dumps(res, indent=2))
            sys.exit(EXIT_OK)

    except OSPCLIError as e:
        payload = e.to_json()
        print(payload, file=sys.stderr)
        print(payload)
        sys.exit(e.exit_code)
    except Exception as e:
        err = OSPCLIError(
            error_type="system_error", 
            message=str(e), 
            exit_code=EXIT_GENERAL_ERROR, 
            guidance="An unexpected system failure occurred."
        )
        payload = err.to_json()
        print(payload, file=sys.stderr)
        print(payload)
        sys.exit(EXIT_GENERAL_ERROR)

if __name__ == "__main__":
    main()
