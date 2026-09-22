---
name: osp-rules
description: Always-on rules for Open ScholarPeer review sessions
---

# Open ScholarPeer — Always-On Rules

These rules apply automatically in any project where Open ScholarPeer is installed.

## Brain protocol (apply on every invocation)

1. **Read `.brain/session.json` first** to understand current state.
2. **Load only the artifacts in the active step's `reads:` contract.** Do not load the full `.brain/`
   directory. A listed artifact that is missing is an input you do not have — **not** a reason to stop.
3. **Update `session.json` around every step.** Set `started_at` when you begin. On finishing, set the
   matching `phases.<name>` block to `completed`, set `completed_at`, and update `resume_from`.
4. **When the user moves past a step without running it, record that.** Set that phase's `status` to
   `"skipped"` and its `skip_reason` to what they told you, or to `"user moved on"` if they said nothing.
   Do this the moment you start the *later* phase — a skip nobody wrote down is a silent degradation, and
   MANIFESTO rule 8 forbids those. The four permitted values are `pending`, `in_progress`, `completed`
   and `skipped`.
5. **Carry every skip forward.** Name it in the artifact's `## Provenance` and say what it cost **this**
   phase — not what it cost an earlier one, which has already been said where it belonged. Each phase
   reports its own consequence, once. `/6-osp-review` collects them all under
   `## What this review did not have`, so whoever reads the review can tell a thin corpus from a
   thorough one. State it; do not repeat it, and never dress it as a warning.
6. **Re-runs overwrite with a warning.** If a step is already `completed`, print one warning, then proceed.

## Persona discipline

- Each numbered command (`/N-osp-*`) activates exactly one persona skill (`osp-<name>-agent`). Do not blend personas.
- The Q&A engine (`/5-osp-qa`) uses two personas at once: Query Agent (main thread) and Answer Generator (subagent, or self-reflection on tools that lack subagents).
- The orchestrator (`osp-orchestrator`) never performs review work — it only routes.

## Subagent vs self-reflection

- **Prefer subagents** for the Q&A engine wherever they are available. The `/5-osp-qa` command opens with a banner saying which mode this tool uses; that banner is generated from the tool's measured capability, so it is the authority, not any list.
- **Fall back to self-reflection** with strict turn markers (`=== Query Agent === ... === END === === Answer Generator === ...`) where subagents are unavailable, and on any tool where the delegation call does not work. Finishing the phase in the weaker mode beats stopping it; note which mode was used in the artifact.
- Self-reflection is a documented weaker substitute. See `KNOWN_LIMITATIONS.md`.

## Phase blocks (required on every phase invocation)

Every phase prints two blocks: an opening one before it does any work, and a closing one when it
ends. **`.cline/defaults/phase_block_template.md` is the only definition of their format** — the rail, the
rules, the labels, the widths and the ASCII fallback all live there and nowhere else. Do not restate
them, here or in a command.

Each phase's command supplies only the values. The closing block must say **what was done** —
findings, counts, highlights — not merely which command comes next. The user is learning the system
as they go, so orient them every time, including on a re-run.

## Reaching the search tools

OSP ships the search tools two ways: as MCP tools, and as a program you run
through `bash`. **MCP is the default. The shell program is the fallback and is
second class** — it costs a process per call, and an approval on hosts that ask
for one.

`/0-osp-onboarding` decides which one this project uses and records it in
`session.json` as `mcp.interface`. Follow what is recorded. If the field is
missing — the project was set up before this existed — decide it yourself, the
same way, and write it.

**One `.env` governs both surfaces**, so the shell program never has a database
MCP lacks. A missing tool is never a reason to change interface.

**If a search fails while the recorded interface is `mcp`, re-probe once and
rewrite the field before you report a gap.** A server that died mid-session
leaves `mcp` recorded, and a server nobody can reach looks exactly like a
database with nothing in it. That is the one confusion this whole layer exists
to prevent.

`.cline/defaults/search_via_cli.md` holds the commands, the `batch` form to prefer, and
what each failure reason means. Read it when the interface is `cli`, or when you
fall back.

## Output discipline

- Every `.brain/raw/*.md` file uses the universal artifact structure: `## Method`, `## Output`, `## Provenance`.
- Reports describe what was done — they are not raw transcripts of tool calls.
- Citations must trace back to retrieved literature; do not invent them.

**Write in plain academic English.** Clarity is not a stylistic preference in research; a reviewer's
comment has to mean one thing to an author anywhere in the world. Prefer the shorter word and the
direct sentence. Define a term the first time a file uses it. Keep the field's vocabulary — it carries
meaning — and drop everything that does not: no buzzwords, no marketing register, no hedging that
conceals what you actually found. This applies to the artifacts and to what you say on screen.

**Assume the user has not read what you wrote.** They see your messages; they have almost never opened
the files in `.brain/`. So whenever you name an artifact, a phase or a finding, say in the same breath
what it is and why it matters. "The historian placed the paper in era 3" tells them nothing. "Your
paper sits in the current era, alongside the three 2025 works it competes with" tells them something.
Give the background, once, and then get to the point.

**Retrieval is what makes this a grounded review, so be transparent about it.** Searching live sources
is what separates this from a model answering out of memory. Native web search and at least one
literature database should be available, and you should say so plainly when they are not — name what
is missing and what it costs this phase. **Then carry on if the user wants to.** Retrieval is required
for a strong review, not required to proceed: the user decides, and the artifact records what they
decided.

## File references in user-facing output

- When mentioning a `.brain/` artifact in a report or reply, use whatever file-reference syntax your own tool provides — `@.brain/raw/01_summary.md` on most, `#file:.brain/raw/01_summary.md` on Copilot CLI. Where a tool has none, write the plain path.
- Always pair the native reference with the plain `.brain/…` path on the continuation line under `DONE`, so users can locate the file whatever their tool does with markdown.

## File ownership

- `.brain/` is gitignored — never commit it.
- `.open-scholar-peer/` (MCP server + venv) is gitignored — never commit it.
- Tool-specific config files (`.mcp.json`, `.claude/`, etc.) at project root are user-editable.
- Adapter content under `extensions/.{tool}/` in this repo is **generated by the sync script** — edit `extensions/_shared/` instead and re-run `scripts/sync_adapters.py`.
