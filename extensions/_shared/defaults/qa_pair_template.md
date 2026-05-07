# Q&A — {{criterion_label}}

> **Criterion definition:** {{criterion_definition}}

## Method

- **Mode:** `{{subagent | self-reflection}}` (subagent preferred where supported)
- **Context bundle loaded:** structured summary, domain narrative, missing baselines, review guidelines
- **Query strategy:** probing weaknesses specific to {{criterion_label}}; cross-referenced against external context where applicable
- **Discrepancy flagging policy:** any answer that contradicts a paper claim is logged with `[DISCREPANCY]` tag

## Output

### Q1
<Probing question targeting {{criterion_label}}>

### A1
<Answer grounded in the structured summary and external context. If the question depends on novelty or comparison to prior work, the answer must cite specific entries from `02_retrieved_literature.md` or `03_domain_narrative.md`. Flag discrepancies with `[DISCREPANCY]` and explain.>

### Q2
<...>

### A2
<...>

### Q3
<...>

### A3
<...>

### Q4
<...>

### A4
<...>

### Q5
<...>

### A5
<...>

### Q6
<...>

### A6
<...>

### Q7
<...>

### A7
<...>

### Q8
<...>

### A8
<...>

### Q9
<...>

### A9
<...>

### Q10
<...>

### A10
<...>

## Provenance

- Papers cited in answers: <list with paperId/URL where available>
- External tools used during answering: <web_search, osp-mcp.search_arxiv, osp-mcp.search_semantic_scholar, ...>
- Discrepancy count: <N>
