## Reaching the search tools on this tool

This tool has no MCP client, so the literature sources are not tool calls here.
They are a program you run in the shell. Everything else in the protocol is
unchanged.

List what this project has:

```bash
.open-scholar-peer/mcp/.venv/bin/python .open-scholar-peer/mcp/osp_cli.py list
```

Run one:

```bash
.open-scholar-peer/mcp/.venv/bin/python .open-scholar-peer/mcp/osp_cli.py \
  call search_arxiv '{"query": "retrieval augmented generation", "max_results": 10}'
```

`schema <tool>` prints one tool's full argument list. Arguments are a JSON
object; the result is JSON on standard output.

Read the exit code, because it separates two things that look alike:

- **0** — the call ran. An empty list means the search matched nothing.
- **1** — the call ran and failed. The output carries `reason`, which says
  whether the provider blocked you, rate-limited you, or timed out. None of
  these mean "no papers exist", and none may be recorded as a finding.
- **2** — the call itself was wrong: unknown tool, bad arguments. Fix and retry.

If a database is switched off for this project, the output says so plainly
rather than returning nothing. Treat that as a gap in the corpus and record it,
the same as any other unavailable source.
