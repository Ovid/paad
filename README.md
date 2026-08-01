# PAAD — Defense-in-Depth for AI-Assisted Development

<p align="center">
  <img src="images/paad.png" alt="PAAD — Pushback, Alignment, Architecture, Discipline" width="600">
</p>

## "AI slop" is technical debt with better marketing

We have been accumulating technical debt since long before AI showed up, and
we already know how to handle it: review the requirements, review the plan,
review the architecture, review the code. Every one of those is an old,
boring, well-understood engineering skill.

What AI changed is not the nature of the debt. It's the speed it arrives at.

- **Vibe coding** piles up debt fast.
- **Spec-driven development** piles it up slowly.
- Neither piles up zero.

That's the problem and it isn't new. It's just faster than the review
habits most teams have, so the debt lands before anyone looks at it.

**PAAD** (pronounced "pad") is how you stay on top of it — the same review
layers your team already believes in, applied at the speed the assistant is
working.

## Engineering-driven AI, not AI-driven engineering

Most organizations adopting AI right now have it backwards. A developer tells
the AI what to do and hopes the AI can take over. The AI is happy to oblige —
it always is — and the developer finds out what it decided when the code
lands.

That's **AI-driven engineering**: the assistant sets the pace, and the
engineers are downstream of decisions they never saw made.

PAAD replaces it with **engineering-driven AI**. Same speed, opposite
direction: you see what the AI is about to do while you can still change it,
and you make the calls.

| | AI-driven engineering | Engineering-driven AI |
|---|---|---|
| The spec | Whatever you typed, unchallenged | `pushback` argues with it before anyone builds it |
| The plan | Assumed to match the spec | `alignment` checks both directions |
| The code | A green CI run | `agentic-review` puts six specialists on the PR |
| The structure | Discovered later, expensively | `agentic-architecture` finds it while it's cheap |
| The decisions | The model's | Yours, on the record |

You stay in the driver's seat. That is the point, and it's also the cost: PAAD
gives you visibility and control, not autopilot.

### What PAAD can't fix

An engineer has to drive this — including knowing when the tool is wrong.

- **PAAD reports; you decide.** It doesn't know your deadline, your users, or
  which risk you're willing to carry. A finding is an argument, not a verdict.
- **It's non-deterministic**, like the assistant it's checking. Run it twice
  on the same branch and you'll get overlapping, not identical, results. Run
  the important ones more than once.
- **A report you ignore is worse than no report.** `agentic-architecture` on a
  codebase nobody has time to change just produces a document that makes
  everyone feel bad.
- **It can't fix a problem that isn't technical.** No skill in here rescues a
  project that's short on time, short on staff, or aimed at the wrong thing.
- **It's not a replacement for human review.** It's a much stronger automated
  backstop, which is a different job.

If you want the assistant to think for you, PAAD is the wrong tool. It exists
for engineers who want to stay responsible for the result and need help
keeping up.

## The four letters

PAAD is a system of AI agent skills addressing four common failure modes in
AI-assisted development:

| Area | What it addresses |
|------|-------------------|
| **P**ushback | Weak specs, hidden assumptions, vague requirements, and risky omissions before implementation begins |
| **A**lignment | Gaps between requirements, design, implementation plans, and the work that is actually about to happen |
| **A**rchitecture | Structural issues that make code harder to extend, reason about, and maintain over time |
| **D**iscipline | The need to consistently apply review, testing, and quality checks instead of skipping them under time pressure |

Your team already runs specs, tests, code review, CI, QA, and incident
response — layers that exist because mistakes are cheap to fix early and
expensive to fix late, and because humans are stochastic. AI is stochastic
too. PAAD's argument isn't that AI needs *special* safeguards; it's that AI
needs the *same* safeguards, running fast enough to keep up with it.

