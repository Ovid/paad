# Changelog

All notable changes to the `paad` plugin. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions are semver and
match `plugins/paad/.claude-plugin/plugin.json`.

Entries cover the distributed plugin. Repo-only work (project-local
`.claude/skills/`, docs, design notes, README) is listed only where it changes
what a plugin user sees.

## [Unreleased]

## [1.20.0] — 2026-07-26

### Added
- `vibe` gained a **rationalization table** — "When You're About to Skip a Step".
  Every excuse in it was produced verbatim by an agent working a real timed task
  under this skill, not invented: two independent runs both reached for "the
  existing suite is my safety net", and the baseline runs supplied the
  duplicate-coverage and one-line-change variants. Each row pairs the excuse with
  why it is almost-but-not right.
- `vibe`: RED now covers the case where an existing test encodes the old behaviour
  — common on any requirement change, and hit by three of four agents in testing.
  Updating that test and running it before touching the source is a valid RED;
  changing a test *after* the source to make a red suite go green is not, and the
  ordering is the entire difference. New stop condition when the agent cannot tell
  a superseded requirement from a real regression, with matching digraph branch.

- `paad:help` gained a **"Picking between them"** routing block in its overview —
  one line per skill saying what to reach for instead. Routing lives here because
  `help` is already the skill users ask "which one fits my situation", and its
  overview loads only when someone asks that question.
- Four skills (`agentic-a11y`, `agentic-architecture`, `makefile`, `pushback`)
  carry a short **When NOT to Use This Skill** section — 187 words total, six
  bullets. Each names a constraint that binds *while the correct skill is running*:
  don't let an engineering audit be mistaken for a VPAT, don't pad a report when
  the scope is a handful of files, don't edit a generated Makefile, don't run a
  full critique when the user asked for implementation. An earlier draft put such a
  section on all eight skills (1,048 words); the bullets that only said "use a
  different skill" were cut. Skill selection reads the frontmatter description, and
  an agent handed an explicit `/paad:<skill>` does not abandon it — so a routing
  bullet in the body is read only by an agent already past the point of using it.
- **Common Mistakes** tables added to `alignment`, `help`, `makefile`, `pushback`,
  and `vibe`, matching the tables the other four skills already carried. In `vibe`
  and `help` the rows that restated something already written in the same file were
  dropped rather than kept for symmetry.

### Changed
- `help`: description rewritten as a trigger ("Use when the user asks which paad
  skills exist…") so it fires on questions like "what can paad do", instead of
  only on an explicit `/paad:help`.
- `vibe`: description no longer summarizes the skill's guardrails. A description
  that restates the workflow becomes a shortcut Claude takes instead of reading
  the body — which for `vibe` meant skipping the mandatory red/green/refactor cycle.
- Every new rule added in this release states its rule and one sentence of reason,
  not a paragraph. These files are prompts: the rationale costs context on every
  invocation, and `fix-architecture` — which stops when context runs low — was the
  skill that grew most. The full reasoning for each rule lives in this changelog,
  where it costs nothing at runtime and is addressed to the reader who needs it.
- The remaining seven skill descriptions gained a boundary clause naming what each
  skill is *not* for — phrased **negatively only**. The `vibe` fix above is the
  general rule: a description that summarizes what a skill *does* becomes a
  shortcut taken instead of reading the body. "Not for checking code against a
  spec" refines the trigger; "cross-checks two documents against each other" would
  be a workflow summary, and is exactly what these clauses avoid.
- `fix-architecture`: handles a developer who pre-answers or refuses the setup
  questions. An invocation like "fix F-02 and F-11, don't ask me a bunch of
  questions, just go" previously had no rule covering it, so the whole Setup
  conversation — including the dependency scan and the Step 4 plan confirmation —
  got skipped along with the questions. Answered questions may now be skipped; the
  scan and Step 4 may not, because they aren't questions but work that produces
  information the developer doesn't have (that fixing F-02 likely resolves F-11,
  that the batch is sized for solo work in a shared repo — both named in the skill's
  own Common Mistakes). The floor is one message stating every assumption, and one
  confirmation. Being told to skip the questions is not approval of a plan the
  developer has not seen.
- `agentic-review`: the uncommitted-changes pre-flight now stops and waits. It said
  only "ask" while the checks around it said "Stop and wait", so answering on the
  user's behalf was defensible. It isn't a courtesy check: the Verifier reads the
  **working tree** at each finding's `file:line`, so with uncommitted changes
  present it verifies code the specialists never saw — findings get dropped as
  already-handled because an uncommitted edit handles them, and anchors drift
  against the touched-lines map. The digraph node is now `ASK and WAIT`, since a
  bare `ASK:` beside bold `STOP:` nodes read as non-blocking there too.
