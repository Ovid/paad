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

## Subagent path resolution — verified mechanism (PR1)

The Agent Skills spec covers the agent that activates the skill but
does not explicitly cover subagents dispatched via the Task tool. PR1
locked this down.

**Mechanism:** The dispatched subagent inherits "skill dir as command
root" — relative paths in the dispatch prompt resolve against the
skill's directory and Just Work. The parent does *not* need to compute
an absolute path before embedding it in the dispatch prompt.

**Evidence:** PR1's dispatch prompt instructs the Spec Compliance
subagent to "Read `references/spec-compliance.md` from
this skill's directory before producing findings; treat its
instructions as binding." During post-extraction verification, the
subagent successfully read the reference file and produced output
faithful to its instructions (e.g., the bail-out output explicitly
cites "Per the reference's instruction not to invent intent from the
diff itself"), confirming the relative path resolved correctly without
any parent-side absolute-path computation.

**Cross-PR implication:** Future extractions copy the same
dispatch-prompt shape (see "Conventions established by the pilot").
No prompt-time path manipulation is needed.

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
- **PR1 bail-out fixture:** `5f03453` — `Update PAAD logo with cleaner style` (binary-only diff,
  subject-only body, no PR — nothing for Spec Compliance to infer intent from). No intent
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

**Working-tree version drift = older skill at older commit.** Because
`plugins/paad/.claude-plugin/plugin.json` is part of the working tree,
checking out a historical commit also rolls the *plugin's* version
back. If the fixture commit predates the feature being baselined
(e.g., bail-out fixture `5f03453` is at plugin v1.11.0, before Spec
Compliance existed), the SKILL.md the loader reads at that working
tree won't have the feature at all — `--plugin-dir` doesn't help,
because the plugin dir's contents *are* the historical SKILL.md.

**Mitigation: synthesize older fixtures on top of HEAD.** Cherry-pick
just the file changes (e.g., `git checkout <fixture-SHA> -- <path>`),
re-commit on a temp branch from current HEAD with the original
fixture's commit-message shape (subject only, no body, no PR). The
synthetic commit is content-equivalent to the original but the
working tree stays at the current plugin version. Run
`/paad:agentic-review` with the temp branch's parent as base.

**Cross-PR implication:** Any future-phase fixture commit older than
the working-tree version of the skill being tested needs the
synthesis treatment. Recent fixtures (post the relevant feature's
landing) can be checked out directly. Each phase's PR1 should pick
fixtures with this gotcha in mind.

**Synthesis edge case: byte-identical file across history.** When
synthesizing a fixture by cherry-picking a single file (`git checkout
<fixture-SHA> -- <path>`), the operation no-ops if the file's bytes
at HEAD are already identical to the fixture commit's version.
Discovered with `images/paad.png`: at HEAD it was already byte-
identical to its state at `5f03453`. Workaround: reach one further
back (`<fixture-SHA>^:<path>`) to get the *previous* version, bring
it forward instead, and accept that the synthetic diff goes in the
opposite direction byte-wise. Content properties match (binary diff,
no body, no PR), which is what the bail-out test cares about.

**Caveat: zero-finding baselines are weaker tests.** PR1's fixture 1
(`83aa677`) produced "Spec compliance: clean" with zero findings —
substantively rich (the summary cites S5/S6/S10 by name and locates
each in the diff) but no actual `Missing` or `Deviation` finding.
Fixture 2 bails out. Both are valid signals but neither catches an
extraction that subtly produces *wrong* findings (false positives,
mis-categorized findings, lost `category: out-of-scope-addition`
tag). The behavioral checklist must lean on *content of the
explanations* (intent source named, S5/S6/S10 explicitly addressed,
bail-out enumeration of intent sources checked), not finding counts.

**Cross-PR implication:** If a future-phase post-extraction baseline
diverges only in surface phrasing while passing all checklist items,
consider adding a third fixture that synthesizes a deliberate
deviation (e.g., a commit whose body promises X but whose diff omits
X) to give the test set a finding-producing signal. Hold this in
reserve — don't reach for it unless the current pair of fixtures
proves insufficient at green time.

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

### Dispatch prompt template (PR1)

Established by PR1 (Spec Compliance). Subsequent extractions copy this
shape verbatim, swapping the lens name and ref path. In the parent
`SKILL.md`, the entry for each extracted lens reads:

```markdown
**<Lens> additional instructions:** The <Lens> specialist's
instructions live at `references/<lens>.md`. That file
covers <one-line inventory of the ref's contents — intended as a
TOC for SKILL.md readers, not duplicated content>. The dispatch
prompt for the <Lens> specialist must include this instruction
verbatim:

> Read `references/<lens>.md` from this skill's
> directory before producing findings; treat its instructions as
> binding.
```

Notes on the shape:

- The path appears twice in SKILL.md: once in the prose ("instructions
  live at..."), once in the binding-instruction blockquote. Both are
  required — the prose makes the path discoverable when reading
  SKILL.md, the blockquote is the literal text the dispatch prompt
  must inject into the subagent.
- The inventory sentence is a TOC, not a paraphrase of the ref's
  content. Keep it short. If you find yourself duplicating the ref's
  prose into the inventory, prefer the ref.
- The structural-guardrail check (`scripts/check_extracted_refs.sh`)
  enforces both: that the ref path is referenced in SKILL.md, and
  that the chosen sentinel phrase is *only* in the ref file.

### Reference file shape (PR1)

Each `references/<lens>.md` file starts with:

1. A `# <Lens> — additional instructions` top-level heading.
2. A short blockquoted role-statement orienting the reader: name
   the role, the dispatching skill+phase, the parent-vs-this-file
   boundary, and the imperative to read before writing findings.
   One paragraph.
3. The body — distinctive content for the lens, either a verbatim
   move from the prior inline block in `SKILL.md` or new content
   authored specifically for the lens (see "Finding: empty
   specialists" below).

### Parent-self-read variant (PR8)

PRs 1–7 dispatch a subagent that reads the ref. PR8's pattern is
different: there is no subagent — the orchestrator (the agent that
activated the skill) reads the ref itself when it enters the
relevant phase. The dispatch shape adapts:

- The parent `SKILL.md`'s section keeps essential parent-side state
  (file paths, directory creation, anything the parent does
  immediately before reading the ref).
- The dispatch sentence becomes "**Before [phase action], read
  [the ref]**" rather than "the dispatch prompt for the subagent
  must include..."
- The ref's role-statement quote names the parent agent as the
  reader, not a subagent ("This is parent-side material... The
  orchestrator reads these instructions when entering [phase]").

Use this variant when the content being extracted is consumed by
the orchestrator itself — report templates, output formats,
parent-side rules — rather than by a dispatched subagent.

### Finding: "empty" specialists deserve authored content (PR2–PR6)

The Phase 1 design assumed every specialist had distinctive inline
instructions to extract. When Phase 1's `SKILL.md` was inspected at
PR2 time, the actual situation was:

- **Spec Compliance** had a substantial ~30-line inline block
  (PR1 verbatim move).
- **Error Handling & Edge Cases** and **Contract & Integration**
  had one-paragraph instructions (PR3, PR4 verbatim moves).
- **Logic & Correctness**, **Concurrency & State**, and
  **Security** had no distinctive inline content — just the
  common base prompt with the lens name swapped.

Rather than skipping the three "empty" lenses, we dispatched three
subagents (one per lens) to think like that specialist and propose
distinctive instructions that would meaningfully improve the lens's
reviews beyond the base prompt. All three returned substantive,
defensible recommendations (sibling-path comparison + finding
subtypes for Logic; anchor-on-changed-surface + bail-out + 7-item
checklist for Concurrency; trust-boundary anchoring + OWASP walk +
LLM-miss patterns + severity floor for Security). PRs 2, 5, 6
landed those drafts as new content; PRs 3, 4 were verbatim moves.

Both flavors are extractions in the structural sense (ref file
under `references/`, manifest row, dispatch paragraph in
`SKILL.md`). They differ only in whether content existed
previously.

**Cross-phase implication:** when an extracted skill has lenses
with no distinctive inline content, dispatch a "think-like-this-
specialist" subagent before defaulting to "skip." The base prompt
is general; lens-specific structure (taxonomies, anchoring rules,
bail-outs, drop rules) measurably improves consistency.
