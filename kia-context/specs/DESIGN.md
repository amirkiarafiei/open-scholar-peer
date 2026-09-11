---
description: >
  The design system, in the DESIGN.md format — a machine-readable token block paired with prose
  explaining what each token means and when to reach for it. Written so an agent building an interface
  has both the exact values and the intent behind them. It starts generic and becomes specific to this
  product as the interface finds its own look; both states are correct, and the agent updates it as the
  design moves.
  NOT here: component implementation, framework class names, or why an option was rejected
  (BRAINSTORM.md).
authority: blueprint
writes: agent, as the interface evolves
status: active
covers: the visual system as it is today
last_updated: "{{YYYY-MM-DD}}"
---
---
name: "{{system name}}"
description: "{{one line — the feeling this system is going for}}"
colors:
  primary: "{{#1A1C1E}}"
  on-primary: "{{#FFFFFF}}"
  surface: "{{#FFFFFF}}"
  on-surface: "{{#1A1C1E}}"
typography:
  h1:
    fontFamily: "{{Public Sans}}"
    fontSize: "{{3rem}}"
    fontWeight: "{{700}}"
    lineHeight: "{{1.1}}"
  body:
    fontFamily: "{{Public Sans}}"
    fontSize: "{{1rem}}"
    lineHeight: "{{1.5}}"
rounded:
  sm: "{{4px}}"
  md: "{{8px}}"
spacing:
  sm: "{{8px}}"
  md: "{{16px}}"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    borderRadius: "{rounded.md}"
---

# 🎨 DESIGN — The design system

> **Delete this file if this project has no interface.** A library, a service, a pipeline or a research
> project does not need one, and an empty design system is a file people trust by mistake.

> **The two blocks above are both required, and they are different things.** The first is kiacontext's
> frontmatter — six fields, never changed. The second is the DESIGN.md token block, which the standard
> puts in the file's own front matter; here it sits directly beneath ours, because kiacontext's banner
> has to come first. Tokens are the normative part of this file. Prose explains them.

> **The sections below are the standard's prescribed order, not an invention of ours** — and the
> specification allows any of them to be omitted. Drop what this project does not have, add what it does.

**References** · [google-labs-code/design.md](https://github.com/google-labs-code/design.md) ·
[the specification](https://stitch.withgoogle.com/docs/design-md/specification) ·
[Claude Design](https://support.claude.com/en/articles/14604397-set-up-your-design-system-in-claude-design)

**Contents** · [Overview](#overview) · [Colors](#colors) · [Typography](#typography) ·
[Layout](#layout) · [Elevation & Depth](#elevation--depth) · [Shapes](#shapes) ·
[Components](#components) · [Do's and Don'ts](#dos-and-donts)

---

## Overview

> The design philosophy in a short paragraph. What this system is going for, and the one motif or idea
> everything else follows from.

## Colors

> What each colour *means*, not only what it is. A reader should be able to pick the right token from
> this section without seeing the interface.

## Typography

> The faces, the scale, and which role each size plays.

## Layout

> The grid, the spacing steps, and the rule for which step goes where.

## Elevation & Depth

> Shadows, layering, and what sits above what.

## Shapes

> Radii, borders, and the shape language.

## Components

> The shared pieces and their states. The standard expresses variants — hover, active, pressed — as
> separate named entries in the token block; this section says when to use each.

## Do's and Don'ts

> **Write the measurement next to the don't.** *"Avoid low contrast"* gets ignored. *"White on the accent
> measures 2.02:1 — use the `on-` partner token"* does not. A don't with a number attached is the most
> useful thing in this file.

| Do | Don't |
|---|---|
| {{the correct move}} | {{the tempting wrong one, with the measurement that killed it}} |
