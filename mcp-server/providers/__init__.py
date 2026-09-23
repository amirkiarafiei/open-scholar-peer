"""Provider modules for osp_mcp. Each module exposes plain (non-MCP) functions
that the FastMCP tool wrappers in osp_mcp.py call into.

Adding a new provider:
  1. Create `providers/<name>.py` with the search/get-detail functions.
  2. Import it in `osp_mcp.py` and decorate wrapper functions with `@mcp.tool()`.
"""


def window(text: str, max_chars: int, offset: int) -> dict:
    """Cut a readable window out of a long document.

    The end is snapped BACKWARDS to the last paragraph break inside the final
    tenth of the window, then to a line break, then to a space. A blind cut
    lands anywhere: on 1706.03762 it split `$1.2\\cdot10^{21}$` across two
    windows, and the dangerous version of that is a cut between "26.3" and
    "0", which leaves a reader a plausible, wrong number.

    `returned_chars` is the snapped length, so a caller adding
    `offset + returned_chars` still chains exactly. `next_offset` is given
    outright so nobody has to do the arithmetic; it is None at the end.
    """
    total = len(text)
    offset = max(0, int(offset))
    max_chars = max(100, min(int(max_chars), 200000))

    chunk = text[offset:offset + max_chars]
    reached_end = offset + len(chunk) >= total

    # >= 50, not > max_chars: the guard used to be `len(chunk) > 200`, which
    # is false when max_chars IS 200, so the snap never ran for small windows
    # and the cut landed mid-word.
    if not reached_end and len(chunk) >= 50:
        floor = int(len(chunk) * 0.9)
        for sep in ("\n\n", "\n", " "):
            cut = chunk.rfind(sep, floor)
            if cut > 0:
                chunk = chunk[:cut]
                break

    end = offset + len(chunk)
    return {
        "text": chunk,
        "offset": offset,
        "returned_chars": len(chunk),
        "total_chars": total,
        "truncated": end < total,
        "next_offset": end if end < total else None,
    }
