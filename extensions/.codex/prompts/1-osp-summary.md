---
description: "OSP Phase 1: Internal Compression — extract claims, method, evidence"
reads: [".brain/session.json", ".brain/input/paper.{pdf,md}"]
writes: [".brain/raw/01_structured_summary.md", ".brain/session.json"]
---

# /1-osp-summary — Internal Compression

Extracts the paper's claims, method, and evidence into a structured summary Ŝ that downstream personas rely on.

## Activation

Invoke the `osp-summary-agent` skill. The agent assumes the Summary Agent persona and follows that skill's protocol exactly.

## Inputs — none of these is a gate

- `phases.onboarding.status == "completed"` in `session.json`. If onboarding was skipped you have no
  venue and no review guidelines; extract the summary anyway, and record under `NOTE` and in Provenance
  that the venue is unknown. Mention `/0-osp-onboarding` once. Do not insist, and do not refuse.

## The one thing that cannot be worked around

Every other input in this protocol is optional. This one is not: with no readable text of the paper there
is nothing to review, so this guard stops — and it is the only place in Open ScholarPeer that does.

PDF/DOCX/TEX in `.brain/input/` is not enough on its own; a binary path handed to the agent is the
single biggest cause of silent downstream failure.

Before activating the skill, verify in this order:

1. **`.brain/input/paper.md` exists and is readable** — ideal case, proceed.
2. **`.brain/input/paper.md` is missing but a PDF/DOCX exists** — try to convert it now using the `markitdown` MCP tool (`convert_to_markdown`). Save the result to `.brain/input/paper.md`. Update `session.json.paper.parsed_path`.
3. **`markitdown` MCP is unavailable AND only a PDF/DOCX is present** — stop here, and say why in one
   line: there is no readable text to summarise. Print:
   > Paper at `.brain/input/<file>` is in a binary format and `markitdown` MCP is not available. Either:
   >   (a) install markitdown — `uvx markitdown-mcp --help` confirms it is fetchable; plain
   >       `uvx markitdown-mcp` starts the server and waits, which looks like a hang — or
   >   (b) convert the paper manually and place the markdown at `.brain/input/paper.md`, or
   >   (c) if your host tool reads this format natively (Claude Code reads PDFs, for one), read it
   >       yourself, write the extracted text to `.brain/input/paper.md`, and re-run.
4. **Nothing in `.brain/input/`** — stop here too; there is no paper. Point at `/0-osp-onboarding`,
   which will help locate it.

Do NOT silently proceed with a PDF path on the assumption that the host tool will handle it. Even if it can, the conversion result becomes part of the audit trail and must be in `.brain/input/paper.md`.

## Opening block (print before step 1)

Render the **opening block** exactly as `.codex/defaults/phase_block_template.md` defines it — that
file holds the rail, the rules and the widths, and it is the only place they are written down.
This is phase **2 of 7** (`summary`); read the rail's state from `session.json`. Values:

      DOING    compress the paper into claims and evidence
      READS    .brain/input/paper.md
      WRITES   .brain/raw/01_structured_summary.md
      COST     ~2 min, no external calls

## Steps

1. Run the hard input guard above.
2. Read `.brain/session.json` and `.brain/input/paper.md` (the validated markdown produced or verified by the guard).
3. Activate the `osp-summary-agent` skill — it owns the extraction protocol (claims, method, evidence) and the output format.
4. The skill writes `.brain/raw/01_structured_summary.md`.
5. The skill updates `session.json`:
   - `phases.summary.status = "completed"`
   - `phases.summary.completed_at = <now>`
   - `phases.summary.notes = "<N> claims, <M> evidence items, method identified"`
   - `resume_from = "literature"`

## Closing block (print when the phase ends)

Render the **closing block** from `.codex/defaults/phase_block_template.md`. **Build the rail from
`session.json`** — `●` only where `status == "completed"`, `○` for `pending` *and* `skipped`. A
phase the user skipped must not show as done.
Drop `BLOCKED` and `NOTE` when there is nothing to put on them. Values:

      DONE     <N> claims, <M> evidence items, method identified
               .brain/raw/01_structured_summary.md
      NEXT     /2-osp-literature   retrieve prior work


## Re-run behavior

If `phases.summary.status == "completed"`, warn the user once that re-running will overwrite, then proceed.
