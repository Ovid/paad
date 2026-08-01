# Build mode — the five stages

Loaded when `.reviews/test-roadmap/test-roadmap.md` does not exist yet — the first run against a
repo, or any run after that file was deleted. Five stages, run in order, each
handing a concrete artifact to the next: Detect, Grade, Plan, Critique, Write.

## Stage 1 — Detect (main agent)

Identify the stack from manifests and config rather than assumption —
`package.json`, `pyproject.toml`/`setup.cfg`, `go.mod`, `Cargo.toml`, `Gemfile`,
`pom.xml`/`build.gradle`, `composer.json`, `cpanfile`/`Makefile.PL`, `*.csproj`,
`mix.exs`, and so on. This list is examples, not a closed table — the skill must
never hardcode a language. Where it needs a per-ecosystem fact, it looks for the
signal in the repo rather than consulting a built-in list.

Detect **four** things, all from repo signals:

1. **How tests are invoked, and what test files exist.** Read the manifest's test
   script/target and enumerate the test files it would run.
2. **Whether a coverage tool is available.** Used read-only, later, in Stage 3 for
   gap-finding — **never as a quality signal**. Where none is detectable, Stage 3
   falls back to agent judgment reading source, and says so in the plan rather
   than silently proceeding as if coverage output existed.
3. **Whether a test-data mechanism exists** — fixtures, factories, seed scripts,
   testcontainers, a `conftest.py`, a `factories/` or `fixtures/` directory. This
   feeds Stage 3: an integration or e2e phase that needs constructed data cannot
   be planned honestly against a repo with no way to construct it.
4. **How this repo separates test tiers, and the per-tier run + coverage
   command.** The three tiers — unit, integration, e2e — must end up
   *distinguishable* and *independently coverage-runnable* (a stated requirement,
   see *The three tiers must be independently runnable*, below). The mechanism
   that makes them so is **not universal** — it is a *selector* the ecosystem
   already expresses, and it varies: a test directory (`tests/unit/`,
   path-selected), a filename marker, a test tag/marker (`pytest -m`, Go
   `//go:build`), a build target (`cargo test --lib`/`--test`, a `.csproj` or
   Jest project), or a test label (CTest `-L`). Detect which the repo uses, and
   derive per tier the command that runs *just that tier* and the command that
   runs it *with coverage*. **Do not assume the selector is a directory.** These
   per-tier commands are recorded in `## Decisions` (Stage 5).

**Stage 1's output is a discovery, not a boundary.** It tells you what tests exist
and how to run them; it does not exhaustively partition the repo into "test" and
"production," and nothing downstream may treat it as a safety fence. There is no
path fence anywhere in this skill — bug injection happens in a disposable
worktree (`references/break-it-check.md`), so no path-based fence is needed to
keep mutation off production code.

## Stage 2 — Grade (fan-out subagents)

**Skipped entirely when no tests exist.** Greenfield goes straight to Stage 3 —
there is nothing to grade.

Where tests exist, dispatch subagents partitioned by test tier or directory.
Each subagent reads its partition against `references/test-theater.md` and
returns a compact **structured verdict** — never pasted test source, never
diffs. A legacy suite is thousands of lines the main agent must not absorb.

Each subagent returns:

- **Per weak test found:** file, line, pattern name (verbatim from
  `test-theater.md`), a one-sentence statement of why it fails to catch
  regressions, and a suggested replacement.
- **Per mock or fixture encountered:** a ledger classification (see *The
  test-double & fixture ledger*, below).

**Cardinality containment.** The number of instances is unbounded by design — a
legacy suite may yield hundreds of weak tests — and the design contains that
rather than merely asserting it away:

- The **full verdict list** is written to `.reviews/test-roadmap/test-suite-analysis.md`, never
  returned to main context.
- **Main context receives counts and the top-K by severity only.** A 400-item
  grading result must never land in the resume context budget. Bounding each
  verdict's size while leaving the list itself unbounded in main context is the
  same defect wearing a different hat — both the per-item size and the list
  length must be bounded before anything reaches the main agent.

## Stage 3 — Plan (main agent)

Identify behaviors worth testing that are not tested. Group them into phases
across the three tiers — unit, integration, e2e. Build the ledger. Draft phases
in the canonical format defined in *Stage 5 — Write*, below.

Two Stage 1 findings feed this stage:

