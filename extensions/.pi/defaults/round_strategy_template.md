# Literature Round {{round_number}} — {{strategy_slug}}

## Method

- **Strategy:** `{{strategy_slug}}` (one of: `sub-domain-anchor`, `method-anchor`, `temporal-expansion`)
- **Goal of this round:** {{strategy_goal}}
- **Tools used:** every retrieval tool you actually called this round. Pick the
  ones that suit the paper's field — a biomedical database is worth a call only
  when the paper touches medicine, biology, public health or psychology, and
  firing it on a CS paper pollutes the corpus.
  - `<tool>` — `<why it was in scope this round>`
  (A code-and-data repository search is never in scope here — it finds software,
  not papers.)
- **Tools not called:** `<tool>` — `not installed in this project` | `out of scope: <reason>`
- **Tools that failed:** `<tool>` — `<the reason from the error record>`.
  An `error` key means the provider failed and you did not get to look. An
  empty list means it looked and found nothing. Never report the first as the
  second.
- **Query formulation rules for this round:**
  - Round 1 (sub-domain-anchor): use the paper's stated sub-domain and primary keywords; aim for the canonical 10–20 most-cited works in this area.
  - Round 2 (method-anchor): switch to the proposed method's name and key technical terms; find prior or concurrent work using the *same technique*.
  - Round 3 (temporal-expansion): the 12 months **before `paper.cutoff_date`**; explicitly include pre-prints, workshop papers, and concurrent submissions; goal is catching what static knowledge cutoffs miss.
- **Retention criteria:** keep papers that are (a) directly comparable on task or method, (b) cited >5 times if older than 12 months, (c) any pre-print regardless of citations if from the last 6 months and topically relevant.

## Output

| # | ID | Title | Authors | Year | Venue | Source(s) | Why kept |
|---|---|---|---|---|---|---|---|
| 1 | <DOI, arXiv id or URL> | <title> | <authors> | <year> | <venue> | <source>,<source> | <one-line justification> |
| 2 | ... | ... | ... | ... | ... | ... |

### Notes on what was excluded
<Brief mention of papers that surfaced but were dropped, with reason. Helps the next round avoid re-discovering them.>

## Provenance

- **Queries run:**
  - `<query 1>` — via `<tool>` — `<N results, K kept>`
  - `<query 2>` — via `<tool>` — `<N results, K kept>`
  - ...
- **Total unique papers retained from this round:** `<N>`
- **Time spent (approx):** `<N>` LLM-tool roundtrips
