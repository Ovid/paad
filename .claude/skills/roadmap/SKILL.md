---
name: roadmap
description: Read the feature roadmap, find the next unplanned phase, brainstorm it, and update the roadmap with the resulting document name
---

## Start

Announce: **"Checking for in-progress runs and roadmap layout…"**

Read @CLAUDE.md.

## Per-Phase Checklist File

One checklist per `/roadmap` run, created right after step 2a (branch checkout succeeded), updated at the end of every subsequent step. The checklist lives at `docs/roadmap/plans/YYYY-MM-DD-<topic>-checklist.md` — alongside the design and plan files for the same run.

### Filename

`YYYY-MM-DD-<phase-slug>-checklist.md`, where `<phase-slug>` is the **phase filename slug** (defined immediately below), and `YYYY-MM-DD` is the day step 0 → step 1 fires (start date) — so the design / plan / checklist for one run sit alphabetically adjacent in `plans/`.

#### Phase filename slug

A single rule, used by checklist filenames here and referenced from §2a and §Appendix:

1. Take the phase title text (everything after the `Phase N:` or `Phase Na:` prefix in the roadmap heading).
2. Lowercase.
3. Drop apostrophes (`'`, `'`, `'`) **without** inserting a separator (so `Editor's` becomes `editors`, not `editor-s`).
4. Replace any run of non-`[a-z0-9]` characters with a single hyphen.
5. Strip leading and trailing hyphens.
6. If the result is empty (e.g. the title was only Unicode/CJK characters that collapsed to nothing), fall back to `phase-N` using the phase number — including any sub-letter — from the heading. `Phase 3a: 漢字` → `phase-3a`.

Examples:

| Phase heading                                  | Phase filename slug                  |
|------------------------------------------------|--------------------------------------|
| `Phase 1: Backend Foundation`                  | `backend-foundation`                 |
| `Phase 3a: Movie Data Cleaning`                | `movie-data-cleaning`                |
| `Phase 7: User Authentication implementation`  | `user-authentication-implementation` |
| `Phase 9: Editor's Polish`                     | `editors-polish`                     |
| `Phase 12: Implementation`                     | `implementation`                     |

**This rule does NOT drop the trailing `implementation`/`impl`/`feature` word.** The §2a branch slug is this same rule with one extra step (drop that trailing word) — branch names benefit from terseness; filenames benefit from accuracy. The decision-log filename slug (§Appendix) is also separate (heading-based with phase-N prefix for year-at-a-glance browsability); see §Appendix Slug rule.

The `phase_slug` frontmatter field on the checklist is the phase filename slug verbatim — it is the linkable name future tooling can use to correlate the checklist with its sibling design / plan files in `plans/`.

### Schema

```markdown
---
phase: 'Phase 2: agentic-architecture references conversion'
phase_slug: agentic-architecture-references
branch: ovid/agentic-architecture-refs
roadmap: docs/roadmap/roadmap.md
started: 2026-05-02
last_updated: 2026-05-02
design_file: docs/roadmap/plans/2026-05-02-agentic-architecture-references-design.md
plan_file: null
decision_log: null
---

# Phase 2: agentic-architecture references conversion — Run Checklist

## Steps
- [x] 1. Read roadmap
- [x] 2. Identified next unplanned phase
- [x] 2a. Working branch created: `ovid/agentic-architecture-refs`
- [x] 3. Extract phase context
- [x] 4. Brainstorm → design saved
- [ ] 5. Record plan filename in roadmap
- [ ] 6. Pushback review
  - [ ] 6a. Pushback returned all findings
- [ ] 7. CLAUDE.md review
- [ ] 8. Write implementation plan
- [ ] 9. Alignment check
  - [ ] 9a. Alignment returned all findings
- [ ] 10. Write decision log entry
- [ ] 11. Announce completion

## Pushback Findings
(populated during step 6, transcribed by step 10)

### [1] Lens 3 spec contradicts §Key Architecture Decisions
- **Severity:** Critical
- **Category:** Contradiction
- **Summary:** The Lens 3 spec requires X, but §Key Architecture Decisions in CLAUDE.md mandates Y for cross-cutting consistency. The two cannot both hold; one must yield.
- **Status:** open
- **Resolution:** _(pending)_

### [2] Phase scope bundles refactor + new feature
- **Severity:** Important
- **Category:** Scope
- **Summary:** This phase combines the references-package extraction (refactor) with new lens content (feature), violating the one-refactor-OR-one-feature PR rule from CLAUDE.md.
- **Status:** closed
- **Resolution:** fixed-in-design — split into 2a (refactor) + 2b (feature)

## Alignment Findings
(populated during step 9, transcribed by step 10)
```

### Field rules