- `agentic-review`: the Verifier is dispatched with the current contents of every
  file named by a finding. It has its own tools, but a Verifier left to fetch its
  own context under budget pressure pattern-matches the finding text instead — and
  that output is indistinguishable from a real verification pass, so findings reach
  the report carrying severity labels the user reads as confirmed against the code.
- `agentic-review`: Phase 1 step 9 records which adjacent files the caller/callee
  tracing added and carries the list into the report's `Scope:` field. Steps 6-8 are
  the only thing making the manifest wider than the diff, and the manifest feeds all
  six specialists *and* the backlog pre-filter — collapse it and the pre-filter
  narrows with it, so backlog entries in adjacent files stop matching and get
  re-minted as duplicates. Delegating the tracing to the Contract & Integration
  specialist is explicitly not a substitute: its greps inform its own findings, they
  don't widen what the other five read.
- `agentic-review`: large-diff partitioning (500+ lines) is required rather than
  advisory, with a workable fallback. Specialist attention degrades across a long
  input, so one agent reading a 900-line diff whole reviews its tail less carefully
  than its head, and nothing in the output shows which part got the thin pass. When
  12 dispatches aren't affordable, split into two passes over disjoint file subsets
  and say which subset the report covers, rather than silently reviewing at half
  coverage — a thin finding list on a large diff reads as good news. The six
  specialist reference files now scale their size buckets to the file set the
  instance was handed rather than to Phase 1's whole-diff classification, which is
  what the buckets meant once partitioning became mandatory.
- `fix-architecture`: Fix Loop approval points are now stops, not announcements.
  Every pre-flight check ends with "Stop and wait", but the Fix Loop's approval
  points only said "present it and get confirmation" / "Developer chooses" — so
  presenting an approach and starting work in the same turn was defensible. The
  Setup rule (ask, wait, then act) is now stated to apply to the whole loop, with
  two non-approvals named explicitly: the Setup Step 4 batch approval covers which
  flaws are in scope and never how one gets fixed, and a single viable option still
  needs a yes. Reinforced at all three sites, most firmly at the
  not-unit-testable fork where one of the four options being "presented" is *fix
  without tests*.
- `fix-architecture`: marking a flaw "Fixed (pre-existing)" now needs the
  developer's agreement. It was the only outcome in the flaw-validation table with
  no human in the loop, and the only one that both removed work and required no
  permission — while writing a *terminal* status that permanently excludes the flaw
  from later sessions. The agent must now show the commit that removed the flaw and
  the current state of the cited code, and say so rather than guessing when it
  can't identify the resolving commit. Targeted reading is also explicitly not
  grep-only: drifted line numbers or a missing symbol mean read the structure,
  because a rename is not a fix. The digraph routed both this outcome and "false
  positive" straight to marking, bypassing an approval the prose already required
  for false positives; both now go through the developer.