- **Coverage, for gap-finding only.** Where a coverage tool was detected, run it
  read-only to locate behaviors with *no test at all*. Coverage answers "what is
  untested," which it does well; it never answers "is this test any good," which
  it cannot — a line can be covered by a test that asserts nothing. This
  distinction is inviolate: coverage percentage is never evidence a test is
  worth keeping, in this stage or any other. Where no coverage tool exists, this
  is agent judgment reading source, and the plan states that plainly rather than
  presenting judgment as if it were tool output.
- **Test-data mechanism.** If a phase needs constructed data and Stage 1 found
  no mechanism to construct it, the phase carries a **surfaced note** — *"requires
  a test-data mechanism this repo lacks"* — rather than being planned as if it
  were executable as written. Finding un-runnability at plan time is the point
  of having a plan stage; finding it at the gate is the expensive place to find
  it.

**Legacy phases pin current behavior.** Where a phase characterizes existing
code, every assertion it proposes must match what the code *currently does*.
Behavior that looks wrong is never turned into a different assertion or a code
fix — characterizing a legacy system and fixing its bugs are two hard problems,
and this stage does the first one only. Where a wrong-looking behavior clears the
inclusion gate in *The findings log* (below), it is recorded there — a concrete,
actionable entry the developer works from later — and the phase that pins it
carries a one-line pointer to that entry. Where it does not clear the gate, it is
dropped, not written down as a vague note: a findings log of hunches is noise the
developer learns to skip, the same cry-wolf failure the clean-run rule exists to
prevent.

## Stage 4 — Critique

Invoke `references/test-pushback.md` mode `critique-plan` against the draft
plan Stage 3 just produced. Findings are **fixed inline, in the draft, on the
spot** — no report is written; there is nothing to hand off, only phases to
rewrite or drop before Stage 5 writes them to disk.

The governing rule, restated because it is the gate the whole stage exists to
enforce:

> **Every phase must name the bug it would catch.** If a phase cannot answer
> *"what breakage makes these tests go red?"*, it is not a phase — it is
> coverage theater. Rewrite it or drop it.

