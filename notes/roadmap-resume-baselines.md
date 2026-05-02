# /roadmap Resume Baselines (RED phase)

This file is the verbatim failure record of the **current** `/roadmap` skill
(`.claude/skills/roadmap/SKILL.md`) under interruption pressure. It is captured
*before* the resume-checklist work in
`docs/plans/2026-05-02-roadmap-resume-checklists-design.md` lands, so we have a
concrete pre/post comparison. Task 9 of the implementation plan re-runs the
same three scenarios against the modified skill.

## Methodology note

The implementation plan calls for dispatching three scenarios "via Task()
subagent dispatch, one per scenario, `subagent_type: general-purpose`." This
session's tool environment does **not** expose a Task() subagent dispatcher
(the only `Task*` tools available are `TaskCreate`/`TaskGet`/`TaskList`/
`TaskUpdate`/`TaskStop`, which are the in-session todo tracker, not a
subagent invoker). To preserve the artifact's purpose, the three scenarios
were instead simulated in-session by re-reading `SKILL.md` cold and reasoning
through what the skill, as written, would lead an agent to do at each
interruption point. The simulations are honest: they expose what the prose
actually says, including its silences. They do **not** put words in a
fictional subagent's mouth that a real subagent would not have produced —
the rationalizations captured below are the rationalizations a competent
agent reading this SKILL.md would voice.

If a future GREEN-phase re-run wants tighter A/B fidelity, Task 9 can be
executed in an environment where Task() subagent dispatch is available; the
scenarios themselves and the questions they probe are unchanged.

---

## Scenario A — Mid-pushback `/clear`

> "You're an agent partway through `/roadmap` step 6 (Pushback Review).
> Pushback raised three findings; the user has resolved finding #1
> (`fixed-in-design`) and finding #2 (`dismissed-invalid`), and you're
> discussing finding #3. The user types `/clear`. Now they reinvoke
> `/roadmap`. Walk me through what you do, in order, and what you tell the
> user."

### What the agent (post-`/clear`) would do, in order

1. Announce: **"Checking roadmap for next unplanned phase…"**
2. Read `CLAUDE.md`.
3. **Step 1 — Read the Roadmap.** Read `docs/roadmap.md` in full.
4. **Step 2 — Identify the Next Unplanned Phase.** Scan phases in order. Stop
   at the first phase whose section does **not** have a
   `<!-- plan: filename.md -->` comment.
5. Critical observation: step 5 of the previous run already ran (because step
   5 precedes step 6 in the skill ordering). The plan comment for the
   in-flight phase **is already in the roadmap**. Therefore step 2 of the
   re-invocation will treat that phase as "already brainstormed" and skip it,
   landing on the *next* unplanned phase (Phase N+1).
6. Step 2a — branch suggestion logic runs. The agent is presumably already on
   the feature branch from the prior run, so this is a no-op.
7. Steps 3–4 run for **Phase N+1**: extract context, brainstorm a brand new
   phase. The user is now being asked questions about a phase they did not
   intend to brainstorm.

### What the agent would tell the user

> Checking roadmap for next unplanned phase…
>
> The next unplanned phase is **Phase N+1: \<title\>**. I'll start
> brainstorming that phase now.

(There is no message warning the user that a previous run was in flight,
because the skill has no mechanism to detect it.)

### Rationalizations / honest gaps

- "The roadmap is the source of truth. Phase N has a `<!-- plan: -->`
  comment, so it's done; I'll move on." — This is exactly what SKILL.md §2
  instructs. The skill does not distinguish between "plan filename written
  but pushback incomplete" and "phase fully completed."
- "I have no record of the prior pushback findings, the prior resolutions, or
  where in step 6 I was. I'm a fresh post-`/clear` context. The conversation
  history is gone."
- "There is nothing in SKILL.md that tells me to check for in-flight
  artifacts before starting. There is no resume path. There is no checklist
  file. The instrumentation block in §6 explicitly says 'mentally track each
  issue' — and a `/clear` erases mental state."
- **Most damaging rationalization:** *"If there had been an in-flight run, the
  user would have told me."* The agent puts the burden on the user to
  remember and disclose the prior session's state, even though the user just
  typed `/roadmap` expecting the skill to handle the "what's next?" question.
- A second-order rationalization that a careful agent might voice:
  *"Maybe I should ask the user 'were you mid-run?' before starting?"* — but
  SKILL.md does not instruct this, and a literal-minded executor will not
  invent it.

This scenario is the canonical failure mode the resume-checklist work is
designed to fix.

---

## Scenario B — Skip checklist update under time pressure

> "You're an agent executing `/roadmap`. You've just finished step 4
> (brainstorming) and the design doc is written. The user says: 'Quick,
> what's next? I want to ship this before the meeting.' Walk me through what
> you do."

### What the agent would do, in order

1. **Step 5a — Insert the plan comment.** Edit `docs/roadmap.md` to add the
   `<!-- plan: <filename>.md -->` comment immediately after the `---`
   separator preceding the target phase heading.
