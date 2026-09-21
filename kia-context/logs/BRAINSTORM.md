---
description: >
  The decision log. A chronological record of investigations, analysis and conversations between the
  human and the agent, and the decisions they produced. It exists so that months later anyone can read
  it and see that on a given date we considered three options, chose the second, and why — the
  traceability of how the project got its shape. Append-only, dated, numbered, and deliberately terse.
  NOT here: the resulting rule itself (that goes to MANIFESTO.md or ARCHITECTURE.md), the work done
  (PROGRESS.md), or a write-up of every fix — see the entry test below.
authority: background
writes: agent, whenever a decision is made
status: active
covers: "Extensions phase, 2026-04-23 onward — D1 onward, O1 onward"
last_updated: "2026-09-21"
---

# 🧠 BRAINSTORM — Why we chose what we chose

> **D1–D11 were reconstructed from git history and `docs/` on 2026-09-11, not captured from the work as
> it happened.** Treat them as approximate. Where a document states the reasoning outright it is quoted;
> where only a commit exists, the entry says the reasoning is inferred. **D12 onward was recorded live.**

> **← Previous:** none. This is part one.
> **Next →** none yet. When this file is split, the pointer goes here and in the new part.

**Contents**

| § | |
|---|---|
| [What earns an entry](#what-earns-an-entry) | The test, before you write |
| [Decision log](#decision-log) | D1 onward |
| [Open questions](#open-questions) | O1 onward |

---

## What earns an entry

> **An entry earns its place when an alternative was rejected, or when a measurement changed our minds.**

Not every fix. Not every refactor. If an outsider would read it later and ask *"why was it done this
way?"*, write it; otherwise the commit message already covers it. Number permanently, date absolutely,
and always say what was **rejected** — that is the part that stops it being re-proposed in three months.

---

## Decision log

### D1 · Ship as tool-native files, not a plugin or a web app — 2026-04-23

**Considered:** marketplace plugins per vendor / a hosted web app first / plain files copied in by a shell installer
**Chose:** plain files, ReviewerOS-style installers
**Because:** the design document's stated core philosophy — *"Eliminate vendor lock-in and UI dependency… The system must live where the developers and researchers already work."*
**Rejected marketplaces because:** a per-vendor package is exactly the lock-in the project exists to remove.
**Rejected web-app-first because:** it rebuilds the proprietary interface being avoided. It was designed in full — DeepAgents JS backend, a forked Deep Agents UI with a phase stepper — and deferred to `src/backend` / `src/frontend`.
**Rule that follows:** MANIFESTO rule 1.

### D2 · One canonical source, generated adapters — 2026-04-23 (design) / 2026-05-08 (built)

**Considered:** maintain each tool's directory by hand / generate all of them from one source
**Chose:** generate
**Because:** drift was named at t=0 as the known risk of the plain-files model, with the mitigation written down as a source hierarchy: canonical content lives once, tool adapters are generated from it, installers only copy already-synced folders. Fourteen hand-maintained copies of an eight-step protocol diverge silently.
**Rejected hand-maintenance because:** nothing errors when two adapters disagree; the user just gets a different review.
**Rule that follows:** ARCHITECTURE §7, and the Golden Rule in `AGENTS.md`.

### D3 · MCP exposes dumb tools only — 2026-04-23

**Considered:** rich tools (`fetch_literature` doing search + filter + dedup) / atomic stateless functions
**Chose:** atomic
**Because:** the design document put it in capitals — *"MCP is NEVER used for agentic logic, orchestration, or multi-step heuristics."* Deciding what to search and when to stop is the reasoning the paper is about; moving it into a server hides it.
**Rejected rich tools because:** they make the interesting half of the method invisible and untunable.
**Rule that follows:** MANIFESTO §7 (permanent no), ARCHITECTURE §9.

### D4 · Enforce paper hyperparameters structurally, not numerically — 2026-05-08

**Considered:** a config field for `k` and `N_QA` / enforce by required file structure
**Chose:** file structure — three round files must exist on disk
**Because:** host tools expose no hyperparameters to a slash command, and a model asked to "do three rounds" will report three rounds without doing three. A file that must exist cannot be hallucinated.
**Rejected config because:** there is nothing to configure — no process reads it.
**Cost accepted:** temperature 0.7 is simply unreachable and is documented as lost.
**Rule that follows:** ARCHITECTURE §4; `docs/KNOWN_LIMITATIONS.md` §7.

### D5 · Subagents where available, self-reflection where not — 2026-05-08

**Considered:** subagents only (drop unsupported tools) / self-reflection everywhere (uniform) / subagents with a documented fallback
**Chose:** the fallback, published as weaker
**Because:** the design preferred real context isolation wherever a host tool offers it — an isolated context window per delegated task, rather than one agent holding every role; dropping three tools would contradict D1.
**Rejected uniform self-reflection because:** it would degrade the 11 tools that can do it properly.
**Rejected silent fallback because:** presenting a weaker method as equivalent is the dishonesty MANIFESTO rule 7 exists to prevent.
**Measured:** 11 of 14 tools support subagents.
**Superseded in part by D16 (2026-09-11):** the decision stands, but the count does not — Antigravity gained
subagents, so it is 12 of 14 and the fallback covers only Mistral Vibe and OpenHands. Left as written
because it was true on 2026-05-08; read D16 for the current shape.

### D6 · `N_QA` 10 → user-configurable, default 2 — 2026-05-08

**Considered:** the paper's fixed 10 / a fixed lower number / user-chosen with a low default
**Chose:** user-chosen at `/5-osp-qa` start, default 2, persisted in `session.json`
**Because:** cost is criteria × pairs. A seven-criterion venue at 10 pairs is 70 subagent calls before the review is even written.
**Rejected fixed 10 because:** it made a first run prohibitively slow and expensive for a user evaluating the tool.
**Trade accepted:** a departure from the paper, so the step now prints the multiplication and a guide (2 quick / 5 thorough / 10 exhaustive) and lets the user choose.
**Commit:** `dd5ac6f`.

### D7 · One literature round per invocation — 2026-05-08

**Considered:** all three rounds in one command / one round per invocation with a progress banner
**Chose:** one per invocation
**Because:** three rounds is 25–35 tool calls and several minutes with no output; users could not tell it apart from a hang.
**Rejected all-at-once because:** it hid progress and gave no point to inspect a round before the next.
**Commit:** `7b60b3a`.

### D8 · Self-contained venv per project, not PyPI — 2026-05-08

**Considered:** publish `osp-mcp` to PyPI / build a venv in the user's project
**Chose:** per-project venv at `.open-scholar-peer/mcp/`
**Because:** nothing to install globally, nothing to keep in step with a release, and the server version always matches the adapter that was installed with it.
**Rejected PyPI because:** it adds a global dependency and a release cadence to a project whose whole pitch is "run it with what you already have". Still listed as deferred, not refused.

### D9 · arXiv via the official package, not raw HTTP — 2026-05-08

**Considered:** hand-rolled HTTP against the arXiv API / the `arxiv` Python package
**Chose:** the package
**Because:** rate limiting and result paging are handled correctly rather than approximately.
**Commit:** `473b7a1`. *Reasoning inferred from the commit message; no document records it.*

### D10 · Drop the `_osp_managed` marker from merged MCP configs — 2026-05-08

**Considered:** keep a marker key so the installer knows which entries it owns / drop it
**Chose:** drop it
**Because:** a measurement changed our minds — the extra key failed Gemini CLI's config validation and broke the tool outright.
**Consequence accepted:** ownership tracking moved to a sidecar file rather than an inline key.
**Commit:** `cdda9dd`.

### D11 · Per-call timeout 30s → 90s — 2026-05-10 → 2026-06

**Considered:** 30s / 90s / no timeout
**Chose:** 90s, overridable via `OSP_CALL_TIMEOUT` in `.env`
**Because:** real Semantic Scholar and Google Scholar calls exceeded 30s often enough that the timeout was the failure, not the API.
**Rejected no timeout because:** one hung HTTP call wedges a stdio server with no way for the user to see why.
**Commits:** `7e58e90`, `a184822`, `c26a091`.

### D12 · Adopt kiacontext as the project's memory — 2026-09-11

**Considered:** keep everything in `docs/` and `AGENTS.md` / add a context harness beside them
**Chose:** the harness, with `docs/` kept as the human-facing layer
**Because:** `docs/` records *what* was built and `AGENTS.md` records *how to work on it*, but nothing recorded *why* — five months of decisions existed only in commit messages, and commit messages do not say what was rejected.
**Rejected docs-only because:** `docs/PHASES.md` had already gone stale in exactly this way — every phase ticked at the top, every underlying deliverable checkbox left unticked.
**Rule that follows:** none yet; this is process, not product.

### D13 · Phase 1 stays sequential, not parallel — before 2026-07-31

**Considered:** run Summary, Literature, Historian and Baseline Scout concurrently / keep them sequential
**Chose:** sequential
**Because:** simplicity and fidelity to the method. The paper's Phase 1 is drawn as two parallel tracks, so the parallel version is the more faithful reading of the diagram — but Historian consumes the Literature corpus and the Scout leans on it too, so only part of it is genuinely parallelisable.
**Rejected parallel because:** the sequencing is also what gives the user a point to stop and read each artifact, which later became MANIFESTO rule 6.
**Status:** deferred, not refused.
**Source:** recorded only in `docs/PHASES.md` "Out of Scope"; carried here on 2026-09-11 when that file was retired, otherwise it would have been lost.

### D14 · Retire `IDEA.md` and `PHASES.md` from `docs/` — 2026-09-11

**Considered:** keep both in `docs/` / delete both outright / move the origin document into the harness and delete the build plan
**Chose:** `docs/IDEA.md` → `kia-context/genesis/IDEA.md` (frozen); `docs/PHASES.md` deleted
**Partly reversed by D18 (2026-09-12):** moving the whole file into the harness was wrong — `kia-context/` holds the harness's own files, not imported documents. Its content was absorbed and the file deleted. The `PHASES.md` half stands.
**Because:** `docs/` is for people using and contributing to the project — contracts, layout, limitations, troubleshooting. Those two were *input context* for building it, which is what the harness is for. `IDEA.md` is cited as provenance ~20 times across `kia-context/` and stays live so those citations remain checkable; `PHASES.md` is fully superseded by `logs/PROGRESS.md`.
**Rejected deleting IDEA too because:** it would leave every provenance citation pointing at a file you can only recover with `git show`, which is the sort of friction that gets a citation ignored rather than followed.
**Rejected keeping both because:** `PHASES.md` had already gone stale in the way D12 describes, and a second, competing progress tracker beside `PROGRESS.md` would go stale again.
**Consequence:** the release procedure in `AGENTS.md` now updates `PROGRESS.md` instead of `PHASES.md` checkboxes.

### D15 · Commit the kiacontext skills so cloners get them — 2026-09-11

**Considered:** leave the per-tool skill installs local and gitignored (the repo's existing convention for root tool directories) / commit them
**Chose:** commit `skills/kia-context-*/` under `.claude/`, `.agents/`, `.opencode/` and `.hermes/`
**Because:** the harness is only useful if the agent working in a clone can actually run `/kia-context-sync`. Making every contributor install it separately means most will not, and the context files rot.
**Rejected committing the whole of `/.agents/` because:** it also holds a locally-installed copy of the OSP Antigravity-CLI adapter, which duplicates `extensions/.agents/` and would drift against it silently. Only the kiacontext skills are tracked; the rest of each tool directory stays ignored.
**Rule that follows:** none — this is repository hygiene, not product.

### D16 · Antigravity moves from self-reflection to subagents — 2026-09-11

**Considered:** leave the classification alone / flip the capability flag / flip it *and* ship custom subagent definition files under `.agents/agents/`
**Chose:** flip the flag, and treat Antigravity exactly like the other subagent-capable tools
**Because:** Antigravity 2.0 documents an asynchronous subagent framework — `invoke_subagent`, custom subagents at `.agents/agents/<name>.md`, an `/agents` panel, a 10-level nesting cap. The old classification was not a preference, it was a fact that expired, and while it stood every Antigravity user got the documented *weaker* Q&A phase (D5) for no reason.
**Rejected leaving it because:** self-reflection is a substitute, not an equivalent — MANIFESTO rule 7.
**Rejected shipping custom subagent files because:** no other tool has them. OSP's personas are skills, and a tool-specific agent-definition format would be a new artifact type for the sync script to produce and keep in parity. Parity with the other 13 *is* the fix here. Noted as O8 instead.
**Measured:** subagent-capable tools 11 → 12 of 14; self-reflection now covers only Mistral Vibe and OpenHands. Blast radius before starting: 14 files carried the claim, 8 of them canonical or code.
**Rule that follows:** none new — ARCHITECTURE §4 and `docs/KNOWN_LIMITATIONS.md` §1 updated in place.

### D17 · Antigravity degrades instead of insisting — 2026-09-11

**Considered:** keep the hard "MUST delegate / do NOT self-reflect" banner D16 gave Antigravity / ship a real subagent definition so the hard banner is safe (O8) / add a third Q&A mode that tries delegation and falls back
**Chose:** the third mode, `prefer-subagent`
**Because:** D16 asserted a capability nobody has run. Review raised it as O11: the banner orders delegation to `osp-answer-generator-agent`, but that persona ships as a *skill*, while Antigravity's mechanism is `invoke_subagent` over definitions at `.agents/agents/<name>.md`. If the skill is not reachable that way, a hard banner leaves the phase with no target and the fallback that used to cover it removed. The owner cannot test `agy` right now, so the wording has to work either way.
**Rejected the hard banner because:** an absolute instruction is only safe when the capability is confirmed. Here it converts an unknown into a failure.
**Rejected shipping the definition file because:** still O8 — a tool-specific artifact type no other adapter has, and it would not help the five other tools resting on the same assumption.
**Consequence:** `adapt_qa_body_for_tool()` now has three modes, not two. The banner asks Antigravity to try delegation, fall back to turn markers if it is unavailable, finish the phase either way, and record `Mode:` in the artifact so the run says which happened.
**Also:** the owner asked for no "MUST"/"do NOT" in this banner. The eleven confirmed-subagent tools keep the absolute wording — there the capability is known, and the absolute is what stops the Query Agent answering its own questions.
**Rule that follows:** none new. MANIFESTO rule 8 (fail loudly, never degrade in silence) is satisfied by the `Mode:` line: the degradation is recorded in the artifact, not hidden.

### D18 · `kia-context/` holds only harness files, never imported documents — 2026-09-12

**Considered:** keep `genesis/IDEA.md` as a frozen import (D14) / absorb its content into the harness files and delete it / delete it outright and let the citations point at git
**Chose:** absorb, then delete
**Because:** the owner ruled it directly — *"You are not allowed to add docs such as IDEA.md or things like that to kia-context. You can only integrate their CONTENT and not the WHOLE FILE."* The harness is seven files with defined authority; a 339-line design document parked in `genesis/` is a second, unversioned source of truth sitting next to them, and D14 had already had to bolt a banner on it listing five places it was stale. A file that needs a staleness banner does not belong in the folder whose whole purpose is being true.
**Rejected keeping it because:** D14's justification — "cited ~20 times, so it stays live" — had the dependency backwards. The citations were the problem, not the reason. A claim that only holds because a frozen document is still on disk is a claim that is not actually written down.
**Rejected deleting outright because:** several citations were pointer-only (*"§3.4 names drift as the known risk"*) and would have left the harness asserting things with nothing behind them.
**How:** every pointer-only citation was rewritten to state the substance inline, so each claim now stands on its own. The document stays readable in history at `git show c93d344:docs/IDEA.md`, referenced once from `GENESIS.md` and once from `SEED.md` rather than twenty times.
**Rule that follows:** `kia-context/` contains `INDEX.md` and the six harness files, and nothing else. Content from elsewhere is integrated, never parked.

### D19 · Which open databases to add, and which to refuse — 2026-09-19

**Considered:** stay on arXiv + Semantic Scholar + Google Scholar / add every open source (OpenAlex, PubMed, bioRxiv, medRxiv, IACR, PMC, DBLP, Zenodo, ACM DL, IEEE Xplore) / add a chosen few by role
**Chose:** add **Europe PMC**, **Zenodo** and **OpenAlex**. Defer bioRxiv/medRxiv. Refuse DBLP, ACM DL, IEEE Xplore, Crossref, PubMed, CORE, IACR.
**Because:** the owner's framing was the strong argument — *"we can say we support every open DB that is necessary"*, and every source above except OpenAlex needs no key at all. That is a real product claim and it fits MANIFESTO rule 1. Each admitted source also has a job nothing else does: Europe PMC = full text over REST with no PDF parsing; Zenodo = code/data release checking; OpenAlex = retraction flags.
**Measured, and it decided things:** of the owner's ~30 reviewed papers, about **5 or 6 are health or biology** (Frontiers, `Sage/digital-health-mental-fatigue`, `MDPI/information_urinary_infection`, `MDPI/information_explain_mental_health`). arXiv covers almost none of that, so the biomedical gap is real rather than hypothetical.
**Rejected DBLP because:** it is dead. Four probes on 2026-09-19 hit an Anubis proof-of-work bot wall, including with a normal browser User-Agent and with the competitor's own. Not transient.
**Rejected ACM DL and IEEE Xplore because:** subscription or paid key. They break MANIFESTO rule 1 outright.
**Rejected Crossref, PubMed, bioRxiv/medRxiv, CORE, IACR because:** redundant, flaky, or too narrow. Detail in `logs/PROGRESS.md` under *Reference*.
**Deferred bioRxiv/medRxiv, and this one changed twice.** First read: unusable, no keyword search. The owner pushed back with the API docs, and he was right to — reading them properly showed a **subject-category filter**, **abstracts inside every record**, a **recent-days endpoint**, a **`jatsxml` full-text link** and a **`published` field** giving the journal DOI. Corrected position: they are **a feed, not a search engine**. You cannot ask "find papers about X"; you can ask "give me every bioinformatics preprint from July". Volume measured: one month unfiltered **5,906** papers (~60 calls), with `category=bioinformatics` **631** (~7 calls). Making them useful needs a plain `contains` filter in the tool — which is a filter, not orchestration, so it would **not** break D3. Left out of M11–M13 only because Semantic Scholar already indexes both **with** real keyword search; their unique value is freshness and free full text. Revisit under O13.
**Rule that follows:** none new. MANIFESTO rule 1 already covers the no-subscription test.

### D20 · Full text comes from arXiv and Europe PMC, and is never written to disk — 2026-09-19

**Considered:** stay metadata-only / Unpaywall + a PDF parser for everything / arXiv's own files plus Europe PMC's REST full text
**Chose:** arXiv (PDF or LaTeX source) plus Europe PMC (XML over REST). Unpaywall deferred.
**Because:** metadata is not enough for the Baseline Scout or the Q&A engine — *"does the cited paper actually report that number?"* cannot be answered from an abstract. Europe PMC serves full text over a plain REST call with **no key and no PDF to parse**, which is the cheapest path that exists. arXiv's text is free to anyone.
**Corrected a wrong claim:** the 2026-09-19 review said OSP "has no full-text access". Wrong, and the owner caught it. arXiv always had free full text; the gap was our code storing `pdf_url` and never opening it.
**Rejected Unpaywall-first because:** it only pays off once a PDF reader exists, and it needs an email parameter. It is the right answer later for non-arXiv, non-biomedical papers.
**Constraint that follows:** a read tool **returns text and writes nothing**. The competitor persists to `./downloads`; that would break the stateless rule in D3. Returning text keeps the tool atomic.
**Note for implementation:** `arxiv` 4.0.1 removed `Result.download_pdf` and `download_source`, so fetch by plain HTTP from `pdf_url` / `source_url`. LaTeX source is cleaner than PDF for maths and two-column layouts, but arrives as `.tar.gz`.

### D21 · The installer asks which databases to use, and offers to take keys — 2026-09-19

**Considered:** enable every provider always / an env-var opt-in / let the user choose during install
**Chose:** choose during install, as an extension of the M9 TUI
**Because:** OpenAlex is the first source after Semantic Scholar that wants a key, so the user has to be told *before* installing which sources are free, which need a key, which take an optional key, and what domain each covers. The owner asked for this as a readable table the user clicks through, in the same keyboard model as the M9 picker.
**Also chose:** offer to type each key during the install, with a clear skip. If skipped, point at `.env`. **A key is never required to finish installing** — that would breach MANIFESTO rule 1.
**Rejected always-on because:** every extra provider costs the agent a longer tool list on every request, and a user reviewing CS papers has no use for biomedical sources.
**Scheduled as:** M13 S5–S7.
**Refined on 2026-09-20, after seeing it run.** Three changes, all from watching the flow rather than reasoning about it. The agent picker now comes **before** the database picker: which agents you use is the decision you already know the answer to, and the databases follow from the papers you review. The database picker starts with **arXiv and Semantic Scholar only** rather than all six — starting with everything hands a CS reviewer four sources they will never call and a longer tool list on every request, and adding one is a single keypress. And keys are now behind **one yes/no question** instead of a prompt per database: with the default pair that is one question rather than an interrogation, and the answer defaults to "no, I will use .env later".
**Rule that follows:** whichever picker runs last carries the Install button, and its label says what pressing it actually does — "Continue" when a question still follows, "Install" when it does not. An installer that promises to install and then asks one more thing spends trust it does not need to.

### D22 · A blocked scrape is not retried — measured, not assumed — 2026-09-20

**Considered:** copy the competitor's behaviour (rotate the User-Agent, retry with backoff) / detect the block and fail at once / route through a proxy
**Chose:** detect and fail at once. Keep retries only for faults that can pass on their own — a dropped connection, a timeout, a 5xx. Keep User-Agent rotation because it is harmless, and keep an optional proxy env var.
**Because it was tested, as the owner asked.** Five requests to Google Scholar about eight seconds apart from one ordinary address: **every one answered HTTP 429**, and four different User-Agent strings — Chrome 124 on Windows, Chrome 131 on macOS, Firefox 133 on Linux, and none at all — returned **byte-identical** bodies. The block is on the address, not the client string, so rotation changes nothing. Later in the same session Google stopped answering at all and requests timed out. Retrying a refusal therefore only spends the caller's 90-second budget on a host that has already said no, and leaves nothing for the other providers.
**Second measurement that shaped it:** the retry budget must fit inside `OSP_CALL_TIMEOUT`. At three attempts of 30 s the worst case was 93 s against a 90 s ceiling, so the caller would have seen a bare "timed out" instead of the message explaining the block — losing the very thing B9 was for. Now 20 s × 3 plus backoff = 63 s, pinned by a test.
**Rule that follows:** every failure is one exception family (`GoogleScholarUnavailable`, with `GoogleScholarBlocked` beneath it) and every error record carries a machine-readable `reason`. An empty list means one thing only: the search ran and matched nothing.
**Corrected the same day, and the correction is the interesting part.** The first implementation detected a block by looking for phrases — "unusual traffic", "not a robot", "our systems have detected". Google echoes your query into the page title and into every result, so a perfectly good results page for a paper called *"I'm not a robot: (Deep) Learning to Break Semantic Image CAPTCHAs"* was reported as a block. That is **this decision inverted**: telling the agent the provider is down when it answered, and doing it precisely to the reviews most likely to search those words. Detection is now structural only — HTTP status, the `/sorry/` redirect, and interstitial element ids matched in attribute position — so a paper that merely discusses reCAPTCHA cannot trip it. The general rule: **never detect a provider's state with words that could appear in the content it returns.**

### D23 · The Semantic Scholar client runs with its own retry loop switched off — 2026-09-20

**Considered:** leave the package default (`retry=True`) / turn it off and fail in one round trip / write our own bounded retry
**Chose:** `retry=False`, and translate the 429 into an error that names the cause and tells the user a key would fix it.
**Because a measurement changed our minds.** The package reports HTTP 429 as `ConnectionRefusedError`, and its tenacity policy retries that ten times with exponential backoff from 5 s to 60 s — roughly **375 seconds inside one call**. The tool layer gives up at 90 s, but `asyncio.to_thread` cannot cancel the thread, so the orphaned worker keeps hitting a rate-limited API for minutes after the agent has already been told the call timed out, making the next call likelier to be throttled in turn. Measured before and after on the same call: **stalled past a 300 s timeout, then failed in 1.3 s.**
**Rejected our own bounded retry because:** it buys nothing a caller cannot do better. The agent has three other providers and knows the whole plan; the provider does not.
**Cost, stated plainly:** a transient 429 that one retry would have cleared now fails. That is the right trade — a fast honest failure beats a six-minute stall nobody sees the end of.
**Note for whoever reads the package source:** catching `ConnectionRefusedError` is not enough. tenacity wraps it in `RetryError` even with retrying off, so the exception chain has to be walked.

### D24 · No PDF library — the reader is already installed — 2026-09-20

**Considered:** add `pypdf` and parse PDFs ourselves / serve LaTeX only and fail on PDF-only papers / serve LaTeX and hand PDFs to the markitdown server the installer already registers
**Chose:** the third.
**Because:** `scripts/merge_mcp_config.py` registers **two** MCP servers on every install — `osp` and `markitdown` (`uvx markitdown-mcp`) — and markitdown returns the full text of an arXiv PDF, tables included. Checked on `arxiv.org/pdf/1706.03762` on 2026-09-20. A PDF dependency would have duplicated something every user already has.
**And the two routes are not ranked, they are complementary.** LaTeX keeps table structure: `ByteNet \citep{...} & 23.75 & & & &\\` has explicit blank cells, so a value stays attached to its row. markitdown's conversion of the same table flattens into loose columns, and naive alignment attributes 39.2 to the wrong system. Maths survives as `$O(n^2 \cdot d)$` rather than `O(n2 · d)`. But markitdown keeps the **printed reference numbers, the author list and the affiliations**, none of which exist in the source. So: LaTeX for numbers and method text, markitdown for the bibliography.
**Constraint that follows:** the arXiv reader must say what it cannot do. Its source has `\citep{key}` markers and no reference list, so a citation cannot be resolved from it — the docstring names `get_semantic_scholar_paper_references` for that.

### D25 · Read tools may cache, and may collapse duplicate downloads — 2026-09-20

**Considered:** no cache at all (strictly stateless) / a small cache / a cache plus single-flight
**Chose:** a bounded cache of parsed paper text, plus one download per paper however many callers ask at once.
**Because the cost was measured, not imagined.** Reading a long paper takes several windows, and without a cache each one re-downloaded and re-parsed the whole tarball — six fetches for a 300k-character paper, each paying arXiv's three-second gap. Worse, nine concurrent readers of the *same* paper caused **six** downloads and three of them were refused with `ArxivBusy` for a paper that was already being fetched. The Q&A engine runs subagents in parallel and they read the same paper, so that is the normal path.
**Why this does not break D3:** both change *when* an answer arrives, never *what* it is — the same argument that already allows one shared HTTP client per provider. Anything that changes the answer is not allowed.
**Sizing was also measured.** At two entries, a phase reading three papers in turn missed on every single read: 41/41/40 downloads over 200 reads, a 0% hit rate, which is worse than no cache because each miss still pays the gap. Eight entries holds a working set. After the fix: nine threads → one download, and the round robin → three downloads instead of thirty.
**Known limit:** cached text never expires, so a paper revised on arXiv under the same id serves the old text for the life of the process. Acceptable for a server that lives as long as one review.

### D26 · The prompts describe capabilities, never tool names — 2026-09-21

**Considered:** keep the hardcoded tool list and add "if available" / list the tools but gate each on a check / describe what each source is *for* and let the agent discover what it has
**Chose:** the third.
**Because M13 made the old approach a lie.** The user now picks which databases are installed, so a prompt naming `search_europe_pmc` is promising something that may not exist. Five canonical files name tools this way. "If available" would patch the grammar without fixing the problem: the list still reads as a menu the agent expects to find.
**And naming tools was never the useful part.** The lists carried no judgement at all. Nothing told the agent that Google Scholar is blocked often enough that failure is the normal case, that Europe PMC is pure noise on a CS paper, or that native web search is not optional. A name is not knowledge.
**The owner's framing, which is the right one:** give a high-level overview of what each kind of source is good for, and let the agent judge from the paper's topic. Be careful not to promise the tools exist — the agent has to discover, judge and choose.
**Rejected a long guide because:** a block the agent skims is worse than a short one it reads. Target ten lines, not a manual.
**Scheduled as:** M14 P1–P6.

### D27 · No step is a gate — the user may skip anything — 2026-09-21

**Considered:** keep the three-round requirement (it is what the paper specifies) / make only the literature rounds optional / make every phase skippable and record the choice
**Chose:** the third.
**Because the protocol was enforcing a recommendation as a law.** Three rounds is what ScholarPeer recommends; it is not a correctness property, and each round costs real tokens. Nine prerequisite or refusal lines across six of the eight commands block a phase whose inputs are missing. The owner: *"It is not user-friendly to block the user."*
**The thing that makes this safe is recording, not refusing.** A skipped phase is written into `session.json` and into the artifact's Provenance, so the final review can say what it did not have. That keeps MANIFESTO rule 8 — report honestly — while removing the block. A thin review that admits it is thin is more useful than no review.
**Rejected "literature only" because:** the same objection applies to every phase, and fixing one would leave the inconsistency as a trap.
**Cost, stated plainly:** a user who skips everything gets a poor review. That is their call to make, and the artifact will say so.
**Explicitly not solved here:** O6, cascading invalidation. Re-running an early phase still leaves downstream artifacts stale, and a skip makes that no worse.
**Scheduled as:** M15 K1–K7. Closes O2.

### D28 · One phase block, chosen by looking at five of them — 2026-09-21

**Considered:** five candidate designs, shown rendered rather than described — a phase rail, an icon column, a two-line minimum, a mini card, and a file tree. Then three variations of the winner.
**Chose:** the rail, welded into the top rule, with `DONE` / `BLOCKED` / `NEXT` labels and an aligned value column, bounded above and below by rules.
**Because the current block answers the wrong question.** Seven hand-written blocks, one per command, each drifted from the others. They list what happened in prose and never say *where you are* — which across a seven-phase protocol is the thing a user most wants. A rail answers it with no words at all.
**Why the rail beat the alternatives:** the tree is better when a phase's value is its files, but most phases produce one; the two-line version is the shortest but loses the blocked-provider warning, which must never be buried; the card is the prettiest and the most fragile, since fixed-width boxes break below about 78 columns (O19).
**Why `BLOCKED` gets its own label:** a provider failure reported as prose gets skimmed. Recording a block as "no papers found" is exactly the bug M11 spent a milestone removing, and it would be a poor joke to reintroduce it in the reporting layer.
**Constraint that follows:** the block must be legible as raw text. Not all fourteen tools render markdown, so it is plain text with box-drawing characters and an ASCII fallback, the same treatment `install.sh` gives its glyphs.
**Scheduled as:** M16 R1–R7.

### D29 · MANIFESTO rule 2 amended — the system never skips, the user may — 2026-09-21

**Considered:** leave rule 2 alone and lean on the word *"silently"* / amend it in place / drop the clause about skipping
**Chose:** amend it in place.
**Because M15 reads as a direct contradiction of it.** Rule 2 said *"Steps are not silently merged, skipped, reordered, or 'optimised' into one pass."* M15 makes every step skippable. The word *"silently"* does technically carry the exception — a recorded skip is not a silent one — but a rule that needs that much reading is a rule the next agent will apply wrongly, in whichever direction suits it.
**The distinction the amendment draws** is the one that matters and was never written down: *the system* may not skip a step to save itself work; *the user* may skip anything, because it is their time and their tokens. Those are different acts that the old wording collapsed into one prohibition.
**What keeps it honest is recording, not refusing.** The skip lands in `session.json` and in the artifact's Provenance, so the final review states what it did not have. That is MANIFESTO rule 8 doing its job — degrade loudly — rather than rule 2 being weakened.
**Rejected dropping the clause because:** the prohibition on the *system* quietly merging or reordering steps is the whole reason the seven personas stay separate. That half is load-bearing and unchanged.
**Never renumbered.** Rule 2 keeps its number and its position; only its text moved. This decision is the record of why.
**Also measured while doing it:** the gate count in M15's plan was **9**; the real figure is **17** — 14 in `commands/` and 3 in `skills/`, including the orchestrator's master gate at `osp-orchestrator/SKILL.md:20`, which the original measurement never looked at because it only counted `## Prerequisites` bullets.

### D30 · A shared block means values in the callers, not a rendered copy — 2026-09-21

**Considered:** each command inlines its finished block and also points at the template / each command carries only its values and the template is rendered from them / a build step that generates the blocks into the commands
**Chose:** the second.
**Because the first is what we already had, with extra steps.** M16 shipped its first pass that way and it *looked* right — every command named `defaults/phase_block_template.md`. Then the measurement: `grep -rlE '── [●◐○]' extensions/_shared/` returned **11 files**. Changing a glyph or a column width meant eleven hand edits, and the blocks would drift apart again exactly as the seven originals had. The milestone existed to stop that and had reproduced it.
**Rejected a build step because** the adapters are already generated from `_shared/`; generating *into* `_shared/` would make the canonical tree partly derived, and the one rule everyone relies on is that `_shared/` is what a human edits.
**What makes the second work** is that a prompt is read by a model, not a compiler: "render the closing block from `defaults/phase_block_template.md`, values below" is an instruction it can follow. The template gained a phase-position table so the rail can be built without guessing.
**The measurement that settles it:** one file carries a rail today, and `test_parity.py::check_phase_blocks` fails the build if a second one appears. The convention became a mechanism.
**Cost, stated plainly:** an agent that ignores the pointer prints something ad-hoc, where before it had a copy to imitate. Two examples stay in the template to make that unlikely.

### D31 · Every tool's MCP config is written by the installer — the TOML excuse was never measured — 2026-09-21

**Considered:** keep emitting a paste-ready snippet for Codex, Mistral Vibe, OpenCode and OpenHands / write each tool's real config / write what we can and paste a prompt into the user's agent for the rest
**Chose:** the second, for all four.
**Reversing what was never decided.** The snippet path arrived inside `6942464 feat: add support for 8 new AI tools (13 total)` with no entry here — it was a shortcut taken while adding eight tools at once, and it then hardened into `ARCHITECTURE.md` as a fact: *"print a paste-ready snippet for tools whose config is TOML, global, or otherwise not safely machine-editable."* Every later review read it as deliberate and left it alone.
**What measuring it found, against the real binaries:**
- **OpenCode** — not TOML at all. The snippet we generated was already the correct schema, written to the wrong path. `.opencode/opencode.json` is project-local, merges into global per key, and the project wins. Verified by loading it: `markitdown` reported **connected**.
- **Codex** — `codex mcp add` is real, non-interactive, idempotent, and edits `config.toml` through `toml_edit`, so comments and formatting survive. We printed the command and did not run it.
- **Mistral Vibe** — appending an `[[mcp_servers]]` block to arbitrary TOML parsed cleanly in 8 of 9 hostile cases; the 9th raises and is caught. 13 cases now covered by a test.
- **OpenHands CLI** — `~/.openhands/mcp.json` is the same `{"mcpServers": {...}}` shape `merge_mcp_config.py` already writes.
**And a defect the excuse was hiding.** The Vibe snippet omitted `transport`, which is a pydantic discriminator: pasting it does not fail one entry, it **invalidates the user's whole config file**. We shipped that for four months. A manual step nobody executes is a manual step nobody tests.
**Rejected the paste-a-prompt fallback because** it turned out to be needed exactly once — the OpenHands **web UI**, whose MCP settings are a database row behind an authenticated API. The agent cannot write that either, so the fallback would not have worked there anyway. A snippet remains for those users.
**Rejected writing Codex's project-local config** even though it outranks global: it only applies to folders the user has marked trusted, and `trust_level` also governs approval policy and sandbox mode. An installer must not widen a user's security posture to win a config convenience.
**Measured after:** 14 of 14 tools wired automatically; zero manual MCP steps outside the OpenHands web UI. Verified by running each installer into a sandbox and reading the config back.

### D32 · The paper's N_QA is 10 per review, not per criterion — and the default stays at 2 anyway — 2026-09-21

**Considered:** re-weight the Q&A budget to match the paper (5 novelty + 5 soundness) / raise the default / leave it
**Chose:** leave it, knowing the number now means something different from what we thought.
**The measurement.** Appendix C gives `C_ScholarPeer ≈ C_fixed + k + N_QA` with `C_fixed ≈ 7`, `k = 3`, `N_QA = 10`, *"approximately 20 calls per paper review"*. So the 10 is a **per-review total**, split across two aspects — novelty and soundness — and only novelty gets the search-enabled answerer. Verified in the PDF, not inferred.
**What we had said was wrong.** `ARCHITECTURE.md` justified our default with *"Ten pairs across every criterion was judged too expensive as a default"* — a 5× overstatement of the paper's cost. And our default is not a discount at all: 2 × 5 criteria = 10, the paper's own number, just spread across criteria like "clarity" that cannot be verified against anything external.
**Kept anyway, and this is the owner's call, made knowingly:** per-criterion Q&A generalises the paper's two fixed aspects to the venue's real criteria, which is a better fit for a tool that reads the actual review form. Re-weighting would buy fidelity to a hyperparameter and lose that.
**Recorded because** an outsider comparing the two will ask why the default is 2 when the paper says 10, and the honest answer — *it is the same total, allocated differently, and we chose the allocation* — is not derivable from the code.

### D33 · The writing rules live in `osp-rules.md`, not in sixteen prompt files — 2026-09-21

**Considered:** fold them into the existing `## Output discipline` / give them their own section built around a concrete test / split them, register into the rules and the context-asymmetry rule into the phase block
**Chose:** the first, on the owner's decision.
**The problem is two problems.** One is register: an LLM writing a review drifts to hedging or buzzwords, and a reviewer's comment has to mean one thing to an author reading English as a second language. The other is sharper — the agent has just read `02_retrieved_literature.md` and the user has not, so it says *"the historian placed the paper in era 3"* and communicates nothing. It overestimates shared context every phase, predictably.
**Why `osp-rules.md`.** It is always-on, ships to every user project, and `merge_agents_md.sh` regenerates the `AGENTS.md` block from it, so one edit reaches all 14 tools. Putting it in the 8 commands and 8 skills would be sixteen copies that drift — the thing M16 had just finished removing.
**Cost accepted:** always-on text is not free. It competes for attention with the brain protocol and the error-vs-empty rule, which prevent actual defects. Three paragraphs was judged the ceiling.
**Evidence it was needed** arrived from the same review that prompted it: nothing anywhere told the user the final review is a draft they sign. The agent handed over a verdict with no context, which is exactly the failure the second rule describes.

---

## Open questions

> Noticed and deliberately not decided. Raised again later, never silently dropped.

| | Question | Raised | State |
|---|---|---|---|
| **O1** | Four commands repeat "The skill writes `<artifact>`" as two consecutive numbered steps (`1-osp-summary` 4–5, `3-osp-historian` 5–6, `4-osp-baseline-scout` 6–7, `6-osp-review` 5–6). Looks like a bad edit synced to all 14 adapters. Cosmetic, or does it cause a double write? | 2026-09-11 | **closed 2026-09-21 (M15)** — a bad edit, confirmed in three of the four files (`1-osp-summary`, `3-osp-historian`, `6-osp-review`; `4-osp-baseline-scout` had already been fixed). Duplicate removed, following steps renumbered, and `completed_at` added where it was required by the rules but never set. |
| **O2** | `6-osp-review.md` prerequisites still require "all `05_qa_<slug>.md` files exist with **10 pairs** each" — stale since D6 made the count configurable. User-visible: the step may refuse a valid session. | 2026-09-11 | **closed 2026-09-21 (M15)** — the whole prerequisite block went; the count is now whatever `qa_pairs_per_criterion` asked for, and a criterion with no pairs is reported, not refused. |
| **O3** | `.brain-template/session.json` never declares `phases.literature.rounds_completed`, which `2-osp-literature.md` reads. Works by defaulting to 0; should the schema declare it? | 2026-09-11 | **closed 2026-09-21 (M15)** — yes. Declared in both initialisers, along with `skip_reason` and a `skipped` status. Verified mechanically: every `phases.*` field the prompts write is now declared, and the template and the `init_brain.sh` fallback are identical in shape. |
| **O4** | Kiro's adapter maps commands to `hooks/` while every other tool uses a commands-like directory (`sync_adapters.py`, `ToolCaps` for `kiro`). Deliberate, or a mistake nobody has run into? | 2026-09-11 | open |
| **O5** | The live end-to-end run on a real paper is marked done (`b8aa4df`) but no artifact records its result. Should a reference run be committed as evidence? | 2026-09-11 | open |
| **O6** | Cascading invalidation — re-running an early phase leaves downstream artifacts stale with no warning (`KNOWN_LIMITATIONS.md` §8). Deferred, not solved. | 2026-09-11 | open |
| **O7** | Drift between `_shared/` and the adapters is caught only when someone remembers to run `--check`. A pre-commit hook or CI job was scoped and deferred. | 2026-09-11 | open |
| **O8** | Antigravity supports *custom* subagent definitions (`.agents/agents/<name>.md`, YAML frontmatter with `tools`, `model`, `commandExecutionPolicy`). Should `osp-answer-generator-agent` ship as a real one there, rather than relying on the host to route a skill? It would tighten the Q&A isolation, but it is a tool-specific artifact type no other adapter has. See D16. | 2026-09-11 | open |
| **O9** | A tool's capability can expire without anyone noticing — Antigravity's did, and OSP shipped the weaker Q&A path for months (D16). Nothing re-checks the capability matrix against vendor docs. Is that worth automating, or is it inherently a human job? | 2026-09-11 | open |
| **O10** | `scripts/test_install.sh` merged throwaway `/tmp` paths into the developer's real global MCP configs on every run, for six installers, since the smoke test was written. Fixed by redirecting `HOME` — but nothing stops the next test harness from doing the same. Should running any `install_*.sh` outside a sandbox be made harder? | 2026-09-11 | open |
| **O11** | Is a persona *skill* reachable through Antigravity's `invoke_subagent`, or does it need a registered definition at `.agents/agents/<name>.md` (O8)? Kiro, Junie, Kimi, Qwen and OpenCode rest on the same skill-as-subagent assumption and nobody has confirmed it on any of them either. **Mitigated, not answered:** D17 made Antigravity try-then-fall-back, so the phase completes either way and the artifact's `Mode:` line records which path ran — reading that line after one real run answers this. | 2026-09-11 | open (mitigated) |
| **O12** | Every provider adds tools, and the whole list ships in every agent request. We are at 15 tools; M12 and M13 could take it past 25. At what point does the list start hurting tool choice more than the extra source helps? Nobody has measured it. | 2026-09-19 | **answered 2026-09-20 by M13.** The number landed at 22 with every database on, and the installer now decides which are registered, so a project carries only what it chose — three databases is 17 tools, one is 3. The underlying question — *where* the list starts hurting choice — is still unmeasured, but it is no longer forced on anyone. See D21, and O17 on the cache the gating made worth adding. |
| **O13** | bioRxiv/medRxiv deferred in D19. They are a feed, not a search engine, but they carry free full text (`jatsxml`), same-day freshness and a preprint-to-journal link (`published`). Worth adding as an explicit "recent preprints" tool once M12 exists? Also: **neither API documents a rate limit**, and a category-filtered month is ~7 calls. | 2026-09-19 | open |
| **O14** | There is still **no deduplication** across providers. The same paper already returns from arXiv, Semantic Scholar and Google Scholar in three different shapes, and M12/M13 add more sources. `refactor/migrate-mcp-to-scripts` already has a normalised cross-provider record shape that would fix it. Should that land before or with M13? | 2026-09-19 | open |
| **O15** | `mcp-server/requirements.txt` had no upper bound on `mcp`, so a fresh install resolved to **mcp 2.2.0**, which deleted `mcp.server.fastmcp` and renamed `FastMCP` to `MCPServer`. The server could not import at all — reproduced in an empty virtualenv on 2026-09-20 and fixed by pinning `mcp<2.0`. Migrating to `MCPServer` is the real answer and has not been done. Until it is, that ceiling is load-bearing. Related: B11 predicted exactly this for `arxiv` and nobody thought to check `mcp`, which is O9 wearing different clothes. | 2026-09-20 | open |
| **O16** | Full text is read in windows, and a window boundary is chosen by text alone — snapped back to the nearest paragraph break. That stops a number being cut in half, but it still cuts sections in half. Returning whole sections was considered and rejected because a Methods section routinely exceeds any sensible `max_chars`, so a character cap is still needed as a backstop. Is there a better unit than either? | 2026-09-20 | open |
| **O17** | `read_arxiv_paper` keeps a two-entry cache of parsed paper text so that paging does not re-download the tarball for every window. That is process state, justified the same way as the shared HTTP client under D3 — it changes when an answer arrives, never what it is. But it is the first cache in the server, and nobody has decided whether that is a pattern or an exception. | 2026-09-20 | open |
| **O18** | The live provider script is the only thing that exercises `mcp-server/providers/`, and it depends on APIs that were unreachable for much of 2026-09-20 — Semantic Scholar refused connections, Google Scholar stopped answering, OpenAlex timed out. The `sort` defect survived M11 review for exactly that reason. `--strict` and the "NOTHING WAS PROVED" banner make a hollow run visible, but nothing *re-runs* it later. Recorded HTTP fixtures would close the gap; they would also go stale. Unresolved. **2026-09-21:** OpenAlex now verified live — 6 checks, including a known retracted DOI flagged `isRetracted=True` and a nonsense DOI raising rather than returning empty. **Semantic Scholar has now rate-limited this machine on two consecutive days**, so its data path has never once been proved; only its 429 path has. | 2026-09-20 | open |
| **O19** | Both installer menus corrupt below about 78 terminal columns: the frame wraps, so `drawn` under-counts and each redraw leaves another copy of the title behind. `hr()` already caps at 78, so the installer quietly assumes an 80-column terminal. Measured 2026-09-20 by bisection — tools menu smears at ≤76 columns, databases at ≤77. Pre-existing, layout 0 only, and every height was tested but no narrow width was. Should the menus measure width the way they already measure height? | 2026-09-20 | open |
| **O22** | **OpenAlex moved to pay-as-you-go**, found while sourcing the README's rate limits on 2026-09-21. Keyless is **$0.10/day ≈ 100 calls**; a free key gives $1/day ≈ 1,000. Every response carries `cost_usd` (measured: 0.001 for a one-result search). Our recorded figures — "100,000 calls/day" and "~10 searches a day" — were both wrong. MANIFESTO rule 1 says no source may require a subscription and that a key only lifts a rate limit; a hundred calls a day is close enough to the edge of "works without a key" to be worth deciding deliberately rather than by default. Also: the `mailto` polite pool is no longer documented anywhere, though `providers/openalex.py:59-61` still sends it. Keep OpenAlex ticked by default, demote it, or require the free key? | 2026-09-21 | open |
| **O21** | `/0-osp-onboarding` pre-scaffolds `05_qa_<slug>.md` for every criterion, so a file's existence says nothing about whether its Q&A ran. That defeated **both** of the reviewer's completeness tests at once (2026-09-21, found by outside review). Patched by reading `criteria_progress` instead — but pre-scaffolding an empty artifact is a trap any future check will fall into the same way. Should onboarding stop creating them, or should every artifact carry a "filled" marker? | 2026-09-21 | open |
| **O20** | A malformed arXiv query — a dangling operator, an unbalanced paren — is wrapped in parentheses and sent as-is. arXiv answers 400, and the package retries a deterministic failure three times: **4 requests and 10.2 s**, all of it holding the single connection arXiv's terms allow. With `_LOCK_WAIT` at 15 s, two of these in flight make a legitimate concurrent call fail with `ArxivBusy`. Measured 2026-09-20. Validating arbitrary arXiv query syntax ahead of the call is its own can of worms, and the package gives no clean way to skip a retry for a 400. Left open rather than half-fixed. | 2026-09-20 | open |

---

> **← Previous:** none.
> **Next →** none yet.
