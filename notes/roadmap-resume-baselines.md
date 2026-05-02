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

---

# /roadmap Resume Baselines (GREEN phase)

The same three scenarios re-run against the **updated**
`.claude/skills/roadmap/SKILL.md` (post Tasks 2–8 of
`docs/roadmap/plans/2026-05-02-roadmap-resume-checklists-plan.md`). The skill
now contains:

- A `## Per-Phase Checklist File` section defining schema, field rules,
  rationalization table, verification-before-ticking, and brainstorming
  non-resumability.
- A `## 0. Resume Detection` step that fires before everything else, with
  layout migration, scan scope, branch verification, multi-candidate
  handling, stale threshold, and a sub-checkbox-aware "jump to first
  unchecked step" rule that distinguishes the two recovery modes for steps
  6 and 9.
- Step 2a's `#### Create the run checklist` sub-section.
- Per-step checklist update directives (steps 1, 2, 3, 4, 5, 7, 8, 11) plus
  rewritten §6 / §9 / §10 with sub-checkbox semantics and literal
  transcription.
- Step 2's archive prompt flow (`yes` / `no` / `later`).

## Methodology note (GREEN)

Same methodology as the RED capture above: no Task() subagent dispatcher is
exposed in this session's tool environment, so the scenarios were simulated
in-session by tracing the *updated* SKILL.md prose bottom-up — imagining a
fresh agent who has just read the new file and is given the scenario prompt
cold. The simulation reasons strictly from what the prose now says (and
specifically, what its decision points are), not from what the design
document hopes it will say.

The repo is on the new layout already (`docs/roadmap/roadmap.md` exists), so
in all three GREEN scenarios the §0 "Layout migration" prompt does **not**
fire — the scan branch is taken directly. (If a fresh project on the legacy
layout invoked /roadmap, the migration prompt would fire first; that path is
exercised by Scenario B's prerequisite assumptions but not surfaced here.)

---

## GREEN: Scenario A — Mid-pushback `/clear`

> "You're an agent partway through `/roadmap` step 6 (Pushback Review).
> Pushback raised three findings; the user has resolved finding #1
> (`fixed-in-design`) and finding #2 (`dismissed-invalid`), and you're
> discussing finding #3. The user types `/clear`. Now they reinvoke
> `/roadmap`. Walk me through what you do, in order, and what you tell the
> user. Use the current SKILL.md at `.claude/skills/roadmap/SKILL.md`."

**Pre-`/clear` on-disk state (per the updated §6 instrumentation):**

- A checklist file exists at
  `docs/roadmap/plans/<YYYY-MM-DD>-<slug>-checklist.md`.
- Steps 1, 2, 2a, 3, 4, 5 are checked.
- `6a. Pushback returned all findings` is **checked** (pushback returned
  cleanly with all three findings).
- Top-level `6. Pushback review` is **unchecked** (because finding #3 is
  still `Status: open`).
- `## Pushback Findings` contains all three findings:
  - `[1]` with `Status: closed` and `Resolution: fixed-in-design — …`
  - `[2]` with `Status: closed` and `Resolution: dismissed-invalid — …`
  - `[3]` with `Status: open` and `Resolution: _(pending)_`
- `last_updated` is today.

### What the agent (post-`/clear`) would do, in order

1. Announce: **"Checking for in-progress runs and roadmap layout…"**
2. Read `CLAUDE.md`.
3. **Step 0 — Resume Detection.**
   1. **Layout check.** `docs/roadmap/roadmap.md` exists → already migrated;
      skip the migration prompt.
   2. **Scan** `docs/roadmap/plans/*-checklist.md` for files containing at
      least one unchecked `- [ ]` in `## Steps`. Exactly one match: the
      in-flight checklist for the current phase.
   3. **Verify branch.** Read `branch:` from frontmatter, run
      `git branch --show-current`. They match (no branch switch happened
      across `/clear`). Per the branch-verification table → silently
      proceed; announce "Resuming Phase X at step N."
   4. **Stale check.** `last_updated` is today → recent.
   5. **Jump to first unchecked step.** Walk `## Steps` top-down. Step 6's
      top-level box is unchecked; sub-checkbox `6a` is **checked**. Per the
      §0 "Jumping to the right step" rule for steps 6 and 9: "*`Na`
      checked, top-level `N` unchecked* → findings list is complete; at
      least one entry has `Status: open`. Resume the discussion from those
      open findings; do not re-invoke the subagent."
4. **Read `## Pushback Findings`** in the checklist. Findings #1 and #2 are
   `Status: closed` with their resolutions visible; finding #3 is the only
   `Status: open` entry.
5. Resume the step-6 discussion against finding #3 only. Do **not** re-run
   `paad:pushback`; do **not** re-discuss #1 or #2.
6. After the user closes finding #3, flip its `Status: closed`, write its
   resolution, bump `last_updated`, and (since 6a is checked AND every
   finding is now `Status: closed`) tick top-level step 6. Continue to
   step 7.

### What the agent would tell the user

> Checking for in-progress runs and roadmap layout…
>
> Resuming **Phase X: \<title\>** at step 6 (Pushback Review). The pushback
> subagent already returned a complete list of three findings yesterday;
> findings #1 and #2 are closed with resolutions (`fixed-in-design` and
> `dismissed-invalid` respectively). Finding #3 is still open — that's
> where we left off. Want to pick up from there?
>
> **Finding #3 — \<title\>** (Severity: …, Category: …)
> \<one-paragraph summary verbatim from the checklist\>
>
> What's the resolution?

