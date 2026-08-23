---
name: paad-help
description: Use when the user asks which paad skills exist, what a paad skill does, which one fits their situation, or how to invoke one — including "what can paad do", "list the paad skills", "is there a paad skill for X", or a request for the arguments of a named paad skill
metadata:
  internal: true
---

**On invocation:** announce "Running paad:paad-help v1.30.2-preview" before anything else.

# paad Help

Show help for paad skills. If `$ARGUMENTS` matches a skill name, show detailed help for that skill. Otherwise, show the overview.

## Arguments

- `/paad-help` — show all available skills
- `/paad-help vibe` — show detailed help for a specific skill
- `/paad-help agentic-review` — skill names with hyphens work too


## Behavior

If `$ARGUMENTS` is provided and matches a skill name (with or without the `paad:` prefix), show the detailed help for that skill only. If the argument doesn't match any skill, say "Unknown skill: [name]. Available skills:" and show the overview.

Do NOT read files or run commands. All help text is below.

## Common Mistakes

| Mistake | What to do instead |
|---------|-------------------|
| Paraphrasing or summarizing the help text | Display the blocks verbatim. Arguments and output paths are exact; a paraphrase invents flags that don't exist. |
| Answering for a skill not listed here | If it isn't below, it isn't a paad skill. Say "Unknown skill: [name]" and show the overview. |
| Running the skill the user asked about | They asked what it does, not for it to happen. Show the help and stop. |

---

## Overview (no arguments)

When showing the overview, display exactly this:

```
paad — Engineering-driven AI.
Use your engineering excellence — the one thing AI reliably skips.

Available skills:

  /agentic-a11y [path]                  Accessibility audit (web, mobile, desktop, CLI, games)
  /agentic-architecture [path...]       Multi-agent architecture analysis (strengths & flaws)
  /fix-architecture [report]            Fix architectural flaws from an analysis report
  /agentic-review [base-branch] [path]  Multi-agent code review of current branch (bug hunting)
  /alignment [files...]                 Requirements-to-tasks alignment + TDD rewrite
  /makefile                             Create or update a Makefile with standard targets
  /pushback [document]                  Spec/PRD/doc critic (finds issues before you build)
  /vibe [task description]              Safe vibe coding with TDD guardrails

Experimental — may change or be withdrawn in any release, including patches:

  /agentic-dedup [scope]                Find semantic duplication (same meaning, different code)
  /agentic-owasp [scope]                Security review against the OWASP Top 10:2025
  /handoff [save|resume]                Hand this session's work to a fresh session, in writing
  /rethink [what to re-examine]         Verify the premises under options already on the table
  /test-roadmap                         Plan and build a test suite that catches real regressions

Picking between them:

  Want structural flaws found?          agentic-architecture (diagnoses, does not fix)
  Want them fixed?                      fix-architecture (needs a report first)
  Want bugs in a branch?                agentic-review (a diff, not the codebase)
  Want accessibility barriers?          agentic-a11y (not general correctness)
  Want duplicated logic found?          agentic-dedup (experimental; reports,
                                        never refactors)
  Worried about security specifically?  agentic-owasp (experimental; the OWASP
                                        Top 10:2025, never exploits or fixes)
  Have no tests, or tests you distrust? test-roadmap (experimental; the only
                                        skill that writes and commits code)
  Have one document, is it any good?    pushback (a spec, a steering file, a
                                        generated report)
  Been handed options, are they sound?  rethink (experimental; checks premises,
                                        does not invent alternatives)
  Out of context, work unfinished?      handoff (experimental; writes a file for
                                        a NEW session — /compact stays in this one)
  Have a spec AND a plan, do they match? alignment (needs both; does not read code)
  Making a small change?                vibe (1-3 files, same module)
  Change is clearly multi-module?       write a plan, then alignment against it
  Build is broken?                      none of these — makefile manages targets,
                                        it does not debug builds

Run /paad-help <skill-name> for detailed help on a specific skill.

Invoking: the names above are slash commands on Claude Code. If your
assistant does not take them, ask for the skill by name ("run the pushback
skill"). If another plugin ships a skill with the same name, disambiguate with
the paad: prefix — /paad:vibe rather than /vibe.
```

