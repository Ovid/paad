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

## Expected baseline drift after commit `29f213c` (references-package hardening)

Commit `29f213c` ("agentic-review: tighten contracts in references
package") landed eleven contract tweaks to the references package
*after* the PR1 baselines (`paad/code-reviews/pr1-*-2026-05-01-*.md`)
were captured. Future verify-side runs against the same fixtures will
diverge from those PR1 baselines in predictable ways. **Treat the
following as expected drift, not regression.**

- **Universal:** every Review Metadata block now ends with an
  additional bullet `- **Verifier warnings:** none` (or with a
  sublist of warning lines when any were emitted). PR1 baselines end
  metadata at `Intent sources consulted:`. Diff this in.
- **Likely on multi-specialist findings:** the merged categorical
  confidence is now the max of contributing specialists' numeric
  confidences (per `references/verifier.md` step 5). Previously
  unspecified — the verifier may have averaged or otherwise picked.
  Findings whose merged confidence flips Medium↔High should be
  inspected once but not treated as regressions.
- **Possible on Logic & Correctness findings:** the (a)/(b)/(c)
  anchor rule in `references/logic-correctness.md` requires every
  finding to articulate input + path + observable wrong output. A
  stricter specialist may now drop findings that previously passed
  on the looser "input/output pair" rule. Before re-capturing, scan
  baseline Logic findings for ones that don't articulate the path —
  if they now drop, that's intended.
- **Cosmetic:** `Field-encoding rules` now live in
  `references/verifier.md` (not `report-template.md`). Citations of
  rule location may shift; rule content unchanged.

If the next phase's baseline-verify diff shows *only* drifts on this
list, treat as expected. Anything else needs root-cause analysis.

## One-at-a-time decision flows: label scope, not just severity

**Discovered:** During the review pass that produced commit `29f213c`,
findings were presented to the user one-at-a-time in C/I/S severity
tiers (Critical / Important / Suggestion). The tier signaled *impact
if unaddressed* but not *blast radius of the fix*. Two findings tiered
as "Important" had vastly different scopes:

- **I2** ("BAIL detection ordering") — single-sentence prose edit,
  one file, ~30 seconds.
- **I4** ("verifier-warning format and rendering") — three
  coordinated edits across `verifier.md`, `report-template.md`,
  and `SKILL.md`; new output channel; renumbered Post-Review steps;
  new metadata field; two warning subtypes. Effectively a small
  feature.

From the user's chair, both decisions present the same approve/reject
affordance. A quick "yes" to I4 implicitly authorized a multi-file
mini-feature; the framing didn't surface the cross-file blast radius
upfront.

**Cross-flow implication:** when presenting findings one-at-a-time
for approval, label scope explicitly alongside severity. A simple
prefix works: *"I4 (cross-file, 3 edits)"* vs. *"I2 (single-line
edit)"*. Severity tier ≠ scope; conflating them costs the user
clarity on what they're authorizing per click. This applies to any
review-pass flow, not just the references-package work.

## Runtime contracts (untested)

Commit `29f213c` added several cross-file semantic contracts to the
agentic-review references package that the existing structural
guardrails (`scripts/check_extracted_refs.sh`,
`scripts/extracted-refs.tsv`) cannot verify. These are LLM-driven
runtime invariants — a maintainer changing any of the listed
sections must hand-verify the others stay in sync. Build a behavioral
test harness or add static greps if/when one of these silently breaks
in the wild.

**Contracts to grep before editing the named sections:**

1. **`verifier-warning:` channel exists in three places.** Defined in
   `references/verifier.md` (step 0 and the Field-encoding rules
   File/Symbol bullet); rendered by the orchestrator per
   `references/report-template.md`'s empty-section rules and Review
   Metadata block; surfaced to the user in
   `plugins/paad/skills/agentic-review/SKILL.md`'s Post-Review step
   6. Renaming the prefix or the metadata field in any one place
   without updating the others silently breaks the channel.
   Grep: `verifier-warning` should appear across all four files.