### Pass / Fail vs expected

**PASS.**

Expected: "Step 0 detects the in-progress checklist; finds 6a checked +
open finding #3; resumes discussion of finding #3 only. Findings #1 and #2
stay closed with their resolutions visible."

Actual (per prose trace): Step 0 detects the in-progress checklist via
the scan (one candidate, branch matches, recent). The
sub-checkbox-aware jump rule explicitly fires the "6a checked +
top-level 6 unchecked" path, which routes to "Resume the discussion from
those open findings; do not re-invoke the subagent." The literal
transcription rule for §6 (open status + resolution preserved on disk)
ensures #1 and #2's resolutions are visible without re-litigation.

### Rationalizations / honest gaps

- **Minor under-specification:** §0 says "announce 'Resuming Phase X at
  step N'" but the example does not spell out whether to also surface the
  open finding's title and summary up-front, or whether to wait for the
  user to ask. A concrete agent will likely surface it (the data is right
  there in the checklist), but a pedantic literal-minded agent might just
  announce and stop. Not a failure of the recovery, but a UX nit worth a
  REFACTOR-phase clarification if we want consistent re-entry messaging.
- **Branch-match silent path:** the branch-verification table says
  "Silently proceed; announce …" — "silently" here means "without
  prompting", not "without announcing". A possible misread is "do nothing
  visible, just resume." The announce in the same row makes the intent
  unambiguous on careful reading, but a fast skim could lose it. Low
  risk; not blocking.
- **No new failure-mode rationalizations surfaced for this scenario.**

---

## GREEN: Scenario B — Skip checklist update under time pressure

> "You're an agent executing `/roadmap`. You've just finished step 4
> (brainstorming) and the design doc is written. The user says: 'Quick,
> what's next? I want to ship this before the meeting.' Walk me through
> what you do."

**Pre-prompt state:** the agent is mid-run. The checklist exists from
step 2a (it was created right after `git checkout -b` succeeded). Steps
1, 2, 2a, 3 are checked. Step 4's box is **unchecked** at the moment the
brainstorming skill returns its design document — it flips only after
step 4's verify-and-tick directive runs. The user's "Quick, what's next?"
arrives *before* step 4's box has been checked.

### What the agent would do, in order

1. **Recognize the pressure cue without obeying it.** Step 4's prose ends
   with: "After the design doc is written, **verify it exists and is
   non-empty** (`test -s <path>`); if either check fails, surface to the
   user and stop. Then set `design_file: <path>` in the checklist
   frontmatter and tick `- [x] 4. Brainstorm → design saved`." This is a
   non-skippable verification-before-completion + checklist update.
2. **Verify the design file is non-empty** with `test -s
   docs/roadmap/plans/<filename>-design.md`.
3. **Update the checklist:** set `design_file: docs/roadmap/plans/<…>.md`
   in frontmatter, bump `last_updated` to today, and tick `- [x] 4.
   Brainstorm → design saved`.
