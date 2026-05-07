"""Provider modules for osp_mcp. Each module exposes plain (non-MCP) functions
that the FastMCP tool wrappers in osp_mcp.py call into.

Adding a new provider:
  1. Create `providers/<name>.py` with the search/get-detail functions.
  2. Import it in `osp_mcp.py` and decorate wrapper functions with `@mcp.tool()`.
"""