See `test-pushback.md` for the full pass, including the supporting rules (exit
status and coverage are never evidence; every double and fixture is classified;
legacy phases characterize, they don't fix).

## Stage 5 — Write (main agent)

All generated files live under `.reviews/test-roadmap/` — create that directory if
it does not yet exist. Two artifacts always, plus a third when this run turned up
any qualifying finding:

- **`.reviews/test-roadmap/test-roadmap.md`** — the `## Decisions` section first, then the
  phases.
- **`.reviews/test-roadmap/test-suite-analysis.md`** — full grading verdicts and the ledger.
  This is the sink for anything unbounded (Stage 2's full list, the ledger in
  full); main context never carries it.
- **`.reviews/test-roadmap/test-roadmap-findings.md`** — the findings log (see *The findings
  log*, below), written only if Stage 3/4 recorded at least one entry. If they
  recorded none, this file is not created here — execute mode creates it the
  first time a phase surfaces a qualifying finding.

**These artifacts are read by the developer, so they follow `references/test-pushback.md
§ Talking to the developer`.** In particular the ledger's class names
(`boundary`, `scaffold`, `data`) and any pattern names cited from
`test-theater.md` are jargon to a newcomer — gloss each in plain words the first
time it appears in the analysis doc (e.g. *"`scaffold` — a stand-in that only
exists because the code is hard to test as written; it marks test debt to retire
later"*). A weak-test verdict states, in plain terms, what regression the test
would let through, not just its pattern label.

**`.reviews/test-roadmap/test-roadmap.md` is always the target.** Everything this
skill generates lives under `.reviews/test-roadmap/` — its own namespace, so it never
clutters the developer's `docs/` and sits where PAAD tooling expects it. That
also sidesteps colliding with a hand-written `docs/roadmap.md` a repo may keep for
other reasons. The roadmap file's path is the router's signal for which mode to
load on the next invocation, so it is **load-bearing and not configurable** — do
not rename it, alias it, move it back under `docs/`, or write phases anywhere
else.

**Then commit the artifacts.** `git add .reviews/test-roadmap/test-roadmap.md
.reviews/test-roadmap/test-suite-analysis.md` — and `.reviews/test-roadmap/test-roadmap-findings.md` if it was
written — and commit them before build mode ends. This is
not optional bookkeeping: the roadmap is the router's resume signal, and
requirement 2 is resumability across *fresh clones*. An uncommitted roadmap
does not survive a clone, so the next run finds no `.reviews/test-roadmap/test-roadmap.md` and
silently rebuilds from scratch — the exact churn resumability exists to
prevent. Execute mode already commits each `Landed:` line the same way (step
5); build mode committing its own output is the same rule at the front of the
lifecycle, not a new one.

**Then list every file this run wrote**, one line per path — the roadmap is the
whole deliverable of build mode and it is easy to miss among the conversation:

```
Files written or updated:
  new  .reviews/test-roadmap/test-roadmap.md  (14 phases)
```

**Then tell the developer the total, in plain words.** Build mode's approach
menus fire *before* any plan exists, so during them there is no phase total to
show — the first instant it is knowable is right here, once Stage 5 has written
every phase. State it at the handoff, and make the loop explicit — **this run
planned the work, it did not do any of it**, and one phase lands per run from

to write Phase 1 of 14, and keep running it: one phase per run, 14 runs to
finish."* This is the developer's first sight of the end of the tunnel, and from
here on every phase the skill names carries its `Phase X of Y` per
`references/test-pushback.md § Talking to the developer`. A developer who stops
after this run has a plan and zero tests, so do not end build mode without
saying what the next invocation does.

### The canonical phase format

Every phase, in both build mode's draft and execute mode's updates, takes this
exact shape:

```markdown
## Phase 3: Billing retry & dunning integration tests

Tier:     integration
Catches:  a retry exhausting without transitioning the account to dunning;
          a partial refund double-crediting.
Produces: tests/integration/billing/
Branch:   billing-integration-tests
Landed:
```

Field semantics:

- **`Tier:`** — exactly one of `unit`, `integration`, `e2e`. Stage 3 already
  groups behaviors by tier, so this is honestly authorable at plan time (unlike
  the rejected `Covers:` field, which asked Stage 3 to enumerate something it
  never produces). It makes *which tier a phase belongs to* explicit in the
  roadmap itself — satisfying the distinguishability half of the tier
  requirement without depending on where the files physically land — and it
  selects which recorded per-tier run/coverage command (see `## Decisions`)
  applies to this phase.
- **`Catches:`** — the anti-theater gate from Stage 4, preserved in the artifact
  so a later reader can audit whether the phase was honest. It is also
  `break-it-check`'s behavior input: it names the *behavior* to mutate, not a
  path. A path is neither necessary (the behavior locates the code) nor
  sufficient (directory granularity cannot pick a line to mutate).
- **`Produces:`** — paths the phase creates, as **documentation only**. It is
  **not** a completion signal. A later reader uses it to find the phase's
  output; no control flow in this skill infers phase status from it.
- **`Branch:`** — a human-readable breadcrumb recording the working branch the
  phase's tests were committed on. **Not a machine signal, and not a per-phase
  branch the skill creates** — execute mode commits each phase onto the current
  working branch and the suite accumulates there (see `execute-test-roadmap.md
  § What execute mode writes`).
- **`Landed:`** — empty until `break-it-check` passes for this phase, then set
  to `YYYY-MM-DD <sha> (<operator>)`. **Human-clearable; the skill itself never
  clears it.** A cleared `Landed:` line is a human declaring the phase needs
  redoing — the skill has no mechanism that would ever produce that state on
  its own.

Each phase's definition-of-done includes a recommendation to run `agentic-review` on the accumulated working branch before it is merged upstream, if available. This is not bundled into execute mode: `agentic-review` requires a fresh session with no substantive history, so calling it from within the test-roadmap session would be inert.

### The test-double & fixture ledger

Every test double and fixture, existing or proposed, gets one classification:

| Class | Meaning |
|---|---|
| `boundary` | Permanent and correct. A real external edge: network, clock, randomness, a payment gateway, a third-party API, filesystem where relevant. |
| `scaffold` | Exists only because the surrounding code resists testing. Test debt. Names the refactor that retires it — that refactor is *deferred*, named now and actually done only when it is actually planned, not during this pass. |
| `data` | Constructed test data that is permanent and correct — a seeded account, a factory-built order, a fixture record. Neither an external edge (`boundary`) nor debt a refactor retires (`scaffold`). |

An unclassified double is a gap in the plan, not a detail to leave for later.
**When in doubt between `boundary` and `scaffold`, or when a double goes
unexamined, default to `scaffold`.** The harm is asymmetric: a `scaffold`
silently promoted to permanent hides test debt indefinitely, while a `boundary`
mistakenly recorded as `scaffold` only leaves a note a human later deletes.

When a unit resists testing so completely that even a `scaffold`-mock test can't
be written, the artifact is not a mock but a **skipped stub** that names the
obstacle and surfaces it through the framework's skip-with-reason mechanism — see
execute mode's *Units too hard to test*. It is still `scaffold`-class debt (the
refactor that makes the unit testable retires it); it is a last resort, and it
never counts as coverage.

### The findings log

While pinning current behavior, the skill will notice code that looks wrong — a
return that contradicts its own docstring, a validator that accepts what its name
says it rejects. It never fixes these (Inviolate #1: characterize now, fix
later), but it records the good ones so the developer finishes with a concrete
to-do list instead of a vague memory that "something looked off." That list is
`.reviews/test-roadmap/test-roadmap-findings.md`.

This is **not** the "findings" of *Approaches vs findings* below — those are
test-quality verdicts (a weak test, a mock's class) and go to the ledger. This
log is production-code bugs the developer will fix later, watching the
characterization tests break as they do.

**The inclusion gate — verified and actionable, or it is not logged.** A log of
hunches is noise the developer learns to skip, the same cry-wolf failure the
clean-run rule guards against. An entry is written **only if all three hold**;
miss any one and the observation is dropped, never downgraded to a vague note
(there is no second-tier "maybe" list, and nothing lands elsewhere):

1. **Demonstrable current behavior** — a specific input→output or code path, not
   a general unease. Where a characterization test pins it, cite that test: the
   test *is* the reproduction.
2. **A concrete contradiction, cited** — in-repo evidence the behavior violates:
   a docstring, a type signature, an adjacent validation, a stated invariant, a
   test name asserting otherwise. This is a **citation of two things in the repo
   that disagree**, never the agent's own ruling on what the code *should* do —
   which of the two is right stays the developer's call, and Inviolate #1 stays
   intact.
3. **A clear action** — a specific next step, e.g. *"reconcile the docstring at
   `email.py:40` with the return at `email.py:52`."*

**Entry format** — one block per finding:

Each field is its own bold-labeled paragraph, separated by blank lines — never
bare adjacent lines, which markdown reflows into a single paragraph:

```markdown
## F3 — `is_valid_email` accepts the empty string

**Where:** src/email.py:52

**Behavior:** `is_valid_email("")` returns True.

**Contradicts:** the function's own docstring (src/email.py:40): "returns True
only for a syntactically valid address."

**Action:** decide which is correct and reconcile them.

**Pinned by:** Phase 6 — its test locks in the current True. Fixing the code
turns that test red; that is the signal to update the test, not a regression.
```

`Pinned by:` is filled where a phase's test pins the behavior (always so for a
finding surfaced *while writing* that phase; for one surfaced at plan time, it
names the phase that will pin it). It is the line that makes the finding
actionable *and* ties it to the suite: the developer knows in advance which test
will go red, and that red is success.

The log is **append-only and committed with whatever produced it**, so it
survives a fresh clone like the roadmap does. The main agent never holds the
whole file in context — it appends entries, it does not re-read the accumulated
log each run.

### Approaches vs findings

Two different things reach the developer during a run, and they are not
handled the same way.

**Approaches** — genuine forks where the answer is taste or is expensive to
reverse. Roughly four to six across a whole run: test framework/runner, suite
strategy (unit-first / e2e-first / risk-first), phase ordering, whether to
rewrite the weak tests Stage 2 found. Every approach goes to a menu whose full
format is defined once in `references/test-pushback.md § Presenting approaches`
— **load that section before presenting the first menu**, because by the time a
run reaches this point it is deep in analysis and the format is no longer in
context. The compact rule, restated here so it is in front of you at the moment
you present rather than only in a file that may not be loaded:

> Put the menu's substance in a **written prose menu in your own reply**: one
> decision, every option with its own pro and con, a recommendation grounded in
> this repo, and the deep-dive (a skeptical adversarial pass over the options)
> as the last option. Then collect the answer with **one** structured-question
> call — the harness's picker — carrying **exactly one question**, the options
> as short labels only (the deep-dive included). That call is just the enter-key:
> it blocks until the developer answers, so *one decision at a time* and *wait
> for the answer* are enforced by the tool, not left to you remembering to stop.
> **Never put more than one question in that call, and never let the picker
> carry the menu's substance** — pros and cons, recommendation, and deep-dive
> stay in the prose above it. A picker carrying the whole menu is what batched
> decisions as tabs and dropped three of the four required parts in the field; a
> one-question selector does neither, and unlike a bare prose menu it cannot be
> followed by more work until the developer answers. Full format and wording:
> `§ Presenting approaches`.

This is the one place the reference's format is deliberately restated rather
than only pointed at: it is a *reflex at the point of use*, and a pointer to an
unloaded file is not a reflex.

**Not on the menu — recorded defaults.** Some things look like a choice but have
a dominant default and are cheap to reverse, so they are decided once and
recorded, not voted on. **Test organization** is one of these: it is a *detected
fact* about how the repo already separates tiers, not a taste choice, so it goes
to `## Decisions`, not to a menu — putting it on one would blow the 4–6-approach
ceiling for a decision that isn't the developer's to make.

The organization must leave the tiers distinguishable and independently
coverage-runnable (see below), but the *form* is whatever the detected ecosystem
expresses — a tier directory only where the ecosystem uses an external,
path-selected test tree, and a tag/marker/build-target/label elsewhere. An
earlier version of this note argued against a "group by tier" layout on the
grounds that two phases sharing a tier directory would manufacture a false-landed
collision. That reasoning is now spent: the completion model was rewritten so
`Landed:` is the sole signal (see `execute-test-roadmap.md § Completion model`) —
nothing infers completion from a directory's contents anymore, so two phases in
one tier directory each latch via their own `Landed:` line and collide on
nothing. Tier grouping is therefore safe; it just isn't an operator *menu* item,
because it's detected, not chosen.

**Findings** — verdicts derived from evidence: a weak-test classification, a
mock classification. These are not approaches; asking a human to vote on a
classification is asking them to vote on a fact. Findings go to the ledger,
consistent with Stage 4's own rule that findings are fixed inline, not
reported.

**`scaffold` mocks are batched, not surfaced one-by-one.** They are recorded to
the ledger en bloc, not raised as individual decisions during grading — on a
legacy codebase, the case that produces the most `scaffold` entries, one-by-one
surfacing would mean dozens of serial decisions in a single sitting. The
retiring refactor for each is named when that refactor is actually planned,
which is both less overwhelming and a better moment to name it than during a
grading fan-out.

**Silence defaults to `scaffold`** — restated here because it governs what gets
written to the ledger during this stage, same reasoning as above: the harm of
under-classifying is asymmetric, so inattention is made safe by construction
rather than relying on a human reading every entry carefully.

### The three tiers must be independently runnable

The suite must leave unit, integration, and e2e (1) **distinguishable** — a
developer new to the repo can tell which tier a test belongs to — and (2)
**independently coverage-runnable** — they can run coverage over *just* the unit
tier, or *just* integration, and so on.

The distinguishability half is carried by the `Tier:` field on every phase (and,
where the ecosystem's convention already separates tiers on disk, by the layout
too). The independent-coverage half is carried by **recording, per tier, the
command that runs it with coverage** — because per-tier coverage is *not* a
universal "point the coverage tool at a directory" operation:

- Coverage instruments the **source under test**, never the test files, so
  pointing a coverage tool at a directory of tests does not scope coverage to a
  tier. What scopes it is the tier's *selector* applied to the coverage run.
- The selector is a directory only in ecosystems that use external,
  path-selected test trees (Python, PHP, Ruby, Perl). Elsewhere it is a tag
  (Go `-tags`, `pytest -m`), a build target (`cargo test --lib`/`--test`, a
  `.csproj`, a Jest project), or a label (CTest `-L`).
- In colocated-test ecosystems the tier directory *cannot exist*: Go `_test.go`
  files must live in the package under test, and Rust unit tests are
  `#[cfg(test)]` modules compiler-bound inside `src/` — both reproduced by
  construction (see the design's *Verification notes*). Mandating a `unit/`
  directory there is impossible, not merely awkward.

So the skill records the *commands*, not a layout. This is the only formulation
that holds across every ecosystem — the invariant is "there is a command that
runs exactly one tier with coverage," and its selector is detected, not assumed.

### `## Decisions`

Every recorded default and every approach the developer picked is written to a
`## Decisions` section at the top of `.reviews/test-roadmap/test-roadmap.md`, before the first
phase. Execute mode reads this section on every resume and **never re-asks**
anything recorded there — without it, menus would fire again on every run and
the resumability requirement fails through the front door. Record at minimum:
the chosen test framework/runner, the suite strategy, phase ordering, the
weak-test rewrite decision (if grading ran), the test-organization default, and
**the per-tier run + coverage commands** — one line each for unit, integration,
and e2e — so both execute mode and the developer can run and cover each tier
independently. A worked shape:

```markdown
## Decisions

Tiers (run | coverage):
- unit:        `pytest tests/unit`            | `pytest --cov=pkg tests/unit`
- integration: `pytest -m integration`        | `pytest --cov=pkg -m integration`
- e2e:         `playwright test`              | (no coverage tool for this tier)
```

Where a tier has no coverage tool, say so on its line rather than omitting it —
an absent line reads as "forgotten," a stated "(none)" reads as "checked."
Keep each entry to the decision and its one-line reason — this section is a
record for a machine to skip past, not a design document.
