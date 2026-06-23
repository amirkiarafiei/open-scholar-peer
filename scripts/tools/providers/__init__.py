"""Provider modules for osp_cli. Each module exposes plain functions
that the subcommands in osp_cli.py call into.

Adding a new provider:
  1. Create `providers/<name>.py` with the search/get-detail functions.
  2. Import it in `osp_cli.py` and register appropriate subcommands.
"""
