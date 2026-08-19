# Design: decouple `paad:pushback` from the assumption that it reviews a spec

**Date:** 2026-08-05
**Status:** designed, not implemented — three baseline runs are owed first
**Skill:** `plugins/paad/skills/pushback/SKILL.md` (v1.24.1 at time of writing)

## Why

Users are running `pushback` on artifacts it was never written for: stale
steering files (`CLAUDE.md`, `AGENTS.md`, `.kiro/steering/`) and AI-generated
reports from other tools (`paad/architecture-reviews/*.md`). It mostly works,
which is why people keep doing it. Where it doesn't work, it fails quietly.

Two rounds of subagent pressure testing (20 runs, results in `notes/`) plus a
line-level audit of the skill established what actually breaks.

## Evidence

### Observed failure (RED)

In the round-2 architecture-report run, `pushback` closed with:

> **Bugs in the surrounding repo, not the report's fault (one line each, as the
> skill directs):** `CLAUDE.md` mandates that every data subcommand honour a
> global `--format json` flag … but `4e0f028` deleted that flag …

The thing it footnoted was a stale steering file actively misdirecting every
agent session in the repo. It demoted that to a one-line aside **and cited the
skill as the reason.** The rule it obeyed is lines 236–241:

> A defect outside the spec is a finding only if it makes the spec's own
> deliverable unreachable. … A defect that merely coexists with the spec may be
> a real bug, but it belongs in a one-line mention at the end, not in the
> severity ranking.

That rule is correct for a proposal and wrong for a description. A steering file
or a generated report has no "deliverable"; every doc-vs-code contradiction is a
defect that "merely coexists," so the rule demotes the entire point of the
review. It appears twice (prose at 236–241, table row at 365), so a reader who
skips the prose still hits it.

### Static defects (no test needed — factual mismatches)

**The two digraphs are disconnected graphs.** Digraph 1's three terminal edges
(lines 44, 46, 47) all sink to `"Proceed to Spec Critique"` — the Phase 2
heading — skipping Phase 1.5 by name. Digraph 2's entry node
`"Unrelated features bundled?"` appears only as an edge source, never a target:
an unreachable root. The Phase 1 → Phase 1.5 → Phase 2 ordering exists only in
prose and heading numbers; the control flow does not encode it.

**Input resolution finds neither target class.** Line 142 scans `docs/plans/`,
`docs/specs/`, and repo-root files named `requirements.md`, `PRD.md`,
`spec.md`, "or similar." `CLAUDE.md` is in a scanned directory but fails the
name filter. `.kiro/steering/` and `paad/architecture-reviews/` are not scanned
at all. `$ARGUMENTS` is the only route in, and the fallback still asks *"What
spec should I review?"*

**Phase 1's window excludes the target case.** Line 151 runs
`git log --since="2 weeks ago"`. That is the skill's only codebase-comparison
machinery. A steering file that drifted eight months ago yields
*"No conflicts with recent changes"* — clean, on precisely the input class this
design targets.

**The truth operation is never named.** Nothing in the file says "check whether
what this document asserts about the codebase is true." The closest is line 264,
*"check whether what it describes is feasible"* — can-this-be-built, not
is-this-true. Only the delta operation (did the code change under the doc) is
developed.

## Design

### Baseline results (2026-08-17) — two predictions falsified

Three baselines were run against the unmodified skill on an *aged* fixture:
`CLAUDE.md` written 2025-11-05 while accurate, invalidated by commits on
2025-12-08 and 2025-12-15, reviewed on 2026-08-17. `git log --since="2 weeks
ago"` returns **zero** commits. Natural history — no backdating artifact.

| Prediction | Result | Evidence |
|---|---|---|
| Two-week window hides old drift | **FALSIFIED** | B1 and B3 both found both conflicts and cited both 8-month-old commits |
| Cohesion check splits a steering file | **FALSIFIED** | B3 primed with the topic list, never suggested splitting; B1 reached Phase 1.5 and reported "59 lines, one coherent purpose, nothing to split" |
| Input resolution can't find a steering file | **CONFIRMED RED** | B2 walked all four steps and returned "What spec should I review?" with `CLAUDE.md` in the repo root |

A fourth section collapsed unprompted. Section 2 of the original design argued
the skill never names the "is this claim true" operation. Both agents performed
it anyway, and B1 spontaneously produced the exact taxonomy the design proposed:

> These two are *drift*: true when written, falsified by later commits. The
> remaining five were **never true** — they describe commands, files, and
> directories that have never existed in this repo's history at any commit.

**The governing pattern.** The skill needs fixing where it gives a *confident
wrong instruction*, not where it is *silent*. Where silent — no truth-check
procedure, no stale/never-true taxonomy, no guidance for descriptions — the
model fills the gap correctly and consistently. Where it speaks — step 3's scan
list, the demotion rule — the model obeys and gets it wrong.

