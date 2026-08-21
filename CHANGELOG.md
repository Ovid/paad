# Changelog

All notable changes to the `paad` plugin. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions are semver and
match `plugins/paad/.claude-plugin/plugin.json`.

Entries cover the distributed plugin. Repo-only work (project-local
`.claude/skills/`, docs, design notes, README) is listed only where it changes
what a plugin user sees.

## [Unreleased]

### Fixed
- **`/paad:pushback` and `/paad:alignment` no longer advance to the next issue
  when you ask a question about it.** They answer and re-put the same options;
  only a decision or "stop" moves on. ([#13](https://github.com/Ovid/paad/issues/13))

## [1.30.0] — 2026-08-20

### Added
- **`/paad:agentic-owasp [scope]` — multi-agent security review against the
  OWASP Top 10:2025. Experimental.** Seven specialists cover the ten categories;
  a finding ships only if it traces an attacker-controlled source to a sink and
  says why the controls in that path do not hold, otherwise it becomes a
  hardening note. It reads code — it never starts the app, reaches a host, or
  runs attacker-shaped input without its own explicit yes, and it never fixes
  what it finds. Reports land in `paad/owasp-reviews/`. See README for the
  design and `/paad:help agentic-owasp` for arguments.
- **`/paad:handoff [save|resume]` — hands this session's work to a fresh
  session, in writing. Experimental.** Writes a `handoff.md` you can read and
  correct before anything is built on it, which is the one thing `/compact`
  cannot offer. Verifies with tools whatever is checkable, marks the rest
  inferred. See `/paad:help handoff`.

### Changed
- **`/paad:pushback` findings now name what would change their severity** — the
  off-disk fact that would move or dissolve the finding and what it flips to, or
  an explicit "unconditional".
- **`/paad:pushback` reviews documents, not just specs.** Its input scan now
  finds agent steering files (`CLAUDE.md`, `AGENTS.md`, `.cursorrules`,
  `.kiro/steering/`, copilot instructions) and generated `paad/*-reviews/`
  output. Claude Code only: the Kiro and Antigravity exports strip the Input
  Resolution section, so those copies still expect you to name the document.

### Fixed
- **`/paad:pushback`'s reality check missed old invalidating commits.** Phase 1
  ran `git log --oneline -50 --since="2 weeks ago"`; the two limits are ANDed and
  the date usually bound first, so a document broken by an eight-month-old commit
  was reported clean. Now `git log --oneline -50`.
- **`/paad:pushback`'s first digraph sent all three terminal nodes to Phase 2,**
  skipping Phase 1.5 Scope Shape, which itself had no entry edge. Both fixed.

## [1.24.1] — 2026-08-01

### Fixed
- **The README's update instructions no longer mention `/plugin update`.** That
  slash command does not exist — `update` is not one of `/plugin`'s
  subcommands, so it silently opens the plugin browser and discards its
  arguments. The README carried it as a warning, which still left readers a
  command string to try. The panel action (**Installed** → **paad** → **Update
  now**) and the `claude plugin update paad@paad` shell CLI are what work, and
  they are now all the docs describe.

## [1.24.0] — 2026-08-01

### Added
- **`paad:rethink` (experimental) — verify the premises under options you have
  already been given.** Shipped experimental alongside `agentic-dedup` and
  `test-roadmap`: its arguments, verdicts, and output shape may change, or the
  skill may be withdrawn, in any release including a patch. Where `pushback` critiques a spec before anyone builds it, `rethink`
  critiques an *answer*: it extracts everything a recommendation depends on,
  including the assumptions nobody stated, and checks them against primary
  sources — the software, not the documentation describing it. It reports one
  of five verdicts, and the one that earns its keep is **Lucky**: premises that
  hold but that nobody checked. A conclusion that is right by luck reads
  exactly like one that is right by method, right up until it isn't.

  It deliberately does not produce an option list. An alternative appears only
  when verification exposed a defect, and then exactly one, tied to that
  defect. It writes no files.

  Because you probably ran it *unsure* about the options, it does not stop at
  the verdict. Every run ends by re-presenting the options in plain language —
  no jargon, no internal names, pros and cons for each — and recommending one
  with its reason. Where the call also turns on something it cannot see, like a
  deadline or an unshipped roadmap, it gives both halves: the option the
  evidence supports, plus the specific missing input and what it would flip the
  answer to. It goes silent only when the evidence supports no default at all.

### Changed
- **`paad:pushback` now has to defend every finding it raises.** Before an issue
  is presented it must be statable as "if the spec ships as written, **Y**
  happens, because **Z**" — Y a concrete consequence, Z a mechanism resting on a
  named file and line, command output, or commit. Candidates that can't fill
  both are dropped, and the run reports how many were discarded, so a short
  review is visibly short on purpose rather than short on effort. Omissions
  still qualify: "the spec permits both A and B, they produce different results,
  and nothing selects between them" is defensible even before the code exists.
  A bug in the surrounding code earns a ranked slot only when it makes the
  spec's own deliverable unreachable; otherwise it gets one line at the end.
  Pressure-testing showed the real work happens while writing Z — you cannot
  fill it without going to the code, and going to the code is what kills the
  findings that don't survive.
- **`paad:pushback` no longer writes a report by default.** It wrote one on
  every run, including a hundred-plus lines restating a review the user had just
  watched happen. Now the report is for what the conversation loses: it lands
  when issues went undiscussed, or when you ask for one. Its summary drops the
  derivable counts and states in a sentence what has to happen before
  implementation, instead of a ready/not-ready verdict that reviewers kept
  overriding anyway. The end-of-run question now offers spec, report, or both,
  which is what it always meant.
- **`paad:pushback` asks before editing your spec after you stop the review.**
  "Good enough" ends the review, not just the current issue; applying changes
  you already agreed to is fine, but it confirms first.
- **`paad:pushback` no longer counts requirements to decide a spec is too big.**
  A dozen requirements can be facets of one small change. It estimates the diff
  instead.
- **`paad-analyst` can now read the web.** The read-only analysis subagent
  gains `WebSearch` and `WebFetch` so `rethink` can check a claim against a
  vendor's own documentation. It holds repository and network access at the
  same time, so its instructions now forbid putting repository content into an
  outbound request — no source, paths, or identifiers in a search query, and no
  URL assembled from anything it read. The other four dispatching skills inherit
  the capability; they had no reason to leave the repository before and still
  don't, and the agent is told to prefer the local answer.

  On Pi this maps to nothing, because Pi has no web tool. `rethink` there
  verifies against the repository alone and returns `Ungrounded` for anything
  that needs an outside source. See README's Pi section.

- **`vibe` and `makefile` now announce what they wrote too.** 1.23.0 gave the
  `Files written or updated:` block to the eight skills that produce reports and
  left out the two that write code and configuration. `vibe` was the gap that
  mattered — it is the skill that writes and commits source. Both now close a
  run with the file list, and `make check-announce` enforces it rather than
  relying on anyone noticing.
- **The announce block names artifacts, not every path.** The rule said "every
  path it touched", which on a large run buries the line that needed reading.
  The test is visibility, not file type: reports, indexes, backlogs, roadmaps,
  findings logs, and edited spec and plan documents get named individually,
  because a developer never sees them land. Source and test files are the work
  they are already watching, so they come as a count with a pointer to the diff;
  naming a few is allowed, never required. `fix-architecture` motivated it — its
  prose demanded every file while its own example listed only the report, so a
  session touching thirty files was told to list all thirty. `test-roadmap`
  execute mode gets the same threshold.

## [1.23.0] — 2026-08-01

### Added
- **Pi package support, experimental.** A root `package.json` declares the
  skills directory as a [Pi](https://pi.dev/) package, so
  `pi install git:github.com/Ovid/paad` installs every canonical PAAD skill.
  The multi-agent skills additionally need a Pi subagent extension and a
  read-only analyst agent, neither of which can ship inside the package — Pi's
  manifest has no way to declare agents. Without them those skills run every
  lens in one context with the full toolset, silently: no parallelism, no
  context isolation, and no read-only guarantee. The README says so, and
  `scripts/convert_skills.py` now generates `pi/agents/paad-analyst.md` — a Pi
  translation of the plugin's analyst, restricted to
  `read, grep, find, ls, bash` — for users to drop into `~/.pi/agent/agents/`.
  Packaging and layout may change or be withdrawn in **any** release, including
  a patch release — the semver promise the Claude Code plugin carries does not
  apply.

### Changed
- **Every skill that writes a file now ends by listing what it wrote.** Runs
  were leaving reports, indexes, backlogs, roadmaps, findings logs, and edited
  spec documents in the repo without the developer noticing. `agentic-review`,
  `agentic-architecture`, `agentic-dedup`, `agentic-a11y`, `alignment`,
  `pushback`, `fix-architecture`, and `test-roadmap` now print a
  `Files written or updated:` block — one line per path, marked new or
  updated — before the summary and next-step advice. `alignment` and `pushback`
  had no closing announcement at all; the others named the report but not the
  index or backlog they also touched.
- **`test-roadmap` now says how it is meant to be used, every run.** Developers
  were running it once, getting a roadmap, and stopping with no tests written.
  Build mode's handoff now states that it planned the work and wrote no tests,
  and that one phase lands per run. Execute mode gains a final step: name the
  next phase and say to run `/paad:test-roadmap` again — or, when every phase has
  landed, say the roadmap is finished and stop inviting further runs. The README
  and `paad:help` entries lead with the same run-once-then-repeat model.

## [1.22.0] — 2026-07-26

### Changed
- **Analysis subagents no longer carry file-editing tools.** `agentic-review`,
  `agentic-dedup`, `agentic-a11y`, and `agentic-architecture` now dispatch every
  specialist and verifier as `paad-analyst`, a subagent type whose toolset omits
  `Edit`, `Write`, and `NotebookEdit`. Subagents had been observed editing source
  code to test whether a finding was real. Running the existing test suite, a
  linter, or a type checker unchanged is still allowed.
  This closes the observed failure mode, not the whole category: `Bash` stays,
  because the `agentic-dedup` and `agentic-architecture` specialists do their own
  `git`/`find` recon, so a subagent that ignores its instructions can still reach
  `sed -i` or shell redirection. That is prose-enforced, not mechanical.
- Each dispatch prompt also states the rule in prose, because the exported
  Kiro/Antigravity copies have no subagent-type mechanism and the prose is the
  only protection there. Specialists cap a finding's confidence at 79 when
  confirming it would require a code change and say what would confirm it;
  verifiers apply their skill's existing drop rule instead of a cap.
- In Claude Code, `agentic-a11y` and `agentic-architecture` subagents now receive
  untrusted-input handling, which they previously had no form of — their
  specialists and verifiers ran against arbitrary repositories with no injection
  defense. This arrives via the shared `paad-analyst` role prompt, which the Kiro
  and Antigravity exports do not include, so those copies still lack it.

### Fixed
- **`test-roadmap`: the `break-it-check` worktree no longer lands under `.git/`.**
  `git worktree add .git/…` hard-fails with `could not create leading
  directories` wherever `.git` is a file rather than a directory — a submodule, a
  `git worktree add` checkout, or a `--separate-git-dir` repo. It now goes to
  `${TMPDIR:-/tmp}/paad-test-roadmap-<run-id>/<phase>`, which keeps the original
  guarantee that nothing the gate creates lands in your working tree.
- **`test-roadmap`: the worktree sweep no longer destroys a concurrent session's
  work.** It filtered by path prefix, which identifies "worktrees under this
  path" rather than "worktrees belonging to my run" — so a second session's sweep
  force-removed a live sibling worktree mid-mutation. It now requires an exact
  path-component match on the current run's id.

## [1.21.0] — 2026-07-26

### Added
- **Experimental skills.** Two skills ship as explicitly experimental: their
  arguments, output paths, and behavior may change or be withdrawn in any
  release, **including a patch release**. The semver promise the other skills
  carry does not apply to them. Each carries an `EXPERIMENTAL` banner as the
  first thing in its body, an `EXPERIMENTAL.` lead in its frontmatter
  description, and the word "experimental" in `paad:help` and the README. They are marked
  rather than renamed — an `experimental-` name prefix would force a breaking
  rename the day one graduates.
- `agentic-dedup` (experimental) — a multi-agent hunt for **semantic** duplication: code
  that means the same thing behind different names, syntax, control flow, or
  independently evolved implementations. Not a syntactic clone detector; a
  finding must show shared domain meaning, and findings resting on name
  similarity, field-shape similarity, or visual structure are rejected in
  verification, as is any duplication that turns out to be an intentional
  bounded-context boundary. Six discovery strategies feed five specialists
  (Semantic Equivalence, Type & Constraint Equivalence, Domain Boundary &
  Intent, Divergence Risk, Refactoring Safety) and a skeptical verifier.
  Reports to `paad/dedup-reviews/` with a cross-run `INDEX.md`, states each
  constraint relationship as exact / overlap / subset / superset / drift, and
  records rejected candidates so the next run does not rediscover them. It
  never refactors — the report is the deliverable. Arguments: a path scope,
  `--changed <base>`, `--type-constraints`, `--domain "<term>"`.
- `test-roadmap` (experimental) — plans and builds a test suite that catches real
  regressions, in phases, across as many sessions as it takes. Every phase must
  name the bug it would catch; one that cannot is coverage theater and gets
  rewritten or dropped. Before a phase counts as done it injects that very bug
  in a disposable `git worktree` and confirms the test goes red — a passing
  command and a covered line are never accepted as proof a test is any good.
  Grades pre-existing tests against a test-theater catalog (assertion-free,
  tautological, snapshot-only, over-mocked, happy-path-only), logs concrete
  bugs it finds while pinning behavior without ever fixing them, and resumes
  across unrelated commits, squash merges, and fresh clones. Routing is one
  file-existence check: `paad/test-roadmap/test-roadmap.md` absent → build
  mode, present → execute mode.

  **This is the first paad skill that writes and commits code** — tests, one
  commit per phase, onto your working branch. It refuses to run on
  `main`/`master`/`trunk` and offers to create a working branch first.

  Adapted from [Ovid/test-suite-generator](https://github.com/Ovid/test-suite-generator),
  which was always intended to land here; that repo's design doc and decision
  log remain the long-form record.

### Changed
- **Repo tooling.** `make check-extracted-refs` and its 163-line self-test are
  replaced by `make check-references` (`scripts/check_references.py`). The old
  check verified a *migration*: that a chunk of prose had moved out of a
  SKILL.md into `references/`, tracked by a hand-maintained manifest of sentinel
  sentences. That migration finished; git history is its record, and every new
  extraction meant inventing another sentinel. The new check verifies the
  invariant that actually persists — every `references/` path named anywhere in
  a skill resolves to a real file, and every reference file is named by
  something. It covers all 13 reference files instead of the manifest's 8
  (`test-roadmap`'s were unguarded), needs no manifest, and catches orphaned
  reference files the old check could not see. What it no longer enforces: the
  *wording* of a dispatch line. That convention now lives only in
  `notes/convert-skills.md`.
- `scripts/convert_skills.py` now copies each skill's `references/` into the
  Kiro export. It never did, so `agentic-review` exported as a router pointing
  at eight files that weren't there; `test-roadmap`, which is almost entirely
  reference content, would have been worse. Reference files are rewritten on the
  same terms as SKILL.md bodies rather than copied verbatim, so their output
  paths agree with the SKILL.md that loads them. The text before the first `##`
  is now rewritten too — it holds every digraph by paad convention, and
  `test-roadmap` routes on a path named inside one.

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

[Unreleased]: https://github.com/Ovid/paad/compare/paad--v1.30.0...HEAD
[1.30.0]: https://github.com/Ovid/paad/releases/tag/paad--v1.30.0
[1.24.1]: https://github.com/Ovid/paad/releases/tag/paad--v1.24.1
[1.24.0]: https://github.com/Ovid/paad/releases/tag/paad--v1.24.0
[1.23.0]: https://github.com/Ovid/paad/releases/tag/paad--v1.23.0
[1.22.0]: https://github.com/Ovid/paad/releases/tag/paad--v1.22.0
[1.21.0]: https://github.com/Ovid/paad/releases/tag/paad--v1.21.0
[1.20.0]: https://github.com/Ovid/paad/releases/tag/paad--v1.20.0
[1.19.0]: https://github.com/Ovid/paad/releases/tag/paad--v1.19.0