---

## Detailed Help (per skill)

### agentic-a11y

```
/agentic-a11y [path]

Comprehensive multi-agent accessibility audit of user-facing code.

Supports: web, iOS, Android, React Native, Flutter, desktop, CLI, and games.
Target:   WCAG 2.2 AA baseline, AAA flagged as bonus recommendations.
Output:   paad/a11y-reviews/

Arguments:
  /agentic-a11y                    Audit all user-facing code in the repo
  /agentic-a11y src/components/    Scope to a directory
  /agentic-a11y Modal.tsx          Scope to a file

What it does:
  1. Detects the platform(s) automatically
  2. Dispatches 5 specialist agents in parallel:
     - Screen Reader & Assistive Tech
     - Visual & Color
     - Keyboard & Motor
     - Cognitive & Learning
     - Multimedia & Temporal
  3. Dispatches a Platform-Specific agent if a framework is detected
  4. Verifies findings (filters false positives from component libraries)
  5. Writes a report with:
     - Impact summary by user group
     - Issues ranked by severity (Critical/Serious/Moderate/Minor)
     - WCAG conformance checklist
     - Quick wins (top 5 highest-impact, lowest-effort fixes)

Best used in a fresh session — consumes significant context.
```

### agentic-architecture

```
/agentic-architecture [path...]

Multi-agent architecture analysis. Diagnosis only — finds strengths and
flaws with evidence but does not propose fixes.

Output: paad/architecture-reviews/

Arguments:
  /agentic-architecture                          Full repo
  /agentic-architecture src/                     Scope to a directory
  /agentic-architecture packages/api/ packages/shared/  Multiple dirs

What it does:
  1. Reconnaissance: repo overview, dependency snapshot, steering files
  2. Dispatches 5 specialist agents in parallel:
     - Structure & Boundaries (god objects, cohesion, domain modeling)
     - Coupling & Dependencies (tight coupling, circular deps, abstractions)
     - Integration & Data (API contracts, data ownership, resilience)
     - Error Handling & Observability (error strategy, logging, config)
     - Security & Code Quality (auth, secrets, dead code, test coverage)
  3. Verifies findings (reads actual code, checks git history)
  4. Writes a report with:
     - 14 strength categories assessed
     - 34 flaw/risk types assessed
     - Coverage checklist (every category: observed / not observed / N/A)
     - Hotspots (top 3 files/directories to review)
     - Next questions (max 5, no solutions)

Best used in a fresh session — consumes significant context.
```

### fix-architecture

```
/fix-architecture [report]

Guided fixing of architectural flaws from an agentic-architecture report.
Test-first workflow with developer approval at every step.

Output: Updates the report in paad/architecture-reviews/ with fix status

Arguments:
  /fix-architecture                         Find most recent report
  /fix-architecture path/to/report.md       Use a specific report

Requirements:
  - Must be on a feature branch (not main/master/trunk)
  - An architecture report must exist (run /agentic-architecture first)

What it does:
  1. Pre-flight: branch check, report staleness, test infrastructure,
     baseline test run
  2. Developer conversation:
     - Solo or team? (affects batch size recommendations)
     - Auto-commit or manual review?
     - Flaw triage: high-impact, quick wins, or specific F-IDs
     - Plan confirmation before any code is touched
  3. For each selected flaw:
     - Validates the flaw still exists (checks code and git history)
     - Assesses test coverage, writes safety-net tests if needed
     - Proposes fix options with tradeoffs (recommended option first)
     - Executes with red/green/refactor
     - Handles test failures (distinguishes structural vs behavioral)
     - Commits (one per fix) and updates the report
     - Checks if the fix resolved other flaws too
  4. Post-session summary with remaining flaw count

Status tracking in the report:
  Fixed | Won't fix | Partially fixed | Skipped |
  Fixed (pre-existing) | Attempted, reverted

Best used in a fresh session — consumes significant context.
```

