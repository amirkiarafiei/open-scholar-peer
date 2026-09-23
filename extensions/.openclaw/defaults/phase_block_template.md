# Phase block — the one format every phase prints

Two blocks per phase, built from the same rail: an **opening** block before you do
any work, and a **closing** block once the artifact is written. This file is the
only definition. Do not invent a variant, and do not add a third block.

## The rail

Seven markers, one per phase, always in this order:

`onboarding · summary · literature · historian · baseline_scout · qa · review`

It prints on a line of its own, directly under the top rule, labelled `PROGRESS`.
The top rule carries the phase label and nothing else.

| Marker | Means |
|---|---|
| `●` | done |
| `◐` | running now, **or finished deliberately short** — the user stopped early |
| `○` | not started, or skipped outright |

`◐` is how "you may move on" becomes visible without a sentence. A phase the user
skipped entirely keeps `○` and is named on the `NOTE` line instead.

**Which marker goes where.** Position comes from the command you are running; state
comes from `session.json`, never from the page you read the values on.

| # | Phase | Command | Opening rail | Closing rail |
|---|---|---|---|---|
| 1 | `onboarding` | `/0-osp-onboarding` | `◐──○──○──○──○──○──○` | `●──○──○──○──○──○──○` |
| 2 | `summary` | `/1-osp-summary` | `●──◐──○──○──○──○──○` | `●──●──○──○──○──○──○` |
| 3 | `literature` | `/2-osp-literature` | `●──●──◐──○──○──○──○` | `●──●──◐──○──○──○──○` while rounds remain, `●` once the user moves on |
| 4 | `historian` | `/3-osp-historian` | `●──●──●──◐──○──○──○` | `●──●──●──●──○──○──○` |
| 5 | `baseline_scout` | `/4-osp-baseline-scout` | `●──●──●──●──◐──○──○` | `●──●──●──●──●──○──○` |
| 6 | `qa` | `/5-osp-qa` | `●──●──●──●──●──◐──○` | `●──●──●──●──●──●──○` |
| 7 | `review` | `/6-osp-review` | `●──●──●──●──●──●──◐` | `●──●──●──●──●──●──●` |

A phase that is `skipped` or `pending` in `session.json` shows `○` wherever it appears,
even if a later phase has already run. The rail tells the truth, not the plan.

**ASCII fallback.** Use it when the user asks for it, when `LANG`/`LC_ALL` does not
contain `UTF-8`, or when you can see mojibake in your own earlier output. Otherwise
use the box-drawing form. Decide once at the start of a session and do not switch.

| Unicode | ASCII |
|---|---|
| `●` `◐` `○` | `[x]` `[~]` `[ ]` |
| `──` between markers | `-` |
| `─` in the rules | `-` |
| `—` (em dash) | `--` |
| `·` (middle dot) | `\|` |

The ASCII rail is 27 columns against the Unicode rail's 19. On its own line that
costs the label nothing: the `PROGRESS` line is 38 columns in ASCII against 30 in
Unicode, and both sit well inside 60. The top rule holds the label alone — up to
55 columns before it runs out of rule to pad with. The longest label in use,
`LITERATURE  round 2 of 3`, is 24.

## Opening block

```
── LITERATURE  round 2 of 3 ────────────────────────────────
  PROGRESS ●──●──◐──○──○──○──○
  DOING    retrieve the live reference frame C_dynamic
  READS    .brain/raw/01_structured_summary.md
  WRITES   .brain/raw/02b_literature_round2.md
  COST     ~3 min, ~12 tool calls
────────────────────────────────────────────────────────────
```

## Closing block

```
── LITERATURE  2 rounds ────────────────────────────────────
  PROGRESS ●──●──◐──○──○──○──○
  DONE     41 papers retained, 12 excluded
           .brain/raw/02_retrieved_literature.md
  BLOCKED  google_scholar — blocked (429), nothing was searched
  NOTE     stopped at round 2 of 3, by choice
  NEXT     /2-osp-literature   run round 3  (recommended)
           /3-osp-historian    move on with what you have
────────────────────────────────────────────────────────────
```

## The labels

Use only these, in this order. **Omit any label with nothing to say** — an empty
label is noise, and most blocks will have no `BLOCKED` or `NOTE` line at all.

| Label | Block | What goes on it |
|---|---|---|
| `PROGRESS` | both | the rail. The one label that is never omitted |
| `DOING` | opening | one line: what this phase is for |
| `READS` | opening | the inputs you actually have. `— none` when there are none |
| `WRITES` | opening | the file this phase will write |
| `COST` | opening | rough time and tool calls |
| `DONE` | closing | what was produced, with counts. The artifact path goes on the next line, indented to the value column |
| `BLOCKED` | closing | one line per provider that failed, named, with the reason from the error record |
| `NOTE` | closing | what the user chose that a later reader must know — a skipped phase, a round not run, a check that could not be made |
| `NEXT` | closing | the recommended command first, alternatives indented under it |
| `YOURS` | closing, `/6-osp-review` only | that the review is a draft the user owns, edits and signs. OSP does not submit reviews and does not decide |

## Rules

1. **`BLOCKED` is never folded into prose.** A provider that failed gets its own
   line. An empty list means the search ran and matched nothing; an error means it
   never ran. Reporting the second as the first is a lie about the corpus.
2. **`NEXT` offers, it does not command.** Where the user has a choice, show both
   routes: recommended first, the alternative under it.
3. **Say what a skip costs once** — here, and in the artifact's Provenance. Never
   twice in the same block, and never as a warning banner.
4. **Legible raw.** Not every tool renders markdown. No bold, no links, no nested
   tables inside the block.
5. **Width.** Pad both rules to 60 columns. Keep the phase label short: the top
   rule must not pass 72 columns, and neither may any content line.
6. **Alignment.** Two spaces, the label, then spaces to column 12 for the value.
   Continuation lines start at column 12 with no label. The rail is a value like
   any other: `PROGRESS` is eight characters, so one space puts it at column 12.
