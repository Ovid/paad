# Design: exported skills keep their frontmatter

**Date:** 2026-08-21
**Status:** designed, not implemented
**Touches:** `scripts/convert_skills.py`, `Makefile`
**Split from:** `2026-08-21-paadrc-artifact-root-design.md`, where this was
filed as "a bug fixed in passing". Verification showed it is neither in
passing nor the bug that document described.

## Why

Four of the twelve exported skills ship with a blank or truncated
`description:`. Two more ship Claude-Code-only text inside a description that
was supposed to be neutralized. All of it is one code region — how
`convert_skills.py` handles YAML frontmatter — and none of it touches the
artifact-root work it was originally bundled with.

Measured across all 24 exported `SKILL.md` files (12 Kiro + 12 Antigravity),
description lengths:

```
.kiro/fix-architecture  0     .agent/fix-architecture  346
.kiro/pushback          0     .agent/pushback          339
.kiro/rethink           0     .agent/rethink           357
.kiro/test-roadmap      2     .agent/test-roadmap        2
(all others 167-382 in both)
```

`name:` is present and correct in all 24.

## Three defects, one region

### 1. Kiro descriptions deleted (`convert_skills.py:147-153`, `:59`)

`parts = re.split(r'\n(##+ .*)', content)` puts the YAML frontmatter in
`parts[0]`, and line 153 neutralizes it. Line 59 deletes every line containing
`/paad:`. The descriptions of `fix-architecture`, `pushback`, and `rethink`
each end with a cross-reference to another skill's command — "run
`/paad:agentic-architecture` first", "that's `/paad:alignment`", "which is
`/paad:pushback`" — so the whole line goes.

The comment at 149-152 acknowledges frontmatter is in `parts[0]` and reasons
only about digraphs.

This is not a converter regression. Line 59 predates it; the descriptions were
rewritten to mention `/paad:` commands at `d7a8a83` (2026-07-26) and walked
into a rule that was already there. Present at `6dd93c7` (2026-03-20), gone
from `d7a8a83` onward — twelve consecutive commits, including the v1.30.0 and
v1.30.1 releases.

### 2. Folded scalars truncated (`convert_skills.py:140-142`)

`re.search(r"description:\s*(.*)", content)` captures to end of line.
`test-roadmap`'s source uses a YAML folded scalar — `description: >` on line 3
with the text on lines 4-10 — so the capture is the `>` marker and nothing
else. The Kiro export preserves the scalar intact; the **Antigravity wrapper**,
which interpolates the captured string, gets an empty description.

Fixing defect 1 does not fix this. It needs the extraction to parse YAML rather
than regex a single line.

### 3. Antigravity descriptions leak Claude-only text (`convert_skills.py:214-217`)

The wrapper interpolates the **raw, un-neutralized** description.
`grep -rln 'paad' kiro_and_antigravity/skills/.agent/skills/` returns exactly
`fix-architecture`, `pushback`, `rethink` — the same three as defect 1, failing
the opposite way. `.agent/skills/fix-architecture/SKILL.md:3` ships
`paad/architecture-reviews/` and `/paad:agentic-architecture` to a platform
that has neither.

## Fix

1. Split the frontmatter off before neutralizing; neutralize only the body.
2. Parse the frontmatter as YAML for the wrapper's `name`/`description` rather
   than regexing one line.
3. Neutralize the description before interpolating it into the Antigravity
   wrapper — but neutralize it *as a description*, not as prose: a description
   whose only content was a `/paad:` cross-reference must not become empty.
   Strip the command reference, keep the sentence.

Point 3 is the one with a judgment call in it. The three affected descriptions
end in a sentence fragment that is meaningless off Claude Code ("Not for
cross-checking a spec against a plan — that's `/paad:alignment`."). Dropping the
trailing clause and keeping the rest is the intent; dropping the line is what
happens today.

## Verification

- `make check-export-frontmatter` — every exported `SKILL.md`, both targets, has
  a non-empty `name` and `description`, and no exported description contains
  `/paad:` or a `paad/` path. This is new coverage: `check-frontmatter`
  (`Makefile:169`) walks `plugins/paad/skills/*` only, and `check-export-current`
  compares the export against a fresh export — the bug is deterministic, so it
  passes.
- A description that is a folded scalar round-trips into both targets.

## Open question

**Is `description` actually load-bearing on these platforms?** The claim that
Kiro matches requests against it, and that a blank one makes a skill
unfindable, appears nowhere in this repository except the design document this
spec was split out of. `README.md:467` implies it without naming the field.
One read of the Agent Skills specification settles it.

It decides urgency, not correctness. The fix is right either way; whether it
warrants a release of its own depends on the answer.

## Out of scope

- Whether the Kiro/Antigravity export should continue to exist at all. That is
  open question 2 in the artifact-root design.
- The artifact-root and `.paadrc` work. No line overlap: this spec touches
  `convert_skills.py` 140-142, 147-153, and 214-217; that one touches 42-49 and
  adds a block near 182-204.
