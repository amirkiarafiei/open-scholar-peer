# Generic Peer Review Guidelines (Fallback)

Used when:
1. The user did not specify a venue at onboarding, OR
2. Web search failed to retrieve the venue's official review form, AND
3. The user could not provide review guidelines manually.

## Default criteria

The five criteria below are derived from common ML/NLP/CS conference review forms (ICLR, NeurIPS, ACL, EMNLP) and represent the lowest-common-denominator dimensions a reviewer should evaluate.

| Slug | Label | Definition |
|---|---|---|
| `novelty` | Novelty & Originality | Does the paper present a substantively new idea, framing, dataset, or analysis that is not already established in prior work? Is it a paradigm shift, an incremental extension, or a re-packaging? |
| `technical-soundness` | Technical Soundness | Are the methods correct? Are claims supported by adequate evidence? Are baselines appropriate and ablations meaningful? Are statistical claims justified? |
| `clarity` | Clarity & Presentation | Is the paper well-written? Are figures, tables, and equations clear? Could a competent reader in the sub-field reproduce the work from the description? |
| `significance` | Significance & Impact | Why does this matter? Will it change practice, enable new research, or shift theoretical understanding? Is the problem important? |
| `reproducibility` | Reproducibility | Are code, data, hyperparameters, and compute requirements disclosed? Are results reproducible from the paper alone or with reasonable effort? |

## Final review structure (generic)

When `/6-osp-review` runs without a venue-specific format, it emits:

1. **Summary** — 2–3 paragraph précis of the paper's contribution.
2. **Strengths** — bulleted list grounded in the structured summary + verified Q&A.
3. **Weaknesses** — bulleted list with each item cross-referenced to a discrepancy in the interrogation log or a missing baseline.
4. **Detailed comments per criterion** — one section per criterion above, citing the relevant `05_qa_<slug>.md`.
5. **Questions for authors** — 3–5 questions raised during the Q&A phase that remain unresolved.
6. **Decision recommendation** — accept / weak accept / borderline / weak reject / reject, with one-paragraph justification.
7. **Confidence** — 1–5 scale with a one-sentence rationale.