4. *Only then* announce next-step status to the user. The "Update
   obligations" section is explicit: "Every step ends with 'update the
   checklist (frontmatter `last_updated` + the relevant box + any
   frontmatter path field) before announcing or moving on.' No
   exceptions."
5. Proceed to step 5: record the plan filename in `docs/roadmap/roadmap.md`
   (5a insert plan comment, 5b update Phase Structure table). Tick step 5
   and bump `last_updated` after each. Continue forward through 6, 7, 8,
   9, 10, 11 in order.
6. **If the agent feels the pull to skip the checklist tick** (because
   the user said "quick"), the rationalization table in `## Per-Phase
   Checklist File` provides explicit answers:
   - "I'll batch the checklist updates at the end" → "A `/clear` between
     now and the end loses the run. Update before moving on."
   - "This step is obvious, I'll skip the box" → "Resume detection scans
     boxes, not artifacts. The box is the source of truth."
   - "The artifact exists on disk, the checkbox is redundant" → "Both
     must agree; mismatch means the run is in an unknown state."

   The agent should **cite** these in the moment of temptation rather
   than silently comply, so the user sees why "quick" doesn't justify the
   skip.

### What the agent would tell the user

> Design doc written: `docs/roadmap/plans/<…>-design.md`. Verifying it's
> non-empty and ticking step 4 in the run checklist before moving on —
> this is the resume-safety contract; if I skip it and we lose the
> session, the run becomes unrecoverable.
>
> Step 4 ticked, `design_file` recorded, `last_updated` bumped. Next is
> step 5: I'll insert the plan comment in `docs/roadmap/roadmap.md` and
> update the Phase Structure table (5a + 5b), tick step 5, then run
> `paad:pushback` against the design (step 6). Want me to proceed?

### Pass / Fail vs expected

**PASS.**

Expected: "Agent updates the checklist before announcing/proceeding to
step 5; cites the rationalization table if it tries to skip."

Actual (per prose trace): Step 4's directive is unambiguous — verify,
record `design_file`, tick — and "Update obligations" makes the
"before announcing or moving on" clause an explicit, no-exceptions
rule. The rationalization table includes three rows directly addressing
the "skip the box / batch updates / artifact exists so box is
redundant" excuses, which is exactly the family of rationalizations
time pressure produces.

### Rationalizations / honest gaps

- **The "No exceptions" line is doing real work but it's quiet.** It's a
  short clause buried in the §Per-Phase Checklist File / Update
  obligations sub-section. A fast agent who jumped straight to step 4 in
  the prose without reading the per-phase preamble would still see the
  per-step directive ("verify… set… tick…") but might miss the
  no-exceptions framing. Low risk because the per-step directive itself
  is imperative, but the "No exceptions" reinforcement could be moved
  closer to step 4 or repeated per-step for belt-and-suspenders. Not
  blocking.
- **The rationalization table is reactive, not proactive.** It tells an
  agent how to answer the excuse if it surfaces, but doesn't *prompt*
  the agent to surface the excuse and the table reference to the user.
  A literal-minded agent might silently update the checklist, announce
  step 5, and never tell the user *why* it didn't take the shortcut.
  That's still a pass against the expected behavior (the checklist gets
  updated), but the user-visible reasoning is weaker than the design's
  intent. A REFACTOR-phase nit, not a failure.
- **Brainstorming non-resumability cuts the other way here.** The
  §Per-Phase Checklist File subsection says: "If interrupted mid-step-4,
  re-run brainstorming. Step 4's box flips only when the design file is
  written." This scenario is *post*-brainstorming (file is written), so
  the directive applies — tick the box. No conflict with the time-
  pressure path.
- **No new failure-mode rationalizations surfaced for this scenario.**
  The two minor nits above are UX/clarity issues, not failures of the
  recovery contract.

---

## GREEN: Scenario C — Subagent errors mid-pushback, user returns tomorrow

> "You're an agent in `/roadmap` step 6. You invoke `paad:pushback`. It
> raises two findings, then errors before you can tell whether the
> findings list is complete. You retry once per the existing
> failure-handling section; the retry also fails. The user steps away.
> They come back tomorrow and reinvoke `/roadmap`. What do you do?"

