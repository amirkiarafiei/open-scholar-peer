---
description: "OSP Phase 0: Venue lookup, paper detection, criteria scaffolding"
reads: [".brain/session.json"]
writes: [".brain/raw/00_review_guidelines.md", ".brain/raw/05_qa_<slug>.md (per criterion)", ".brain/session.json (incl. mcp.interface)"]
---

# /0-osp-onboarding — Stage 0: Onboarding

Prepares the review environment. Recommended first — every later phase runs without it, on generic
criteria and with no venue.

## Activation

Invoke the `osp-orchestrator` skill (no domain persona needed for this step).

## Opening block (print before step 1)

Render the **opening block** exactly as `defaults/phase_block_template.md` defines it — that
file holds the rail, the rules and the widths, and it is the only place they are written down.
This is phase **1 of 7** (`onboarding`); read the rail's state from `session.json`. Values:

      DOING    set the venue, find the paper, scaffold criteria
      READS    .brain/input/   whatever you put there
      WRITES   .brain/raw/00_review_guidelines.md
               .brain/session.json
      COST     ~1 min, one web search

## Steps

### 1. Read session state

- Read `.brain/session.json`. If it is missing, write it yourself from the v2 schema and carry on —
  the installer's scripts are not kept in the user's project, so do not send them looking for one.
- If `phases.onboarding.status == "completed"` and `qa_criteria` is non-empty, ask the user whether to re-run (which would overwrite `00_review_guidelines.md` and any pre-scaffolded `05_qa_*.md` files). If they decline, exit.

### 2. Locate the paper and ensure a readable text version

- Check `.brain/input/` for a paper file. Common extensions: `.pdf`, `.md`, `.tex`, `.docx`.
- If empty, look in the project root as well — the installer tells the user to put the paper there.
  Ignore `README`, `AGENTS`, `CLAUDE` and similar. Show what you found and ask them to confirm.
- Whenever the user points at a file, wherever it is, **copy it into `.brain/input/` yourself.** The
  same applies to any supporting material they offer later. Never ask them to move a file by hand.
- **Always produce `.brain/input/paper.md`** (the canonical readable form):
  - If the original is `.md`, ensure it's named `paper.md` (rename if necessary).
  - If the original is `.pdf` / `.docx` / `.tex`, attempt conversion with the `markitdown` MCP tool (`convert_to_markdown`). Save output to `.brain/input/paper.md`.
  - If `markitdown` is unavailable, **do not silently advance**. A readable paper is the one input the
    protocol cannot work around. Tell the user so, and offer two routes: (a) install markitdown
    (`uvx markitdown-mcp --help` confirms it is fetchable), or (b) hand over a markdown conversion of
    their own. Wait for one of them.
    This and the same guard in `/1-osp-summary` are the **only** two places in Open ScholarPeer that
    stop. Everything else recommends and carries on.
- Save `paper.path` (original) and `paper.parsed_path` (the canonical `.brain/input/paper.md`) into `session.json`.

### 2b. Record the paper's identifier and its cutoff date

Two fields, asked together, in one short exchange. Both matter later, and neither can be recovered
afterwards.

- **`paper.id`** — a DOI, an arXiv id, or a URL; whichever the user has. Take one, do not ask for
  several. If the paper has none — an unpublished manuscript under review is the normal case — write
  `"unpublished"` and move on.
- **`paper.cutoff_date`** (`YYYY-MM-DD`) — the date the paper was submitted. **Prior art is judged as of
  this date.** Propose a default and let them correct it: the arXiv v1 date if you can see one,
  otherwise today. Say in one line why it matters: *work published after this date was not available to
  the authors, so it cannot count as a missing citation.*

### 2c. Decide how you reach the search tools, and write it down

Do this once, here, and record the answer. Every later phase follows it instead
of working it out again.

**Do not try to answer this by looking at your own tool list.** Hosts disagree
about what a crashed server looks like, a tool list can be a snapshot taken at
start-up, and this project may have switched some databases off — so a tool
being absent proves nothing. Use these checks, in order:

1. **Is `.open-scholar-peer/mcp/osp_cli.py` on disk?** If not, OSP's search
   layer was never installed. Record `none`, tell the user in one line, and
   carry on — the protocol still runs, on your own knowledge and web search.
