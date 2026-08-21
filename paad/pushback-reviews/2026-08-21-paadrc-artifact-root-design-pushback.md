# Pushback Review: `.paadrc` and a single artifact root

**Date:** 2026-08-21
**Spec:** `docs/plans/2026-08-21-paadrc-artifact-root-design.md`
**Commit:** 6bd0630

## Source Control Conflicts

None. The document is one commit old and its code claims check out against
HEAD: the five path rewrites are at `scripts/convert_skills.py:42-49` exactly,
and the three exported skills really do ship without a `description:` line.

## Issues Reviewed

### [0] Scope cohesion — the frontmatter bug does not belong in this spec
- **Category:** scope imbalance
- **Severity:** serious
- **Issue:** the "bug fixed in passing" section fixes something already shipped
  and broken on `main`, shares no code path with the artifact-root work, and was
  gated behind a design whose own first open question is unverified.
- **Resolution:** split out to `docs/plans/2026-08-21-export-frontmatter-fix.md`.
  Not to be shipped yet. A `/paad:rethink` pass on that decision found the split
  sound but the justification unverified, and widened the bug's real scope from
  three skills to four, by two causes, plus an inverse leak in the Antigravity
  wrappers. All of that is recorded in the new spec.

## Unresolved Issues

The review was stopped after [0]. These three were ranked and never presented.

### [1] Three skills use artifact-path *existence* as control state, and nothing migrates it
- **Category:** omissions
- **Severity:** serious
- **Issue:** "Out of scope: migrating existing `.reviews/` directories … the next
  run writes to `paad/`" treats a root move as cosmetic. It is not, because
  three skills read the artifact tree as state:
  - `test-roadmap/SKILL.md:126-130` — "That is the entire routing logic — one
    file existence check, two branches." Missing `paad/test-roadmap/test-roadmap.md`
    means the build-from-scratch branch, which regrades the whole suite and
    overwrites the `## Decisions` section recorded in the old location.
  - `agentic-review/SKILL.md:96-98` — `paad/code-reviews/backlog.md` is
    project-wide, append-only, explicit-removal-only. A root move silently
    resets it to empty and the accumulated out-of-scope bugs stop being deduped
    against.
  - `fix-architecture/SKILL.md:197` — finds the most recent report in
    `paad/architecture-reviews/`; if none, it stops and tells the user to run
    `/paad:agentic-architecture` first.

  This fires twice: once for existing Kiro/Antigravity users when the `.reviews/`
  rewrites are deleted, and again for any user who adds or edits `.paadrc` later.
  The second case is permanent and affects everyone.
- **Suggested options:**
  1. On a missing artifact root, have the skills that route on existence check
     the two known former roots (`.reviews/`, `paad/`) before taking the
     build-from-scratch branch, and say what they found. Cheap, no migration.
  2. Ship a one-time `make migrate-artifacts` / documented `git mv`, and have
     skills say nothing.
  3. Accept it, but say so in the skills' output rather than in a spec's
     out-of-scope list — "no roadmap found at <root>; if you previously used
     <other root>, move it first."
- **What would change this:** how many Kiro/Antigravity users have accumulated
  artifact state. If effectively none, the export half collapses and only the
  `.paadrc` half survives — still real, still permanent, but moderate rather
  than serious.

### [2] The resolver script may not earn what it costs
- **Category:** feasibility / scope imbalance
- **Severity:** serious
- **Issue:** the design's own preamble already specifies a complete no-script
  path — "read `.paadrc` at the repository root yourself and take the
  `artifact-root:` value; if there is no such file, use `paad/`". Everything the
  script adds is machinery around a fallback that must exist anyway: a shared
  source file, nine committed copies, a new copy path in `convert_skills.py`, a
  new `make check-artifact-root`, a self-check suite, and generated files living
  inside the plugin source tree. Meanwhile open question 3 says a skill may not
  be able to address its own `scripts/` directory, and
  `find plugins/paad/skills -maxdepth 2 -type d -name scripts` returns nothing —
  no skill has ever shipped one, so nothing in this repository demonstrates the
  mechanism works on any platform.
- **Suggested options:**
  1. Prose only. Delete the script, the shared source, the copy step, and the
     new check. `.paadrc` is a two-line file an agent can read with `cat`.
  2. Settle open question 3 first with a one-skill spike, then decide.
  3. Ship as designed.
- **What would change this:** evidence that agents reliably resolve their own
  skill directory on Kiro, Antigravity, and Pi. If they do, the script buys
  determinism and option 3 is defensible. If they don't — which is what open
  question 3 suspects — the fallback is the only path that ever runs.

### [3] `references/` files are outside the preamble's stated scope
- **Category:** omissions
- **Severity:** moderate
- **Issue:** the preamble is placed in `SKILL.md` and scoped to "wherever this
  skill says `paad/`". Reference files are never mentioned, and they carry
  roughly twenty `paad/` paths:
  `test-roadmap/references/build-test-roadmap.md` names
  `paad/test-roadmap/` fifteen times including a literal
  `git add paad/test-roadmap/test-roadmap.md …` at lines 165-166;
  `agentic-review/references/verifier.md` names `paad/code-reviews/backlog.md`
  and is read by a **dispatched subagent** (`agentic-review/SKILL.md:218`
  instructs it to read the file), which never sees the parent SKILL.md preamble.
- **Suggested options:**
  1. State that the preamble governs the skill and everything under its
     `references/`, and have the orchestrator pass the resolved root into every
     dispatch prompt that loads a reference.
  2. Emit the preamble into each reference file too, at generation time.
  3. Leave reference paths literal and accept a split artifact tree.

## Summary

- **Issues found:** 4 (plus 5 candidates dropped for lacking a defensible
  consequence — notably "a wrong root would be silent", which fails because
  every paad skill announces the paths it wrote, and "`make export` now mutates
  its own source tree", a real smell with no consequence I could name)
- **Unresolved:** 3
- **Status:** [1] should be settled before implementation — a permanent,
  everyone-affects-it state loss is not an out-of-scope line item. [2] is worth
  settling before any code is written, because it decides whether most of the
  implementation exists at all. [3] can ride along with the preamble work.