It doesn't replace your current AI-assisted development tools; it complements
them. You like [Superpowers](https://github.com/obra/superpowers/)? Use it
with PAAD for even better results.

PAAD supports **Claude Code** natively and ships as an experimental **Pi**
package. It also supports **Cursor**, **Kiro**, and **Antigravity**.

## Star History

<a href="https://github.com/Ovid/star-history">
  <picture>
    <source media="(prefers-color-scheme: dark)"  srcset=".github/star-history/dark.svg">
    <source media="(prefers-color-scheme: light)" srcset=".github/star-history/light.svg">
    <img alt="Star history for Ovid/paad: 59 stars as of 2026-07-25" src=".github/star-history/light.svg" width="800">
  </picture>
</a>

## Why people are using PAAD

The strongest early adoption has come from four skills:

- **`pushback`**, which critically reviews specs before implementation
- **`alignment`**, which checks whether the planned work actually matches the
  spec and design
- **`agentic-review`**, which performs a deeper pre-merge review than the
  lightweight AI review tools many developers are used to
- **`agentic-architecture`**, which allows you to find and fix the tech debt
  you're accruing over time

One user described `pushback` this way:

> “I'm using it for every non-trivial change, and so far, I think I've argued with 2 of maybe 40 recommendations. It has improved EVERY SINGLE spec I've fed it so far.”

Others have shared similar quotes. For one pair-programming session where I
was teaching AI-assisted development, a developer was astonished when they ran
`pushback` and it explained why his carefully thought out spec could not
possibly work.

If "English is the new programming language," `pushback` is the code review.
In practice, `pushback` consistently improves specifications, and `alignment`
catches gaps between the intended work and the implementation plan before
those gaps become expensive.

`agentic-review` serves a different but equally important role: it reviews a
working branch with multiple specialists looking for logic errors, edge cases,
security issues, and integration problems before merge. In practice, it
catches substantially more than the shallow, single-pass AI reviews now common
in tools like GitHub Copilot. It is not a replacement for human review, but it
is a much stronger automated backstop. Running it more than once is valuable.

The other skills are also valuable, especially for architecture analysis,
accessibility review, and smaller task execution with guardrails. But
`pushback`, `alignment`, and `agentic-review` currently form the core workflow
that delivers the most consistent day-to-day value.

## Design philosophy

PAAD is built to be honest about risk. If your spec is weak, your plan is
misaligned, an architectural decision is fragile, or a change introduces
problems, you hear about it early and plainly. It's for developers and teams
who want better outcomes from AI-assisted coding, not just faster output.

That honesty has a price, and it's tokens. A single feature can cost three or
four times as many, because you're paying to review the spec, review the plan,
and review the code on top of writing it. The bet is that this is cheaper than
shipping the wrong thing and rebuilding it — a good bet for software you'll
maintain for years, a bad one for a prototype you'll throw away on Friday.
Match the ceremony to the stakes.

## Workflow

There's a lot to take in with PAAD, [so I've written an article to explain how
to write production-quality code with
it](https://curtispoe.org/articles/watching-claude-sonnet-outperform-opus).

If you are new to PAAD, start with `/paad:help` to see the available skills and when to use them.

Before working in a repository, I usually run `/paad:makefile` to create a
consistent interface for common tasks such as building, testing, linting,
formatting, and coverage. That foundation makes it much easier for both
developers and AI agents to work against the same quality checks.

A typical workflow looks like this:

1. Write your spec.
2. Run `pushback` to critically review the spec before implementation.
3. Create your final implementation plan from the spec.
4. Run `alignment` to verify that requirements, design, and planned work are
   aligned with decisions.
5. Implement the change.
6. Run `agentic-review` on the working branch before merging (often more than
   once).

Depending on the type of work, I also use (see below for full descriptions):

1. `agentic-architecture` to identify structural issues before they spread
2. `agentic-a11y` for UI changes and accessibility-sensitive work
3. `vibe` for small fixes that still benefit from guardrails

In practice, `pushback` and `alignment` are often worth running more than
once. They are especially useful when a spec evolves or when the
implementation plan changes during execution.

## Installation

### Claude Code

#### Install the plugin

Add the marketplace:

```bash
/plugin marketplace add Ovid/paad
```

Install the plugin:

```bash
/plugin install paad@paad
```

If you're not using Claude Code, see other examples below.

#### Updating the plugin

Installing pins you to the version that was current at the time. New skills and fixes do **not** arrive on their own — you have to pull them, and it takes two steps, because the marketplace catalog and the plugin are refreshed separately.

Refresh the marketplace catalog from GitHub:

```bash
/plugin marketplace update paad
```

Then update the plugin itself:

```bash
/plugin update paad@paad
```

Restart Claude Code to apply the update.

To confirm which version you're on, run any skill — every skill announces its
own name and version on invocation (`Running paad:vibe v<version>`). Compare
that against the version in
[`plugins/paad/.claude-plugin/plugin.json`](plugins/paad/.claude-plugin/plugin.json).
If a skill documented here is missing entirely, you're on an older version —
run the two commands above.

#### Invoking skills

You can invoke skills explicitly with the fully-qualified commands
`/paad:pushback`, `/paad:alignment` and so on. If there are no conflicts with
other skills, you can drop the `paad:`: `/pushback`. Claude Code also
recognizes skill names in natural language, so prompts such as “run a pushback
review on this spec” or “review the architecture of this module” should
trigger the corresponding skill.

### Pi — experimental

Pi support is **not settled**. The package layout, the skills it exposes, and
the extension it depends on may change — or the packaging may be withdrawn — in
**any** release, including a patch release. The Claude Code plugin is the
supported path; if Pi is your daily driver, pin your version and please [file
what breaks](https://github.com/Ovid/paad/issues).

Install PAAD directly from Git:

```bash
pi install git:github.com/Ovid/paad
```

To try a local checkout without installing it permanently:

```bash
pi -e .
```

Invoke a skill with `/skill:<name>` or by name.

#### The multi-agent skills need two more pieces

`agentic-review`, `agentic-architecture`, `agentic-a11y`, and `agentic-dedup`
fan out to subagents. Pi has no subagent support of its own, and Pi's package
manifest has no way to declare agents, so neither piece can ship inside the
package. Without both of them installed, those four skills still *run* — the
orchestrator simply does every lens itself, in one context, holding the full
toolset. You get no parallelism, no context isolation, and **no read-only
guarantee on code the skill is only supposed to read**. Nothing errors and
nothing warns you.

**1. A subagent extension.** Pi ships one as an
[example](https://github.com/earendil-works/pi/tree/main/packages/coding-agent/examples/extensions/subagent),
not as an installable package — it is a clone-and-symlink into `~/.pi/agent/`,
not `pi install`. Follow that example's own README.

**2. The read-only analyst.** This repo generates a Pi copy of the analyst
agent the Claude Code plugin dispatches. Copy it in:

```bash
cp pi/agents/paad-analyst.md ~/.pi/agent/agents/
```

It restricts the agent to `read, grep, find, ls, bash`, which is what keeps an
analysis subagent from editing your code to test whether a finding was real.

Two known rough edges even with both installed. The skills name their subagent
type in Claude Code's syntax (`subagent_type: paad:paad-analyst`), which is not
how Pi's example extension dispatches — you may have to nudge the assistant
toward the `paad-analyst` agent by name. And that extension caps parallel work
at 8 tasks, while `agentic-review` asks for 12 dispatches on diffs over 500
lines; the skill has a documented two-pass fallback for exactly this case, so
say yes to it rather than accepting a half-coverage review.

### Cursor

PAAD skills use the same `SKILL.md` format that [Cursor
skills](https://cursor.com/docs/skills) expect.

All skills (bash/zsh):

```bash
cp -r kiro_and_antigravity/skills/.kiro/skills/* .cursor/skills/
```

All skills (Windows):

```powershell
xcopy kiro_and_antigravity\skills\.kiro\skills\* .cursor\skills\ /E /I
```

One skill (for example, `pushback`):

```bash
cp -r kiro_and_antigravity/skills/.kiro/skills/pushback .cursor/skills/
```

### Kiro

All skills (bash/zsh):

```bash
cp -r kiro_and_antigravity/skills/.kiro/skills/* .kiro/skills/
```

All skills (Windows):

```powershell
xcopy kiro_and_antigravity\skills\.kiro\skills\* .kiro\skills\ /E /I
```

One skill (for example, `pushback`):

```bash
cp -r kiro_and_antigravity/skills/.kiro/skills/pushback .kiro/skills/
```

### Antigravity

Antigravity skills function as wrappers that reference Kiro skill files, so
you need both:

All skills (bash/zsh):

```bash
cp -r kiro_and_antigravity/skills/.kiro/skills/* .kiro/skills/
cp -r kiro_and_antigravity/skills/.agent/skills/* .agent/skills/
```

All skills (Windows):

```powershell
xcopy kiro_and_antigravity\skills\.kiro\skills\* .kiro\skills\ /E /I
xcopy kiro_and_antigravity\skills\.agent\skills\* .agent\skills\ /E /I
```

One skill (for example, `pushback`):

```bash
cp -r kiro_and_antigravity/skills/.kiro/skills/pushback .kiro/skills/
cp -r kiro_and_antigravity/skills/.agent/skills/pushback .agent/skills/
```

### Using skills outside Claude Code

As with Claude Code, with Pi, Cursor, Kiro, and Antigravity, skills are
automatically recognized by your assistant. You can simply ask the assistant to
perform the task, such as:

* “Run a pushback review on this spec”
* “Check whether this plan aligns with the requirements”
* “Analyze the architecture of the backend code”

The assistant will follow the procedures defined in the skill files.

---

### Pushback

#### `/paad:pushback [spec-file]`

If "English is the source code, pushback is the code review."

AI assistants rarely tell you that your spec has problems. `pushback` does. It
critically reviews specs, PRDs, and design plans before work begins so you do
not build on flawed assumptions.

* **Arguments:** `/paad:pushback path/to/spec.md` (specific file) or
  `/paad:pushback` (auto-detect from conversation history or common file
  locations)
* **Source control reality check** — scans recent git history for commits that
  conflict with what the spec assumes, presented before other analysis
* **Scope shape check** — flags unrelated features bundled together and
  oversized specs; suggests splits only when each piece delivers independent
  value
* **6 analysis categories** — contradictions, feasibility, scope imbalance,
  omissions, ambiguity, and security concerns
* **Severity-ordered review** — presents the most consequential issues first,
  one at a time, with concrete options and recommendations
* **Flexible output** — update the spec in place or write a separate report to
  `paad/pushback-reviews/`

---

### Alignment

#### `/paad:alignment [files...]`

AI assistants drift off-scope. `alignment` catches that by checking whether
requirements, design documents, and implementation plans actually match before
code gets written.

* **Arguments:** `/paad:alignment` (auto-detect) or `/paad:alignment
  requirements.md plan.md` (specific files) or `/paad:alignment docs/specs/
  docs/plans/` (directories)
* **Auto-detection** — scans `.kiro/`, `specs/` (spec-kit), `docs/plans/`,
  `docs/specs/`, and common filenames; classifies documents as intent
  (requirements) versus action (tasks)
* **Source control reality check** — scans recent git history for conflicts
  with what the documents assume
* **3 alignment checks** — requirements coverage, scope compliance, and design
  alignment (when design docs exist)
* **Dependency-ordered issues** — surfaces root causes before downstream
  symptoms, one issue at a time
* **Mandatory TDD rewrite** — once aligned, rewrites tasks in
  red/green/refactor format for better implementation outcomes
* **Flexible output** — update documents in place or write a separate report
  to `paad/alignment-reviews/`

---

### Architecture

#### `/paad:agentic-architecture [path...]`

AI can build quickly on weak foundations. `agentic-architecture` identifies
those structural problems before they compound. Five specialists review the
codebase from different angles so issues do not hide behind a single
reviewer’s blind spots. This skill is diagnostic only; it does not propose
fixes.

* **Arguments:** `/paad:agentic-architecture` (full repo) or
  `/paad:agentic-architecture src/` (scoped) or `/paad:agentic-architecture
  packages/api/ packages/shared/` (multiple directories)
* **Parallel analysis** — five specialists run simultaneously, followed by a
  verification phase that filters false positives by reading code and checking
  git history
* **14 strength categories** — including modular boundaries, cohesion,
  coupling, error handling, observability, security, and testability
* **34 flaw and risk types** — including god objects, tight coupling, circular
  dependencies, leaky abstractions, dead code, missing tests, and hard-coded
  secrets
* **Coverage checklist** — ensures every category is assessed
* **Hotspots** — identifies the files and directories most worth reviewing
* **Report** — written to `paad/architecture-reviews/`

#### `/paad:fix-architecture [report]`

Architecture analysis tells you what is wrong. `fix-architecture` helps you
resolve those findings one at a time with a test-first workflow. Each fix is
validated, tested, tracked, and committed so the work can continue across
multiple sessions.

* **Arguments:** `/paad:fix-architecture` (find most recent report) or
  `/paad:fix-architecture path/to/report.md` (specific report)
* **Pre-flight checks** — branch protection, report staleness detection, test
  infrastructure verification, and baseline test run
* **Developer conversation** — confirms solo versus team workflow, batch size,
  auto-commit versus manual commit, flaw triage strategy, and plan
  confirmation
* **Test-first fixes** — validates that each flaw still exists, writes
  safety-net tests where needed, proposes options with tradeoffs, and executes
  using red/green/refactor
* **Status tracking** — records outcomes in the report: Fixed, Won't fix,
  Partially fixed, Skipped, Fixed (pre-existing), Attempted/reverted
* **Flaw dependency detection** — flags when fixing one flaw resolves others
* **Iterative workflow** — designed to run across multiple sessions against
  the same report

Requires a feature branch (not `main` or `master`) and an existing
architecture report.

**Why sequential?** Architecture fixes happen one at a time rather than in
parallel. Fixing one structural flaw often resolves others, and that
dependency can only be discovered sequentially. Worktree-based parallelism
avoids file collisions, but merging multiple structural refactors back
together is a reliable way to introduce new bugs.

---

### Discipline

Code quality rarely degrades in one dramatic change. More often, it slips
through a series of small decisions that each seem reasonable in isolation.

#### `/paad:agentic-review [base-branch] [path]`

Discipline means reviewing before merging, every time. `agentic-review` uses
multiple specialist agents to examine your branch for logic errors, edge
cases, security issues, and integration problems that lightweight AI review
tools often miss.

Where typical AI review features tend to provide shallow, opportunistic
feedback, `agentic-review` is designed as a deliberate pre-merge quality gate:
parallel analysis, finding verification, deduplication, and severity ranking.

* **Arguments:** `/paad:agentic-review` (diff against `main`) or
  `/paad:agentic-review develop` (diff against `develop`) or
  `/paad:agentic-review main src/auth/` (scoped to a directory)
* **Parallel review** — six specialists examine your branch simultaneously
  (Logic & Correctness, Error Handling & Edge Cases, Contract & Integration,
  Concurrency & State, Security, Spec Compliance), then findings are verified
  against actual code and deduplicated
* **Severity ranking** — Critical / Important / Suggestion
* **Spec Compliance** — pulls intent from PR description, plan/design docs,
  recent commits, or branch name; flags missing features, deviations, and
  out-of-scope additions (replaces the older Plan Alignment agent)
* **Out-of-scope handling** — pre-existing bugs persist to
  `paad/code-reviews/backlog.md`; out-of-scope additions are flagged for
  per-PR decision (keep / split / revert) without backlog persistence
* **Report** — written to `paad/code-reviews/`

Requires a feature branch (not `main` or `master`) with committed changes.

#### `/paad:agentic-a11y [path]`

Discipline also means accessibility is not treated as an afterthought.
`agentic-a11y` scans your codebase for meaningful accessibility barriers and
organizes them by who they affect. **Important**: this skill will help
substantially, but human accessibility review of your application is still
required. Accessibility is important, but hard.

Supports **web, iOS, Android, React Native, Flutter, desktop, CLI, and
games**. Evaluates against WCAG 2.2 AA, applied through WCAG2ICT for non-web
platforms, with AAA noted as bonus recommendations.

* **Arguments:** `/paad:agentic-a11y` (full repo) or `/paad:agentic-a11y
  src/components/` (scoped to a directory or file)
* **Automatic platform detection** — identifies the project’s platform and
  adapts checks accordingly
* **Specialists by disability category** — dedicated reviewers for screen
  reader usage, visual and color contrast, keyboard and motor interaction,
  cognitive load, and multimedia
* **Platform-specific agent** (conditional) — dispatched for
  framework-specific pitfalls such as React, Vue, SwiftUI, Jetpack Compose,
  Flutter, Unity, and others
* **Verification phase** — confirms that barriers are real and not already
  handled by the framework, platform, or component library
* **WCAG conformance checklist** plus platform-specific guidance from sources
  such as Apple HIG, Material Design, and Xbox Accessibility Guidelines
* **Impact summary by user group** — explains how the codebase affects each
  disability category
* **Quick wins** — identifies the five highest-impact, lowest-effort
  improvements
* **Report** — written to `paad/a11y-reviews/`

---

### Workflow

#### `/paad:makefile`

Creates or updates a project `Makefile` with standard targets such as `help`,
`all`, `test`, `cover`, `lint`, and `format`. It detects your stack
automatically and never modifies an existing target without asking first.

Note: this skill might be removed in the future, or moved to a different
namespace. Let me know if you rely on it.

#### `/paad:vibe [task description]`

Speed without recklessness. `vibe` supports smaller fixes and quick changes
while keeping TDD guardrails in place.

* **Arguments:** `/paad:vibe` (prompt for the task)
* **Pre-flight checks** before writing code:

  * test infrastructure exists; if not, warn and ask how to proceed
  * scope check; if the change spans four or more files or crosses modules,
    warn that it may not be a good vibe task
  * architecture smell detection; if a simple task requires too much work,
    investigate deeper issues first
  * reusable component search; look for existing utilities before building
    from scratch
* **Mandatory red/green/refactor** — write a failing test, write the minimal
  code to pass, then refactor; if the test passes or fails unexpectedly, stop
  and reassess
* **Post-fix summary** — suggests relevant next steps such as `agentic-review`
  for security-sensitive changes, `agentic-a11y` for UI changes, or
  architecture review if the fix was harder than expected

#### `/paad:help [skill-name]`

Shows help for all PAAD skills or detailed help for one skill.

* **Arguments:** `/paad:help` (overview of all skills) or `/paad:help vibe`
  (detailed help for one skill)

---

### Experimental skills

These skills are shipped so they get real use, but they are **not settled**.
Their arguments, output paths, and behavior may change — or the skill may be
withdrawn — in **any** release, including a patch release. The semver promise
the other skills carry does not apply to them. If you build a workflow on one,
pin your plugin version, and please [file what
breaks](https://github.com/Ovid/paad/issues).

#### `/paad:agentic-dedup [scope]` — experimental

Duplication that a clone detector finds is the easy kind. The expensive kind
is two pieces of code that *mean* the same thing while looking nothing alike —
a validator and a schema that accept the same values, a `for` loop and a
stream pipeline that compute the same total, a permission check reimplemented
through a different helper chain. Those drift apart silently, and the bug
surfaces when one side is fixed and the other is not.

`agentic-dedup` hunts for shared meaning rather than shared text, and reports only what survives verification.

* **Arguments:** `/paad:agentic-dedup` (whole repo) or `/paad:agentic-dedup
  src/auth/` (scoped) or `/paad:agentic-dedup --changed main` (seeded from the
  branch diff) or `/paad:agentic-dedup --type-constraints` (schemas, type
  aliases, validators, DB constraints) or `/paad:agentic-dedup --domain
  "payments"` (scoped to a domain term)
* **Six discovery strategies** — name and concept search, behavioral
  fingerprints, type and constraint equivalence, control-flow normalization,
  tests read as behavioral specs, and a search for an existing canonical
  utility that the duplicates should have been calling
* **Five specialists in parallel** — Semantic Equivalence, Type & Constraint
  Equivalence, Domain Boundary & Intent, Divergence Risk, and Refactoring
  Safety
* **Skeptical verification** — findings based on name similarity, field-shape
  similarity, or visual structure are rejected, as is anything where the
  duplication is an intentional bounded-context boundary and sharing would be
  the riskier change
* **Relationship, not just a verdict** — the type and constraint table states
  whether two constraints are exact, overlapping, subset, superset, or already
  drifting
* **Rejected candidates are recorded** — so the next run does not spend
  context rediscovering the same false positives
* **Report** — written to `paad/dedup-reviews/`, with a persistent `INDEX.md`
  across runs

It never refactors anything. The report is the deliverable.

#### `/paad:test-roadmap` — experimental

PAAD is risky to use with codebases without a strong test suite. This skill
builds that suite for you.

High coverage numbers lie. A line can be "covered" by a test that asserts
nothing — green forever, catching nothing. So when you finally refactor the
scary part of a legacy codebase, the suite stays quiet and the regression
ships anyway.

`test-roadmap` builds the suite that does *not* stay quiet. It pins your
code's **current** behavior, deliberately including the buggy parts, so that
the day you start changing things the tests break loudly and tell you exactly
what you changed.

**Run it once to get a roadmap. Then keep running it — one phase of tests per
run — until the roadmap is done.**

That is the whole usage model, and it is the one thing people get wrong: they
run `/paad:test-roadmap`, get a plan, and stop with zero tests written. The
command does something different every time you invoke it, because it looks
for `paad/test-roadmap/test-roadmap.md` and routes on whether it exists:

| Invocation | What it does |
| --- | --- |
| **1st run** — no roadmap yet | Detects your stack, grades the tests you already have, and writes a phased plan to `paad/test-roadmap/test-roadmap.md`. **Writes no tests.** |
| **2nd run** | Writes Phase 1's tests, proves they catch the bug they claim to, commits them, marks the phase done. |
| **3rd run** | Phase 2. |
| **…** | …one phase per run… |
| **Final run** | The last phase lands and the skill tells you the roadmap is finished. Then you stop. |

So a 14-phase roadmap takes 15 invocations. Each run ends by telling you where
you are (`Phase 8 of 14 — 7 done, 6 to go`) and whether to run it again. One
phase per run is deliberate: each phase gets written, verified against a
deliberately injected bug, and committed on its own, with a clean context.

Sessions don't need to be consecutive, or even the same session — the roadmap
file is the memory, so you can pick it up tomorrow, on a fresh clone, after a
squash merge, and it resumes from what has already landed.

* **Arguments:** `/paad:test-roadmap` (no arguments — the presence of the
  roadmap file selects build mode or execute mode)
* **Every phase names the bug it would catch** — a phase that cannot answer
  *"what breakage makes these tests go red?"* is coverage theater, and gets
  rewritten or dropped
* **It proves each test actually works** — before a phase counts as done, it
  injects the very bug the phase claims to catch and confirms the test goes
  red; a passing command and a covered line are never accepted as proof
* **Bug injection is disposable** — it happens in a throwaway `git worktree`,
  never in your working tree, database, or config
* **It grades the tests you already have** — existing tests are classified
  against a catalog of test theater (assertion-free, tautological,
  snapshot-only, over-mocked, happy-path-only) before anything new is planned
* **It will not call a phase done while the run is noisy** — your whole suite
  runs normally and again under coverage; it fixes what is its own to fix and
  surfaces the rest, and never edits your code to quiet a warning
* **You finish with a bug list you did not start with** — contradictions found
  while pinning behavior are logged with the test that proves them. It never
  fixes them; that is your call
* **Resumable** — across unrelated commits, squash merges, fresh clones, and
  sessions that remember nothing about the last one

Requires a git checkout and a working branch. Started on `main` (or `master`,
or `trunk`), it stops and offers to create a branch first, so your primary
branch never fills up with half-built tests.

**This is the only PAAD skill that writes and commits code.** Every other
skill reports, advises, or edits documents; this one adds tests and commits
them, one commit per phase, onto the branch you are on.

## Local Development

Test the plugin locally without installing it:

```bash
claude --plugin-dir ./plugins/paad
```

Then invoke skills with `/paad:help` to see available commands, or try
`/paad:vibe`, `/paad:pushback`, and the rest directly.

After making changes, run `/reload-plugins` inside Claude Code to pick up
updates without restarting.

### Testing

Run all checks with:

```bash
make test
```

This validates the marketplace and Claude plugin structure, then runs
consistency checks such as package version sync, digraph presence, help and
README coverage, and frontmatter validation. Use `make help` to see all
available targets.

Individual checks can also be run separately:

```bash
make check-versions     # package.json ↔ marketplace.json ↔ plugin.json version sync
make check-digraphs     # every skill (except help) has a digraph
make check-help         # every skill is documented in paad:help
make check-readme       # every skill is documented in README.md
make check-frontmatter  # SKILL.md frontmatter is valid, folder name matches
make check-references   # references/ dispatches resolve; no orphaned reference files
make validate           # claude plugin validate on marketplace + plugins
```

## Contributing

1. Fork the repository and create a feature branch.
2. Make your changes. See `CLAUDE.md` for conventions on adding or modifying skills.
3. Run `make test` to verify everything passes.
4. Open a pull request.

Key rules from `CLAUDE.md`:

* Every skill except `help` must include a Graphviz digraph covering its
  decision points
* Skill folder names must match the `name` field in `SKILL.md` frontmatter
* Use `make bump-version VERSION=X.Y.Z` to keep all versioned files in sync
* Update `README.md`, `paad:help`, and `CLAUDE.md` when adding or changing
  skills

## License

MIT
