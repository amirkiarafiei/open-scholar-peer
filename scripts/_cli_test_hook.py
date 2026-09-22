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

        import importlib.abc
        import importlib.machinery

        class _BlockedLoader(importlib.abc.Loader):
            def create_module(self, spec):
                raise ImportError(f"No module named {spec.name!r} (test hook)")

            def exec_module(self, module):  # pragma: no cover - never reached
                raise ImportError("blocked by the test hook")

        class _Blocker(importlib.abc.MetaPathFinder):
            """Make one module unimportable, the way a broken install does.

            find_spec, NOT find_module. The old two-method protocol
            (find_module/load_module) was deprecated in 3.4 and REMOVED from
            importlib in 3.12: a finder without find_spec is skipped in
            silence, so the blocker would stop blocking and the tests that
            think they are offline would quietly call the real arXiv instead —
            a red build that looks like a code regression, and a breach of this
            suite's promise to touch no network.
            """

            def find_spec(self, name, path=None, target=None):
                if name == _target or name.startswith(_target + "."):
                    return importlib.machinery.ModuleSpec(name, _BlockedLoader())
                return None

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

    elif _MODE == "huge_error":
        # A provider failure whose MESSAGE alone is past the output cap. The
        # envelope must survive the cut; dropping it turned a block into a
        # size problem with exit 0.
        import providers.google_scholar as _gs

        def _huge_block(*a, **k):
            raise _gs.GoogleScholarBlocked("CAPTCHA. " + "detail " * 5000)

        _gs.search = _huge_block

    elif _MODE == "huge_text":
        # A full-text window larger than the cap, carrying the real paging
        # contract. Cutting `text` without correcting returned_chars,
        # truncated and next_offset made half a paper claim to be whole.
        import providers.arxiv as _ax

        _BODY = ("Paragraph %d. " % 0) + "\n\n".join(
            f"Paragraph {i}. " + "word " * 120 for i in range(200))

        def _huge_read(arxiv_id, max_chars=50000, offset=0, **k):
            from providers import window
            out = window(_BODY, max_chars, offset)
            out.update({"arxiv_id": arxiv_id, "source": "latex", "format": "text",
                        "bibliography": []})
            return out

        _ax.read_paper = _huge_read

    elif _MODE == "blocked_provider":
        import providers.google_scholar as _gs

        def _blocked(*a, **k):
            raise _gs.GoogleScholarBlocked("Google Scholar returned a CAPTCHA")

        _gs.search = _blocked