2. **"Sole writer" rule cross-reference.** The rule lives in
   `references/report-template.md` ("The Backlog File" section);
   `references/verifier.md` step 7 back-references it ("see
   `references/report-template.md`'s 'Sole writer' rule"). Renaming
   the section heading rots the back-reference. Grep: `Sole writer`
   should appear in both files.

3. **`[ref-loaded:<lens>]` echo-back tokens.** Each specialist ref's
   dispatch in `SKILL.md` Phase 2 instructs the subagent to emit
   `[ref-loaded:<lens-name>]`. The verifier's pipeline step 0 and
   "Specialist status detection" table key on these tokens.
   Adding/renaming a specialist requires updating the dispatch
   prompt, the verifier's table, and the specialist's BAIL block
   (which also embeds the lens name in the ref-loaded line).

4. **`BAIL: <lens> <reason>` token shape.** Each specialist ref with
   a bail-out clause emits `BAIL: <lens-name> <reason>` as line 2 of
   a bail output. The verifier's "Specialist status detection" table
   and pipeline matches them tolerantly. The
   `report-template.md` empty-section rule keys on
   `BAIL: spec-compliance` specifically for the "Intent sources
   consulted: none — Spec Compliance skipped" metadata branch.
   Renaming a lens or its reason string requires updates in the ref,
   the verifier's table, and (for spec-compliance specifically) the
   report-template empty-section rule.

5. **Idempotent HTML escape and variable-length CommonMark fence.**
   The Field-encoding rules in `references/verifier.md` are
   load-bearing for backlog write/rewrite safety. Any agent that
   rewrites an existing entry must re-apply the rules; a future
   refactor that introduces a separate "rewrite" path must read the
   rules section.

If a future PR touches any named section, walk this list and
hand-verify the linked sites still agree. None of this is enforced
by `make test` today.

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

## Phase 2 / Commit 1 — Integration & Data extraction

### Dispatch shape transfer (agentic-review → agentic-architecture)

The Phase 1 dispatch shape — `**<Lens> additional instructions:**
The X specialist's instructions live at \`references/<lens>.md\`.
That file covers <inventory>. The dispatch prompt for the X
specialist must include this instruction verbatim:` followed by a
blockquote `> Read \`references/<lens>.md\` ... [ref-loaded:<lens>]
... binding.` — applied to `agentic-architecture/SKILL.md` line 98
unchanged. Sentinel `deploy-coupling vector` migrated cleanly:
0 in SKILL.md, 1 in ref. `make check-extracted-refs` went red at
the manifest-add step and green after the dispatch rewrite, on
both first attempts. No path-resolution edge cases surfaced. The
shape transfers verbatim across parent skills with no per-skill
adaptation needed.

### Tournament-dispatched enrichment (Pushback Issue [7] discipline)

For Phase 2, pre-extraction enrichment used the new tournament
discipline: two `general-purpose` subagents dispatched in parallel
with identical prompts, both told they're competing for "five
points." The two proposals overlapped on ~90% of structure (same
8 flaw subtypes + 2 strength subtypes, similar drop-rule taxonomy,
similar severity floors) but diverged meaningfully on bail-out
(Proposal A: single `BAIL:` token + escape hatch in prose;
Proposal B: tiered ladder with `BAIL-PARTIAL` for monolith-with-
egress) and on bonus content (A: 2-of-5 evidence-requirement
supplement; B: cross-lens routing table).

