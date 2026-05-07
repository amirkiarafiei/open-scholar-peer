# Literature Round {{round_number}} — {{strategy_slug}}

## Method

- **Strategy:** `{{strategy_slug}}` (one of: `sub-domain-anchor`, `method-anchor`, `temporal-expansion`)
- **Goal of this round:** {{strategy_goal}}
- **Tools used (must use all available):**
  - `osp-mcp.search_arxiv`
  - `osp-mcp.search_semantic_scholar`
  - `osp-mcp.search_google_scholar`
  - native Web Search (where available)
- **Query formulation rules for this round:**
  - Round 1 (sub-domain-anchor): use the paper's stated sub-domain and primary keywords; aim for the canonical 10–20 most-cited works in this area.
  - Round 2 (method-anchor): switch to the proposed method's name and key technical terms; find prior or concurrent work using the *same technique*.
  - Round 3 (temporal-expansion): filter to the last 12 months; explicitly include arXiv pre-prints, workshop papers, and concurrent submissions; goal is catching what static knowledge cutoffs miss.
- **Retention criteria:** keep papers that are (a) directly comparable on task or method, (b) cited >5 times if older than 12 months, (c) any pre-print regardless of citations if from the last 6 months and topically relevant.

## Output

| # | Title | Authors | Year | Venue | Source(s) | Why kept |
|---|---|---|---|---|---|---|
| 1 | <title> | <authors> | <year> | <venue> | arxiv,semantic_scholar | <one-line justification> |
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
