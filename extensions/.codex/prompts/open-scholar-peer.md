---
description: "Open ScholarPeer dispatcher — show review status and route to the next command"
reads: [".brain/session.json"]
writes: []
---

# /open-scholar-peer — Stateless Dispatcher

This command is **always available**. It reads `.brain/session.json` and tells the user where they are in the review and which command to run next. It never executes review work itself.

## Activation

Invoke the `osp-orchestrator` skill.

## Steps

1. **Read `.brain/session.json`.** If it is missing, OSP is not initialised here. Two cases, and
   neither should send the user hunting for a script that is not in their project:
   - `.brain/` is absent as well — have them re-run the installer from this directory; it merges with
     their existing config rather than replacing it.
   - `.brain/` exists but the file does not — write it from the v2 schema yourself, then carry on.

2. **Print the status block** defined in `.codex/defaults/phase_block_template.md`, labelled
   `OPEN SCHOLARPEER`. The rail is the whole point here — it answers "where am I" with no words.
   Values:

       STEPS    onboard·summary·lit·history·baseline·qa·review
       VENUE    <name>   ·   <N> criteria
       PAPER    <path, or "not yet loaded">
       NOTE     literature stopped at round 2 of 3, by choice
       NEXT     /3-osp-historian   the narrative  (recommended)
                /5-osp-qa           skip ahead

   `NOTE` lists every phase whose `status` is `skipped`, plus any round or criterion left short;
   drop the label when there are none. `NEXT` recommends first, then offers.

3. **Route based on `resume_from`:**

   | `resume_from` | Tell user to run | Description |
   |---|---|---|
   | `onboarding` | `/0-osp-onboarding` | Set venue, locate paper, scaffold criteria |
   | `summary` | `/1-osp-summary` | Internal Compression — claims/method/evidence |
   | `literature` | `/2-osp-literature` | External retrieval, up to 3 rounds — the user chooses |
   | `historian` | `/3-osp-historian` | Build the chronological domain narrative |
   | `baseline_scout` | `/4-osp-baseline-scout` | Find missing baselines & datasets |
   | `qa` | `/5-osp-qa` | Multi-aspect Q&A (loops over criteria) |
   | `review` | `/6-osp-review` | Final consolidated review |
   | `completed` | — | Print location of `.brain/review/final_review.md` and ask if any phase needs a re-run |

4. **Do NOT advance automatically.** Phase boundaries are intentional — they let the user inspect each
   artifact before continuing.
5. **Recommend; never refuse.** The order below is the recommended one, not a lock. If the user asks for
   a phase whose inputs are missing, say in one line what it will be missing and route them to it.

## Output

This command produces no artifact and does not modify `session.json`. It is purely informational.
