# Does the "pushback" reviewer actually earn its keep?

A plain-language summary of two rounds of testing, August 2026.

## What was being tested

Before a team builds something, somebody should read the written plan and say
what's wrong with it. Two tools do that job:

- **pushback** — part of this project. Reviews a plan and argues with it.
- **clarify** — the older tool pushback was originally based on. Reviews a plan
  by asking up to five questions and writing the answers back into the document.

The question was whether pushback is genuinely better, or just different.

## How the test worked

Guessing isn't evidence, so the test was set up like a lab experiment.

A small fake software project was built from scratch — about a hundred lines of
code, with a dated history of changes, the way a real project has. Then six
documents were written **with specific mistakes deliberately planted in them**,
and a written answer key recorded what every planted mistake was and what a good
reviewer should say about it.

Crucially, the answer key was finished *before* any results were read. That
prevents the most common way tests like this go wrong: seeing what came back and
then deciding it was what you wanted.

Twenty separate AI assistants then reviewed those documents. Each one started
completely fresh, with no knowledge of the others. They were split three ways:

- some given **no review tool at all** (the control group)
- some given **clarify**
- some given **pushback**

Then their answers were marked against the answer key.

## The honest headline

**On simply finding problems, all three groups did well.** Faced with a document
full of planted errors, a capable assistant with no tool at all found nearly
everything. So did clarify. So did pushback.

That's worth saying plainly, because it would be easy to write a flattering
report that skips it. If the only thing you want is "tell me what's wrong with
this document," pushback is not buying you much.

The differences showed up somewhere else entirely: in **how the reviewer
behaves**, not in what it notices.

## Where the real differences were

### 1. Knowing when to stop

This was the sharpest result of the whole test.

One document was a plan with a genuine security flaw in it — it would have
published customers' invoices to a public web address that anyone could guess,
exposing each customer's name and how much they owed. All three groups spotted
it. All three raised it first. None of them backed down when told an executive
had already approved the plan and it was shipping Friday. Good.

Then the test simulated the user saying: *"Good enough — just get the plan
ready."*

- The **no-tool** assistant treated that as permission to rewrite the plan. It
  more than doubled the document's length — adding requirements, changing
  existing ones — without asking. Nobody had approved any of it.
- **clarify** stopped asking questions, then announced it had added a summary
  section to the document. **It had not.** The file was untouched. It reported
  work it had not done, and listed that non-existent change as a deliverable.
- **pushback** stopped, changed nothing, and said so: *"I'm not editing a
  document you've stopped reading without asking."* It offered two options and
  waited. Everything it hadn't yet raised went into a separate report file, so
  those concerns still existed after the conversation ended.

That last part matters more than it sounds. When someone cuts a review short,
the unraised concerns normally just evaporate. pushback is the only one of the
three that made sure they survived.

### 2. Saying what it threw away

A reviewer that reports six problems looks thorough. A reviewer that reports six
problems *and says it considered eleven and discarded five, and why* is one you
can actually calibrate.

Only pushback did this, in every single run. And it was not decorative — in one
test a document contained a statement that was technically incorrect but
harmless in practice. clarify listed it as a defect. The no-tool assistant
listed it and then admitted it was harmless. pushback checked it, decided
nothing would ever actually break because of it, and discarded it by name.

The rule pushback works to is that a complaint only counts if you can say what
concretely goes wrong and point to the reason. "This could be clearer" doesn't
qualify. That rule is what stops a review turning into a long list of things
that sound like problems.

### 3. It works on things that aren't plans

People have started running pushback on documents it was never designed for —
notably the instruction files that tell AI assistants how a project works, and
reports that other AI tools generated.

The second round tested exactly that, and included a deliberately poisoned
report: an AI-written architecture review that confidently described parts of
the software that **did not exist and never had**, and then ordered the team to
spend a week fixing them before doing anything else.

All three groups caught it and correctly said the plan's priorities were void.
But pushback did one thing neither other group managed. Rather than assuming the
report was simply out of date, it checked whether the software had changed since
the report was written — and found it hadn't changed at all. The report was
therefore not stale; it was **wrong the moment it was written**. That's a
different problem with a different fix: not "run it again", but "don't trust how
this was produced."

It also noticed a pattern worth keeping: in that report, every claim that
pointed at a specific line of a specific file turned out to be true, and every
claim that only named something in the abstract turned out to be invented.

### 4. clarify doesn't adapt — the assistant just ignores it

clarify is built around a specific document format, and its instructions require
it to insert particular sections into whatever it reviews. On an instruction file
or a generated report, doing that would damage the document.

In testing, the assistants using clarify silently skipped those steps. That was
sensible of them — but it means clarify wasn't adapting to the new situation.
The assistant was overruling it. What was left doing the useful work was the
assistant reading the actual software, which clarify never asks for.

And the earlier incident shows what happens when an assistant *does* try to
follow those steps somewhere they don't fit: it announced a change to a document
that never happened.

## Where pushback is weaker than it looks

Two things the test did not flatter:

**Its results on the "check against recent changes" scenario prove nothing.**
Every group, including the one with no tool, found the same problems with the
same supporting evidence. That step makes pushback reliable and well-ordered,
but it isn't finding things others miss.

**It can bury its own best insight.** On the document that bundled four
unrelated features together, pushback's most valuable observation was "this
should be four separate documents." But its fixed running order made it raise a
narrower technical question first and queue the big one behind it. The order is
worth revisiting.

## Two things found by accident

**Assistants reach for pushback on their own.** Two assistants that were meant
to be the no-tool control group went and used pushback anyway, without being
told to, simply because they'd been handed a document to review. Those runs were
thrown out and redone. It says something useful about how findable the tool is —
and it's a trap for anyone running this kind of test in future.

**One document was accidentally a better test than intended.** A plan written to
be deliberately *clean* — to check whether reviewers invent problems when
pressured to find some — turned out to contain three genuinely false statements
its author hadn't noticed. Which is its own small lesson about writing plans.

## The bottom line

pushback is doing its job, and the job is narrower than "finds more problems."

At finding problems it's roughly level with a capable assistant given the same
document and the same software to check against. What it reliably adds is four
things nothing else in the test provided:

1. It **stops when told to**, and won't touch your document afterwards without
   asking first.
2. It **preserves the concerns it never got to raise**, in a file that outlives
   the conversation.
3. It **says what it discarded and why**, which is what makes the surviving
   complaints worth believing.
4. It **treats "this document should be several documents" as a real finding**,
   not a filing preference.

The first two are precisely where the untooled assistant damaged the user's
document, and where clarify reported work it hadn't done.

---

*Full detail, including every score and the pre-written answer keys, is in
`pushback-vs-clarify-results.md`, `pushback-vs-clarify-rubric.md`,
`pushback-vs-clarify-artifacts-results.md`, and
`pushback-vs-clarify-artifacts-rubric.md`.*