- `branch` is the working branch name from §2a; resume verifies it matches the current branch.
- `design_file`, `plan_file`, `decision_log` go from `null` to a path the moment each artifact is written.
- `last_updated` is bumped on every write (lets stale-checklist detection work without filesystem mtime).
- **Summary** is a one-paragraph description of the finding, written by pushback (or alignment) at the moment the issue is first raised — while the context is still in head. It is *not* generated at transcription time. This is the only field step 10 carries forward as written prose, so writing it now (not later) is what eliminates the "mentally tracked" failure mode the design exists to fix.
- **Status vocabulary** (closed set): `open | closed`. While `open`, the finding is still being discussed. When `closed`, the `Resolution:` line uses one of the existing decision-log resolution values verbatim: `fixed-in-design`, `fixed-in-plan`, `dismissed-invalid`, `dismissed-out-of-scope`, `accepted-as-is`, `deferred`. Status itself has no decision-log analog (every entry there is closed by definition); step 10's transcription drops the `Status:` line and is otherwise a literal copy.
- **Severity / Category** vocabularies are the existing ones from the pushback and alignment sections of the current SKILL.md.
- **Sub-checkboxes for steps 6 and 9.** Each has a `Na` sub-checkbox (`6a. Pushback returned all findings`, `9a. Alignment returned all findings`) flipped only when the corresponding subagent returns cleanly. The top-level `- [x] N` is checked when **both** Na is checked AND no `Status: open` entries remain in the corresponding findings section. The "no open findings" half is a derived condition computed from the file, not a separate checkbox.
- **`phase` field YAML escaping.** Use **single-quoted** YAML scalars: `phase: '<heading>'`. Embedded apostrophes are doubled (`Editor's` → `Editor''s`). Reject literal newlines — if the H2 heading wraps to multiple lines (it shouldn't), take the first line only. No other escaping is required. Why single-quoted: a phase title is contributor-controlled and can contain `"` or `\`; double-quoted YAML would treat both specially, and a crafted title (e.g., one ending with `"` followed by a newline and `design_file: /etc/passwd`) could inject a sibling frontmatter key. Single-quoted scalars require only the `''` doubling, which is harder to weaponize and trivial to apply correctly.

### Update obligations

Every step ends with "update the checklist (frontmatter `last_updated` + the relevant box + any frontmatter path field) before announcing or moving on." No exceptions.

### Rationalization table

| Excuse | Reality |
|---|---|
| "This step is obvious, I'll skip the box" | Resume detection scans boxes, not artifacts. The box is the source of truth. |
| "I'll batch the checklist updates at the end" | A `/clear` between now and the end loses the run. Update before moving on. |
| "I'll keep the open pushback issues in my head" | The next session won't have a head. The checklist *is* the memory. |
| "The artifact exists on disk, the checkbox is redundant" | Both must agree; mismatch means the run is in an unknown state. |
| "Branch mismatch is fine, I know what I'm doing" | The recorded branch is the safety net. Update or override explicitly — never ignore. |
| "There are partial findings on disk — let me merge yesterday's into today's pushback output instead of wiping." | Pushback is partly stochastic — yesterday's findings are not a guaranteed subset of today's. Merging silently corrupts the evidence trail. §0's wipe-and-re-invoke is the only safe recovery when 6a is unchecked. |

### Verification before ticking

Marking step 4 done requires `design_file` to exist at the recorded path and be non-empty. Step 5 requires that 5a's plan comment is present exactly once in `roadmap.md` at the expected position, and that 5b's Phase Structure table status flips actually landed. Step 8 requires `plan_file`. Step 10 requires `decision_log`. This is `verification-before-completion` applied to checklist updates.

#### "Non-empty" file check

Steps 4, 8, and 10 each verify that an artifact file exists and is non-empty before ticking. **Use this check** (not bare `test -s`):

```sh
test -s "<path>" && grep -q '[^[:space:]]' -- "<path>"
```

`test -s` accepts any file with size > 0 — including a one-byte `\n` or a stray-whitespace-only file. The whole point of the verification gate is to catch silent writer failures, and a truncated or whitespace-only artifact passes `test -s` while being functionally missing. The combined check requires at least one non-whitespace byte, which is what "non-empty Markdown document" really means in this context. Surface and stop on either failure.

### Brainstorming non-resumability

If interrupted mid-step-4, re-run brainstorming. Step 4's box flips only when the design file is written.

## 0. Resume Detection

A new step that runs before everything else. Before reading the roadmap or doing any phase work, the skill checks for an in-progress run that needs to be resumed and verifies the project is on the current directory layout.

```dot
digraph step0 {
  "start" [shape=doublecircle];
  "old layout?" [shape=diamond];
  "prompt to migrate" [shape=box];
  "abort run" [shape=doublecircle];
  "scan active plans/*-checklist.md with unchecked steps" [shape=box];
  "candidates" [shape=diamond];
  "fresh run" [shape=box];
  "ask which" [shape=box];
  "verify branch" [shape=diamond];
  "branch matches" [shape=box];
  "branch differs" [shape=box];
  "recorded branch missing" [shape=box];
  "stale check" [shape=diamond];
  "prompt resume vs archive" [shape=box];
  "archive stale checklist" [shape=box];
  "jump to first unchecked step" [shape=doublecircle];
  "current step 1" [shape=doublecircle];

  "start" -> "old layout?";
  "old layout?" -> "abort run" [label="no roadmap anywhere\n(prompt: create docs/roadmap/roadmap.md)"];
  "old layout?" -> "abort run" [label="both layouts coexist\n(prompt: reconcile manually)"];
  "old layout?" -> "prompt to migrate" [label="legacy only:\ndocs/roadmap.md exists\n+ docs/roadmap/ doesn't"];
  "old layout?" -> "scan active plans/*-checklist.md with unchecked steps" [label="already migrated"];
  "prompt to migrate" -> "scan active plans/*-checklist.md with unchecked steps" [label="yes (clean tree → run git mv)"];
  "prompt to migrate" -> "abort run" [label="no/cancel\nor dirty tree without confirmation"];
  "scan active plans/*-checklist.md with unchecked steps" -> "candidates";
  "candidates" -> "fresh run" [label="0"];
  "candidates" -> "verify branch" [label="1"];
  "candidates" -> "ask which" [label="2+"];
  "ask which" -> "verify branch" [label="picked one"];
  "ask which" -> "fresh run" [label="none — start fresh"];
  "verify branch" -> "branch matches" [label="match"];
  "verify branch" -> "branch differs" [label="mismatch"];
  "verify branch" -> "recorded branch missing" [label="gone"];
  "branch matches" -> "stale check";
  "branch differs" -> "stale check" [label="continue/switch"];
  "branch differs" -> "abort run" [label="cancel"];
  "recorded branch missing" -> "stale check" [label="recreate"];
  "recorded branch missing" -> "archive stale checklist" [label="archive"];
  "recorded branch missing" -> "abort run" [label="cancel"];
  "stale check" -> "prompt resume vs archive" [label="last_updated > 30d"];
  "stale check" -> "jump to first unchecked step" [label="recent"];
  "prompt resume vs archive" -> "jump to first unchecked step" [label="resume"];
  "prompt resume vs archive" -> "archive stale checklist" [label="archive"];
  "prompt resume vs archive" -> "abort run" [label="cancel"];
  "archive stale checklist" -> "fresh run";
  "fresh run" -> "current step 1";
}
```

### Layout migration

Step 0's first action is a layout sanity check across three locations: `docs/roadmap.md` (legacy roadmap), `docs/roadmap/roadmap.md` (new roadmap), `docs/plans/` (legacy plans dir), `docs/roadmap/plans/` (new plans dir), and `docs/roadmap-decisions/` (legacy decisions dir, named by earlier versions of this skill).

There are four cases:

1. **No roadmap anywhere** — neither `docs/roadmap.md` nor `docs/roadmap/roadmap.md` exists. **Stop and prompt:**

   > No roadmap found. /roadmap operates on `docs/roadmap/roadmap.md`. Create that file first (a minimal H1 + Phase Structure table is enough), then re-run.

   Do not silently fall through to step 1 — step 1 reads `docs/roadmap/roadmap.md`, and a missing-file error there is less actionable than this prompt.

2. **Both layouts coexist** — both `docs/roadmap.md` AND `docs/roadmap/roadmap.md` exist (or both `docs/plans/` AND `docs/roadmap/plans/` exist, or both `docs/roadmap-decisions/` AND `docs/roadmap/decisions/` exist). A half-migrated state, an accidental hand-creation, or independent files. **Stop and prompt:**

   > Roadmap layout looks half-migrated:
   >   - both `docs/roadmap.md` and `docs/roadmap/roadmap.md` exist (one will be canonical, the other should be removed/merged)
   >   - <list any other coexisting pairs>
   >
   > Reconcile manually (which is canonical?) and re-run /roadmap.

   Do not pick one silently — the user's actual roadmap content can be in either file, and silent abandonment of the other is the I4 footgun this guard exists to prevent.

3. **Legacy layout only** — `docs/roadmap.md` exists, `docs/roadmap/roadmap.md` does not, and (any of `docs/plans/` or `docs/roadmap-decisions/` exists OR neither does). Run the migration prompt:

   > Old roadmap layout detected:
   >   - `docs/roadmap.md` (will move to `docs/roadmap/roadmap.md`)
   >   - `docs/plans/` (will move to `docs/roadmap/plans/`) [if present]
   >   - `docs/roadmap-decisions/` (will move to `docs/roadmap/decisions/`) [if present]
   >
   > Run the migration now? `yes` / `no` / `cancel`

   **Before running any `git mv`, run `git status --porcelain`.** If output is non-empty, the working tree is dirty — surface the paths and ask the user to commit, stash, or explicitly confirm the carry-over before continuing. Layout migration is a one-time, irrevocable structural change that should land in a clean, intentional commit; running it over WIP entrains unrelated changes into the staged moves. Do **not** silently `git mv` over a dirty tree.

   On `yes` (after the dirty-tree gate passes), run `git mv -- <src> <dst>` for each pair that is present. On `no` or `cancel`, abort the run and tell the user the new skill cannot operate on the legacy layout. Once `docs/roadmap/roadmap.md` exists, this prompt never fires again for the project (case 4 takes over). Detection is by presence — no marker file needed.

4. **New layout only (or already migrated)** — `docs/roadmap/roadmap.md` exists, `docs/roadmap.md` does not, and no legacy `docs/plans/` or `docs/roadmap-decisions/` linger. Skip the migration prompt and continue to the scan.

Once layout migration succeeds and resume detection finds no in-progress checklist, fall through to step 1 → step 2; the archive prompt fires from step 2 if applicable.

### Scan scope

The scan reads `docs/roadmap/plans/*-checklist.md` exclusively. It never recurses into `docs/roadmap/archive/` — once a roadmap is archived, its in-progress runs are intentionally abandoned and should not surface as resume candidates.

### Branch verification

| Recorded `branch` vs `git branch --show-current` | Action |
|---|---|
| Match | Silently proceed; announce "Resuming Phase X at step N" |
| Mismatch | Prompt: switch to recorded, continue here (updates `branch` field), or cancel |
| Recorded branch no longer exists locally | Prompt: archive the stale checklist, recreate on current branch, or cancel |

### Multiple candidates

If scan returns two or more checklists with unchecked steps, list them and ask which to resume; offer "none — start fresh" as a fourth option.

### Stale-checklist threshold

**Stale threshold:** 30 days (single labeled constant — change here, nowhere else).

If `last_updated` is more than the stale threshold ago, prompt before resuming:

> Checklist `<filename>` was last updated <N> days ago. Resume the run, archive this checklist (rename out of the scan glob and treat the §0 flow as fresh), or cancel?

Acceptable answers (case-insensitive, exact-match): `resume`, `archive`, `cancel`. Anything else → re-prompt.

- **`resume`** — proceed to "jump to first unchecked step".
- **`archive`** — see §Archiving a stale checklist below; the file is renamed out of scan scope, then §0 falls through to "fresh run" → step 1.
- **`cancel`** — stop the /roadmap run.

### Archiving a stale checklist

When the user picks "archive" — for a stale checklist (this section) **or** for a checklist whose recorded branch no longer exists locally (per the branch-verification table above) — rename the single checklist file out of the `*-checklist.md` scan glob without moving directories:

```
git mv -- docs/roadmap/plans/<original>-checklist.md \
          docs/roadmap/plans/<original>-checklist.stale-<YYYY-MM-DD>.md
```

The `.stale-<YYYY-MM-DD>` infix breaks the `*-checklist.md` scan match (the glob is anchored — files ending in `.stale-…md` no longer surface), so the file no longer appears as a resume candidate but stays alongside the run's design / plan / decision-log artifacts as historical evidence. Use today's date.

After the rename succeeds, treat the §0 flow as a fresh run: fall through to step 1. Do **not** re-scan within the same /roadmap invocation — one archived checklist per /roadmap run keeps the flow predictable.

### Jumping to the right step

The first unchecked `- [ ]` in `## Steps` (treating a top-level step as unchecked if either it or any of its sub-checkboxes is unchecked) is the target. The label after the number identifies which step's prose to load.

For steps 6 and 9, the sub-checkbox `Na` distinguishes two recovery modes:

- **`Na` unchecked** → the subagent never returned a complete findings list (never invoked, errored, or timed out). Wipe the corresponding `## Pushback Findings` (or `## Alignment Findings`) section, re-invoke the subagent from scratch, and start over for that step.
- **`Na` checked, top-level `N` unchecked** → findings list is complete; at least one entry has `Status: open`. Resume the discussion from those open findings; do not re-invoke the subagent.

### Re-validate recorded artifact paths on resume

Before announcing "Resuming Phase X at step N" and handing control back to the per-step prose, **re-check each path-bearing frontmatter field whose corresponding step is ticked**: `design_file` (step 4), `plan_file` (step 8), `decision_log` (step 10). For each ticked-with-recorded-path tuple, run the §"Non-empty" file check (`test -s` + non-whitespace grep) against the recorded path.

On any mismatch — file missing, file zero-size, or file whitespace-only — **stop** and surface to the user. Do **not** auto-recover by clearing the path field or re-running the writing step: the recorded path is part of the run's evidence trail, and silently overwriting it would mask the original loss.

Why this is here: a checklist with `- [x] 4. Brainstorm → design saved` and `design_file: foo.md` ticked means the agent reported step 4 done at some point. If `foo.md` was deleted, moved, or truncated between sessions, downstream steps key off a path that no longer points to the artifact they expect — step 5's plan-comment insertion would point at a non-existent file; step 8 would build on a missing design; step 10's decision log would record a broken `design_file`. Catching this at §0 is cheaper than letting any of those downstream failures land first.

## 1. Read the Roadmap

Read `docs/roadmap/roadmap.md` in full. Each phase heading (## Phase N: …) may have a `<!-- plan: filename.md -->` comment on the line immediately after the `---` separator that follows that phase's section. This comment marks the phase as already brainstormed.

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

**On a fresh run, the checklist file does not exist yet** — it is created at step 2a after the working branch is established, and steps 1, 2, 2a are written *pre-checked* there (the work to reach step 2a has been done by then). Do **not** invent a checklist before step 2a. On a resume, the checklist already exists; tick `- [x] 1. Read roadmap` in place and bump `last_updated`.

## 2. Identify the Next Unplanned Phase

Scan phases in order (Phase 1, 2, 3, … 7). The first phase whose section does **not** have a `<!-- plan: … -->` comment is the target.

If **all** phases have plan comments, the roadmap is fully planned. Surface the archive prompt:

> All phases of this roadmap have been planned. Archive to `docs/roadmap/archive/<slug>/` and start fresh? `yes` / `no` / `later`

Parse the response (case-insensitive, leniently as the §2a accept-grammar):

- **`yes`** — derive `<slug>` from the roadmap.md H1 title using the §Appendix slug rule. **Before any `git mv`, check whether `docs/roadmap/archive/<slug>/` already exists** (e.g., a recycled roadmap title or a restored earlier roadmap). On collision, append a disambiguator until the path is free — first try `<slug>-<YYYY-MM-DD>` using today's date; if that also exists, append a numeric counter (`<slug>-<YYYY-MM-DD>-2`, `-3`, …). Surface the chosen disambiguated path to the user *before* moving so they know where the archive landed. Then run `git mv` to move every entry under `docs/roadmap/` (excluding `archive/` itself) into `docs/roadmap/archive/<chosen-slug>/`. Write a fresh stub `docs/roadmap/roadmap.md` (a minimal H1 + empty Phase Structure table — the user fills it in). Announce: "Archived to `docs/roadmap/archive/<chosen-slug>/`. Start a new roadmap by editing `docs/roadmap/roadmap.md`." Stop.
- **`no`** — write a marker file `docs/roadmap/.archive-declined` containing the SHA-1 of the H1 title. On future runs, if the marker file exists and matches the current H1 hash, skip the archive prompt entirely. Announce the no-op and stop. **Compute the hash without piping the title through a shell command line** — the H1 is contributor-controlled and can contain `$(...)`, backticks, `;`, or other shell metacharacters. Two safe methods, in order of preference: (a) compute SHA-1 in the agent's runtime (e.g., a Python `hashlib.sha1(title.encode()).hexdigest()` call invoked through the in-process tool surface), or (b) write the title to a temporary file with no shell interpolation (heredoc with a single-quoted delimiter, e.g. `<<'__H1__'`), then run `sha1sum < /tmp/h1.txt`. Do **not** use `echo "$H1" | sha1sum` or `printf '%s' "$H1" | sha1sum` — both interpolate `$H1` through the shell.
- **`later`** — leave everything in place; do not write a marker. Announce the no-op and stop.

Same caveat as step 1: on a **fresh run**, no checklist file exists yet (step 2a creates it with steps 1, 2, 2a pre-checked); do not invent one early. On a **resume** where the checklist already exists, tick `- [x] 2. Identified next unplanned phase` in place and bump `last_updated`. *Note:* if step 2 detects "every phase has a `<!-- plan: ... -->` comment," do NOT tick — instead surface the archive prompt described above before continuing.

## 2a. Suggest a Working Branch (if on the primary branch)

### Determine the primary branch name

The "primary branch" is whatever the repository treats as the integration
target — usually `main`, but `master`, `trunk`, `develop`, or any other
name is equally valid. /roadmap must not run on it, so we have to detect
the name first.

Run these checks **in order**, locally, and stop at the first that
succeeds:

1. `git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null` —
   succeeds when the repo was cloned from a remote that exposed a
   default branch. Output is `<remote>/<branch>` (typically
   `origin/main`); split on the first `/` and take the right side as
   the primary branch name.
2. `git symbolic-ref --short refs/remotes/upstream/HEAD 2>/dev/null` —
   common in fork workflows. Same parsing.
3. `git show-ref --verify --quiet refs/heads/main` — if the local repo
   has a `main` branch, treat it as primary.
4. `git show-ref --verify --quiet refs/heads/master` — if the local
   repo has a `master` branch (and step 3 did not match), treat it as
   primary.

If all four checks fail, **stop and ask the user**: "Couldn't auto-detect
the primary branch in this repository (no `origin/HEAD` symref, no
`upstream/HEAD`, no local `main` or `master`). Tell me which branch is
primary, or `cancel` to stop." Wait for a branch name; do not guess.

Do **not** use `git remote show origin` to detect the primary branch.
That command hits the network, and a slow or offline remote should never
gate brainstorming. The four checks above are all local.

Call the resulting branch name `<PRIMARY>` for the rest of this section.

### Pre-check the working tree (runs on every branch path)

**Before** the branch-case handling below, run `git status --porcelain`.
If the output is non-empty, the working tree is dirty. Stop and surface
the paths to the user; ask them to commit, stash, or explicitly confirm
the carry-over before continuing. Do **not** silently proceed to step 3
brainstorming over a dirty tree.

This check runs on **every** §2a path — primary, non-primary, and
detached-HEAD — because every path leads to artifact writes (design doc
in step 4, plan in step 8, decision log in step 10). On a non-primary
branch with uncommitted WIP, those writes would interleave with the WIP
in the next commit; on `<PRIMARY>`, the WIP would ride along to the new
feature branch. Both are silent footguns.

### Inspect the current branch

Run `git branch --show-current` and inspect the result. There are three
cases:

- **Detached HEAD** (output is empty): **stop.** Do not proceed. Tell the
  user the working tree is in detached-HEAD state and any commits this
  skill produces would be reachable only via reflog and pruned by the next
  `git gc`. Ask them to either check out a named branch first or
  explicitly confirm they want to land artifacts on a detached commit.
  Do not silently fall through — empty is "not the primary branch", but
  it is also not a safe place to commit.
- **Named branch other than `<PRIMARY>`**: the working branch is already
  chosen. Skip the slug derivation, suggestion-and-wait, and
  `git checkout -b` sub-sections below; jump straight to "Create the run
  checklist" using the current branch as the recorded `branch:` value.
  (The pre-check above has already run.)
- **`<PRIMARY>`**: **refuse to brainstorm on the primary branch.** The
  artifacts produced by this skill (design doc, implementation plan,
  decision log) MUST land on a feature branch. The primary branch is
  never a valid working directory for /roadmap output — even a solo
  developer needs the safety of an isolable branch. The only paths out
  of `<PRIMARY>` from here are creating a feature branch (suggested or
  override) or cancelling the run. Continue with the slug derivation and
  suggestion below.

### Derive a candidate slug

The §2a **branch slug** is the §Per-Phase Filename / phase filename slug
(defined in §Per-Phase Checklist File / Filename / Phase filename slug),
plus one branch-specific modifier:

- **Drop the trailing word** if it is `implementation`, `impl`, or
  `feature`. Branch names benefit from terseness; the filename slug keeps
  it for accuracy. If dropping leaves the slug empty (e.g. `Phase 12:
  Implementation`), the §Per-Phase fallback (`phase-N`) applies.

Apply the drop step *between* steps 3 and 4 of the §Per-Phase rule (after
apostrophe handling, before non-`[a-z0-9]` collapse). The drop is
case-insensitive on the lowercased title.

Examples (compare against the §Per-Phase Phase filename slug table):

| Phase heading                                  | Branch slug            |
|------------------------------------------------|------------------------|
| `Phase 1: Backend Foundation`                  | `backend-foundation`   |
| `Phase 3a: Movie Data Cleaning`                | `movie-data-cleaning`  |
| `Phase 7: User Authentication implementation`  | `user-authentication`  |
| `Phase 9: Editor's Polish`                     | `editors-polish`       |
| `Phase 12: Implementation`                     | `phase-12`             |
| `Phase 3a: 漢字`                                | `phase-3a`             |

The slug is bare — no `feat/`, no `<username>/` prefix. If the user's
convention adds a prefix, let them apply it via the override path below.

**Branch slug ≠ filename slug.** When step 2a's "Create the run checklist" sub-section runs below, the checklist filename uses the §Per-Phase **filename** slug (which keeps the trailing `implementation`/`impl`/`feature`), not this branch slug. Re-derive the filename slug from the title cleanly; do not reuse `<branch-slug>` directly.

### Present the suggestion and wait

Show the user the candidate name and ask them to accept or override:

> Currently on `<PRIMARY>` (the primary branch). /roadmap will not run
> on the primary branch — it needs a feature branch so the design doc,
> plan, and decision log land off `<PRIMARY>`.
>
> Suggested branch: `<candidate-slug>`. Accept, give me a different
> name, or `cancel` to stop the run.

Parse the response per this explicit grammar (matches are case-insensitive;
a trailing `.`, `!`, or `,` is ignored before matching):

- **Accept** — exactly one of: `yes`, `y`, `yeah`, `yep`, `yup`, `ok`,
  `okay`, `sure`, `lgtm`, `looks good`, `go ahead`, `do it`, `proceed`,
  `accept`, `accepted`. Run `git checkout -b '<candidate-slug>'`. Always
  pass the branch name inside single quotes — never interpolate raw user
  input into the shell command.

  **Accept-token-prefix-with-extras → re-prompt, do NOT silently
  Override.** If the response *starts with* an Accept token followed by
  any non-empty trailing words (e.g. `yes please`, `sounds good`, `go
  for it`, `ok let's go`, `ship it`, `yeah looks great`), the natural
  reading is "I'm accepting" — but Override sanitization would silently
  turn `yes please` into the literal branch name `yes-please`. That is
  almost certainly not what the user meant. Re-prompt: "I read that as
  acceptance with extra words. Reply `yes` to accept the suggested
  `<candidate-slug>`, or give me an explicit branch name." Do **not**
  fall through to Override.
- **Cancel** — exactly one of: `cancel`, `abort`. Stop the /roadmap run
  entirely. Do not check out a branch, do not start brainstorming.
- **"Stay on the primary branch" attempts** — any of:
  - `stay`, `stay here`, `no branch` (branch-agnostic phrasings); or
  - `stay on <X>`, `keep <X>`, `on <X>` where `<X>` is `<PRIMARY>` **or**
    any common primary-branch name (`main`, `master`, `trunk`,
    `develop`). Users frequently type the wrong name out of habit, so
    accept these literals regardless of what `<PRIMARY>` is — `keep
    main` on a `master`-primary repo is still a stay-attempt, not a
    branch name.

  The user is trying to keep working on the primary branch, but /roadmap
  refuses. Print: "/roadmap does not run on `<PRIMARY>` (the primary
  branch). Reply with `cancel` to stop, or a branch name to create."
  Re-prompt; do **not** treat the response as a branch name (otherwise
  `stay` silently becomes `git checkout -b 'stay'`, which is not what
  the user meant).
- **Decline (ambiguous, ask)** — exactly one of: `no`, `nope`, `nah`,
  `n`. A bare negative is too ambiguous to interpret as the literal
  branch name `no`. Ask the user to clarify: "Did you mean cancel the
  brainstorming run entirely, or use a specific branch name? Reply
  with `cancel` or a branch name." Do **not** treat the bare negative
  as Override — `git checkout -b 'no'` is almost certainly not what
  the user wants. Do **not** offer staying on `<PRIMARY>`; this skill
  does not run on the primary branch.
- **Override** — anything else. Treat the entire response as a candidate
  branch name and run it through the slug rule above (lowercase, collapse
  non-`[a-z0-9]` to hyphens, strip leading/trailing) **before** passing it
  to git. If the sanitized result equals `<PRIMARY>`, or any common
  primary-branch name (`main`, `master`, `trunk`, `develop`), reject it:
  print "Cannot create a feature branch named `<sanitized>` — that's a
  primary-branch name. Choose a different name, or `cancel`." and
  re-prompt. Otherwise run `git checkout -b '<sanitized-name>'` with the
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
  choose a different name, or `cancel` the run?" Wait for the user's
  decision; do not switch silently — the existing branch may carry
  unrelated WIP that the user does not want to land roadmap artifacts
  on. Staying on `<PRIMARY>` is not an option.
- **Any other failure** — surface the full git error and stop. Do not
  fall through to step 3 brainstorming on `<PRIMARY>`; that is the
  very thing §2a was designed to prevent.

Only proceed to step 3 after the branch decision is made *and* the
checkout succeeded.

#### Create the run checklist

After `git checkout -b` succeeds, write a new checklist file to:

```
docs/roadmap/plans/<YYYY-MM-DD>-<phase-slug>-checklist.md
```

where `<YYYY-MM-DD>` is today's date and `<phase-slug>` is the **phase
filename slug** (§Per-Phase Checklist File / Filename / Phase filename
slug). **Do not reuse `<branch-slug>`** — the branch slug drops the
trailing `implementation`/`impl`/`feature` word; the filename slug keeps
it. Re-derive cleanly from the phase title.

Populate the frontmatter:

```yaml
---
phase: '<full Phase N: Title text from the roadmap heading — single-quoted; double any embedded apostrophe>'
phase_slug: <phase-slug>
branch: <branch name created above>
roadmap: docs/roadmap/roadmap.md
started: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
design_file: null
plan_file: null
decision_log: null
---
```

Initialize the body with:

- The H1: `# <full phase title> — Run Checklist`
- The `## Steps` block (all 11 step boxes including the `6a` and `9a`
  sub-checkboxes), with steps **1, 2, and 2a pre-checked** (the work
  to reach this point is done):

  ```
  - [x] 1. Read roadmap
  - [x] 2. Identified next unplanned phase
  - [x] 2a. Working branch created: `<branch>`
  - [ ] 3. Extract phase context
  - [ ] 4. Brainstorm → design saved
  - [ ] 5. Record plan filename in roadmap
  - [ ] 6. Pushback review
    - [ ] 6a. Pushback returned all findings
  - [ ] 7. CLAUDE.md review
  - [ ] 8. Write implementation plan
  - [ ] 9. Alignment check
    - [ ] 9a. Alignment returned all findings
  - [ ] 10. Write decision log entry
  - [ ] 11. Announce completion
  ```

- Empty `## Pushback Findings` and `## Alignment Findings` sections,
  each with the placeholder line `(populated during step N,
  transcribed by step 10)`.

## 3. Extract the Phase Context

Collect the full text of the target phase section from the roadmap (everything between its `## Phase N` heading and the next `## Phase` heading or end of file). This is the spec input for brainstorming.

Also note:
- Which earlier phases it depends on (listed under ### Dependencies).
- The current date (for the plan filename).

Tick `- [x] 3. Extract phase context` and bump `last_updated`.

## 4. Brainstorm

Invoke the `superpowers:brainstorming` skill. When the brainstorming skill asks what you're building, provide:

- The phase name and goal from the roadmap.
- The full phase section text as context.
- That the output should be a **design document** saved to `docs/roadmap/plans/`.

Follow the brainstorming skill's process completely. It will explore requirements, ask the user questions, and produce a design document. Also, think of the design from the standpoint of a writer. Is it truly useful for them? If you think it could be more useful, discuss this with the user.

When brainstorming, apply the PR scope rules in CLAUDE.md (§Pull Request Scope) — flag to the user if this phase bundles more than one feature or refactor and should be split before a plan is written.

After the design doc is written, **verify it exists and is non-empty** per §Per-Phase Checklist File / "Non-empty" file check (rejects whitespace-only files, not just zero-byte ones); if either check fails, surface to the user and stop. Then set `design_file: <path>` in the checklist frontmatter and tick `- [x] 4. Brainstorm → design saved`.

## 5. Record the Plan Filename

After brainstorming produces a document in `docs/roadmap/plans/`, update `docs/roadmap/roadmap.md` in **two places**:

Step 5 mutates `roadmap.md` — the source of truth for "next unplanned phase" — in two places. It must be **idempotent on resume** (5a re-running must not duplicate the comment) and **verified before ticking** (a partial 5a/5b must not flip the box). Both halves run before the single `- [x] 5` tick. If a `/clear` lands between 5a and 5b, the box stays unchecked, resume re-enters step 5, 5a's idempotency guard skips the already-inserted comment, and 5b re-runs to completion.

### 5a. Insert the plan comment

The plan comment lives on the line immediately after the `---` separator that precedes the phase heading.

**Idempotency guard.** Before inserting, read `docs/roadmap/roadmap.md` and check whether a `<!-- plan: ... -->` line already appears immediately after the `---` separator preceding the target phase heading. If one is present, skip the insertion (a prior interrupted run already wrote it). Do **not** insert a second comment — `## 2. Identify the Next Unplanned Phase` keys off the first such comment per phase, and a duplicate makes downstream parsing undefined.

**Insertion (when no comment is present yet):**

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

**Verification.** After the insertion (or after the idempotency skip), re-read `docs/roadmap/roadmap.md` and confirm exactly one `<!-- plan: <filename> -->` line appears on the line immediately after the `---` separator preceding the target phase heading, and that the filename matches the design doc just created. If zero or two-plus matches, **stop** and surface to the user — do **not** tick step 5.

### 5b. Update the Phase Structure table statuses

In the **Phase Structure** table near the top of the roadmap, make two updates:

1. **Mark the current phase as "In Progress"** — change its status from `Planned` to `In Progress`.
2. **Mark the previous phase as "Done"** — if the phase immediately before the current one has status `In Progress`, change it to `Done` (it must have been completed if we're moving on to brainstorm the next phase).

The valid statuses are:

- **Planned** — not yet started
- **In Progress** — brainstorming or implementation underway
- **Done** — shipped and merged to the primary branch

**Idempotency guard.** Re-applying 5b on resume is naturally idempotent: setting a row already at `In Progress` to `In Progress` is a no-op, and the previous-phase flip from `In Progress` → `Done` is a no-op once it has already been done. No duplicate-edit hazard exists here.

**Verification.** After the table edit, re-read the **Phase Structure** table and confirm: (a) the target phase row's status is exactly `In Progress`; (b) if the prior phase row was `In Progress` before the edit, it is now exactly `Done`. If either check fails, **stop** and surface to the user — do **not** tick step 5.

### Tick step 5

Tick `- [x] 5. Record plan filename in roadmap` and bump `last_updated` **only after both 5a and 5b verifications above pass**. A failed verification (zero/duplicate plan comment, or the table row didn't actually flip) leaves the box unchecked, which is the resume signal to re-enter step 5 — 5a's idempotency guard ensures the second run lands cleanly.

## 6. Pushback Review

Invoke the `paad:pushback` skill against the design document just created in `docs/roadmap/plans/`. If English is the new programming language, pushback is code review for the plan — catch contradictions, feasibility issues, scope problems, and ambiguity before any implementation begins.

After pushback completes, discuss the findings with the user and update the design document to address any valid concerns before moving on.

**Instrumentation for the decision log.** For each issue pushback raises, append a finding entry to the checklist's `## Pushback Findings` section with `Severity` (Critical / Important / Minor — pushback assigns these), `Category` (Contradiction / Feasibility / Scope / Omission / Ambiguity / Security / Other — taken from which check fired), `Summary` (one paragraph written *now* while the context is fresh — this is the prose step 10 will copy verbatim), `Status: open`, and `Resolution: _(pending)_`. When the pushback subagent returns cleanly, tick `6a. Pushback returned all findings`. When discussion closes a finding, flip `Status: closed` and write the resolution using the closed vocabulary (`fixed-in-design`, `fixed-in-plan`, `dismissed-invalid`, `dismissed-out-of-scope`, `accepted-as-is`, `deferred`) followed by a one-sentence detail of what changed or why it was dismissed. Tick top-level step 6 only when **both** 6a is checked AND every finding has `Status: closed`.

If pushback raises zero issues, tick 6a and step 6 immediately — a clean pushback is itself evidence, and the empty `## Pushback Findings` section (with the placeholder line preserved) is what step 10 will transcribe.

**Failure handling.** If the `paad:pushback` invocation itself errors,
times out, or returns malformed output (anything that is not a usable
pushback report), retry **once**. If the retry also fails, **stop**
and surface the failure to the user — name the failure mode and the
last output (or error text). Do **not** record "no issues" or "clean
pushback" in the decision log: that wording is reserved for runs
where the skill returned successfully with zero findings. The
decision log's purpose is evidence; a failed pushback recorded as a
clean pushback corrupts the evidence trail. If pushback fails on
retry, leave the (possibly partial) findings in `## Pushback Findings`
as-is. The 6a sub-checkbox stays unchecked, which signals a future
resume to wipe the section and re-invoke pushback per §0 (resume
detection).

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

Tick `- [x] 7. CLAUDE.md review` after the discussion concludes, regardless of whether CLAUDE.md was edited.

## 8. Write the Implementation Plan

Invoke the `superpowers:writing-plans` skill against the finalized design document. The writing-plans skill will produce a bite-sized TDD task list that turns the design into concrete, reviewable commits.

When invoking writing-plans, provide:

- The path to the finalized design document from step 4.
- The constraints captured during steps 6 and 7 (pushback findings, any CLAUDE.md edits that must land as part of the phase).
- Repository-specific constraints from `CLAUDE.md` (§Testing Philosophy coverage floors, §Pull Request Scope one-refactor / one-feature rule, zero-warnings rule).
- That the plan should be saved alongside the design in `docs/roadmap/plans/` with filename pattern `YYYY-MM-DD-<topic>-plan.md`.

The plan must honor the PR scope rules: a single roadmap phase is a single PR. If the plan would naturally span multiple PRs (for example, a refactor followed by a feature), split at the phase boundary in the roadmap first and re-run this skill against each sub-phase.

After the plan doc is written, **verify it exists and is non-empty** per §Per-Phase Checklist File / "Non-empty" file check (rejects whitespace-only files, not just zero-byte ones); if either check fails, surface to the user and stop. Then set `plan_file: <path>` in the checklist frontmatter and tick `- [x] 8. Write implementation plan`.

## 9. Alignment Check

Invoke the `paad:alignment` skill against the implementation plan just produced. Alignment catches coverage gaps, scope creep, and design-vs-plan mismatches — it verifies that every requirement in the design is traced to at least one task, every task maps back to a requirement, and every task is expressed in TDD red/green/refactor format.

Pass the alignment skill both documents:

- The design document from step 4 (the source of truth for requirements).
- The implementation plan from step 8 (the breakdown being aligned).

After alignment completes, discuss any findings with the user and update the plan (and occasionally the design) to close the gaps. Do not proceed to announcement until the plan and design are aligned, or the user explicitly accepts any remaining gaps.

**Instrumentation for the decision log.** For each issue alignment raises, append a finding entry to the checklist's `## Alignment Findings` section with `Severity` (Critical / Important / Minor — alignment assigns these), `Category` (one of `missing-coverage`, `out-of-scope`, `design-gap`, `tdd-format`), `Summary` (one paragraph written *now* while the context is fresh — this is the prose step 10 will copy verbatim), `Status: open`, and `Resolution: _(pending)_`. When the alignment subagent returns cleanly, tick `9a. Alignment returned all findings`. When discussion closes a finding, flip `Status: closed` and write the resolution using the closed vocabulary (`fixed-in-design`, `fixed-in-plan`, `dismissed-invalid`, `dismissed-out-of-scope`, `accepted-as-is`, `deferred`) followed by a one-sentence detail of what changed or why it was dismissed. Tick top-level step 9 only when **both** 9a is checked AND every finding has `Status: closed`.

If alignment raises zero issues, tick 9a and step 9 immediately — a clean alignment is itself evidence, and the empty `## Alignment Findings` section (with the placeholder line preserved) is what step 10 will transcribe.

**Failure handling.** Same as step 6: if `paad:alignment` errors,
times out, or returns malformed output, retry **once**, then stop and
surface to the user. Do **not** record "no issues" or "clean
alignment" in the decision log unless the skill returned successfully
with zero findings. If alignment fails on retry, leave the (possibly
partial) findings in `## Alignment Findings` as-is. The 9a
sub-checkbox stays unchecked, which signals a future resume to wipe
the section and re-invoke alignment per §0 (resume detection).

## 10. Write the Decision Log Entry

Write a single Markdown file to `docs/roadmap/decisions/YYYY-MM-DD-<phase-slug>.md` capturing this run.

**Filename slug rule:** lowercase the phase heading, drop apostrophes (no separator inserted), replace any run of non-`[a-z0-9]` characters with a single hyphen, strip leading/trailing hyphens, and fall back to `phase-N` (using the phase number, including any sub-letter, from the heading) if the result would otherwise be empty. `Phase 7: Editor's Polish & Polish` → `phase-7-editors-polish-polish`. Combine with today's date in `YYYY-MM-DD` form.

**Model field:** read from your own system context (the system prompt always identifies the model you are running on, e.g., `claude-opus-4-7`). Use the bare model ID, no version suffixes.

Transcribe `## Pushback Findings` and `## Alignment Findings` from the checklist into the decision log file. Transcription is a literal copy of every finding minus the `Status:` line (decision log entries are always closed by definition). Severity counts in the decision log frontmatter come from counting the checklist's findings — single source of truth eliminates the "mentally tracked counts don't sum" reconciliation hazard the prior version of this skill warned about.

Follow the schema in §Appendix: Decision Log Entry Schema (at the bottom of this skill) exactly — YAML frontmatter, then the body sections.

Then update `docs/roadmap/decisions/INDEX.md` by **prepending** one row to the `## Entries` table (newest entry on top). The row contains: date, phase title, model, pushback C/I/M counts (counted from the checklist's `## Pushback Findings`), alignment C/I/M counts (counted from the checklist's `## Alignment Findings`), and a relative link to the entry file just written.

If a /roadmap run produced zero pushback issues *and* zero alignment issues, still write the entry and the index row — a clean run is evidence too. The body sections are the empty-section single-line form from the §Appendix schema (`Pushback raised no issues.` / `Alignment raised no issues.`).

**Severity-count sanity check.** Counts come from a single source — the checklist's findings sections — so `critical + important + minor` summing to `total` is by construction once derived from one scan. If the sum disagrees, the cause is a malformed finding entry on disk (e.g. a missing `Severity:` line, or a `Severity:` value outside the closed Critical/Important/Minor set). Do **not** adjust counts; fix the malformed checklist entry and re-derive.

After the decision log is written, **verify it exists and is non-empty** per §Per-Phase Checklist File / "Non-empty" file check (rejects whitespace-only files, not just zero-byte ones); if either check fails, surface to the user and stop. Then set `decision_log: <path>` in the checklist frontmatter and tick `- [x] 10. Write decision log entry`.

## 11. Announce Completion

Per §Update obligations ("update the checklist before announcing or moving on. No exceptions"), tick `- [x] 11. Announce completion` and bump `last_updated` **before** printing the announcement block. The checklist is now fully ticked and serves as the historical record of the run.

Then print:

> **Roadmap updated.** Phase N: [Name] brainstormed and planned.
> - Design: `docs/roadmap/plans/<filename>-design.md`
> - Plan: `docs/roadmap/plans/<filename>-plan.md`
> - Decision log: `docs/roadmap/decisions/<filename>.md`
> Next unplanned phase: Phase M: [Name] (or "all phases planned").

Offer to move to implementing the plan (via `superpowers:subagent-driven-development` or `superpowers:executing-plans` in a separate session), or to review the updated roadmap.

## Appendix: Decision Log Entry Schema

The decision log captures, for every /roadmap run, what `paad:pushback` and `paad:alignment` caught and how each finding was resolved. Each entry is one Markdown file with YAML frontmatter and a structured body. The purpose is evidence — a body of receipts that the upstream skills (brainstorming, writing-plans) miss real things even when run by the most capable model.

### File location

- Entries: `docs/roadmap/decisions/YYYY-MM-DD-<phase-slug>.md` (one per /roadmap run)
- Index: `docs/roadmap/decisions/INDEX.md` (one row per entry, newest on top)

If a phase is brainstormed more than once on different days, each run produces its own dated entry — the history is preserved.

### Frontmatter

```yaml
---
date: 2026-04-26
phase: 'Phase 3a: Export Foundation'
model: claude-opus-4-7
design_file: docs/roadmap/plans/2026-04-26-export-foundation-design.md
plan_file: docs/roadmap/plans/2026-04-26-export-foundation-plan.md
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

Counts come from a single scan of the checklist findings, so the sum holding is by construction; see step 10's "Severity-count sanity check" for the malformed-input case.

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

The decision-log filename slug is **deliberately distinct** from the §Per-Phase phase filename slug used by `plans/` artifacts:

- **Input** is the full phase **heading** including the `Phase N:` prefix (so the resulting slug carries the phase number — useful when scanning a year of decision-log filenames at a glance in `decisions/`). The §Per-Phase filename slug is title-only.
- **Trailing-word handling** matches the §Per-Phase rule (keeps `implementation`/`impl`/`feature`); only the §2a branch slug drops them.

Procedure: lowercase the phase heading, drop apostrophes (`'`, `'`, `'`) without inserting a separator, replace any run of non-`[a-z0-9]` characters with a single hyphen, strip leading and trailing hyphens, and fall back to `phase-N` (using the phase number — including any sub-letter — from the heading) if the result would otherwise be empty.

Examples:

- `Phase 3a: Export Foundation` → `phase-3a-export-foundation`
- `Phase 7: Editor's Polish & Polish` → `phase-7-editors-polish-polish`
- `Phase 12: Implementation` → `phase-12-implementation`

Cross-reference summary for one phase (`Phase 7: User Authentication implementation`):

| Artifact                                           | Slug                                          | Rule                            |
|----------------------------------------------------|-----------------------------------------------|---------------------------------|
| Branch (§2a)                                       | `user-authentication`                         | filename slug + drop suffix     |
| Design / plan / checklist filename in `plans/`     | `user-authentication-implementation`          | §Per-Phase phase filename slug  |
| Decision-log filename in `decisions/`              | `phase-7-user-authentication-implementation`  | §Appendix slug rule (this one)  |

### Why this schema

The single `model` field assumes one model per /roadmap run (true ~99% of the time). Per-issue resolution tracking is what makes this evidence rather than a list of complaints — "pushback caught N important issues, M of which became design changes" is a much stronger argument than "pushback raised N things." Severity counts in the index let a year of entries be skimmed at a glance for patterns. Closed-set vocabularies (categories, resolutions) keep entries comparable across runs and trivially aggregatable by future tooling.

