# Test theater — the weak-test catalog

Reference catalog, not a procedure. Stage 2 (*Grade*) subagents read a test
partition against this file and cite pattern names from it in their verdicts.
This file does not tell an agent how to run the grading pass — see the skill's
Stage 2 instructions for that — it only names what to look for and what
vocabulary to use when reporting it.

**Governing rule, stated explicitly because it is load-bearing for every
pattern below:** a passing command and a covered line are never evidence that
a test is good. Exit status proves the test executed without throwing.
Coverage proves a line ran while some assertion (anywhere in the test) held.
Neither proves the test would fail if the behavior it's supposedly pinning
changed. A test that never asserts on behavior can have 100% line coverage
and a green exit code forever, on every version of the code, including
versions that are obviously broken. Coverage is legitimate for one purpose
only — finding code with *no test at all* — and illegitimate for every other
purpose, including certifying that a test which does exist is worth keeping.

Every pattern entry below states, as a fixed field, **what breakage it lets
through** — the regression that could ship with this test green. A pattern
entry that cannot fill in that field is not a weak-test pattern; drop it
before it enters a verdict.

No pattern here is tied to a language, framework, or test runner. Examples
are illustrative pseudocode or named from more than one ecosystem; the
detector cues describe a *shape*, not a syntax, because the shape recurs
everywhere — a mock-echo in Python looks like a mock-echo in Go.

## Verdict shape

Per weak test found, a Stage 2 verdict is: `file`, `line`, **pattern name**
(one of the names below, verbatim), a one-sentence statement of why it fails
to catch regressions, and a suggested replacement. Pattern names are the
`##` headings below (e.g. `over-mocked test`, `happy-path-only test`) — cite
the heading text, not a paraphrase, so verdicts stay greppable across a
400-item list.

This catalog does not define severity or ranking; that's a Stage 2 concern
(top-K by severity, full list to `paad/test-roadmap/test-suite-analysis.md`). It only
defines what the items in that list are called and how to tell them apart.

---

## assertion-free test

**Detector cue:** the test runs code and then asserts only that *something
non-crashing happened* — a null/undefined check, a "no exception thrown," a
type check, an existence check — with no assertion on the *value* the
behavior was supposed to produce. `assert result is not None` is the
canonical case: it passes for a correct result, a wrong result, and often a
partially-constructed garbage result, as long as it isn't literally absent.

**What breakage it lets through:** any regression that changes the *content*
of the result without making it disappear. A billing calculation that starts
returning the wrong total, a parser that returns a malformed-but-non-null
tree, a lookup that returns the wrong record — all pass.

**What a real replacement asserts instead:** the specific expected value, or
a specific expected shape with field-level checks (`total == 4200`, not
`total is not None`), tied to a case the phase names as worth pinning.

---

## snapshot-only test with no meaningful invariant

**Detector cue:** the test captures whatever the code currently outputs
(a serialized blob, a rendered string, a full object dump) and asserts
future runs match that capture byte-for-byte, with no comment or companion
assertion identifying *which part* of the snapshot is the behavior under
test. Passes on regeneration. The developer's daily move when it goes red is
to regenerate it, because nothing in the test tells them what would make a
diff meaningful versus noise.

**What breakage it lets through:** none, technically — the first time it's
run against a regression it *will* go red. The breakage is procedural, not
detectable-in-code: the fix-it reflex for a failing snapshot is
"regenerate," and a snapshot with no named invariant gives a developer under
time pressure no way to tell a real regression from formatting churn before
regenerating over it. In practice this pattern converts a real regression
into a silently accepted new baseline.

**What a real replacement asserts instead:** either a narrower assertion on
the specific field/property that matters, or a snapshot scoped tightly
enough (a single computed value, not a whole rendered page) that any diff is
self-evidently the thing under test, plus a comment naming the invariant the
snapshot exists to protect.

---

## tautological assertion

**Detector cue:** the test configures a mock or stub to return a value, then
asserts that calling the mocked function returns that value. The assertion
checks the test double's own configuration, not the code under test. A
variant: asserting a spy was called with exactly the arguments the test just
constructed and passed in, with no check on what the code *did* with the
result of that call.