### agentic-review

```
/agentic-review [base-branch] [path]

Multi-agent bug-hunting code review of the current branch.

Output:   paad/code-reviews/<branch>-<timestamp>-<short-sha>.md (per-review)
          paad/code-reviews/backlog.md (project-wide, persistent)

Arguments:
  /agentic-review                    Diff against the default branch
  /agentic-review develop            Diff against a different branch
  /agentic-review main src/auth/     Scope to a directory

  One argument is read as a base branch if git can resolve it, otherwise
  as a path if it exists on disk. If it is both -- "docs", "release",
  "test" and "api" are ordinary names for either -- the skill stops and
  asks rather than guessing.

Requirements:
  - Must be on a feature branch (not the repository's default branch,
    resolved from origin/HEAD, falling back to main/master/trunk)
  - Uncommitted changes: asks whether to review the committed state or wait

Stops before reviewing when:
  - The base branch does not resolve
  - A path filter was given and does not exist
  - An argument is neither a ref nor a path, or is ambiguously both
  - An argument holds a character git could read as a flag
  - The default branch cannot be determined at all
  - The filtered diff is empty

What it does:
  1. Reconnaissance: diff stats, file manifest, callers/callees
  2. Dispatches 6 specialist agents in parallel:
     - Logic & Correctness
     - Error Handling & Edge Cases
     - Contract & Integration
     - Concurrency & State
     - Security
     - Spec Compliance — pulls intent from PR description, plan/design
       docs, recent commits, or branch name; flags missing features,
       deviations, and out-of-scope additions (replaces the older
       Plan Alignment agent)
  3. Verifies findings (reads actual code, filters false positives)
  4. Classifies each finding as in-scope (this branch caused/worsened it),
     out-of-scope (pre-existing bug — persists to project-wide backlog),
     or out-of-scope-addition (this branch added it but the spec didn't
     promise it — flagged for per-PR user decision)
  5. Writes a report with:
     - In-scope issues ranked: Critical / Important / Suggestion
     - Out-of-scope bugs batched by tier with handoff instructions
     - Out-of-scope additions in a separate section for keep/split/revert
       decisions (no backlog persistence)
     - Each finding: file:line, bug, impact, suggested fix, confidence,
       and the model that found it
     - Backlog updates surfaced in metadata

Best used in a fresh session — consumes significant context.
```

### alignment

```
/alignment [files...]

Checks that requirements and implementation plans are aligned.
Rewrites all tasks in TDD red/green/refactor format (mandatory).

Output: paad/alignment-reviews/

Arguments:
  /alignment                              Auto-detect documents
  /alignment requirements.md plan.md      Specific files
  /alignment docs/specs/ docs/plans/      Directories

Auto-detection scans: .kiro/, specs/ (spec-kit), docs/plans/, docs/specs/,
common filenames, and conversation history.

What it does:
  1. Classifies documents as intent (requirements) vs action (tasks)
  2. Reality check: scans git history for conflicts
  3. Three alignment checks:
     - Requirements coverage (every requirement has tasks?)
     - Scope compliance (every task maps to a requirement?)
     - Design alignment (if design docs exist)
  4. Presents issues one at a time, dependency-ordered:
     - Missing requirements first (root causes)
     - Design gaps second
     - Missing/orphaned tasks last (symptoms)
  5. Rewrites all tasks in red/green/refactor format
  6. Updates documents or writes a separate report

Works within an existing conversation — no fresh session needed.
```

### makefile