Ovid picked Proposal A wholesale on the bail-out simplicity
trade-off (single token + escape hatch reads cleaner than tiered
encoding for this lens's most common case — pure CLI tools). The
landed ref is Proposal A's content with no modifications.

**Observation, not yet a cross-phase rule:** tournament dispatch
costs roughly 2× the wall-clock of a single dispatch but produces
two independent proposals to compare side-by-side, which exposes
trade-offs the orchestrator must surface for judgment (here: the
bail-out simplicity-vs-rigor decision). Whether this depth pays
its cost across the remaining four lenses is the open question for
commit 2.

### Existing inline rule modifications

Proposal A's authored enrichment preserved the existing inline
rule in the `## Verbatim from SKILL.md` block but layered sharper
semantics on top:

- "If this is not a distributed system…" → formalized as `BAIL:
  integration-data not-distributed` machine-readable token, with
  explicit escape hatch for single-service backends with public
  API surface (the case the original rule glosses over).
- "Services coupled through shared schemas" → split into
  `data-ownership-violation` (concurrent writers, flaw 17) and
  `shared-database` (cross-unit reads of private tables, flaw 18).
  The conflated phrasing produced findings that didn't map cleanly
  to either flaw number.
- "Non-idempotent operations" → added inverse drop rule (must-not-
  retry operations like payment capture should *not* be flagged
  for missing idempotency).
- "API contracts without compatibility discipline" → absorbed into
  `contract-drift` subtype with sharper criteria (evidence of
  producer/consumer disagreement, not merely absence of a
  registry).

The verbatim block stays unchanged; the authored enrichment
overrides via sharper rules.

### Smoke test outcome (paad-as-fixture)

Token present + bail-out fires = **Pass** (row 1 of the four-
outcome verdict table). The Integration & Data lens correctly
recognized paad as Tier-0 (single deployment unit, no inter-unit
communication surface) and emitted `BAIL: integration-data
not-distributed`. The verifier classified the bail as legitimate
in its Analysis Metadata. Coverage Checklist marked flaws
14, 15, 16, 17, 18, 19, 24, 26 and strengths S6, S12 all as "Not
applicable (single deploy unit)." No findings were produced for
this lens, exactly as the new ref instructs.

The bail-out shape that landed in the report (`BAILED legitimately:
not-distributed`) shows the verifier surfaces the bail reason
verbatim in the report's metadata — useful for downstream
debugging if a future bail is ever called into question.

## Phase 2 / Commit 2 — Four remaining specialists

### Tournament cadence held; sequential at lens level

Four lenses extracted in sequence (Coupling & Dependencies →
Error Handling & Observability → Security & Code Quality →
Structure & Boundaries), each with a tournament dispatch
(two parallel `general-purpose` subagents, identical prompts).
Per-lens outcomes:

- **Coupling & Dependencies:** Ovid picked **B**. Distinguishing
  feature was a dedicated lens-boundary table (8 rows) explicitly
  routing diagnostics out to Structure / Integration. Loser had
  a "git log on the file before flagging" calibration rule and a
  typestate drop-rule that B lacked.
- **Error Handling & Observability:** Ovid picked **A**. A's
  three-way split of flaw 21 (`missing-emission` / `no-correlation`
  / `log-without-trace`) mapped to three different fix patterns;
  loser's two-way split was leaner but lost distinguishability.
  Bonus: A's `wrong-error-type` and `config-unsafe-default` are
  named flaws unique to that proposal.
- **Security & Code Quality:** Ovid picked **B**. B added
  `supply-chain-discipline` as an S10 strength (covers
  vuln-scanning + SBOM + signed artifacts) that A missed. B's
  drop-rule 6 (dynamic imports / plugin registries / framework
  auto-discovery) prevents the most common false-positive class
  for dead-code findings.
- **Structure & Boundaries:** Ovid picked **A**. A's anchor 7
  ("refactor-history calibration" — `git log` patterns calibrate
  severity: recent restructure → caveat or drop, long quiescence
  → severity ↓, frequent firefighting → severity ↑) was the
  unique contribution. B had finer subtype granularity
  (`singleton-mutable`, `god-module`) but lacked the calibration.

### Cross-lens consistency emerging

By lens 4, the Phase 2 enrichment shape has **stabilized into
a 9-section template** that every lens shares:

1. Inline-rule scoping preamble (3–5 sharpenings of the verbatim).
2. Anchoring (5–7 numbered facts to enumerate).
3. Bail-out (3–5 reasons + escape hatch).
4. Finding subtypes (closed-set table per flaw + per strength).
5. Drop rules (8–13 false-positive guards).
6. Severity floor (High / Medium / Low minima per subtype).
7. Lens-boundary discipline (table routing to sibling lenses).
8. Evidence requirements (at-least-two-of-N checklist).
9. Scale rigor (Trivial / Small / Medium / Large guidance).

This template was not specified up front — it emerged from
the Integration & Data ref (commit 1) and propagated through
the four B-commit lenses via subagent template-study. Phase 3
(`agentic-a11y` references conversion) should adopt the
template as the explicit starting point rather than re-deriving
it.

### Sentinel-collision lesson (logged once for future phases)

Commit 2 hit one sentinel collision: `telemetry-deferred-to-platform`
was both a bail-out reason in `error-handling-observability.md`
and named in the SKILL.md inventory line that summarized the ref's
bail-outs. The structural validator caught it (sentinel must NOT
appear in SKILL.md), and the recovery was to pick a different
sentinel from the body (`fails-open` from the severity-floor
section).

**Discipline going forward:** pick a sentinel that names a
*diagnostic detail* in the ref body, not a *labeled subtype or
bail-out reason* that the inventory line will likely summarize.
Internal phrases like `deploy-coupling vector` (Phase 2 commit 1),
`abstraction-by-anticipation` (commit 2 / coupling), `fails-open`
(commit 2 / error-handling), `build-time bake-in` (commit 2 /
security), and `refactor-history calibration` (commit 2 /
structure) all met this bar — none are subtype labels, none
appear in inventory lines.

### Tournament-dispatch cost vs. value (preliminary)

Five tournaments dispatched (one per lens, plus the Phase A lead).
Wall-clock cost: each tournament adds 2–3 minutes of subagent
time plus 1–2 minutes of orchestrator surfacing + Ovid judgment.
Net per lens: ~5–8 minutes of human-in-the-loop time.

Value: in three of five tournaments, Ovid picked the proposal
that had a *unique structural contribution* the loser lacked
(B.1 lens-boundary table; B.3 supply-chain strength; B.4
refactor-history calibration). In one (A.2 / Integration &
Data), Ovid picked the simpler bail-out (single token + escape
hatch) over the more rigorous tiered ladder. In one (B.2 /
Error Handling), Ovid picked the more granular subtype taxonomy.

**Pattern:** tournaments produce *visibly different* trade-offs
that Ovid can judge in seconds once surfaced tightly. The cost
is mainly in surfacing — pre-tournament concern was subagent
cost, but the actual bottleneck is the orchestrator's
side-by-side compression. Tighter compression (after Ovid's
"wall of text" feedback on the first surfacing) cut surfacing
time roughly in half from B.1 onward.

**Recommendation for Phase 3:** keep tournaments per lens but
budget the surfacing as the dominant cost; subagents are cheap
relative to human-judgment latency. The five-section side-by-side
format that emerged in B.2–B.4 is the working baseline.

### Lens-boundary discipline value

The lens-boundary tables added in B.1–B.4 explicitly route
diagnostics out: "if it's about X, it's owned by lens Y." This is
the single biggest defense against the verifier's deduplication
step doing all the cross-lens routing work. Phase 1 didn't have
these tables; they emerged in Phase 2 and look load-bearing for
quality. Phase 3 should ship lens-boundary tables in every ref
from the start.

## Phase 2 / Commit 3 — Verifier extraction

### Tournament outcome — merge

Sixth tournament dispatch (one for the verifier). Both proposals
converged on the same overall structure but diverged on shape:
A was procedural (numbered 8-step pipeline) with a unique subtype
equivalence table for dedup, prompt-injection preamble, and a
detailed telemetry annotation taxonomy (5 specific tags). B was
reference-shaped with a unique consolidated subtype catalog table
across all 5 lenses and an explicit "what this verifier is NOT"
anti-list that distinguishes from `paad:agentic-review`'s Phase 1
verifier (no in-scope/out-of-scope routing, no backlog dedup, no
field-encoding rules).

Ovid picked **merge** — the contributions were complementary, not
competing. Final ref combines:

- **A's procedural pipeline** (steps 0–7: ref-loaded check → bail
  handling → read code → evidence floor → confidence threshold →
  subtype/impact validation → dedup → final sweep)