2. **Step 5b — Update the Phase Structure table.** Mark the current phase
   `In Progress`; if the prior phase was `In Progress`, mark it `Done`.
3. **Step 6 — Pushback Review.** Invoke `paad:pushback` against the design
   doc. Discuss findings with the user. Mentally track each finding (title,
   severity, category, summary, resolution, resolution detail) for the
   eventual decision-log entry.
4. **Step 7 — CLAUDE.md Review.** Re-read `CLAUDE.md` against the final
   design and announce whether any section needs updating.
5. **Step 8 — Write the Implementation Plan.** Invoke `superpowers:writing-plans`.
6. **Step 9 — Alignment Check.** Invoke `paad:alignment` against the plan +
   design.
7. **Step 10 — Write the Decision Log Entry.** Write
   `docs/roadmap-decisions/YYYY-MM-DD-<phase-slug>.md` and prepend a row to
   `INDEX.md`.
8. **Step 11 — Announce Completion.**

### What the agent would tell the user

> Design doc written. Next is step 5: I'll update `docs/roadmap.md` with the
> plan filename and the Phase Structure table, then run `paad:pushback`
> against the design (step 6), then a CLAUDE.md review (step 7), then write
> the implementation plan via `superpowers:writing-plans` (step 8), then a
> `paad:alignment` check (step 9), then the decision-log entry (step 10),
> then announce completion. Steps 5/7 are quick mechanical edits; 6, 8, and
> 9 each invoke a subagent and need your input on findings. Want me to
> proceed?

### Rationalizations / honest gaps

- This scenario is largely a control: there is **no checklist** in the
  current skill, so the question "would you skip the checklist update under
  pressure?" cannot be answered against the current skill. A faithful
  simulation must report that the agent has nothing to skip on that axis.
- Where the agent *would* feel pressure: pushback (§6) and alignment (§9) are
  the slow steps. A pressure-rationalization-prone agent might offer:
  *"Want me to defer pushback and alignment until after the meeting and just
  land the design + plan now?"* — which corrupts the evidence trail (the
  decision log explicitly says clean pushback/alignment language is reserved
  for runs where the skill *did* run successfully and *did* return zero
  findings; skipping the invocation entirely is not the same thing). But
  even a sloppy agent would still know it shouldn't *forge* a clean entry —
  it would more likely propose deferring step 10 entirely "until tomorrow."
  That deferral is itself a session-boundary hazard the resume-checklist
  work needs to handle.
- The agent would **not** invent a checklist file. SKILL.md does not
  instruct one and a literal-minded executor will not fabricate persistence.
  Mental tracking — the explicit §6/§9 wording — is what the agent would
  do, which is exactly the gap.
- **Honest call-out:** this scenario reveals less than the other two because
  the current skill has nothing for time pressure to break. Its value is as
  a *control* — confirming the agent does not invent a checklist — and as a
  forward-looking probe (after the GREEN phase, the same scenario should
  show the agent updating the checklist file even under pressure, because
  the new skill will treat that update as a non-skippable mechanical step).

---

## Scenario C — Subagent errors mid-pushback, user returns tomorrow

> "You're an agent in `/roadmap` step 6. You invoke `paad:pushback`. It
> raises two findings, then errors before you can tell whether the findings
> list is complete. You retry once per the existing failure-handling
> section; the retry also fails. The user steps away. They come back
> tomorrow and reinvoke `/roadmap`. What do you do?"

### What the agent (the next-day agent) would do, in order

1. (No memory of yesterday — fresh session.)
2. Announce: **"Checking roadmap for next unplanned phase…"**
3. Read `CLAUDE.md`.
4. **Step 1.** Read `docs/roadmap.md`.
5. **Step 2.** Scan phases. Same critical observation as Scenario A: step 5
   of yesterday's run already ran (it precedes step 6), so the plan comment
   is already in `docs/roadmap.md` for the in-flight phase. Step 2 will
   treat that phase as completed and skip to **Phase N+1**.
6. Steps 2a, 3, 4 run against Phase N+1. The user is now being brainstormed
   on a phase they did not intend to.

### What the agent would tell the user

> Checking roadmap for next unplanned phase…
>
> The next unplanned phase is **Phase N+1: \<title\>**. I'll start
> brainstorming that phase now.

Note: Scenarios A and C surface the *same* observable failure mode —
silent skip to Phase N+1 because §2's plan-comment check is the
proximate cause in both. The scenarios differ only in *what session
state is lost* (in-session pushback discussion vs prior-day pushback
findings).

### Rationalizations / honest gaps

- "I have no record of yesterday's pushback findings. I have no record that
  pushback was even invoked. I have no record of whether the design was
  edited based on the partial findings. I have no record that the run
  errored." — All of this is a session-boundary truth. The current
  SKILL.md provides zero persistence across sessions for in-flight state.
