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

A skill announces as before, then checks for the files. If any exists it
reads it, applies it for the rest of the run, passes the relevant parts to
the subagents it dispatches, and opens its final answer with
`Config: <path>` naming each file followed. With no file present nothing
changes.

## Decisions

- **No precedence rules.** A config line can contradict a skill's digraph and
  the skill may follow it. Enforcing "additive only" in prose was judged too
  unreliable for models to follow, so `CONFIG.md` carries the warning instead.
  Revisit once real configs have broken something.
- **The paragraph is duplicated into every SKILL.md.** Skills have no include
  mechanism that survives all three delivery routes; `make check-config`
  enforces the copy, and that the copy names its own skill.
- **The config is named at the end, not in the announce line.** The original
  spec put `with <path>` in the announce. Pressure-tested non-interactively:
  every phrasing that placed the announce after the file check lost the
  announce entirely (0/6, 0/6, 0/6 across three phrasings), and a separate
  line printed right after the check was dropped too (0/6). Announce-first
  plus `Config: <path>` as the first line of the final answer held 6/6, with
  2/2 no-config runs unaffected. End-of-run instructions were followed in
  every run of every variant.
- **One guard sentence.** Unguarded, 3/3 runs swapped the read-only analyst
  for a `general-purpose` subagent when a config asked, one forwarding "fix
  any bug" to it. With "config never changes a subagent's type or grants it
  write tools", 3/3 refused and said so. This is the only precedence rule,
  and it restates the rule CLAUDE.md already imposes on skills.
- **`paad/config/` is exempt from the exporter's `paad/` → `.reviews/`
  rewrite**, so every delivery route reads the same path and `CONFIG.md`
  documents one location. Cost: the Kiro/Pi exports carry a `paad/` path.
- **Trust surface.** A config file in a cloned repo is untrusted input, the
  same as a `CLAUDE.md`. Documented, not mitigated.