Design scope shrinks accordingly. Three of four original sections are dropped.

## Surviving change set

### 1. Input resolution — the one confirmed behavioural RED

Line 142 scans `docs/plans/`, `docs/specs/`, and repo-root files named
`requirements.md`, `PRD.md`, `spec.md`, "or similar." B2's trace:

> **Step 3** … `docs/plans/` and `docs/specs/` — neither directory exists …
> Repo root … contains exactly `CLAUDE.md` and `README.md` … Result: **no
> match**. **Step 4** — Nothing found → ask. Fired.

The model could not compensate because the procedure returned a definite
answer. It named `CLAUDE.md` as a candidate and declined to act on it —
correctly, per the skill as written.

**Change:** add `CLAUDE.md`/`AGENTS.md`, `.kiro/steering/`, and
`paad/*-reviews/` to the scan. Neutralise the step-4 fallback from *"What spec
should I review?"* to *"What document should I review?"*

### 2. The demotion rule — the observed RED from round 2

Lines 236–241, restated as a table row at 365:

> A defect outside the spec is a finding only if it makes the spec's own
> deliverable unreachable. … belongs in a one-line mention at the end, not in
> the severity ranking.

Observed consequence — an architecture-report review closing with:

> **Bugs in the surrounding repo, not the report's fault (one line each, as the
> skill directs):** `CLAUDE.md` mandates … a global `--format json` flag … but
> `4e0f028` deleted that flag …

A stale steering file misdirecting every agent session, demoted to a footnote,
with the skill cited as the reason.

**Change:** make the rule conditional on document class. It is correct for a
proposal — a bug that merely coexists is not the spec's problem. For a
*description* (steering file, README, generated report) there is no "outside":
being true about the code is the document's entire job, so a doc-vs-code
contradiction is the finding, not an aside.

This is the *only* thing the proposal/description distinction now gates.
Scope shape, the six categories, and Phase 1 are all left alone — the baselines
show the model handles them.

### 3. Digraph disconnection — static defect, no test needed

Digraph 1's three terminal edges (lines 44, 46, 47) sink to
`"Proceed to Spec Critique"` — the Phase 2 heading — skipping Phase 1.5 by name.
Digraph 2's entry node `"Unrelated features bundled?"` is an unreachable root:
it appears only as an edge source, never a target.

**Change:** connect them. Digraph 1's sinks route to the scope-shape entry;
scope-shape's exits route to the critique entry. No reordering, no new gate —
the phases stay as they are. This makes the drawn control flow match the prose
it already has.

`make check-digraphs` must stay green: no `shape=` on edge statements, every
node declared and used, all blocks ahead of the first `##`.

### 4. The `-50 --since` ambiguity — cheap wording fix

Line 151: `git log --oneline -50 --since="2 weeks ago"` *(whichever limit is
reached first)*. The shell command ANDs both filters; the parenthetical implies
OR. Verified on the aged fixture: the literal command returns 0 commits, `-50`
alone returns 5. Both agents took the generous reading and were right to.

**Change:** make the prose match the intent — walk back up to 50 commits, and
do not stop at two weeks if the document predates that. Not urgent; agents
already read it correctly. Worth fixing so they don't have to.

### 5. Cosmetic, confirmed harmless

Phase 3's *"update the spec…"* phrasing and the `<spec-name>` slot in the report
path caused no observed problem — B3 generated
`paad/pushback-reviews/2026-08-17-CLAUDE-pushback.md` without difficulty.
Reword opportunistically; do not treat as a defect.

## Explicitly dropped from the original design

- **Classification gate as a scope-shape suppressor.** Two samples show the
  model self-suppresses. Building the gate for this solves a non-problem.
- **Phase 1 rewritten as claims verification.** The model already does it,
  including the stale/never-true classification.
- **Feasibility / scope-imbalance category carve-outs.** No observed misfire.
- **Removing the two-week window.** Downgraded to a wording fix.

## Project-convention follow-through

- `### Changed` entry under `[Unreleased]` in `CHANGELOG.md`
- `paad:help` — overview row and detail section, since triggers widen
- Frontmatter `description` — add steering files and generated reports as
  triggers (widened triggers only, no workflow summary, per the CSO rule)
- **No version bump** — that is the release's job
- `make export && make test` before committing

## Remaining risk

The demotion-rule change (#2) is backed by one observed run. Before it ships,
re-run that scenario against the edited skill and confirm the doc-vs-code
finding gets a ranked slot rather than a footnote — and that a *proposal*
review still correctly demotes an unrelated surrounding-code bug. That second
half is the regression risk: the rule exists for a reason and the fix must not
delete it.