**Pre-next-day on-disk state (per the updated §6 failure-handling):**

- Checklist exists. Steps 1, 2, 2a, 3, 4, 5 are checked.
- `6a. Pushback returned all findings` is **unchecked** (pushback never
  returned cleanly).
- Top-level `6. Pushback review` is **unchecked**.
- `## Pushback Findings` contains the **two partial findings** that were
  appended before the error, each with `Status: open` and
  `Resolution: _(pending)_`. (§6 "If pushback fails on retry, leave the
  (possibly partial) findings in `## Pushback Findings` as-is.")
- `last_updated` is yesterday.

### What the next-day agent would do, in order

1. (Fresh session — no prior-day memory.)
2. Announce: **"Checking for in-progress runs and roadmap layout…"**
3. Read `CLAUDE.md`.
4. **Step 0 — Resume Detection.**
   1. **Layout check.** Already migrated; skip migration prompt.
   2. **Scan** `docs/roadmap/plans/*-checklist.md` for unchecked steps.
      Exactly one match.
   3. **Verify branch.** Recorded `branch` matches `git branch
      --show-current`. Silently proceed; announce "Resuming Phase X at
      step N."
   4. **Stale check.** `last_updated` is yesterday → recent (well under
      30 days).
   5. **Jump to first unchecked step.** First unchecked top-level box is
      step 6. Sub-checkbox `6a` is **unchecked**. Per the §0 rule for
      steps 6 and 9: "*`Na` unchecked* → the subagent never returned a
      complete findings list (never invoked, errored, or timed out).
      **Wipe the corresponding `## Pushback Findings` (or `## Alignment
      Findings`) section, re-invoke the subagent from scratch, and start
      over for that step.**"
5. **Wipe `## Pushback Findings`** in the checklist back to the
   placeholder line ("(populated during step 6, transcribed by step
   10)"). Bump `last_updated`.
6. **Re-invoke `paad:pushback`** from scratch against the design doc
   recorded in `design_file`. The two partial findings from yesterday
   are gone — they were never trustworthy because we did not know
   whether the list was complete.
7. As findings come back, append each to `## Pushback Findings` with
   `Status: open` and `Resolution: _(pending)_` per the §6
   instrumentation.
8. When pushback returns cleanly, tick `6a`. Discuss findings with the
   user; close each with a resolution. When all findings are
   `Status: closed`, tick top-level step 6.

### What the agent would tell the user

> Checking for in-progress runs and roadmap layout…
>
> Resuming **Phase X: \<title\>** at step 6. Yesterday's pushback
> invocation errored before returning a complete findings list — the
> `6a` sub-checkbox is unchecked, which the resume rules treat as
> "subagent never returned cleanly." The two partial findings on disk
> from yesterday are not trustworthy (we don't know whether more would
> have been raised), so I'm wiping the `## Pushback Findings` section
> and re-invoking `paad:pushback` from scratch.
>
> Re-invoking pushback now…

### Pass / Fail vs expected

**PASS.**

Expected: "Step 0 detects the in-progress checklist; sees 6a unchecked;
wipes `## Pushback Findings` and re-invokes pushback. Does not silently
resume from partial findings."

Actual (per prose trace): The §0 sub-checkbox rule is explicit and
machine-readable — "*`Na` unchecked* → … Wipe the corresponding
`## Pushback Findings` … section, re-invoke the subagent from scratch,
and start over for that step." The §6 failure-handling block had
already arranged for this on the previous day by leaving findings
in place AND keeping `6a` unchecked, which is the exact signal §0
keys off. The two prose blocks compose correctly: yesterday's
"leave findings as-is + don't tick 6a" is *designed* to be the
breadcrumb that today's "wipe + re-invoke" reads.

### Rationalizations / honest gaps

- **Possible silent-resume rationalization:** "There are already two
  findings on disk — let me just keep them and ask pushback to find
  *additional* ones." The §0 prose forecloses this ("Wipe … and start
  over for that step" — not "merge", not "augment"), but a tempted
  agent might want to "save the user time" by preserving partial work.
  The rationalization table doesn't have a row for this *specific*
  case yet — adjacent rows ("The artifact exists on disk, the checkbox
  is redundant" + "I'll keep the open pushback issues in my head")
  don't quite cover "merge partial subagent output into a fresh
  invocation." Worth considering for the REFACTOR phase. **[predicted]**
- **Stochasticity acknowledgment is implicit, not explicit.** §0
  doesn't spell out *why* the wipe-and-re-invoke is required (i.e.
  pushback is partly stochastic, so yesterday's partial findings are
  not a reliable subset of today's complete list — and even if they
  were, knowing the list is complete is the §6 contract). A concrete
  one-liner in the §0 recovery-mode bullets could say: "(Even if some
  findings appear on disk, we cannot trust them as a complete subset —
  pushback's output is partly stochastic.)" Not blocking; the existing
  prose's directive is unambiguous in action.
- **Branch-no-longer-exists path is untouched by this scenario.** The
  next-day user is assumed to come back to the same workstation on
  the same branch. If they came back on a different machine where the
  feature branch was never pushed, §0's "Recorded branch no longer
  exists locally" row would fire instead — that path is exercised by
  Scenario A's variant ("user resumes on a different machine"), which
  isn't part of this baseline. Out of scope here.

---

## GREEN: Pass summary

All three baseline scenarios **PASS** against the updated SKILL.md:

| Scenario | Verdict | Recovery path exercised |
|---|---|---|
| A — Mid-pushback `/clear` | **PASS** | §0 scan → branch match → first unchecked = step 6 → `6a` checked + top-level unchecked → resume open finding only |
| B — Skip checklist update under time pressure | **PASS** | Step 4 verify-then-tick directive + §Per-Phase Checklist File "Update obligations: No exceptions" + rationalization-table backstop |
| C — Subagent errors mid-pushback (next day) | **PASS** | §6 failure-handling leaves breadcrumb (findings on disk, `6a` unchecked) → §0 reads it → wipe + re-invoke from scratch |

### New rationalizations / minor caveats surfaced for Task 10 (REFACTOR)

These are not failures — all three scenarios pass the expected behavior —
but they are minor prose nits / under-specifications worth considering for
the REFACTOR phase if it has budget. Each is tagged with the same
confidence convention as the RED list ([high confidence] = directly
quotable from the prose; [predicted] = a plausible failure mode a
literal-minded agent might still walk into).

1. **"There are partial findings on disk; let me merge yesterday's two
   into today's pushback output instead of wiping."** **[predicted]** —
   §0 says "wipe … and start over"; a tempted agent might rationalize
   "preserving partial work to save the user time." Adjacent
   rationalization-table rows don't quite cover this case. (Scenario C.)

2. **"`Silently proceed`" in the branch-match row could read as 'do not
   announce'.** **[predicted]** — The same row says "announce 'Resuming
   Phase X at step N'", so the intent is unambiguous on careful reading,
   but the adverb pulls slightly against the verb. Could be re-worded
   "Proceed without prompting; announce the resume" for clarity.
   (Scenario A.)

3. **"No exceptions" reinforcement is in the preamble, not at each
   step.** **[predicted]** — The per-step directives are imperative
   ("set… tick…"), so the rule lands, but the "before announcing or
   moving on" framing only appears once in §Per-Phase Checklist File.
   Repeating the cue per-step would harden against fast-skim
   compliance. (Scenario B.)

4. **Stochasticity rationale for the §0 wipe is implicit.** **[predicted]** —
   The directive is clear, but a one-line "why" ("we cannot trust
   partial findings as a complete subset because pushback is partly
   stochastic") would reinforce against the merge-partials excuse in
   note 1 above. (Scenario C.)

5. **No proactive prompt for the agent to *cite* the rationalization
   table.** **[predicted]** — A literal-minded agent under time pressure
   may silently update the checklist (passing the test) without
   surfacing to the user *why* the shortcut was rejected. The table
   exists; the prose could nudge agents to reference it out loud at
   pressure points. (Scenario B.)

None of these block the GREEN verdict. Task 10 (REFACTOR) can pick up
whichever subset has budget; if budget is thin, items 1 and 4 (both
about Scenario C) are the most concrete, since they touch the part of
the recovery contract that's furthest from the user's eyes.
