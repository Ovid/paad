# Skill Conversion Notes

Cross-PR learnings discovered while converting paad skills to use the
`references/` progressive-disclosure pattern from the Agent Skills spec.
The plan-of-record lives in `docs/plans/` (the latest dated design doc).
This file is the running scratch pad — facts that affect *future* PRs go
here, not the per-PR commit messages.

## Spec alignment

- The Agent Skills spec (https://agentskills.io/specification) defines
  `references/` for content loaded on demand, separate from `SKILL.md`
  (always loaded at activation) and metadata (always loaded at startup).
- The spec says relative paths inside `SKILL.md` resolve to the skill
  directory root: "the agent runs commands from there." This applies to
  both code blocks and references like `references/foo.md`.
- The same convention is described as the "Skill with Heavy Reference"
  layout in `superpowers:writing-skills`. Our pattern is the same one,
  applied to subagent dispatch.

## Subagent path resolution — open question for pilot

The spec covers the agent that activates the skill. It does **not**
explicitly cover subagents dispatched via the Task tool. Possibilities:

1. The subagent inherits "skill dir as command root" — relative paths
   in the dispatch prompt Just Work. Cleanest case.
2. The subagent lands in the user's repo CWD with no skill awareness.
   Parent must resolve to absolute path before embedding in the prompt.
3. Some middle ground (env var, prompt-time substitution).

**Pilot must lock this down.** If (1) holds, the design stays as
written. If (2), every dispatch site needs a resolution step (likely a
Bash `pwd`/`realpath` inside the parent's skill dir, captured into a
shell variable, embedded in the prompt). Update this note with the
verified answer after PR1 lands.

## TDD for skill extractions = subagent pressure scenarios

Per `superpowers:writing-skills`: TDD for documentation means
dispatching a subagent against a fixture, watching it fail without the
skill content properly accessible, and watching it succeed once the
content is in place. Structural Makefile checks (file exists, content
moved, dispatch prompt references the path) are **guardrails for CI**,
not the test of record.

The "red" we want per PR is: subagent dispatched against a known
fixture diff produces wrong output when the extracted content is
unreachable, then produces equivalent-to-baseline output once the
references file is correctly wired up.

## Fixture strategy

Pointed at a known commit in this repo's history that exercises the
specialist's distinctive behaviors (decision: option ii from the
brainstorm — over a hand-crafted synthetic fixture or trusting whoever
runs the PR's smoke test). The commit SHA goes in the PR's description
and in this file under "Fixtures used" once the pilot identifies one.

Risk: history rewrites or branch deletes can break the reference. If
that becomes a problem, promote the fixture to a tagged commit or move
to option (i) — a hand-crafted synthetic fixture under `paad/test-fixtures/`.

### Fixtures used

(populated as PRs land)

- **PR1 behaviors fixture:** `83aa677` — `agentic-review: plug Phase 2/3 contract gaps (S5, S6, S10)`. Intent
  source: commit body (three named findings S5/S6/S10, each listing concrete artifacts the change must
  produce — e.g., a Symbol-field contract, the literal `<file-scope>` sentinel, prompt-injection language
  for Phase 2 specialists). Expected Spec Compliance behaviors: plausible `Missing` finding (one of the
  S5/S6/S10 sub-bullets not landing in the +5/-3 single-file diff, e.g., the Symbol contract or
  prompt-injection wording underspecified), and a possible `out-of-scope-addition` for any wording change
  in the diff not anchored to S5/S6/S10.
- **PR1 bail-out fixture:** `5f03453` — `Update PAAD logo with cleaner style`. No intent
  source. Expected Spec Compliance behavior: skipped output.

## Order of attack

1. **Spec Compliance specialist** — first, because it has the most
   distinctive content (the `category: out-of-scope-addition` tag, the
   intent-source priority list, the retro-edited-spec failure mode,
   missing-artifact detection). Easiest to detect failure if the
   subagent silently no-ops on the ref read.
2. The other five specialists in any order.
3. **Verifier** — pulls out blame/promotion/demotion logic and backlog
   dedup details. Higher-stakes than a single specialist because the
   verifier is dispatched once after all specialists complete.
4. **Phase 4 report template** — purely parent-side material, not
   subagent-targeted. Different sub-pattern of progressive disclosure
   (parent reads ref only when entering report phase).

## Cross-skill candidates (post-pilot)

After the eight `agentic-review` PRs land, identify candidates in:

- **agentic-architecture**, **agentic-a11y** — same multi-specialist
  shape; likely benefit identically.
- **alignment**, **fix-architecture** — check for conditional content
  ("if X, do Y") where Y can move to a ref loaded only when X holds.
- **pushback**, **vibe** — likely thin enough to not benefit; verify.
- **makefile**, **help** — almost certainly out of scope.

This list is a first cut; the full plan after the pilot will revisit it
with whatever the pilot teaches us.

## Behavioral verification must use `--plugin-dir`

**Discovered:** During PR1 Task 2 baseline-capture attempt, the fresh
Claude Code session loaded the marketplace-cached paad version
(`~/.claude/plugins/cache/paad/paad/1.11.0/`) instead of the
working-tree version (`1.14.0`). Cached v1.11.0 predates the Spec
Compliance specialist entirely, so any "baseline" captured against it
would be useless as an acceptance criterion for the extraction.

**Mitigation:** Every behavioral verification session in this pilot —
baselines, broken-extraction reds, post-extraction greens, refactor
re-verifications, and equivalent verifications in Phases 2–5 — must
launch the Claude Code session with `--plugin-dir`:

```
claude --plugin-dir /Users/ovid/projects/paad/plugins/paad
```

(or the relative form `claude --plugin-dir ./plugins/paad` from the
repo root). This is already documented in `CLAUDE.md` under "Adding a
new skill" step 6 ("Test locally with `claude --plugin-dir
./plugins/paad`"). The pilot adopts it as a standing requirement, not
an optional flag.

**Cross-PR implication:** Update PR1 Task 4 Step 8/9 procedures and
the equivalent steps in any future-phase plan to mention the
`--plugin-dir` launch explicitly. Future contributors who skim the
plan without reading this notes file will otherwise reproduce the
same staleness trap.

**Optional belt-and-braces verification:** Inside the launched
session, before invoking `/paad:agentic-review`, ask: "What version
will `/paad:agentic-review` announce on invocation?" The skill's
announce line carries the version literal. If the answer is the
expected version, the right SKILL.md is loaded. If it's the cached
older version, the `--plugin-dir` flag wasn't honored.

**Working-tree state hazard.** The pilot uses temporary branches
(`pr1-baseline-behaviors`, `pr1-baseline-bailout`, etc.) checked out
at fixture commits. These checkouts mutate the *shared* working tree
on disk, so an in-progress session in the same checkout sees the
fixture's historical state — including missing recent files like
`notes/` itself. When orchestrating across two sessions, complete the
fixture run and clean up the temp branch *before* the orchestrating
session writes anything to working-tree paths that didn't exist at
the fixture commit.

## Working branch

Phase 1 work lands on the existing `ovid/skill-breakdown` branch, **not**
on per-extraction feature branches. The eight extractions are sequential
commits (or small commit clusters) on this branch. "PR" in the design
doc refers to the logical extraction unit, not a separate GitHub PR.

If a single PR for all eight commits is too large to review, we'll
revisit at that point — the work is naturally chunked at the commit
level so partial pushes / stacked PRs remain an option.

## Conventions established by the pilot

(populated as PRs land — directory layout, naming, dispatch-prompt
wording, anything mechanical that future PRs should copy verbatim)
