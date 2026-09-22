# Reaching the search tools through the shell

Read this when `session.json` records `mcp.interface` as `cli`, or when an MCP
search fails and you must fall back.

The tools, the arguments, the results and the error envelope are the same as the
MCP ones. Only the calling convention differs.

## The commands

**Run these from the project root** — the directory holding `.brain/`. The
paths below are relative to it. From anywhere else, put the project root in
front of them, because a wrong working directory cannot be reported as JSON:
the shell fails before Python starts, so there is nothing to print a `reason`.

List what this project has:

```bash
.open-scholar-peer/mcp/.venv/bin/python .open-scholar-peer/mcp/osp_cli.py list
```

Run one tool:

```bash
.open-scholar-peer/mcp/.venv/bin/python .open-scholar-peer/mcp/osp_cli.py \
  call search_arxiv '{"query": "retrieval augmented generation", "max_results": 10}'
```

`schema <tool>` prints one tool's full argument list. Arguments are a JSON
object. The result is one JSON document on standard output.

## Run a round as one batch

**Prefer `batch` over repeated `call`.** One round of searches is one command:

```bash
.open-scholar-peer/mcp/.venv/bin/python .open-scholar-peer/mcp/osp_cli.py batch '[
  {"tool": "search_arxiv",    "arguments": {"query": "...", "max_results": 10}},
  {"tool": "search_openalex", "arguments": {"query": "...", "limit": 10}}
]'
```

It returns one result per call, in the order you sent them, each with its own
`ok` and its own error envelope. A failing call never stops the others.

Three reasons this matters, all measured:

- Every separate call is a new process, and a new process forgets the arXiv
  rate limit, the parsed-text cache and the de-duplication. In one batch they
  all work again.
- A three-round phase is about eighteen calls. As separate calls that is over a
  minute of pure start-up and enforced waiting.
- On hosts that ask permission per command, eighteen calls is eighteen prompts.

The deadline applies to **each call**, not to the batch, so one slow provider
cannot spend the whole budget.

## Branch on `reason`, never on the exit code

Every failure carries a `reason`. That is the field to act on. The exit code is
a coarse hint and nothing more — a database switched off for this project and a
misspelled argument both exit 2, and they need opposite responses.

| `reason` | What it means | What to do |
|---|---|---|
| `blocked` | the provider refused us | Record a corpus gap. Never a finding. |
| `rate_limited` | too many requests | Record a corpus gap. Try later, not immediately. |
| `busy` | another call holds the single allowed connection | Retry once, after the others. |
| `timeout` | the call passed its limit and was abandoned | Record a corpus gap. Nothing was searched. |
| `unavailable` | the source is off, or cannot serve this | Record a corpus gap. If it says the database is switched off, say so in Provenance — the user chose that. |
| `not_found` | the identifier matched nothing | A real answer. Not a gap. |
| `bad_request` | the call was wrong | Fix the arguments and retry. Run `schema <tool>`. |
| `failed` | something else went wrong | Record a corpus gap and name the message. |

**None of these mean "no papers exist."** Only an empty list `[]` means the
search ran and matched nothing.

## When a result says it was cut

A cut is always declared in the result itself, in one of three shapes. Look for
`osp_truncated` — it is the one key common to all of them.

| Shape | Where the marker is | What you are holding |
|---|---|---|
| A **list of records** | an extra last element | the records above are complete; the rest were not returned |
| A **single record** | merged into the record | the record is **not** complete — `osp_how_to_get_the_rest` names which fields were shortened and by how much |
| A **full-text window** | merged into the record | a shorter window than you asked for, with `next_offset` corrected — keep calling with it until it is null |

Say in Provenance which of these you got. A cut result is not a failure and not
an empty one: ask for fewer results, page with `offset`, or raise
`--max-bytes`.

## Traps

- **Quoting.** A title with an apostrophe breaks shell quoting. Pass the JSON on
  standard input instead:

  ```bash
  .open-scholar-peer/mcp/.venv/bin/python .open-scholar-peer/mcp/osp_cli.py \
    call search_arxiv - <<'JSON'
  {"query": "what's new in retrieval", "max_results": 5}
  JSON
  ```

- **A command that never returns.** Every call is bounded, and `--timeout
  <seconds>` lowers the bound. If a command has not answered, it is waiting on a
  provider, not on you.
- **Standard error.** Logging is off by default so that `2>&1` still parses as
  JSON. Add `--verbose` only when diagnosing.
- **Group your commands.** On a host that asks permission per command, send one
  shell invocation rather than many.