```
/makefile

Creates or updates a project Makefile with standard targets.

Arguments:
  /makefile    Create a new Makefile or update an existing one

What it does:
  1. Detects your stack (reads CLAUDE.md, README, package.json, etc.)
  2. Checks if a Makefile already exists
  3. Creating: builds from scratch with all required targets
  4. Updating: adds missing targets; asks before changing existing ones

Required targets (always included):
  help     List all targets with descriptions
  all      Full CI pass (lint + format + test)
  test     Run test suite
  cover    One-shot coverage report
  lint     Lint (with autofix if available)
  format   Format code

Extra targets (build, dev, preview, etc.) added only if the project
supports them.

Key rules:
  - Never modifies an existing target without explicit approval
  - Forces one-shot mode for coverage (no watch-mode hanging)
  - Uses self-documenting pattern (## comments + grep/awk help target)
  - Balanced test output: concise on success, detailed on failure

No fresh session needed — this is a lightweight workflow skill.
```

### pushback

```
/pushback [document]

Critically reviews a spec, PRD, or design before you start building —
or any document that makes claims about the code, such as an agent
steering file (CLAUDE.md, AGENTS.md) or a generated analysis report.
Every finding must name a concrete consequence and the mechanism behind
it; candidates that can't are dropped and reported as discards. Each
finding also names the off-disk fact that would change its severity —
or says it is unconditional.

Output: the conversation, plus your spec if you ask for edits.
        Writes paad/pushback-reviews/ only when issues go undiscussed
        or you ask for a report.

Arguments:
  /pushback path/to/spec.md    Review a specific file
  /pushback                    Auto-detect from conversation or files

Auto-detection checks: conversation history first, then common locations
(docs/plans/, docs/specs/, requirements.md, PRD.md, spec.md), then agent
steering files (CLAUDE.md, AGENTS.md, .cursorrules, .kiro/steering/,
.github/copilot-instructions.md) and generated analysis (paad/*-reviews/).

What it does:
  1. Reality check: scans git history for conflicts with what the
     spec assumes (presented upfront — showstoppers first)
  2. Scope shape check:
     - Feature cohesion: flags unrelated features bundled together
       (things that would be separate PRs)
     - Spec size: flags oversized specs, suggests splits only when
       each piece delivers independent value
  3. Analyzes the spec across 6 categories:
     - Contradictions
     - Feasibility (given the current codebase)
     - Scope imbalance
     - Omissions
     - Ambiguity
     - Security concerns
  4. Presents issues one at a time, most impactful first
  5. For each: concrete options from best to worst, with recommendation
  6. Stop when you say "good enough"
  7. Updates the spec or writes a separate report

Works within an existing conversation — no fresh session needed.
```

### rethink

```
/rethink [what to re-examine]          EXPERIMENTAL

Independently verifies the premises under options that are already on
the table. Reports what it checked, and how it checked it.

Experimental: arguments, verdicts, and output shape may change — or the
skill may be withdrawn — in any release, including a patch release.

Output: none — it speaks in the conversation and writes no files.

Arguments:
  /rethink                    Re-examine the most recent option set
  /rethink the caching approach   Name which decision, if several are live

What it does:
  1. Extracts every premise the recommendation depends on, including
     the unstated ones, and sorts them:
     - checkable now (a primary source exists)
     - checkable by experiment (names the cheapest one)
     - not checkable (judgment, taste, prediction)
  2. Dispatches one read-only subagent to verify them against
     PRIMARY sources — the software, not its documentation
  3. Reports one of five verdicts:
     - Sound          premises hold, and were checked
     - Lucky          premises hold, but nobody checked them
     - Wrong reason   a premise is false, the conclusion survives
     - Premise false  a premise is false, the conclusion does not
     - Ungrounded     unsettleable; names the experiment that would settle it
  4. Per premise: what was claimed, what was found, what was checked
  5. Re-presents the options in plain language — no jargon, no internal
     names — with pros AND cons for each, and says what verification
     changed about their standing
  6. Recommends one, with the reason. Where the call also turns on
     something it cannot see — a deadline, headcount, an unshipped
     roadmap — it still recommends, then names that input and what it
     would flip the answer to. It withholds entirely only when the
     evidence supports no default at all

What it deliberately does NOT do:
  - Produce an option list. It is not pushback. It proposes an
    alternative only when verification exposed a defect, and then
    exactly one, tied to that defect.
  - Write, edit, or create any file.

Use it when a choice rests on cited docs, remembered behavior, or
premises nobody tested. Not for critiquing a spec — that is pushback.
```

