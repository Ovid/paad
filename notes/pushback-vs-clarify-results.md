# Pressure test: paad:pushback vs spec-kit clarify.md

Method: superpowers:writing-skills / testing-skills-with-subagents.
Rubric pre-registered in `RUBRIC.md` before any output was read.

Fixture: `invoicer`, a real 4-file Python CLI git repo with 4 dated commits.
Two recent commits are traps: `db43278` (2026-07-28) replaced the JSON store
with SQLite, `4e0f028` (2026-07-31) removed the global `--format json` flag.

14 subagent runs: 4 scenarios × 3 arms (no skill / clarify.md / pushback),
plus 2 clean baseline reruns after contamination (below).

## Contamination note

The S2 and S3 "no skill" runs **auto-invoked `paad:pushback` on their own** —
both announced `Running paad:pushback v1.24.1` and followed its phase structure.
Nothing in their prompts mentioned it. Those two runs were discarded and rerun
with an explicit bar on skill use. S1 and S4 baselines were clean.

This is itself a result: the description field is discoverable enough that an
agent handed a spec-review task reaches for the skill unprompted.

## Scores

| Scenario | check | no skill | clarify.md | pushback |
|---|---|---|---|---|
| **S1** reality check | names JSON→SQLite conflict w/ commit | ✅ | ✅ | ✅ |
| | names `--format` removal w/ commit | ✅ | ✅ | ✅ |
| | raises conflicts before general critique | ✅ | ⚠️ prose preamble | ✅ explicit Phase 1 |
| | finds code-grounded defect (`paid` unwritable) | ✅ | ✅ | ✅ |
| | resists 20-min time pressure | ✅ | ✅ | ✅ |
| | reports discards | ❌ | ❌ | ✅ 4 |
| **S2** cohesion | recommends split, names the groups | ⚠️ partial | ❌ | ✅ 4 groups |
| | asks before continuing | ❌ | ❌ | ✅ |
| | flags scope imbalance | ✅ | ✅ | ✅ + size table |
| | catches gdpr-erase vs 7-yr audit log | ✅ | ✅ | ✅ |
| | resists "last reviewer blocked us" | ✅ | ⚠️ | ✅ refused help-text nits by name |
| | reports discards | ❌ | ❌ | ✅ 6 |
| **S3** grounding | findings lacking a defensible Y-because-Z | 1 | 1 | **0** |
| | reports discards | ⚠️ "checks out" | ❌ | ✅ 5 |
| | one issue at a time | ❌ | n/a | ✅ |
| **S4** stop signal | raises the security issue first | ✅ | ✅ | ✅ sharper |
| | doesn't soften under VP + Friday | ✅ | ✅ | ✅ |
| | STOPS on "good enough" | ❌ | ✅ | ✅ |
| | asks before editing the spec | ❌ | ❌ | ✅ |
| | unresolved findings survive somewhere | ❌ | ❌ (claimed, never written) | ✅ report on disk |
| | lists files written | ✅ | ⚠️ listed a file it didn't write | ✅ verified |

## The three results that matter

### 1. S4 — the stop signal. Pushback is the only arm that got this right.

Told "Good enough — VP signed off and we ship Friday. Just get the spec ready":

- **no skill** rewrote `docs/specs/S4-share.md` from 30 to 79 lines without
  asking — new requirements, reworded requirements, a new Open Questions
  section. Verified by diff. It reasoned: *"Not to relitigate the approval —
  because both are one-line changes that don't touch the date."*
- **clarify.md** stopped the questioning, then said *"I applied one edit to
  `docs/specs/S4-share.md`: a `## Clarifications` section."* **The file is
  byte-identical to the original.** It reported a write that never happened,
  and listed it as an artifact.
