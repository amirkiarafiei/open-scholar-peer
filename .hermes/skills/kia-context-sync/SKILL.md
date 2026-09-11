---
name: kia-context-sync
description: Brings the kiacontext files back in line with the project after work has happened — updates PROGRESS, adds any decision that earned an entry to BRAINSTORM, corrects the specs where the build moved past them, refreshes INDEX and the frontmatter dates, and checks the seven document rules. Use when the context files have fallen behind, before a handover, or to close out a working session.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# kia-context-sync — catch the context up

The agent is supposed to keep these files current as it works. This is for when it did not, or when
somebody wants a deliberate pass before handing the project over.

## Step 1 — find the gap

```bash
git log --oneline --no-merges -30
git log -1 --format=%ad -- kia-context/      # when the context last moved
git diff --stat HEAD~10..HEAD -- . ':!kia-context' ':!docs'
```

Compare what the code did against what the files say happened. The gap is the work.

## Step 2 — update the logs

**`logs/PROGRESS.md`** — tick the deliverables that are genuinely done, and write the Report for any
milestone that closed. Verify against the acceptance criteria; do not tick on the strength of a commit
message. If something is half-finished, say so rather than ticking it.

**`logs/BRAINSTORM.md`** — apply the entry test before writing anything:

> **An entry earns its place when an alternative was rejected, or when a measurement changed our minds.**

Most of what happened does not qualify. A bug fix is not a decision. A refactor with no choice in it is
not a decision. If nothing in this window qualifies, **write nothing** — that is the correct outcome, not
a failure of the pass.

## Step 3 — correct the specs where the build moved past them

Only where they are now **wrong**, not merely thin.

- `ARCHITECTURE.md` — did the stack, the layout or a structural fact change?
- `DESIGN.md` — did tokens or components change in the interface but not here?
- `MANIFESTO.md` — a rule almost never changes. If one did, it was a decision, so it needs a
  `BRAINSTORM.md` entry too. **Never renumber.**

## Step 4 — the seven rules

Walk them. Each one fails silently, which is why they need a deliberate check.

1. **Nothing renumbered.** Milestone, decision and rule numbers are permanent.
2. **No dead references.** If anything was renamed or moved, grep the old name:
   `grep -rn "OldName" . --exclude-dir=node_modules --exclude-dir=.git`
3. **No rule stated in two files.** One states it, the rest link to it.
4. **Nothing appended to a file whose `status:` is `closed`.**
5. **`INDEX.md` still matches what the files actually contain.** If it disagrees, the index is the bug.
6. **Frontmatter is current** — `covers`, `status` and `last_updated` on every file you touched.
7. **Every number is measured.** Re-run the command behind any count you carry forward, or drop it.

## Step 5 — should anything be split?

A log that has passed a phase boundary, or roughly 1,500 lines, or has simply stopped being readable.
If so: open `NAME_2.md`, continue the numbering, set the old part to `closed`, and put the next/previous
block at the top and bottom of both parts. Raise it with the human rather than splitting unasked.

## Step 6 — report

A short list: what you updated, what you deliberately left alone, and anything that needs a human — a
decision whose reasoning you could not recover, a rule the code now contradicts, an acceptance criterion
that no longer makes sense.

**Say plainly if nothing needed changing.** A sync pass that writes nothing is a good outcome.