### vibe

```
/vibe [task description]

Safe vibe coding. Quick fixes with TDD guardrails.

Arguments:
  /vibe fix the login timeout    Task description inline
  /vibe                          Ask what needs fixing

What it does:
  1. Understands the task (asks clarifying questions if needed)
  2. Pre-flight checks:
     - Test infrastructure exists?
     - Scope check (4+ files = warning)
     - Architecture smell (simple task but hard work = investigate)
     - Reusable components (search before building from scratch)
  3. Implements with mandatory red/green/refactor:
     - RED: one failing test first — a new one, or an existing test
       updated to the new expectation (stop if unexpected behavior)
     - GREEN: write minimal code to pass
     - REFACTOR: clean up duplication, hard-coded values, patterns
  4. Post-fix summary with contextual follow-up suggestions:
     - Security-sensitive code → /agentic-review
     - UI changes → /agentic-a11y
     - Harder than expected → /agentic-architecture

No fresh session needed — this is a lightweight workflow skill.
```

### agentic-dedup

```
/agentic-dedup [scope]

EXPERIMENTAL — arguments, output paths, and behavior may change or be
withdrawn in any release, including patch releases.

Multi-agent hunt for semantic duplication: code that means the same thing
behind different names, different syntax, different control flow, or
independently evolved implementations. Not a syntactic clone detector.

Output: paad/dedup-reviews/<branch-or-scope>-<timestamp>-<sha>.md
        paad/dedup-reviews/INDEX.md (persistent, newest run on top)

Arguments:
  /agentic-dedup                     Scan the repository
  /agentic-dedup src/auth/           Scope to a path or module
  /agentic-dedup --changed main      Seed from the diff against main
  /agentic-dedup --type-constraints  Schemas, type aliases, validators
  /agentic-dedup --domain "payments" Scope to a domain term

What it does:
  1. Reconnaissance: manifest grouped by semantic domain, not by extension
  2. Candidate discovery via six strategies: name/concept search,
     behavioral fingerprints, type & constraint equivalence, control-flow
     normalization, tests as behavioral specs, canonical utility search
  3. Dispatches 5 specialist agents in parallel:
     - Semantic Equivalence
     - Type & Constraint Equivalence
     - Domain Boundary & Intent
     - Divergence Risk
     - Refactoring Safety
  4. Verifies findings — rejects name-only, shape-only, and structural
     matches, and anything where duplication is the safer choice
  5. Writes a report with:
     - Findings ranked Critical / Important / Suggestion
     - Type and constraint equivalence table (exact/overlap/subset/drift)
     - Rejected candidates, so the next run does not rediscover them
     - A consolidation strategy with a safe migration sequence

Never refactors anything. The report is the deliverable.

Best used in a fresh session — consumes significant context.
```

### agentic-owasp

