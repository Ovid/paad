# test-pushback — how the skill talks to the developer, plus critique mode

This file holds three independent, referenceable pieces. The mode files and
`break-it-check.md` point at them by name rather than inlining them, so each
stays defined once:

- **`§ Talking to the developer`** — the plain-language rule that governs
  *everything* the skill says to the developer.
- **`§ Presenting approaches`** — the menu format used whenever the skill
  puts a genuine fork in front of the developer.
- **mode `critique-plan`** — the adversarial pass Stage 4 runs against the
  skill's *own* draft plan before Stage 5 writes it.

The sections don't depend on each other and can be pointed at on their own.

---

## § Talking to the developer

Everything the skill says to the developer is in **plain language**. The person
reading may not know this codebase, the test runner, or the programming
language — and they know nothing about this skill's internals. So the design's
own working vocabulary stays *inside these files* and never reaches them
unglossed: `break-it-check`, "the gate," "latch," "mutation," "operator," "the
ledger," `boundary`/`scaffold`/`data`, "characterization," "theater,"
`Landed:`, "the phase block," "build mode"/"execute mode" are words for the
agent, not for the developer.

Translate, don't emit:

- **Name what you're doing in ordinary words, not by its codename.** Not
  "running break-it-check" — instead: *"I'll check these tests actually work by
  slipping a realistic bug into a throwaway copy of the code and confirming the
  tests catch it. Your real code is never touched."*
- **Report findings as what they mean for the tests, not by their label.** Not
  "this test is theater" — instead: *"this test still passed after I
  deliberately broke the code it's meant to check, so it isn't really testing
  that behavior."*
- **When a term does live in the written artifacts** (a tier name, a
  `boundary`/`scaffold` classification), gloss it in plain words the first time
  the developer sees it.

The test is simple: if a sentence would only make sense to someone who has read
this skill's design, rewrite it until it makes sense to someone who has not.

**Always locate a phase for the developer: "Phase X of Y."** Whenever you name a
phase to the developer, render `Phase <its written number> of <total phases in
paad/test-roadmap/test-roadmap.md>`, so they always know how much is left — the end of the
tunnel, not just the current step. On the forward-looking "next phase" prompt and
on any completion question, add progress: `— N done, M to go after this`.
Recompute all three from the roadmap on every run — never cache them:

- **Y** = count of phase blocks currently in `paad/test-roadmap/test-roadmap.md`. Because it
  is recomputed each run, it stays honest when a human adds or drops a phase: the
  total just updates next time, rather than going stale.
- **done** = count of phases whose `Landed:` line is filled in.
- **M** = Y − done − 1 (everything neither finished nor the phase in hand).