2. **Call one OSP search tool.** If it answers, record `mcp` and stop here.
3. **Otherwise the shell is the fallback — but first check the shell can reach
   the network**, because some hosts allow no outbound traffic from `bash`:

   ```bash
   python3 -c "import urllib.request as u;u.urlopen('https://api.openalex.org/works?per-page=1',timeout=5).read(1);print('NET_OK')" 2>/dev/null || echo NET_BLOCKED
   ```

   `NET_OK` → record `cli`. `NET_BLOCKED` → record `none` and **say so plainly**:
   this host cannot reach the paper databases from the shell. A blocked shell
   that goes unreported becomes an empty corpus that reads like a complete one.

Write the answer to `session.json` at `mcp.interface`. Then confirm it in one
line, for example *"Search: MCP (22 tools)"* or *"Search: shell fallback"*.

### 3. Identify the venue

- **Always ask the user explicitly**, even if the paper's title page, header, or metadata already shows a venue. Do not auto-fill from the paper.
- Use your tool's native ask/input mechanism if one is available (e.g. ask_user, an interactive prompt, or a confirmation dialog). If no native ask exists, print the question and wait for a reply.
- **If the user declines to name one, take `"unspecified"` and move on** with the generic criteria. A venue sharpens the review; it is not required to produce one.
- Ask: "Which venue or journal are you reviewing for? (e.g. ICLR 2026, NeurIPS 2025, Nature Machine Intelligence, arXiv-only)"
- If the paper appears to list a venue, show what you found and ask the user to confirm or correct it: "The paper mentions [venue]. Is that the submission venue you want to review against, or a different one?"
- Save `venue.name` and `venue.year` to `session.json`.

### 4. Retrieve venue review guidelines (fallback chain)

Try in order, stop at the first that succeeds:

1. **Web search** for the venue's official review form / reviewer instructions / scoring rubric. Use queries like `"<venue> <year> reviewer guidelines"`, `"<venue> review form"`, `"<venue> reviewer checklist"`.
2. **Ask the user** to paste guidelines if web search came up empty or returned irrelevant content.
3. **Generic fallback:** copy `defaults/generic_review_guidelines.md` into `.brain/raw/00_review_guidelines.md`.

Set `venue.criteria_source` in `session.json` to `"web"`, `"user"`, or `"generic"` accordingly. Set `venue.source_url` if web-sourced.

### 5. Write `00_review_guidelines.md`

Write the retrieved/provided/generic guidelines to `.brain/raw/00_review_guidelines.md` using the universal artifact structure (Method / Output / Provenance):

- **Method:** how the guidelines were sourced (web search query, user paste, generic fallback).
- **Output:** the actual guidelines content. Include the venue's scoring rubric, the required review sections, and the criteria the venue uses.
- **Provenance:** source URL or "user-provided" or "generic fallback".

### 6. Extract criteria and populate `qa_criteria[]`

Parse the guidelines to extract the evaluation criteria. Each criterion becomes an entry in `session.json.qa_criteria`:

```json
{
  "slug": "novelty",
  "label": "Novelty & Originality",
  "definition": "<one-paragraph definition from the guidelines>"
}
```

If the venue uses 7 criteria, you produce 7 entries. If 3, you produce 3. The number is venue-driven, not fixed.

### 7. Pre-scaffold empty Q&A files

For each criterion in `qa_criteria[]`, create `.brain/raw/05_qa_<slug>.md` from the template at `defaults/qa_pair_template.md` (or the synced equivalent). Pre-fill:
- The criterion label and definition in the header
- Empty `### Q1` … `### Q<N>` placeholders where N = `qa_pairs_per_criterion` (from session.json, default 2)

This is a **structural nudge**: when the Query Agent runs in Phase 5, the empty file is already on disk, signaling the required pair count.

### 8. Update `session.json`

- `phases.onboarding.status = "completed"`
- `phases.onboarding.completed_at = <now ISO 8601 UTC>`
- `phases.onboarding.notes = "Venue: <name>; criteria: <N>; paper: <path>; guidelines source: <web|user|generic>; search: <mcp|cli|none>"`
- `mcp.interface = "<mcp|cli|none>"` from step 2c, if not already written
- `resume_from = "summary"`

## Closing block (print when the phase ends)

Render the **closing block** from `defaults/phase_block_template.md`. **Build the rail from
`session.json`** — `●` only where `status == "completed"`, `○` for `pending` *and* `skipped`. A
phase the user skipped must not show as done.
Drop `BLOCKED` and `NOTE` when there is nothing to put on them. Values:

      DONE     venue <name>, <N> criteria, guidelines <source>
               paper found, readable text confirmed
               .brain/raw/00_review_guidelines.md
               .brain/raw/05_qa_<slug>.md   (<N> pairs each)
               .brain/session.json
      BLOCKED  web search for the venue's form — <reason>
      NEXT     /1-osp-summary   compress the paper