```
/agentic-owasp [scope]

EXPERIMENTAL — arguments, output paths, and behavior may change or be
withdrawn in any release, including patch releases.

Multi-agent security review of source code against the OWASP Top 10:2025.
Reads code. Never starts the app, never sends a request anywhere, never
writes exploit code, never fixes what it finds.

Output: paad/owasp-reviews/<branch-or-scope>-<timestamp>-<sha>.md
        paad/owasp-reviews/INDEX.md (persistent, newest run on top)

Arguments:
  /agentic-owasp                     Review the repository
  /agentic-owasp src/api/            Scope to a path or module
  /agentic-owasp --changed main      Seed from the diff against main
  /agentic-owasp --category A01      One category, or A01,A05,A07
  /agentic-owasp --deps              Supply chain only: deps, CI/CD

What it does:
  1. Reconnaissance: framework defaults first — the ORM, template engine,
     and middleware decide which findings are even real
  2. Attack surface mapping: untrusted sources, dangerous sinks, and the
     controls already sitting between them, each with path:line.
     Then, before specialists launch, an optional benign-execution offer:
     with your explicit yes, specialists may run read-only in-process
     probes — your existing tests, a deparse, a pure-function call on
     ordinary input — to settle questions reading cannot. Never a payload,
     never a server or network, never a write; a separate decision from the
     proof stage below, and off unless you say yes
  3. Dispatches 7 specialist agents in parallel. Six cover all ten
     categories with none left over:
     - Access Control & Authentication     (A01, A07)
     - Injection & Untrusted Input         (A05)
     - Cryptography & Data Protection      (A04)
     - Configuration & Supply Chain        (A02, A03)
     - Design, Integrity & Failure Modes   (A06, A08, A10)
     - Logging, Alerting & Detection       (A09)
     The seventh owns no category and hunts by mechanism instead:
     - Mechanism & Round-Trip              (the seams)
       Round-trip asymmetry between paired APIs, and facts the code
       stores twice where a control reads only one copy. Files its
       findings under the category of the impact.
  4. Exploitability gate: a finding must name an attacker-controlled
     source, a traced path to the sink, and why the existing controls do
     not hold. Anything that cannot becomes a hardening note or is rejected.
     The verifier's job is to refute, not confirm, and it clears a control
     by enumerating the callers that bypass it — not by reading where the
     control lives, and it composes across specialists before rejecting —
     each specialist reports out-of-category observations as fragments, so a
     weakness split across two categories is not lost by both
  5. Optional proof stage: where a sink is reachable in-process, offers to
     write a standalone script per finding that exits 0 while the weakness
     is open, worked down the severity order rather than by whichever
     proof looks easiest. Always asks first, with the trade-offs; never
     executes without a yes. Declining costs nothing — unproven findings
     keep their severity, and each says why it went unproven
  6. Writes a report with:
     - Coverage table across all ten categories — "not assessed" is
       stated, never passed off as clean
     - Findings ranked Critical / High / Medium, hardening notes separate
     - Dependency findings marked called vs present-but-unreachable
     - Every pooled fragment listed individually — path:line, what the
       specialist saw, where it ended up — not just a count, so a sink
       that was seen and dropped stays distinguishable from one nobody
       looked at once the session is gone
     - Rejected candidates, each with the positive evidence that killed
       it, so the next run does not rediscover them
     - A remediation order, which is not severity order

Live credentials are reported by location and type only — never by value,
and rotation comes before anything else in the report.

No report is a complete list of the weaknesses in the code, and the skill
says so at the end of every run — along with why committing the report is
risky even after the findings are fixed: git history is permanent, the
report ages into a false clearance, and the caveats do not travel with the
severity table. Zero findings means one reviewer looked once inside ten
categories and could not prove a path — not that the code is secure. Two
runs find different things, and the larger the codebase the wider the gap,
so union two runs rather than diffing them. Severity states impact;
whether a finding was executed is a separate field and never lowers it.

Scope is gated on size. Past roughly 40 source files the skill stops and
offers a choice: narrow to the untrusted-input surface, split into separate
subsystem passes, or take one wide pass with the dilution recorded in the
report. Breadth costs depth, and it costs it silently — a wide run returns a
different result rather than a shallower one, often reporting more findings
overall while missing a weakness a narrow pass over the same file finds
every time. Prefer several scoped runs to one repository-wide sweep.

Best used in a fresh session — consumes significant context.
```

### test-roadmap