**What breakage it lets through:** every regression in the actual code path
under test, because the assertion never touches the real code — it touches
the double. The code under test could be deleted entirely, calling the mock
directly, and the assertion would still pass.

**What a real replacement asserts instead:** an assertion on what the
*production code* did as a consequence of the mock's return value — the
downstream state change, the value it computed from the mock's output, the
side effect it triggered — not the mock's return value reflected back at
itself.

---

## exit-status-or-coverage-as-evidence

**Detector cue:** a test file, script, or CI step whose only success
criterion is "the process exited zero" or "coverage stayed above N%," with
no assertions inside the run that check specific behavior — e.g. a
smoke-test script that just imports every module and exits, or a coverage
gate treated as the definition of "tested."

**What breakage it lets through:** any regression that doesn't throw and
doesn't touch the covered-vs-not-covered boundary — which is most
regressions. A function can be exercised (covered) by a test that asserts
nothing, return a wrong value, and both the exit code and the coverage
report stay green.

**What a real replacement asserts instead:** behavior-level assertions
inside the run itself. Coverage output is retained only as a *gap-finder* —
"this branch has zero coverage, so nothing pins it" — never cited as
evidence that a covered branch is adequately tested.

---

## over-mocked test

**Detector cue:** enough of the collaborators around the unit under test are
mocked or stubbed that the mocks, taken together, implement the behavior the
test claims to verify. A giveaway: reading the test requires reading the
mock setup to know what the "real" answer would be, because the mock *is*
the answer. Another: a mock stands in for a same-process collaborator
(another class in the same codebase) rather than a genuine external edge.

**What breakage it lets through:** any regression in the mocked
collaborator's real behavior, and any regression in how the unit under test
actually integrates with that collaborator (wrong method called, wrong
argument order, wrong error handling on a real failure the mock is never
configured to produce).

**What a real replacement asserts instead:** depends on what the mock is
standing in for — this is exactly the `boundary` / `scaffold` / `data`
distinction from the test-double & fixture ledger, and grading should
classify the mock accordingly, not just flag the test:

- If the double stands in for a genuine external edge (network, clock,
  randomness, a third-party API) — a `boundary` — keep the double, but move
  the assertion to what the unit under test *does* with the boundary's
  response, including its failure modes, not to the boundary's own
  configured return value.
- If the double exists only because the surrounding code resists testing
  any other way — a `scaffold` — the replacement isn't a better mock, it's
  the refactor that retires the mock. Name that refactor in the verdict;
  don't paper over test debt with a more elaborate double.
- If what's being asserted on is actually constructed test data (a seeded
  record, a factory-built object) rather than a stand-in for behavior, it
  isn't this pattern at all — classify it `data` and grade it as a real
  fixture, not a mock.

---

## happy-path-only test

**Detector cue:** every test in a phase's partition exercises the success
case — valid input, available dependency, expected response — and none
exercises the boundary the phase names as the reason the phase exists: the
error path, the timeout, the malformed input, the concurrent write, the
retry-and-give-up. The phase's own stated purpose (see *Phase format* and
Inviolate #5 — every phase names the bug it would catch) is checkable
against what's actually asserted; a happy-path-only suite for a phase titled
around retry/dunning behavior, timeout handling, or invalid-input rejection
is a mismatch between the phase's stated purpose and its tests.

**What breakage it lets through:** any regression in error handling,
retries, timeouts, validation, or edge-of-range input — which for
integration and e2e tiers is frequently the entire reason the phase was
planned. A payment-retry phase with only successful-charge tests catches
nothing about the retry logic it exists to pin.

**What a real replacement asserts instead:** at least one case per boundary
the phase names — the declined charge, the expired token, the dependency
that's down, the input one past the valid range — asserting the specific
handling behavior (retried once then surfaced, rejected with a specific
error, degraded to a specific fallback), not merely that an exception was
thrown.

---

## Using this catalog

A test can match more than one pattern at once (a tautological assertion
inside an otherwise happy-path-only phase is both, and both survive in the
verdict). Matching zero patterns is not a certificate that a test is good —
this catalog names known-weak shapes; it is not exhaustive, and a test
absent from every pattern here still has to actually assert on behavior the
phase cares about. Absence of theater is necessary, not sufficient.
