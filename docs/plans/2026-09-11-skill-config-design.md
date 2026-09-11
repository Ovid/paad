# Design: per-project skill configuration (`paad/config/`)

**Date:** 2026-09-11
**Status:** Implemented on this branch. Experimental.

**Touches:** every `preview/paad/skills/*/SKILL.md`, `Makefile`, `scripts/convert_skills.py`, `CONFIG.md` (new), `README.md`, `CHANGELOG.md`, `CLAUDE.md`

## Why

People keep writing wrapper skills around paad skills to bolt on their own
behaviour, because the alternative is retyping a long argument list on every
invocation. A config file the skill reads on its own removes the wrapper.

## What

Two optional files, relative to the working directory:

- `paad/config/paad.md` — read by every skill
- `paad/config/<skill-name>.md` — read by that skill only

A skill that finds one or both reads them before announcing, announces
`Running paad:<name> v<ver> with <path>` (one ` with` clause per file found),
applies the instructions for the rest of the run, and passes the relevant
parts to the subagents it dispatches. With no file present the announce line
is unchanged.

## Decisions

- **No precedence rules.** A config line can contradict a skill's digraph and
  the skill may follow it. Enforcing "additive only" in prose was judged too
  unreliable for models to follow, so `CONFIG.md` carries the warning instead.
  Revisit once real configs have broken something.
- **The paragraph is duplicated into every SKILL.md.** Skills have no include
  mechanism that survives all three delivery routes; `make check-config`
  enforces the copy, and that the copy names its own skill.
- **The announce suffix is described outside the quoted literal.** Three
  places key on the exact token `v<ver>"`: `check-skill-versions`, `bump-tree`,
  and `promote.py`. Writing the suffix inside the quotes would ship `-preview`
  into `plugins/` unbumped.
- **`paad/config/` is exempt from the exporter's `paad/` → `.reviews/`
  rewrite**, so every delivery route reads the same path and `CONFIG.md`
  documents one location. Cost: the Kiro/Pi exports carry a `paad/` path.
- **Trust surface.** A config file in a cloned repo is untrusted input, the
  same as a `CLAUDE.md`. Documented, not mitigated.
