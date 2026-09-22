"""sitecustomize hook for test_cli.py — fakes providers without a network.

Python imports `sitecustomize` automatically at start-up if it is on the path,
which is how the tests reach inside a CLI subprocess without changing a line of
shipped code. `core._lazy` returns anything already in `sys.modules`, so a
provider patched here is the one the tools call.

Driven by OSP_TEST_MODE. With it unset this file does nothing at all, which is
what keeps it impossible to leave switched on: nothing in the shipped tree ever
sets it, and nothing in the shipped tree imports this file.
"""
import os
import sys

_MODE = os.environ.get("OSP_TEST_MODE", "")
_MCP_DIR = os.environ.get("OSP_TEST_MCP_DIR", "")

if _MODE and _MCP_DIR:
    sys.path.insert(0, _MCP_DIR)

    if _MODE.startswith("block:"):
        # Make one dependency unimportable, the way a broken install does.
        _target = _MODE.split(":", 1)[1]

        class _Blocker:
            def find_module(self, name, path=None):
                if name == _target or name.startswith(_target + "."):
                    return self
                return None

            def load_module(self, name):
                raise ImportError(f"No module named {name!r} (test hook)")

        sys.meta_path.insert(0, _Blocker())

    elif _MODE == "slow":
        import time
        import providers.arxiv as _ax

        def _slow(*a, **k):
            time.sleep(30)          # far past any deadline the test sets
            return [{"title": "never returned"}]

        # Both a list-returning and a dict-returning tool, so the shape of an
        # outer timeout can be checked for each.
        _ax.search = _slow
        _ax.read_paper = _slow
        _ax.get_details = _slow

    elif _MODE == "huge":
        import providers.arxiv as _ax

        def _huge(*a, **k):
            # 60 records of ~2 KB each: well past the default cap, and every
            # record complete, so truncation is the only thing being tested.
            return [{
                "arxiv_id": f"9999.{i:05d}",
                "title": f"Paper number {i} about retrieval",
                "summary": "x" * 2000,
                "authors": ["A. Author", "B. Author"],
            } for i in range(60)]

        _ax.search = _huge

    elif _MODE == "canned":
        import providers.arxiv as _ax

        def _canned(*a, **k):
            return [{"arxiv_id": "1706.03762", "title": "Attention Is All You Need"}]

        _ax.search = _canned

    elif _MODE == "empty":
        import providers.arxiv as _ax
        _ax.search = lambda *a, **k: []

    elif _MODE == "blocked_provider":
        import providers.google_scholar as _gs

        def _blocked(*a, **k):
            raise _gs.GoogleScholarBlocked("Google Scholar returned a CAPTCHA")

        _gs.search = _blocked