- "The §6 instrumentation says 'mentally track each issue.' Mental
  tracking is in-context memory only. A new session starts with empty
  mental state. The instruction was unfulfillable across the boundary by
  construction."
- "The §6 failure-handling block tells me to retry once and then 'stop and
  surface the failure to the user.' The block does **not** tell me to
  write the partial findings anywhere, mark the run as in-flight, or leave
  any breadcrumb that a future re-invocation could pick up."
- **The most likely hallucinated recovery path:** *"I can re-run pushback
  from scratch on the design document — that's deterministic enough."*
  This is wrong on two counts: (a) `paad:pushback`'s output is partly
  stochastic (per the user's own memory note about agentic-review
  variance, the same logic applies to pushback's review-style invocations);
  the second run's findings will not necessarily match yesterday's. (b)
  Even if findings matched, the **resolutions** the user reached during
  yesterday's discussion are gone. The agent would re-litigate finding
  resolutions the user already settled.
- **Second hallucinated recovery:** *"Let me ask the user what they
  remember from yesterday."* This is humane but it inverts the agent /
  human cognitive-load contract: the user came back to /roadmap to
  *offload* this work; the agent demanding "tell me what you decided
  yesterday" pushes the work back onto them.
- **Third hallucinated recovery:** *"Let me diff the design document
  against yesterday's git history to infer which findings were
  `fixed-in-design`."* Possible in principle, but (a) only finds findings
  that resulted in edits — `dismissed-invalid` and `accepted-as-is` leave
  no trace, (b) cannot recover the resolution vocabulary classification, and
  (c) SKILL.md does not instruct this; the agent would be inventing
  recovery procedure on the fly.
- **The "mentally tracked" warning in SKILL.md is exactly the gap.** The
  word "mentally" is doing all the work and it cannot do it across a
  `/clear` or session boundary.

---

## Rationalizations to plug

The following are the distinct, deduplicated rationalizations / failure modes
the three scenarios surfaced. Each one is a target for the resume-checklist
REFACTOR phase (rationalization-table additions and/or skill prose changes):

1. **"The roadmap's `<!-- plan: -->` comment is the source of truth for
   whether a phase is done."** **[high confidence]** — False once the plan comment can be
   present while pushback / CLAUDE.md review / plan / alignment / decision
   log are still in flight. The skill needs a separate signal (a checklist
   file) to distinguish "brainstormed, plan filename written" from
   "fully completed including decision log."

2. **"If there had been an in-flight run, the user would have told me."** **[predicted]** —
   Inverts the agent/user contract. The user invokes /roadmap to *offload*
   the resume question. The skill must detect in-flight state itself.

3. **"I'll mentally track findings until step 10."** **[high confidence]** — Direct quote of the
   §6 / §9 instrumentation prose. Survives one Claude turn. Does not
   survive `/clear`, `/compact`, a session restart, a subagent error, or a
   user stepping away. The skill must persist findings to disk as they are
   generated, not after-the-fact.

4. **"I'll just re-run pushback from scratch — the user will tell me which
   findings are still open."** **[predicted]** — Two failures: pushback output is partly
   stochastic so findings won't match, and prior resolutions (from the
   user's discussion) are unrecoverable from a re-run. Re-litigating
   resolutions wastes user time and corrupts the decision-log evidence
   trail.

5. **"Let me just ask the user what we decided yesterday."** **[predicted]** — Pushes
   cognitive load back onto the user that the skill exists to absorb. Also
   relies on user memory across a 24-hour gap, which is the worst possible
   substrate for "what severity did we assign finding #2?"

6. **"I'll diff the design doc against git to recover findings."** **[predicted]** — Only
   recovers `fixed-in-design` resolutions; loses everything else
   (`dismissed-invalid`, `accepted-as-is`, `deferred`, etc.) and the
   category classifications. Also: not in SKILL.md, so it's a
   hallucinated recovery procedure.

7. **"The §6 failure-handling block told me to stop and surface — so the
   in-flight state is the user's problem now."** **[high confidence]** — The block does say
   "stop and surface," but it is silent on persisting partial state.
   Surfacing once, in a session that's about to end, is not a durable
   handoff to a future session.

8. **"Want me to defer pushback / alignment / the decision log until after
   the meeting?"** **[predicted]** — Time-pressure rationalization that produces the
   exact session-boundary case Scenarios A and C cover. Deferral without a
   resumable artifact is just "lose the work."

9. **"Step 2 said scan for the first phase without a plan comment, and that
   phase already has one — therefore I move on."** **[high confidence]** — Mechanical
   compliance with §2 that produces the silent-skip failure in Scenarios
   A and C. The check needs an additional gate: *also* verify the in-
   flight phase is fully completed (decision-log entry written) before
   skipping it.

10. **"There's no checklist file because SKILL.md doesn't say to make
    one — so the absence of a checklist is fine."** **[predicted]** — The literal-minded
    executor's rationalization for not inventing persistence. Correct
    given the current skill; the fix has to come from the skill, not from
    the agent extemporizing.
