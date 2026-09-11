<!-- kiacontext:begin -->

## kiacontext — this project's memory. Read this before you start work.

This repository carries a folder called `kia-context/`. It is a small set of Markdown files holding what a
reader of the code cannot see: what is being built right now, what was already decided and why, what was
tried and rejected, and what must never change. The layout is a reusable harness called **kiacontext**;
everything inside it is specific to this project.

> ### 👉 Start by reading `kia-context/INDEX.md`.
>
> It is the map of every other file — one minute of reading, and nothing below makes proper sense
> without it. **Read it before your first substantial action in a session**, not when you get stuck.

**Why this exists.** You start every session with no memory of the last one. The code can tell you *what*
the system does; it can never tell you *why* it is that way, what was already attempted and abandoned, or
which awkward-looking part is deliberate and must not be "improved". Without that, settled arguments get
re-run, decisions get quietly reversed, and work is redone. These files are the part of the project that
survives between sessions.

**They are authoritative.** Where the code and a spec disagree, that is a finding to raise with the
human — not a document to ignore.

**You write these files. The human decides what goes in them.** Every file under `kia-context/` is written
by an agent, out of a conversation — nobody maintains them by hand. Your job is to keep them true.

**How to use them.**

- **Before proposing or building anything:** `specs/MANIFESTO.md` for the boundary you may not cross, and
  the active `logs/BRAINSTORM.md` to check whether your idea was already considered and rejected.
- **Before touching anything structural:** `specs/ARCHITECTURE.md`.
- **Every session:** `logs/PROGRESS.md` holds the current milestone, its deliverables and their
  acceptance criteria — what is being built, and how far it got. How to work through it is written in
  that file, not here.
- **Every file states its own terms.** Its frontmatter says how binding it is, who may write to it,
  whether it is still active, and — in the description — what does *not* belong in it. Read that before
  editing; it beats guessing from the filename.
- **The body of a file is yours; its frontmatter is not.** Every heading, table and section you find in
  these files is a starting suggestion — reshape any of it to fit the project, and delete what does not
  apply rather than leaving it empty. The six frontmatter fields are the exception: they are what make a
  file part of kiacontext, so keep all six on every file and keep their values current.
- **Writing back is part of the work, not an afterthought.** A session that changes the project and
  leaves these files untouched has thrown away everything it learned.

### The layout

Four levels under `kia-context/`, split by **authority**, not by topic.

| | Path | Who writes | What it is |
|---|---|---|---|
| **Map** | `kia-context/INDEX.md` | agent, when files move | What exists, and what points at what |
| **0** | `kia-context/genesis/` | agent, at t=0 | Where this came from. `SEED.md`, `GENESIS.md` |
| **1–2** | `kia-context/specs/` | agent, when explicitly refactoring | The law. `MANIFESTO.md`, `ARCHITECTURE.md`, `DESIGN.md` |
| **3** | `kia-context/logs/` | agent, every session | State. `PROGRESS.md`, `BRAINSTORM.md` |

`docs/` is a different thing entirely: human-facing artifacts, written **only when a human asks for one**.
Agents do not maintain them and do not need to read them to do the work.

**Where a finding goes.** The reasoning into `BRAINSTORM.md` as a numbered decision. The work into
`PROGRESS.md`. A resulting rule goes into `MANIFESTO.md` **or** `ARCHITECTURE.md`, and that split is the
one people get wrong:

- **`MANIFESTO.md` holds a promise.** Somebody chose it and could have chosen otherwise, and it would
  still stand if the whole system were rewritten in another language tomorrow.
- **`ARCHITECTURE.md` holds a fact about how the system is built.** What the things are, how they relate,
  what states they move through, and where a rule is actually enforced.

**A domain rule that sounds like a business rule is usually ARCHITECTURE.** *"An order has one customer
and many lines"* is the data model, not a promise. When a rule is genuinely both, `MANIFESTO.md` states
the promise in one line and `ARCHITECTURE.md` says how it is enforced — never both in full, and never
only the promise, which leaves the mechanism written down nowhere.

### Seven rules for keeping these files honest

Every one of them exists because breaking it cost something, and **not one of them fails loudly** — this
harness is prose, so nothing errors when a link dies or a number goes wrong.

1. **Never renumber.** Rule numbers, decision numbers and milestone numbers get cited from code comments
   and from other documents. **Append. Strike through rather than delete.**
2. **After renaming or moving a file, grep the old name.**
   `grep -rn "OldName" . --exclude-dir=node_modules --exclude-dir=.git`
   Paths resolved at run time and links written in prose are invisible to a test suite.
3. **Never copy a rule into a second file.** Two copies are two rules, and one of them will decide
   something. One file states it; every other file links to it.
4. **A closed file stays closed.** New entries go in the active part. If you are appending to a file whose
   `status:` is `closed`, you are in the wrong file.
5. **The index is a map, not an authority.** If `INDEX.md` disagrees with the file it describes, the file
   is right and the index is the bug.
6. **Frontmatter carries the scope.** `covers` and `status` say which era a file describes; `last_updated`
   says when it was last true. Update them when you edit, or the next reader trusts a stale file.
7. **Every number is measured, or it is left out.** Counts, line totals, test figures, file totals. A
   reasoned number is wrong often enough to be worthless, and writing it down makes it look checked.

### When to write to `BRAINSTORM.md`, and when not to

Not for every fix — that is how a decision log becomes unreadable. An entry earns its place when **an
alternative was rejected**, or when **a measurement changed our minds**: anything an outsider would read
two months later and ask *"why was it done this way?"*. Ordinary work belongs in `PROGRESS.md`, and the
commit message covers the rest.

### Splitting a file

Split on a **phase boundary** first, and on **length** second — roughly 1,500 lines, or whenever the file
has stopped being readable. Continue the numbering, never restart it, and put the next/previous
navigation block at the top and bottom of both parts. Name the parts `NAME.md`, `NAME_2.md`, `NAME_3.md`.

Files that describe **one current state** — `ARCHITECTURE.md`, `DESIGN.md`, `MANIFESTO.md` — are never
split. They change in place.

<!-- kiacontext:end -->