- **A's subtype equivalence table** for dedup (mechanical
  prevention of subtle mis-merges like `god-class` ↔ `tight-coupling`
  collisions)
- **A's prompt-injection preamble** (treat all received content as
  untrusted — matches Phase 1 discipline)
- **A's telemetry annotation taxonomy** (`verifier-recategorized`,
  `verifier-impact-adjusted`, `verifier-dropped`,
  `verifier-history-adjusted`, `verifier-corrected-anchor`)
- **A's refactor-history calibration subsection** (git log severity
  calibration with documented annotation)
- **B's consolidated subtype catalog table** (all flaw + strength
  subtypes across 5 lenses in one reference; the verifier consults
  it mechanically)
- **B's "What this verifier is NOT" anti-list** (defensive against
  Phase 1 reflex)
- **B's per-run renumbered IDs note** (S-1, S-2..., F-1, F-2...
  reset every run; explicit "no stable cross-run IDs")

The merge is ~~660 lines and is the largest specialist ref in the
phase — appropriate, because the verifier's job is to enforce the
discipline that the five specialist refs *describe*. Verbatim
section preserves the original 7-step inline list and the Verifier
prompt block; authored enrichment layers on top.

### Sentinel-collision lesson (second in Phase 2)

Initial sentinel `verifier-recategorized` worked, but the SKILL.md
inventory line drafted to match it accidentally included
"refactor-history calibration" — which is the
`structure-boundaries.md` sentinel from commit 2. Validator caught
it on the first `make test` run. Recovery: rephrased the verifier
inventory line to use "git-log-based severity calibration" instead.

**Discipline going forward (refining the commit-2 lesson):** the
sentinel-must-not-appear-in-SKILL.md check applies across the
*entire* SKILL.md inventory — not just the row's own dispatch
paragraph. When writing a new dispatch line that summarizes a
ref's contents, scan the inventory's prose against every previous
ref's sentinel before committing. Two sentinel collisions in
Phase 2 (`telemetry-deferred-to-platform` at B.2 / Error Handling;
`refactor-history calibration` at C.6 / Verifier) suggest this is a
pattern, not a one-off.

### Smoke test deferred to D.5

Per Ovid's session-management decision, Task C.7 (verifier-specific
smoke test) is folded into Task D.5 (holistic end-of-phase smoke
test). Rationale: the verifier's `[ref-loaded:verifier]` token is
subagent output not directly visible to the user — same shape as
A.7 — and the report's Analysis Metadata block is the visible
signal in both cases. One report read at D.5 covers all five
specialists + verifier + report-template wiring.

Phase 3 should keep the C-style smoke test if and only if it can
be made directly observable (e.g., the orchestrator surfacing the
verifier's confirmation token in its summary). Otherwise consolidate
all token-confirmation smoke tests into the end-of-phase report
read.
