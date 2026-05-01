---
name: roadmap
description: Read the feature roadmap, find the next unplanned phase, brainstorm it, and update the roadmap with the resulting document name
---

## Start

Announce: **"Checking roadmap for next unplanned phase…"**

Read @CLAUDE.md.

## 1. Read the Roadmap

Read `docs/roadmap.md` in full. Each phase heading (## Phase N: …) may have a `<!-- plan: filename.md -->` comment on the line immediately after the `---` separator that follows that phase's section. This comment marks the phase as already brainstormed.

Example of a completed phase:

```markdown
---

## Phase 2: Goals & Velocity
<!-- plan: 2026-04-01-goals-velocity-design.md -->
```

Example of an incomplete phase (no comment, or no `<!-- plan: … -->` line):

```markdown
---

## Phase 3: Export
```

## 2. Identify the Next Unplanned Phase

Scan phases in order (Phase 1, 2, 3, … 7). The first phase whose section does **not** have a `<!-- plan: … -->` comment is the target.

If **all** phases have plan comments, announce:
> **All roadmap phases have been brainstormed.** Nothing to do.

…and stop.

## 2a. Suggest a Working Branch (if on `main`)

Run `git branch --show-current` and inspect the result. There are three
cases:

- **Detached HEAD** (output is empty): **stop.** Do not proceed. Tell the
  user the working tree is in detached-HEAD state and any commits this
  skill produces would be reachable only via reflog and pruned by the next
  `git gc`. Ask them to either check out a named branch first or
  explicitly confirm they want to land artifacts on a detached commit.
  Do not silently fall through — empty is "not main", but it is also not
  a safe place to commit.
- **Named branch other than `main`**: skip the rest of this step. The
  working branch is already chosen.
- **`main`**: do not start brainstorming yet. The artifacts produced by
  the rest of this skill (design doc, implementation plan, decision log)
  should land on a feature branch, not on `main`. Continue with the
  pre-check and suggestion below.

### Pre-check the working tree

Before suggesting any branch, run `git status --porcelain`. If the output
is non-empty, `main` has uncommitted changes that would ride to the new
branch. Stop and surface the dirty paths to the user; ask them to commit,
stash, or explicitly confirm the carry-over before continuing. Do **not**
silently `git checkout -b` over a dirty tree.

### Derive a candidate slug

From the target phase heading, take the title text (everything after the
`Phase N:` or `Phase Na:` prefix), then:

1. Lowercase the title.
2. Drop apostrophes (`'`, `'`, `'`) **without** inserting a separator, so
   `Editor's` becomes `editors`, not `editor-s`.
3. If the trailing word is `implementation`, `impl`, or `feature`, drop it —
   it adds nothing to a branch name.
4. Replace any run of non-`[a-z0-9]` characters with a single hyphen.
5. Strip leading and trailing hyphens.
6. If the result is empty (e.g. the title was only `implementation`, or
   only Unicode/CJK characters that collapsed to nothing), fall back to
   `phase-N` using the phase number — including any sub-letter — from
   the heading. `Phase 12: Implementation` → `phase-12`.
   `Phase 3a: 漢字` → `phase-3a`.

Examples:

| Phase heading                                  | Candidate slug         |
|------------------------------------------------|------------------------|
| `Phase 1: Backend Foundation`                  | `backend-foundation`   |
| `Phase 3a: Movie Data Cleaning`                | `movie-data-cleaning`  |
| `Phase 7: User Authentication implementation`  | `user-authentication`  |
| `Phase 9: Editor's Polish`                     | `editors-polish`       |
| `Phase 12: Implementation`                     | `phase-12`             |

The slug is bare — no `feat/`, no `<username>/` prefix. If the user's
convention adds a prefix, let them apply it via the override path below.

### Present the suggestion and wait

Show the user the candidate name and ask them to accept or override:

> Currently on `main`. Before brainstorming, I'd like to create a feature
> branch so the design doc, plan, and decision log land off `main`.
>
> Suggested branch: `<candidate-slug>`. Accept, or give me a different name?

Parse the response per this explicit grammar (matches are case-insensitive;
a trailing `.`, `!`, or `,` is ignored before matching):

- **Accept** — exactly one of: `yes`, `y`, `yeah`, `yep`, `yup`, `ok`,
  `okay`, `sure`, `lgtm`, `looks good`, `go ahead`, `do it`, `proceed`.
  Run `git checkout -b '<candidate-slug>'`. Always pass the branch name
  inside single quotes — never interpolate raw user input into the shell
  command.
- **Stay on `main`** — exactly one of: `stay`, `stay on main`, `no branch`,
  `keep main`, `on main`. Continue on `main`, but warn the user that
  every commit produced by this skill will land directly on `main`.
- **Decline (ambiguous, ask)** — exactly one of: `no`, `nope`, `nah`,
  `n`, `cancel`, `abort`. A bare negative is too ambiguous to interpret
  as either Stay-on-main or as the literal branch name `no`. Ask the
  user to clarify: "Did you mean stay on `main` (no feature branch),
  or cancel the brainstorming run entirely, or use a specific branch
  name? Reply with one of: `stay`, `cancel`, or a branch name." Do
  **not** treat the bare negative as Override — `git checkout -b 'no'`
  is almost certainly not what the user wants.
- **Override** — anything else. Treat the entire response as a candidate
  branch name and run it through the slug rule above (lowercase, collapse
  non-`[a-z0-9]` to hyphens, strip leading/trailing) **before** passing it
  to git. Then run `git checkout -b '<sanitized-name>'` with the
  sanitized result, single-quoted. If the sanitized result is empty, or
  if the response mixes accept tokens with other text in a way that's
  ambiguous (e.g. `yeah call it foo`), ask the user to clarify rather
  than guess.

### Handle `git checkout -b` failure

After running `git checkout -b '<name>'` (Accept or Override path),
check the exit status. The most common failure is the named branch
already exists (`fatal: a branch named '<name>' already exists`).
Other failures: invalid ref (slug rule did not catch a forbidden
character), refusal to create from a detached HEAD without a starting
commit, or a corrupt index.

On any non-zero exit:

- **"already exists"** — surface the exact message and ask: "Branch
  `<name>` already exists. Switch to it (`git checkout '<name>'`),
  choose a different name, or stay on `main`?" Wait for the user's
  decision; do not switch silently — the existing branch may carry
  unrelated WIP that the user does not want to land roadmap artifacts
  on.
- **Any other failure** — surface the full git error and stop. Do not
  fall through to step 3 brainstorming on `main`; that is the very
  thing §2a was designed to prevent.

Only proceed to step 3 after the branch decision is made *and* the
checkout succeeded.

## 3. Extract the Phase Context

Collect the full text of the target phase section from the roadmap (everything between its `## Phase N` heading and the next `## Phase` heading or end of file). This is the spec input for brainstorming.

Also note:
- Which earlier phases it depends on (listed under ### Dependencies).
- The current date (for the plan filename).

## 4. Brainstorm

Invoke the `superpowers:brainstorming` skill. When the brainstorming skill asks what you're building, provide:

- The phase name and goal from the roadmap.
- The full phase section text as context.
- That the output should be a **design document** saved to `docs/plans/`.

Follow the brainstorming skill's process completely. It will explore requirements, ask the user questions, and produce a design document. Also, think of the design from the standpoint of a writer. Is it truly useful for them? If you think it could be more useful, discuss this with the user.

When brainstorming, apply the PR scope rules in CLAUDE.md (§Pull Request Scope) — flag to the user if this phase bundles more than one feature or refactor and should be split before a plan is written.

## 5. Record the Plan Filename

After brainstorming produces a document in `docs/plans/`, update `docs/roadmap.md` in **two places**:

### 5a. Insert the plan comment

Insert a plan comment on the line immediately after the `---` separator that precedes the phase heading:

**Before:**
```markdown
---

## Phase 3a: Export Foundation
```

**After:**
```markdown
---

## Phase 3a: Export Foundation
<!-- plan: 2026-04-01-export-foundation-design.md -->
```

The filename is whatever the brainstorming skill created (it follows the pattern `YYYY-MM-DD-<topic>-design.md`).

### 5b. Update the Phase Structure table statuses

In the **Phase Structure** table near the top of the roadmap, make two updates:

1. **Mark the current phase as "In Progress"** — change its status from `Planned` to `In Progress`.
2. **Mark the previous phase as "Done"** — if the phase immediately before the current one has status `In Progress`, change it to `Done` (it must have been completed if we're moving on to brainstorm the next phase).

The valid statuses are:

- **Planned** — not yet started
- **In Progress** — brainstorming or implementation underway
- **Done** — shipped and merged to main

## 6. Pushback Review

Invoke the `paad:pushback` skill against the design document just created in `docs/plans/`. If English is the new programming language, pushback is code review for the plan — catch contradictions, feasibility issues, scope problems, and ambiguity before any implementation begins.

After pushback completes, discuss the findings with the user and update the design document to address any valid concerns before moving on.

**Instrumentation for the decision log.** While the pushback discussion happens, mentally track each issue presented so you can write it to the decision log in step 10:

- Title (one line, taken from how pushback presented the issue)
- Severity (Critical / Important / Minor — pushback assigns these)
- Category (Contradiction / Feasibility / Scope / Omission / Ambiguity / Security / Other — taken from which check fired)
- One-paragraph summary in your own words
- Resolution after discussion with the user — exactly one of: `fixed-in-design`, `fixed-in-plan`, `dismissed-invalid`, `dismissed-out-of-scope`, `accepted-as-is`, `deferred`
- One-sentence resolution detail (what was changed, or why it was dismissed)

If pushback raises zero issues, record that — a clean pushback is itself evidence.

**Failure handling.** If the `paad:pushback` invocation itself errors,
times out, or returns malformed output (anything that is not a usable
pushback report), retry **once**. If the retry also fails, **stop**
and surface the failure to the user — name the failure mode and the
last output (or error text). Do **not** record "no issues" or "clean
pushback" in the decision log: that wording is reserved for runs
where the skill returned successfully with zero findings. The
decision log's purpose is evidence; a failed pushback recorded as a
clean pushback corrupts the evidence trail.

## 7. CLAUDE.md Review

Before announcing completion, evaluate whether `CLAUDE.md` needs updating to reflect this phase.

Re-read `CLAUDE.md` with the final design in mind and check each section for drift:

- **§Key Architecture Decisions** — does the phase introduce a new invariant, source-of-truth rule, or cross-cutting pattern that belongs here? (e.g. a new helper that codifies existing invariants should be referenced so future developers route through it.)
- **§API Design** — new endpoints, new error codes, or a new shape for an error envelope?
- **§Data Model** — new tables, new columns, or a change to soft-delete/UUID conventions?
- **§Testing Philosophy** — a new test layer, fixture convention, or coverage requirement?
- **§Target Project Structure** — a new top-level folder or package?
- **§Accessibility / §Visual Design** — a new a11y primitive or visual token worth documenting at the root level?
- **§Pull Request Scope** — does the phase reveal a new PR-scope hazard worth codifying?

If any section needs updating, discuss the proposed change with the user and fold the `CLAUDE.md` edit into the design document as an explicit deliverable of the phase (a task in the plan, not an afterthought). If no section needs updating, state that explicitly so the check is visible.

## 8. Write the Implementation Plan

Invoke the `superpowers:writing-plans` skill against the finalized design document. The writing-plans skill will produce a bite-sized TDD task list that turns the design into concrete, reviewable commits.

When invoking writing-plans, provide:

- The path to the finalized design document from step 4.
- The constraints captured during steps 6 and 7 (pushback findings, any CLAUDE.md edits that must land as part of the phase).
- Repository-specific constraints from `CLAUDE.md` (§Testing Philosophy coverage floors, §Pull Request Scope one-refactor / one-feature rule, zero-warnings rule).
- That the plan should be saved alongside the design in `docs/plans/` with filename pattern `YYYY-MM-DD-<topic>-plan.md`.

The plan must honor the PR scope rules: a single roadmap phase is a single PR. If the plan would naturally span multiple PRs (for example, a refactor followed by a feature), split at the phase boundary in the roadmap first and re-run this skill against each sub-phase.

## 9. Alignment Check

Invoke the `paad:alignment` skill against the implementation plan just produced. Alignment catches coverage gaps, scope creep, and design-vs-plan mismatches — it verifies that every requirement in the design is traced to at least one task, every task maps back to a requirement, and every task is expressed in TDD red/green/refactor format.

Pass the alignment skill both documents:

- The design document from step 4 (the source of truth for requirements).
- The implementation plan from step 8 (the breakdown being aligned).

After alignment completes, discuss any findings with the user and update the plan (and occasionally the design) to close the gaps. Do not proceed to announcement until the plan and design are aligned, or the user explicitly accepts any remaining gaps.

**Instrumentation for the decision log.** Same as step 6: mentally track each alignment issue (title, severity, category, one-paragraph summary, resolution from the closed vocabulary, one-sentence resolution detail). Alignment categories are: `missing-coverage`, `out-of-scope`, `design-gap`, `tdd-format`. If alignment raises zero issues, record that.

**Failure handling.** Same as step 6: if `paad:alignment` errors,
times out, or returns malformed output, retry **once**, then stop and
surface to the user. Do **not** record "no issues" or "clean
alignment" in the decision log unless the skill returned successfully
with zero findings.

## 10. Write the Decision Log Entry

Write a single Markdown file to `docs/roadmap-decisions/YYYY-MM-DD-<phase-slug>.md` capturing this run.

**Filename slug rule:** lowercase the phase heading, drop apostrophes (no separator inserted), replace any run of non-`[a-z0-9]` characters with a single hyphen, strip leading/trailing hyphens, and fall back to `phase-N` (using the phase number, including any sub-letter, from the heading) if the result would otherwise be empty. `Phase 7: Editor's Polish & Polish` → `phase-7-editors-polish-polish`. Combine with today's date in `YYYY-MM-DD` form.

**Model field:** read from your own system context (the system prompt always identifies the model you are running on, e.g., `claude-opus-4-7`). Use the bare model ID, no version suffixes.

Follow the schema in §Appendix: Decision Log Entry Schema (at the bottom of this skill) exactly — YAML frontmatter, then the body sections.

Then update `docs/roadmap-decisions/INDEX.md` by **prepending** one row to the `## Entries` table (newest entry on top). The row contains: date, phase title, model, pushback C/I/M counts, alignment C/I/M counts, and a relative link to the entry file just written.

If a /roadmap run produced zero pushback issues *and* zero alignment issues, still write the entry and the index row — a clean run is evidence too.

## 11. Announce Completion

> **Roadmap updated.** Phase N: [Name] brainstormed and planned.
> - Design: `docs/plans/<filename>-design.md`
> - Plan: `docs/plans/<filename>-plan.md`
> - Decision log: `docs/roadmap-decisions/<filename>.md`
> Next unplanned phase: Phase M: [Name] (or "all phases planned").

Offer to move to implementing the plan (via `superpowers:subagent-driven-development` or `superpowers:executing-plans` in a separate session), or to review the updated roadmap.

## Appendix: Decision Log Entry Schema

The decision log captures, for every /roadmap run, what `paad:pushback` and `paad:alignment` caught and how each finding was resolved. Each entry is one Markdown file with YAML frontmatter and a structured body. The purpose is evidence — a body of receipts that the upstream skills (brainstorming, writing-plans) miss real things even when run by the most capable model.

### File location

- Entries: `docs/roadmap-decisions/YYYY-MM-DD-<phase-slug>.md` (one per /roadmap run)
- Index: `docs/roadmap-decisions/INDEX.md` (one row per entry, newest on top)

If a phase is brainstormed more than once on different days, each run produces its own dated entry — the history is preserved.

### Frontmatter

```yaml
---
date: 2026-04-26
phase: "Phase 3a: Export Foundation"
model: claude-opus-4-7
design_file: docs/plans/2026-04-26-export-foundation-design.md
plan_file: docs/plans/2026-04-26-export-foundation-plan.md
pushback:
  total: 5
  critical: 1
  important: 2
  minor: 2
alignment:
  total: 3
  critical: 0
  important: 1
  minor: 2
---
```

All fields are required. Severity counts under `pushback` and `alignment` must sum to `total`. For a clean run with no findings, set `total: 0` and omit the severity fields.

**If the per-issue tracking from steps 6 or 9 produces severity
counts that do not sum to `total`** (e.g. an issue was downgraded
mid-discussion and the running tally was not updated), **stop** and
reconcile with the user before writing the entry. Do **not** adjust
counts to satisfy the invariant; the invariant is an integrity check,
not a target. Common causes: a finding presented as Important got
re-categorized as Minor during discussion (decrement Important,
increment Minor); a finding was dismissed as a duplicate of another
already-counted item (decrement the original tier, do not add); the
user split one finding into two (increment the relevant tier). In
each case the reconciliation has to be explicit — silently padding
counts to make `total` match would hide the original transition and
corrupt the year-of-entries view that the index supports.

### Body sections

```markdown
# <Phase title> — Decision Log

## Pushback Findings

### [N] <issue title>
- **Severity:** Critical | Important | Minor
- **Category:** Contradiction | Feasibility | Scope | Omission | Ambiguity | Security | Other
- **Summary:** <one paragraph in your own words>
- **Resolution:** <one of the resolution values below> — <one sentence: what was changed, or why it was dismissed>

(Repeat per issue. If pushback raised no issues, replace this whole section with the single line: "Pushback raised no issues.")

## Alignment Findings

### [N] <issue title>
- **Severity:** Critical | Important | Minor
- **Category:** missing-coverage | out-of-scope | design-gap | tdd-format
- **Summary:** <one paragraph in your own words>
- **Resolution:** <one of the resolution values below> — <one sentence: what was changed, or why it was dismissed>

(Repeat per issue. If alignment raised no issues, replace this whole section with the single line: "Alignment raised no issues.")

## Summary

- Pushback raised N issues; M resulted in design changes, K dismissed as invalid, ... .
- Alignment raised N issues; M resulted in plan changes, ... .
```

### Resolution vocabulary (closed set)

- `fixed-in-design` — the design document was edited to address the issue
- `fixed-in-plan` — the implementation plan was edited to address the issue
- `dismissed-invalid` — the user disagreed; the issue was a false positive
- `dismissed-out-of-scope` — valid concern but explicitly deferred to a future phase
- `accepted-as-is` — valid concern, no change needed (e.g., known limitation that does not need addressing)
- `deferred` — valid concern that needs work but cannot be addressed in this run

### INDEX.md format

```markdown
# Roadmap Decision Log Index

This index lists every /roadmap run in reverse chronological order. Each entry
captures issues found by /pushback (after the design) and /alignment (after the
plan), along with how each was resolved.

## Entries

| Date       | Phase                          | Model              | Pushback (C/I/M) | Alignment (C/I/M) | Entry |
|------------|--------------------------------|--------------------|------------------|-------------------|-------|
| 2026-04-26 | Phase 3a: Export Foundation    | claude-opus-4-7    | 1/2/2            | 0/1/2             | [link](2026-04-26-phase-3a-export-foundation.md) |
```

Prepend new rows to the table so the newest entry is always at the top.

### Slug rule

Lowercase the phase heading, drop apostrophes (`'`, `'`, `'`) without inserting a separator, replace any run of non-`[a-z0-9]` characters with a single hyphen, strip leading and trailing hyphens, and fall back to `phase-N` (using the phase number — including any sub-letter — from the heading) if the result would otherwise be empty. Examples:

- `Phase 3a: Export Foundation` → `phase-3a-export-foundation`
- `Phase 7: Editor's Polish & Polish` → `phase-7-editors-polish-polish`
- `Phase 12: Implementation` → `phase-12-implementation` (filename slug keeps the `implementation` suffix; only the §2a branch slug drops it)

### Why this schema

The single `model` field assumes one model per /roadmap run (true ~99% of the time). Per-issue resolution tracking is what makes this evidence rather than a list of complaints — "pushback caught N important issues, M of which became design changes" is a much stronger argument than "pushback raised N things." Severity counts in the index let a year of entries be skimmed at a glance for patterns. Closed-set vocabularies (categories, resolutions) keep entries comparable across runs and trivially aggregatable by future tooling.