X (a phase's written number) and the done-count are **independent** — a phase can
be finished out of order, so do not assume everything numbered below X is done;
report both from the file. Use plain words: say "done," never "landed," "latched,"
or "of Y phases in the roadmap." A worked shape, numbers adding up (7 + this one +
6 = 14): *"Next is **Phase 8 of 14** — 7 done, 6 to go after this: Logger level
filtering & message formatting."*

---

## § Presenting approaches

Use this format only for **approaches** — genuine forks where the answer is
taste or is expensive to reverse (test framework/runner, suite strategy,
phase ordering, whether to rewrite weak tests grading found). Do not use it
for **findings** — verdicts derived from evidence, such as a weak-test
classification or a mock classification. A finding is a fact, not a choice;
asking a human to vote on a fact is the wrong tool. Findings are fixed
inline or recorded to the ledger, not put on a menu.

**Assume the developer does not know this repository.** The person answering
may have opened it for the first time this session — legacy and unfamiliar
code is the case the skill exists for. So every menu must be answerable with
no prior knowledge of the codebase: state each option in plain terms, and
make the recommendation strong enough to follow blind, justified by what
*this repo actually is* — its detected stack, its existing tests, its
structure — not by generic preference. A developer who knows nothing about
the code should be able to take the recommended option and be right.

Every menu, presented unbatched, contains:

- **Each option**, with **pros and cons** stated for it — in terms a
  newcomer to this codebase can weigh, not insider shorthand.
- A **recommendation**, with the **reason** grounded in what was detected in
  *this* repo — not a bare pick and not a generic default.
- A final **deep dive** option — internally, dispatch a subagent to run an
  adversarial pushback against the presented options; but *present it to the
  developer in plain words*, e.g. *"dig deeper: have a second, skeptical pass
  challenge these options and check whether there's a better one."* It
  challenges the menu itself and surfaces any better option it missed, before
  committing to any one on it. All menu text follows `§ Talking to the
  developer`.

**One decision at a time, unbatched.** A menu asks for exactly one decision.
Do not bundle a second question onto it ("...and while we're at it, do you
also want X?") — it splits the developer's attention and degrades the
answer to both. Resolve the decision in front of them, act on it, and only
then raise the next one. A follow-up that is fully determined by the answer
just given is not a second decision — it does not need its own menu, just do
it.

**Collect the answer with a single blocking question, not a prose menu you
merely intend to stop after.** After presenting the menu above, make exactly
**one** structured-question call — your harness's picker — carrying **one
question**, the options as short labels (the deep-dive included). It blocks
until the developer answers, and that is what actually enforces *wait for the
answer* and *one at a time*: a prose menu you only plan to stop after does not
stop the run — a blocking question does. Never carry more than one question in
that call, and never move the menu's substance (pros and cons, the
recommendation, the deep-dive rationale) into it — that stays in the prose above;
the picker is only the selector. A picker made to carry the whole menu is what
batched decisions as tabs and dropped three of the four required parts; a
one-question selector does neither.

If an external `pushback` skill is available in the environment, offer it
as an addition to the adversarial-review option above — never as a
replacement for it and never as a requirement to proceed. This skill is
self-contained by design (Inviolate #6): the menu format works with or
without that skill present, on any agent.

---

## mode `critique-plan`

An adversarial pass against the plan Stage 3 just drafted — the skill
critiquing its own work product before committing to it. Findings from this
pass are **fixed inline, in the draft, on the spot**. No separate report is
written; there is nothing here to hand off, only phases to rewrite or drop
before Stage 5 writes them to disk.

This is not the approach-menu format above — nothing in this mode asks the
developer to choose anything. It is the plan's author, one pass later,
reading the draft adversarially.

### The governing rule

> **Every phase must name the bug it would catch.** If a phase cannot
> answer *"what breakage makes these tests go red?"*, it is not a phase —
> it is coverage theater. Rewrite it or drop it.

This is a gate, not a suggestion. A phase that fails it does not proceed to
Stage 5 in its current form — it gets a `Catches:` line that names an
actual breakage, or it does not survive the draft. Walk every phase in the
draft and ask the question explicitly; do not let a phase through on the
strength of a plausible-sounding title. "Billing retry & dunning
integration tests" is not, on its own, an answer — *"a retry exhausting
without transitioning the account to dunning; a partial refund
double-crediting"* is (see *Phase format*'s worked example). If the answer
you write down is vague enough that it would survive being attached to any
phase in any codebase, it has not actually named a bug — push until it
names the specific breakage this phase's tests would turn red for.

### Supporting rules

**1. No success criterion may reduce to "the command exits 0."** A green
exit code and a covered line are never evidence a test is good — a test
that asserts nothing produces both, forever, including against code that is
obviously broken. This is verified tool behavior, not a hypothetical:

- `go test ./...` exits 0 against a package with no `_test.go` files.
- `jest --passWithNoTests` exits 0 with zero tests collected.
- A fully-skipped test file exits 0 in every runner examined.

Check every phase's stated success criterion against this. If a phase's
definition of done is satisfied by any of the three cases above — or by
anything with the same shape, a run that can complete having asserted
nothing — rewrite the criterion to name the specific assertion that would
have to hold, tied to the bug the phase names it would catch. Coverage
percentage is not evidence either, for the same reason: it is legitimate
only for finding code with no test at all, never for certifying that a
covered line is well-tested.

**2. Every test double and fixture is classified, and every `scaffold`
mock names the refactor that retires it.** Walk the ledger entries the
draft plan touches — new mocks and fixtures a phase would introduce, and
existing ones a phase's tests would exercise. Each must carry one of the
three classes: `boundary` (a genuine external edge — network, clock,
randomness, a third-party API), `scaffold` (exists only because the
surrounding code resists testing — test debt), or `data` (constructed test
data that is permanent and correct — a seeded account, a factory-built
order). An unclassified double is a gap in the draft, not a detail to leave
for later. A `scaffold` mock additionally names the refactor that will
retire it; that refactor is **deferred** — named now, actually done when
that refactor is actually planned, not during this pass. When in doubt
between `boundary` and `scaffold`, or when a double goes unexamined,
default to `scaffold`: the harm is asymmetric, since a `scaffold` silently
promoted to permanent hides test debt, while a `boundary` mistakenly
recorded as `scaffold` only leaves a note someone later deletes.

**3. Legacy phases characterize current behavior; they do not fix it.**
Where a phase's tests would pin behavior of existing code, check that
every assertion the phase proposes matches what the code *currently does*,
not what it *should* do. If the pass turns up behavior that looks wrong,
it is never turned into a different assertion or a code change.
Characterizing a legacy system and fixing its bugs are two different hard
problems; this pass exists to police the first, and to stop the second
from sneaking in disguised as a "more correct" assertion. A wrong-looking
behavior that clears the findings-log inclusion gate (`build-test-roadmap.md
§ The findings log`) is recorded there — verified, actionable, with the
phase that pins it — so the developer gets a real to-do list; one that
does not clear the gate is dropped, not written down as a vague note.

### After the pass

Every phase that survives can answer the governing rule's question in one
sentence, has every double and fixture it touches classified, and — where
it characterizes legacy code — pins current behavior only. Phases that
can't be fixed to clear this bar are dropped from the draft, not carried
forward with a note to "revisit."

If a `pushback` skill is available in the environment, running it in
addition to this pass is strictly additive and should be offered — it is
not required. This skill remains self-contained (Inviolate #6): the gate
above is complete on its own, on any agent, whether or not that skill is
present.