- `fix-architecture`: safety-net tests are **frozen** once the Fix Loop starts.
  Step 3 of Handle Test Failures ("internal unit tests breaking because structure
  changed → propose updating them") previously licensed editing any test, including
  the safety-net tests written minutes earlier — which made the whole phase
  reversible and therefore decorative. Safety-net tests may now be adapted only to
  follow the code (imports, call sites, construction, fixtures); assertions,
  expected values and cases may not be changed, relaxed, skipped or deleted. A
  safety-net test that still fails after its call sites are updated is a behaviour
  change, not a structural one, and routes to the fix-forward-versus-revert
  discussion — it is reporting the regression it was written to catch. The freeze
  covers the tests the phase *credits* as the safety net, written or existing —
  scoping it to "tests written here" switched it off entirely whenever a repo
  already had coverage, which is the common case. Because roughly a quarter of the
  flaw types `agentic-architecture` reports (swallowed errors, non-idempotency,
  hard-coded secrets) are fixed by changing behaviour on purpose, the developer may
  authorize an assertion change at the red-flag stop when the flaw itself is the
  behaviour being asserted. The agent may never make that call alone.
- `fix-architecture` and `agentic-review`: safety gates now require an artifact
  instead of the agent's own say-so. Previously every gate in both skills was
  self-attested — "coverage is good", "tests pass", "baseline is green", "the
  backlog was written" — with nothing forcing the judgement into the open, so a
  hollow gate was indistinguishable from a real one.
  - `fix-architecture` prints a **Safety Net Report** before the first fix: the
    baseline command and counts, pre-existing failures by name, and per flaw the
    named test cases, the command that proved they pass, and the safety-net commit
    SHA. Blank fields are the point — they make a hollow safety net visible.
  - `fix-architecture`: "good coverage" now means naming the specific cases and
    running them. A test file next to the affected code is not coverage.
  - `fix-architecture`: the baseline must be the complete suite with failing tests
    recorded verbatim, and a post-fix failure absent from that list counts as
    caused by the fix — absence of evidence is not a pre-existing failure.
  - `fix-architecture`: the post-fix verification run must be the full suite, not
    the changed module. Structural changes break code at a distance, which is
    exactly what a scoped run cannot see.
  - `agentic-review`: Review Metadata lists all six lenses by name with a per-lens
    status, including `NOT DISPATCHED`. A lens that never ran leaves no other
    trace, so this is the only place its absence can surface.
  - `agentic-review`: a missing `[ref-loaded:verifier]` token now has a
    consequence — re-dispatch once, then warn that classification and all backlog
    directives are unverified. Well-formed output is not evidence the ref was read.
  - `agentic-review`: backlog counts are read back from the file before being
    reported. Only an attempted-and-failed write may skip the backlog.

### Fixed
- `agentic-review`: the new `When NOT to Use` section claimed pre-flight stops when
  changes are uncommitted. It doesn't — pre-flight asks, and "review the committed
  state" proceeds. Reviewing a branch with a dirty working tree is supported, so it
  is not a reason to route elsewhere; only the primary-branch half of that bullet
  survives.
- `fix-architecture`: resolved a contradiction between the Safety Net commit and
  manual-commit mode. One line said safety-net tests are committed "so they survive
  if a fix is reverted"; two lines later, manual mode said to leave changes staged.
  A manual-mode session that hit the revert path destroyed the safety-net tests
  along with the fix. Commit mode now governs fix commits only — the Safety Net
  phase commits in both modes.
- `agentic-review`: the Verifier is now dispatched with the touched-lines map, the
  diff, and the manifest. `references/verifier.md` classifies scope by checking each
  finding's anchor line against that map, but the Phase 3 dispatch listed only
  findings and the backlog slice. Without the map, blame degrades to file
  granularity, the out-of-scope bucket empties, and Post-Review reports "No
  out-of-scope bugs found" without ever having determined it.
- `agentic-review`: the specialist count is now fixed at six everywhere. The
  Common Mistakes rule said "5+" while the Phase 2 table listed six, and only Spec
  Compliance was described as running unconditionally — between them, dropping a
  lens looked sanctioned. Phase 2 now states that all six dispatch every run, that
  whether a lens applies is the specialist's call rather than the orchestrator's,
  and that a predicted `BAIL:` is never a substitute for one that happened.
- `agentic-review`: the "When NOT to Use" note no longer implies the specialist
  count is negotiable — the judgement call is whether to run the skill, not how
  many of the six lenses to dispatch.
- `fix-architecture`: Safety Net gate no longer deadlocks; stops committing reverts.
- `vibe`: removed two invented retry loops, one of which gave wrong advice.
- `agentic-a11y`: existing-tooling gate now has a DROP edge.
- `makefile`, `agentic-architecture`, `alignment`: three review corrections.
- All skills: digraphs moved to the same relative position (after the intro, before the first `##`).
- `scripts/lint_digraphs.py`: dropped the `style=` false positive, fixed chained-edge parsing.

## [1.19.0] — 2026-07-25

### Added
- Every skill except `help` now carries a digraph of its own control flow:
  `agentic-architecture` (analysis flow), `agentic-a11y` (audit flow),
  `alignment` (Phases 2–4), `pushback` (Phases 1.5, 2, 3),
  `vibe` (GREEN/REFACTOR/repeat and the skip-TDD path),
  `fix-architecture` (every stop branch and the Safety Net gate).
- `make check-digraphs` now lints the digraph contents with graphviz
  (`scripts/lint_digraphs.py`), not just the presence of a ```dot fence.

### Fixed
- `agentic-review`: digraph matches Rule 0 routing and the uncommitted-changes stop.
- `makefile`: `shape=` no longer attached to an edge; all nodes declared.

## [1.18.0] — 2026-05-02

### Changed
- `agentic-review`: tightened contracts across the `references/` package,
  plus pushback corrections to the references hardening.

## [1.17.0] — 2026-05-01

### Changed
- `agentic-review`: deterministic bug-class derivation and a closed enum for
  Spec Compliance.
- `agentic-review`: stable status tokens for out-of-scope routing and bail-outs.
- `agentic-review`: untrusted-data preamble propagated to the verifier and
  orchestrator.
- `agentic-review`: ref-loaded echo-back tokens for subagent dispatch.
- `agentic-review`: field-encoding rules for backlog entries; confidence
  mapping codified.
- `agentic-review`: thicker error-handling and contract-integration references.
- `make check-extracted-refs` hardened against silent no-ops.

## [1.16.0] — 2026-05-01

### Changed
- `agentic-review` split into a `references/` package: five specialist lenses,
  the Verifier, and the Phase 4 report template each extracted to their own
  file, flattened to one directory level.

## [1.15.0] — 2026-05-01

### Added
- `agentic-review`: Spec Compliance specialist extracted to `references/`.
- `make check-extracted-refs` — structural guardrail (manifest + check target)
  so extracted references cannot silently drift from the skill.

### Fixed
- `agentic-review`: obsolete `Plan` value dropped from the backlog bug-class enum.
- `agentic-review`: clearer `.gitignore` advice in the security warning; assorted
  arguments, pre-flight, and Phase 2/3 contract gaps closed.
- `help`: `agentic-review` dispatches 6 specialists, not 5.

## [1.14.0] — 2026-05-01

### Changed
- `agentic-review`: the Plan Alignment specialist is replaced by a Spec
  Compliance specialist.

## [1.13.1] — 2026-04-26

### Changed
- `agentic-review`: Post-Review announces the out-of-scope summary explicitly.

## [1.13.0] — 2026-04-26

### Added
- Every skill announces `Running paad:<skill-name> v<version>` on invocation, so
  it is always visible which skill ran and which version produced the behaviour.

### Fixed
- `agentic-review`: soft-warning threshold and empty-Suggestions behaviour aligned.

## [1.12.0] — 2026-04-26

### Added
- `agentic-review` scope classification: findings are split in-scope /
  out-of-scope against a touched-lines map built in Phase 1, with a documented
  backlog file format and lifecycle for the out-of-scope ones.
- `agentic-review`: specialists must attribute findings to their model; Phase 3
  verifier handles classification and backlog dedup; Phase 4 handles empty and
  failure cases; Post-Review warns on security findings and backlog size.

## [1.11.1] — 2026-04-26

Version-numbering note: this release also carried the new `fix-architecture`
skill, which under strict semver warranted a minor bump.

### Added
- `/paad:fix-architecture` — work through architectural flaws documented in a
  `paad/architecture-reviews/` report, resumable across sittings.
- Digraphs for `alignment`, `pushback`, `vibe`, and `makefile`.
- `Makefile` with validation and consistency checks (`make test`).
- Experimental skill copies for Kiro, Antigravity, and Cursor users under
  `kiro_and_antigravity/`.

### Changed
- Skill descriptions rewritten as invocation triggers rather than workflow
  summaries, so Claude picks the right skill from the user's phrasing.
- `alignment`: the TDD task rewrite is skipped when it isn't needed.
- `fix-architecture`: named phases, complexity assessment, accurate triage
  labels; safety-net tests always written before any refactoring, and before any
  fixes in multi-flaw batches; staleness measured by time, not commit count.

## [1.11.0] — 2026-03-15

### Added
- `/paad:makefile` — create or update a project Makefile with standard targets,
  asking before modifying any target that already exists.

## [1.10.0] — 2026-03-15

Version-numbering note: 1.9.0 was never released; 1.8.0 bumped straight to 1.10.0.

### Added
- `pushback`: scope shape check.

### Changed
- **Breaking:** `/paad:a11y` renamed to `/paad:agentic-a11y`.
- `help` output corrected; documents `help` usage and notes that `pushback` and
  `alignment` are worth running more than once.

## [1.8.0] — 2026-03-14

### Added
- `/paad:help` — overview table plus per-skill detail for every paad skill.
  Skill changes now require updating `help` to match.

## [1.7.0] — 2026-03-14

### Changed
- **Breaking:** `/paad:architecture` renamed to `/paad:agentic-architecture` and
  rewritten as a multi-agent analysis.

## [1.6.0] — 2026-03-14

### Added
- `/paad:vibe` — small fixes (1–3 files, same module) at vibe-coding speed with
  TDD guardrails instead of skipped tests and duplicated code.

## [1.5.0] — 2026-03-14

### Added
- `/paad:alignment` — verify requirements/specs against implementation plans,
  with a TDD rewrite of the resulting tasks.

## [1.4.0] — 2026-03-14

### Added
- `$ARGUMENTS` support across all skills, so scope (a path, directory, or branch)
  can be passed positionally: `/paad:<skill> path/to/scope`.

## [1.3.0] — 2026-03-14

### Added
- `/paad:pushback` — review a spec, PRD, or design plan before implementation
  begins.

## [1.2.0] — 2026-03-14

### Added
- `/paad:a11y` — accessibility and WCAG 2.2 audit for user-facing apps.

### Changed
- Skills write their output to `paad/*` directories.

## [1.1.0] — 2026-03-14

### Added
- `/paad:agentic-review` — multi-agent code review of the current branch.
- MIT license.

## [1.0.0] — 2026-03-14

### Added
- Initial release: `paad` plugin marketplace with the `architecture` skill.

[Unreleased]: https://github.com/Ovid/paad/compare/paad--v1.20.0...HEAD
[1.20.0]: https://github.com/Ovid/paad/releases/tag/paad--v1.20.0
[1.19.0]: https://github.com/Ovid/paad/releases/tag/paad--v1.19.0