```
/test-roadmap

EXPERIMENTAL — arguments, output paths, and behavior may change or be
withdrawn in any release, including patch releases. This is the only paad
skill that writes and commits code.

Builds a test suite that catches real regressions, in phases, across as
many sessions as it takes. One command on day 1 and on day 90.

Run it once to get a roadmap, then KEEP RUNNING IT — one phase of tests
per run — until it tells you the roadmap is finished. A 14-phase roadmap
takes 15 invocations. Running it once leaves you with a plan and no
tests.

Output: paad/test-roadmap/test-roadmap.md (the roadmap, and the memory)
        Tests, committed one phase per commit, on your working branch

Arguments:
  /test-roadmap    No arguments — the roadmap file decides the mode

Requirements:
  - A git checkout (bug injection runs in a disposable git worktree)
  - A working branch, not main/master/trunk — it offers to make one

What it does:
  Routing is one check: does paad/test-roadmap/test-roadmap.md exist?

  Absent → BUILD mode, five stages:
     1. Detect   — stack, test runner, and existing tests from manifests,
                   never from a hardcoded language list
     2. Grade    — fan-out subagents grade existing tests for weakness and
                   classify mocks (see the test-theater catalog)
     3. Plan     — phases, each naming the bug it would catch
     4. Critique — a phase that cannot name its bug is coverage theater
                   and gets rewritten or dropped
     5. Write    — the roadmap, including the decisions you settled

  Present → EXECUTE mode, one phase per run:
     - Writes that phase's tests
     - break-it-check: injects the very bug the phase claims to catch,
       in a throwaway worktree, and confirms the test goes red
     - Runs your whole suite, once normally and once under coverage;
       will not call a phase done while the run is noisy
     - Commits the phase and marks it done
     - Ends by telling you where you are (Phase 8 of 14 — 7 done, 6 to
       go) and to run it again, until no phases remain

  Logs concrete bugs it finds along the way. It never fixes them.

Best used in a fresh session — consumes significant context.
```

### handoff

```
/handoff [save|resume]                 EXPERIMENTAL

Writes a handoff.md that lets a FRESH session continue this one's
work, and reads it back on the other side.

Experimental: arguments, file format, and behavior may change — or the
skill may be withdrawn — in any release, including a patch release.

Output: handoff.md in the working directory. Suggests you gitignore it.

Arguments:
  /handoff          Infer: history above → save, empty session → resume
  /handoff save     Write a handoff regardless
  /handoff resume   Read the existing handoff regardless

Why not just /compact:
  /compact   summarizes and keeps working — same session, and the
             summary is machine-written, unreviewed, and buried in
             the transcript where you cannot edit it
  --resume   restores the whole prior conversation, re-paying the
             context cost you were escaping
  /clear     genuinely fresh, carries nothing forward
  handoff    a file a human reads and corrects BEFORE anything is
             built on it

  That review is the only thing it adds. A handoff nobody reads is a
  worse /compact.

Saving:
  1. Checks .gitignore for handoff.md and suggests adding it —
     never edits .gitignore itself
  2. Verifies with tools what agents get wrong from memory:
     commit and branch, what is really IN the last commit (not what
     its message claims), file paths, line numbers, test names,
     whether the suite passes. Unsettleable claims are marked
     inferred, not asserted
  3. Writes the file: goal and what done looks like, decisions and
     why, approaches ruled out and how far they got, constraints the
     user stated, the next step, the verify command
     NOT: architecture tours, session narrative, anything git diff
     already shows — padding makes the file too long to review
  4. Names the two or three claims it is least sure of, instead of a
     generic "review this, AI makes mistakes"

Resuming:
  1. Reads handoff.md, summarizes it in a few lines
  2. Compares the recorded commit against HEAD and reports drift
  3. Asks before proceeding
  4. Confirms the files and state it names still exist, reports every
     mismatch, asks again
  5. Then starts the recorded next step

  Never deletes handoff.md — it is untracked, so git cannot restore
  it. The next save overwrites it.
```
