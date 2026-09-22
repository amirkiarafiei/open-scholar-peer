"""
osp_mcp.py — Open ScholarPeer search tools, served over MCP.

The tools themselves live in `core.py`, which knows nothing about MCP. This
file is the transport adapter: it imports the FastMCP server, registers the
tools this project has switched on, and runs. `osp_cli.py` is the other
adapter, over argv, and it imports `core` too — never this file.

That split is the point. Before it, the command-line fallback imported this
module for its tool registry, so a broken `mcp` package took down the fallback
as well as the thing it was a fallback for.

To add a tool, edit `core.py`. Nothing here names a tool, so nothing here
changes.

Environment variables:
  SEMANTIC_SCHOLAR_API_KEY — optional; provides higher rate limits if set.
  OSP_CALL_TIMEOUT         — per-call timeout in seconds (default: 90).
  OSP_SOURCES              — which databases this project switched on.
"""
from __future__ import annotations

import logging
import os

from mcp.server.fastmcp import FastMCP

import core

# This front end owns the ROOT logger, not just ours: the MCP host reads
# stderr as a log, and the two lines the `arxiv` package emits per call belong
# there alongside our own. core.py deliberately does not call basicConfig.
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

log = core.log

mcp = FastMCP("osp_mcp")

# Gating happens here, at registration time, from a fresh read of OSP_SOURCES.
# A tool this project switched off is simply never registered, so the agent
# never sees it — and core.REGISTRY still knows it exists, which is how the CLI
# tells "switched off" apart from "no such tool".
_ENABLED = core.enabled_sources()
for _tool in core.enabled_tools().values():
    mcp.tool()(_tool.fn)


if __name__ == "__main__":
    if os.environ.get("SEMANTIC_SCHOLAR_API_KEY"):
        log.info("Semantic Scholar API key detected — higher rate limits enabled.")
    else:
        log.info("No SEMANTIC_SCHOLAR_API_KEY in env — Semantic Scholar will use anonymous limits.")
    if os.environ.get("OSP_SOURCES", "").strip():
        log.info("Databases enabled by OSP_SOURCES: %s",
                 ", ".join(sorted(_ENABLED)))
    else:
        log.info("OSP_SOURCES not set — all %s databases enabled.",
                 len(core._ALL_SOURCES))
    log.info("Starting Open ScholarPeer MCP server (osp_mcp), timeout=%ss",
             core.CALL_TIMEOUT.get())
    # One long-lived process, so the lazy provider imports are paid once here
    # rather than on the first call of each — and no two concurrent calls can
    # race to be the first to touch the same module.
    core.warm_providers()
    mcp.run(transport="stdio")
