# Q&A — {{criterion_label}}

> **Criterion definition:** {{criterion_definition}}

## Method

- **Mode:** `{{subagent | self-reflection}}` (subagent preferred where supported)
- **Pairs:** {{qa_pairs_per_criterion}} (from `session.json.qa_pairs_per_criterion`)
- **Context bundle loaded:** structured summary, domain narrative, missing baselines, review guidelines
- **Query strategy:** probing weaknesses specific to {{criterion_label}}; cross-referenced against external context where applicable
- **Discrepancy flagging policy:** any answer that contradicts a paper claim is logged with `[DISCREPANCY]` tag

## Output

<!-- Repeat Q/A blocks exactly {{qa_pairs_per_criterion}} times, numbered Q1/A1 … QN/AN -->

### Q1
<Probing question targeting {{criterion_label}}>

### A1
<Answer grounded in the structured summary and external context. Cite specific entries from `02_retrieved_literature.md` or `03_domain_narrative.md` where applicable. Flag discrepancies with `[DISCREPANCY]` and explain.>

### Q2
<...>

### A2
<...>

<!-- … continue Q3/A3 through Q{{qa_pairs_per_criterion}}/A{{qa_pairs_per_criterion}} -->

## Provenance

- Papers cited in answers: <list with paperId/URL where available>
- External tools used during answering: <web_search, osp-mcp.search_arxiv, osp-mcp.search_semantic_scholar, ...>
- Discrepancy count: <N>