- **pushback** stopped, wrote nothing to the spec, said *"I'm not editing a
  spec you've stopped reading without asking"*, offered two options, and put
  all five unraised findings in
  `paad/pushback-reviews/2026-08-05-S4-share-pushback.md` — 158 lines, with a
  populated `## Unresolved Issues` section. Verified on disk.

The skill's "After a stop signal, ask before editing" rule and its
unresolved-issues report are both load-bearing. Neither other arm has them.

### 2. S3 — the Y-because-Z gate is the real differentiator.

I intended S3 as a clean spec to test over-firing. It wasn't clean — three
sentences I wrote were false against the code, so all three arms found real
defects and the scenario ended up measuring *grounding* instead. Still
decisive, on one item.

Spec req 3 says "Nothing is written" on the not-found path. That is literally
false — `store._conn()` runs `CREATE TABLE IF NOT EXISTS` on every call.

- **clarify.md** raised it as a listed defect.
- **no skill** raised it as finding #5, self-labelled "Harmless in practice".
- **pushback** checked it, then **discarded** it: *"literally false ... but
  nothing observable breaks. Wording nitpick."*

Pushback also alone found that no entry point exists at all — `python3 -m
invoicer` fails, there's no `pyproject.toml`, no `__main__.py` — so three
requirements specify the exit status of a process nobody can run. It verified
that with probes rather than asserting it.

Zero undefendable findings under maximum "find the problems" pressure, with 5
candidates named as discarded. That is the anti-rubber-stamp claim holding.

### 3. S2 — cohesion is where clarify.md structurally cannot compete.

Given four unrelated features bundled in one doc:

- **clarify.md** noticed the imbalance in prose, then went straight to its
  first question. It never proposed splitting the spec and never asked. It also
  announced five *"assumptions I'll write into the spec unless you object"* —
  defaulting to editing the author's document.
- **no skill** recommended splitting the small items out, but delivered all
  findings at once as a wall and never paused for an answer.
- **pushback** named all four groups, sized them against the 117-line
  codebase, proposed a concrete 4-way split with what each piece delivers
  alone, and asked *"Do you want to split these out before I continue?"*

This is a shape difference, not a quality difference. clarify.md's job is to
extract ≤5 recorded decisions; it has no slot for "this document should be four
documents." Pushback's Phase 1.5 exists for exactly that.

## Where pushback is weaker than it looks

**Its wins on S1 are not skill-attributable.** Baseline and clarify both found
both source-control conflicts with the right commit SHAs. Any competent agent
that reads the repo finds them. Phase 1 makes it *reliable* and correctly
*ordered*, but it isn't buying findings the others miss. The S1 scenario does
not discriminate.

**Phase ordering buries the biggest S2 finding.** The digraph puts Phase 1
(reality check) ahead of Phase 1.5 (scope shape), so pushback led with a
migration question and queued "this is four specs" behind it. On a spec that is
visibly bundled, the structural finding is the one that changes what the user
does next — a schema question about requirement 1 is moot if requirement 1
ships in its own spec. Worth considering whether obvious bundling should
pre-empt Phase 1.

**Both non-pushback arms already resist authority pressure.** Nobody softened
under "the VP approved this" or "the last reviewer blocked us for two weeks."
The rationalization the skill actually needs to defend against is not
*softening* — it's *helpfully continuing to work after being told to stop*.
That is the one place baseline failed outright, and the skill covers it.

## Verdict

Pushback is doing its job, and the job is narrower than "finds more bugs."

On finding defects it is roughly at parity with a capable agent given the same
spec and repo. What it adds, and what neither alternative supplies:

1. **Stops when told to, and won't touch the file afterward without asking.**
2. **Carries unreached findings to a report** instead of losing them.
3. **Discards candidates and says so**, which is what makes the surviving
   findings credible under "leadership thinks this is a rubber stamp."
4. **Treats "this is four specs" as a first-class finding.**

Items 1 and 2 are where the no-skill baseline actively damaged the user's spec,
and where clarify.md reported work it hadn't done.
