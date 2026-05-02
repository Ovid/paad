# Agentic Code Review: skill-roadmap-refuse-main

**Date:** 2026-05-02 10:48:33
**Branch:** skill-roadmap-refuse-main -> main
**Commit:** 99eebc3e2bcdcfeefb5b30abf56afa4443b26a9d
**Files changed:** 15 | **Lines changed:** +2202 / -67
**Diff size category:** Large (markdown — skill prose, design, plan, baselines)

## Executive Summary

This branch is a substantial rewrite of the personal `/roadmap` skill at `.claude/skills/roadmap/SKILL.md`, introducing per-phase checklist files, Step 0 resume detection + auto-migration, an archive-on-all-planned lifecycle, and a one-time `docs/roadmap/` restructure. The implementation faithfully executes the 12-task plan, but specialist review surfaced 7 Critical and 14 Important findings — most concentrated in the §0 digraph (missing edges that the prose's decision tree relies on), the new checklist-vs-roadmap state coherence (non-idempotent step 5, no resume-time path validation), filename-slug rules that diverge across artifacts of the same run, and a leftover finding-count "reconciliation" block that the new single-source-of-truth design rendered unreachable. The skill is *behaviorally close to ready* but ships safety-gate gaps that an interruption-resilience skill should not have.

## Critical Issues

### [C1] Digraph: stale-check "archive" branch is undefined and unreachable
- **File:** `.claude/skills/roadmap/SKILL.md:126, 146-148`
- **Bug:** §0 digraph declares `prompt resume vs archive` but only the `resume` edge is drawn. The "archive a stale checklist" outcome (also mentioned at line 177 for the recorded-branch-missing path) has no defined semantics: does it move the single checklist file? Delete it? Archive the whole roadmap?
- **Impact:** Agent confronted with a stale checklist and the user picking "archive" has no defined action and may invent behavior — possibly archiving the entire roadmap when the user only meant to discard one stale run.
- **Suggested fix:** Define archive-stale-checklist semantics (e.g., `git mv` the single checklist into `docs/roadmap/plans/archived/` or `docs/roadmap/archive/.stale/`), and add the corresponding edge `prompt resume vs archive → <archive terminal> [label="archive"]`. Same treatment for the recorded-branch-missing archive option at line 177.
- **Confidence:** High
- **Found by:** Logic & Correctness, Edge Cases & Recovery

### [C2] Step 5 has no verification-before-ticking gate
- **File:** `.claude/skills/roadmap/SKILL.md:99-101, 533`
- **Bug:** The verification-before-ticking rule (lines 99-101) lists steps 4, 8, 10. Step 5 mutates `roadmap.md` — the source of truth for "next unplanned phase" — in two places (5a inserts the plan comment, 5b updates the Phase Structure table) and ticks unconditionally.
- **Impact:** A failed/partial 5a leaves no `<!-- plan: -->` marker. The next /roadmap run sees the phase as still unplanned and re-picks it. The clobbered roadmap is a real risk: step 5 is the only mechanism that durably records "this phase has been brainstormed."
- **Suggested fix:** After 5a, grep for the inserted `<!-- plan: -->` line at the expected location. After 5b, re-read the Phase Structure table and confirm the status flips happened. Tick step 5 only if both succeed.
- **Confidence:** High
- **Found by:** Logic & Correctness

### [C3] Step 5 is not idempotent on resume between 5a and 5b
- **File:** `.claude/skills/roadmap/SKILL.md:495-533`
- **Bug:** One tick covers two roadmap.md edits. If a `/clear` lands between 5a (insert plan comment) and 5b (Phase Structure table flip), resume jumps to step 5 (still unticked) and re-runs both. 5a is non-idempotent — it would insert a duplicate `<!-- plan: ... -->` comment line.
- **Impact:** Step 2's "first phase without a plan comment" scan would now find two comments on the same phase; downstream parsing is undefined. Silent corruption of the roadmap's machine-readable state.
- **Suggested fix:** Make 5a idempotent (check for an existing `<!-- plan: -->` line on the line after the `---` separator and skip insertion if present). Optionally split 5/5b into separate sub-checkboxes so each completes independently.
- **Confidence:** High
- **Found by:** Concurrency & State

### [C4] Step 10 finding-count "reconciliation" block is structurally a no-op
- **File:** `.claude/skills/roadmap/SKILL.md:632` (and matching block at 683-695 in the Appendix)
- **Bug:** The new design pulls both `total` and per-severity counts from the same source (the checklist's findings sections). The invariant `critical + important + minor == total` is therefore tautological — it cannot fail by construction. The 13-line "stop and reconcile with the user before writing the entry" warning is dead code carried over from the prior in-head-tracking design.
- **Impact:** The reconciliation block is misleading prose: an agent reading it will burn cycles validating an invariant that cannot break, and the false sense of integrity-checking obscures that there is *no* real cross-check between the checklist and the decision-log frontmatter.
- **Suggested fix:** Delete the reconciliation block, or rewrite it as a single sentence acknowledging the single-source-of-truth design ("Counts are derived from the checklist; no independent reconciliation is required"). If a real cross-check is wanted, add one (e.g., re-count from the checklist after writing the decision log frontmatter and assert equality).
- **Confidence:** High
- **Found by:** Logic & Correctness, Concurrency & State

### [C5] Step 11 ticks after announce — direct contradiction with global "before announcing" rule
- **File:** `.claude/skills/roadmap/SKILL.md:86, 646`
- **Bug:** Line 86 mandates "update the checklist … **before** announcing or moving on." Line 646 instructs: "After announce, tick `- [x] 11. Announce completion`." The two rules disagree about ordering for the terminal step.
- **Impact:** Under rationalization pressure ("the obligations block said before announcing, so I'll update first") the agent could double-announce or skip the tick entirely. More importantly, it teaches the agent that the rule has unstated exceptions, which weakens the rule's hold on every other step.
- **Suggested fix:** Either tick before printing the announcement block, OR carve an explicit exception in §Update obligations naming step 11. Pick one and remove the contradiction.
- **Confidence:** High
- **Found by:** Contract & Integration

### [C6] Layout migration omits `docs/roadmap-decisions/`
- **File:** `.claude/skills/roadmap/SKILL.md:155-163` (and design doc lines 83-84)
- **Bug:** The migration prompt lists only `docs/roadmap.md` → `docs/roadmap/roadmap.md` and `docs/plans/` → `docs/roadmap/plans/`. The design explicitly states: "The `docs/roadmap-decisions/` location named by the existing skill prose collapses into `docs/roadmap/decisions/`." For projects on the prior layout that already have a populated `docs/roadmap-decisions/`, the migration silently leaves it behind, and step 10 writes to the new location — split decision logs across two directories.
- **Impact:** Directory hygiene (one of the design's five goals) silently fails for any project with prior decision logs. The user has to manually find and migrate `docs/roadmap-decisions/` themselves, with no warning the migration was incomplete.
- **Suggested fix:** Add a third bullet to the migration prompt and a third `git mv` covering `docs/roadmap-decisions/` → `docs/roadmap/decisions/`. Detection should fire if either source directory exists.
- **Confidence:** High
- **Found by:** Logic & Correctness

### [C7] Slug rule divergence: branch + checklist filename drop trailing words; decision log filename keeps them
- **File:** `.claude/skills/roadmap/SKILL.md:18, 303-318, 419-425, 757-761`
- **Bug:** Three slug rules co-exist:
  - §2a branch slug (303-318): drops trailing `implementation`/`impl`/`feature`.
  - §Per-Phase Checklist filename (18) + 2a "Create the run checklist" (425): "reuse the §2a slug" → also drops the suffix.
  - §Appendix decision-log slug (757-761): explicitly keeps the suffix (line 761: "filename slug keeps the `implementation` suffix; only the §2a branch slug drops it").

  For "Phase 7: User Authentication implementation":
  - branch: `user-authentication`
  - checklist: `…-user-authentication-checklist.md`
  - decision log: `…-phase-7-user-authentication-implementation.md`
- **Impact:** The three artifacts for one run no longer share a slug component. The design's promise (line 18) that "design / plan / checklist for one run sit alphabetically adjacent in `plans/`" breaks for any phase with a trailing-word title — and any future tooling correlating checklist `phase_slug` to decision log filename will mismatch.
- **Suggested fix:** Pick one rule and apply it everywhere. Most consistent: keep the suffix in all filenames (the carve-out at line 761 already documents this is intentional for filenames), and drop only in branch names (where short matters). Then §Per-Phase Filename should reference the §Appendix rule, not the §2a rule. Add a one-line note to §2a that branch slug ≠ filename slug.
- **Confidence:** Medium-High
- **Found by:** Logic & Correctness, Contract & Integration

## Important Issues

### [I1] Digraph: cancel edges absent from "branch differs" / "recorded branch missing"
- **File:** `.claude/skills/roadmap/SKILL.md:140-145, 174-177`
- **Bug:** The branch verification table (174-177) offers `cancel` for both Mismatch and Recorded-branch-missing. The digraph has neither edge.
- **Impact:** Per CLAUDE.md's digraph requirements, every branching path in the prose must appear in the digraph. An agent following the digraph as the safety-gate authority drops cancellation as an option here.
- **Suggested fix:** Add `branch differs → abort run [label="cancel"]` and `recorded branch missing → abort run [label="cancel"]`.
- **Confidence:** High
- **Found by:** Logic & Correctness, Contract & Integration

### [I2] Digraph: "ask which" → "fresh run" missing edge
- **File:** `.claude/skills/roadmap/SKILL.md:138, 181`
- **Bug:** Multi-candidate prompt (line 181) explicitly offers "none — start fresh" but the digraph routes "ask which" only to "verify branch."
- **Impact:** User who picks "none" lands the agent in branch verification on a non-existent recorded branch — undefined behavior.
- **Suggested fix:** Add `ask which → fresh run [label="none — start fresh"]`. Re-label the existing edge to `[label="picked one"]`.
- **Confidence:** High
- **Found by:** Logic & Correctness, Edge Cases, Contract & Integration

### [I3] Brand-new project (no roadmap.md anywhere) drops into step 1 against a non-existent file
- **File:** `.claude/skills/roadmap/SKILL.md:196-197` + §0 fall-through
- **Bug:** If neither `docs/roadmap.md` nor `docs/roadmap/roadmap.md` exists, §0 takes the "already migrated or fresh project" edge → 0 candidates → "fresh run" → step 1 reads a non-existent file.
- **Impact:** First-time `/roadmap` user gets a file-not-found error, not a graceful "create one first" prompt.
- **Suggested fix:** In §0, before the scan, also check whether `docs/roadmap/roadmap.md` exists; if neither it nor the legacy file exists, prompt: "No roadmap found. Create `docs/roadmap/roadmap.md` first, then re-run." Stop.
- **Confidence:** High
- **Found by:** Edge Cases & Recovery

### [I4] Both legacy and new layout coexist → legacy file silently abandoned
- **File:** `.claude/skills/roadmap/SKILL.md:155-163`
- **Bug:** Detection condition is "`docs/roadmap.md` exists AND `docs/roadmap/` doesn't." If both exist (half-migrated state, manual creation, or independent files), the migration is skipped and the legacy file is silently ignored on every run.
- **Impact:** The user's actual roadmap content can be in either file; the skill picks the new-layout one without warning. Any in-progress plans in `docs/plans/` are invisible to resume detection.
- **Suggested fix:** When both `docs/roadmap.md` and `docs/roadmap/roadmap.md` exist, prompt the user to reconcile (which is canonical?) before continuing. Same treatment for `docs/plans/` vs `docs/roadmap/plans/`.
- **Confidence:** Medium-High
- **Found by:** Edge Cases & Recovery

### [I5] §0 layout migration runs `git mv` on a dirty tree without check
- **File:** `.claude/skills/roadmap/SKILL.md:155-163`
- **Bug:** §0 has no `git status --porcelain` pre-check before the migration `git mv`s. §2a has the equivalent check at line 296, but only inside its primary-branch path.
- **Impact:** Layout migration is a one-time, irrevocable structural change that should land in a clean, intentional commit. Running it over WIP entrains unrelated changes into the staged moves.
- **Suggested fix:** Run `git status --porcelain` before the migration `git mv` block. On dirty tree, surface paths and ask user to commit/stash/confirm before proceeding.
- **Confidence:** High
- **Found by:** Edge Cases & Recovery

### [I6] Step 2 archive `yes` overwrites pre-existing `archive/<slug>/` with no collision check
- **File:** `.claude/skills/roadmap/SKILL.md:229`
- **Bug:** `git mv` into an existing `docs/roadmap/archive/<slug>/` either fails noisily mid-operation (leaving a partial archive) or, depending on git's semantics, merges silently. No pre-check.
- **Impact:** A user who recycles roadmap titles or restores an earlier roadmap and runs through it again gets a half-completed archive that requires manual git surgery to repair.
- **Suggested fix:** Before the `git mv`, check `test -d docs/roadmap/archive/<slug>`. On collision, append a disambiguator (e.g., `<slug>-2`, `<slug>-YYYYMMDD`) and surface the rename to the user.
- **Confidence:** High
- **Found by:** Edge Cases & Recovery

### [I7] §2a accept-grammar rejects common positive phrases → silently creates branches named after them
- **File:** `.claude/skills/roadmap/SKILL.md:344-388`
- **Bug:** Acceptance is exact-match against a fixed list. Common phrasings like `yes please`, `sounds good`, `go for it`, `ok let's go`, `ship it` fall through to **Override**, get sanitized (e.g., `yes-please`), pass primary-name rejection, and run `git checkout -b 'yes-please'`.
- **Impact:** The most natural ways users say "yes" silently become literal branch names. The §2a accept-grammar (~40 lines of careful prose) is the single richest source of silent misclassification in the skill.
- **Suggested fix:** Either (a) match prefix against the accept list and treat matched-then-extra-words as Override of the remainder, (b) detect any accept token at the start of the response and re-prompt for clarification rather than silently treating as Override, or (c) explicitly reject ambiguous mixes. The closing prose at 386-388 already gestures at (c) for `yeah call it foo` — extend it.
- **Confidence:** High
- **Found by:** Edge Cases & Recovery

### [I8] `test -s` accepts whitespace-only files as "non-empty"
- **File:** `.claude/skills/roadmap/SKILL.md:493, 590, 634`
- **Bug:** `test -s` returns true for any file size > 0. A 1-byte `\n` or a stray-whitespace file passes verification.
- **Impact:** The whole point of "verification before completion" is to catch silent writer failures. A truncated/zero-content file passes the gate, the box ticks, the resume detection thinks the step is done, and the artifact is functionally missing.
- **Suggested fix:** Combine size with content check: `test -s "$path" && grep -q '[^[:space:]]' "$path"`. Or require an expected H1/header pattern.
- **Confidence:** High
- **Found by:** Edge Cases & Recovery

### [I9] Steps 1 and 2 prose says "tick" but no checklist exists yet on a fresh run
- **File:** `.claude/skills/roadmap/SKILL.md:217, 233, 414-465`
- **Bug:** On a fresh run, the checklist isn't created until step 2a (line 414). Steps 1 (line 217) and 2 (line 233) prose says "Tick `- [x] 1. Read roadmap`" and "Tick `- [x] 2. Identified next unplanned phase`" — but there's nothing to tick. The 2a block at line 448 backfills both as pre-checked, but the prose at 217/233 is misleading.
- **Impact:** An agent following the prose literally will either error or write a partial checklist before 2a does — breaking 2a's creation contract. Even if the agent reasons through it, the contradiction leaves an opening to "fix" by writing a checklist early.
- **Suggested fix:** Reword steps 1 and 2's tail to: "(No checklist yet on a fresh run — these steps will be backfilled as pre-checked at step 2a.)" Or move the create-checklist-file moment to immediately after step 1.
- **Confidence:** High
- **Found by:** Logic & Correctness, Contract & Integration

### [I10] Resume doesn't re-validate previously-recorded artifact paths still exist
- **File:** `.claude/skills/roadmap/SKILL.md:99-101, 188-194`
- **Bug:** Verification gates ticking, but on resume, a checklist with step 4 ticked and `design_file: foo.md` recorded — yet `foo.md` was deleted between sessions — §0 jumps to step 5 without re-validating prior artifacts.
- **Impact:** Step 5 then writes `<!-- plan: foo.md -->` pointing at a non-existent file. Subsequent /roadmap runs treat the phase as planned, while the actual design doc is gone — silent reference rot.
- **Suggested fix:** As part of §0, if the resume target is step 5 or later, re-check existence and non-emptiness of each path-bearing frontmatter field whose corresponding step is ticked. On mismatch, surface to the user and stop.
- **Confidence:** High
- **Found by:** Logic & Correctness

### [I11] §2a dirty-tree check is gated on the PRIMARY-only path
- **File:** `.claude/skills/roadmap/SKILL.md:271-300`
- **Bug:** The "Named branch other than `<PRIMARY>`" path (line 283-284) explicitly says "skip the rest of this step" — which skips the dirty-tree pre-check at line 296.
- **Impact:** A user already on a feature branch with WIP can have roadmap artifacts (design doc, plan, decision log writes) interleaved with that WIP in their next commit. The recorded "safety net" branch in the checklist doesn't exist yet at this point.
- **Suggested fix:** Pull the `git status --porcelain` check up out of §2a's primary-only sub-section so it runs on every branch path before any new artifact writes begin.
- **Confidence:** High
- **Found by:** Contract & Integration

### [I12] YAML frontmatter `phase` field has no escape contract
- **File:** `.claude/skills/roadmap/SKILL.md:24, 431`
- **Bug:** The phase title is read from the roadmap heading and interpolated raw into a double-quoted YAML scalar. A heading containing `"`, `\`, or a literal newline corrupts the YAML or could inject a sibling key (e.g., `branch:`).
- **Impact:** Resume detection then fails to parse the checklist, forcing manual recovery. A more crafted title could steer the agent into reading/writing attacker-chosen paths during step-4/8/10 verification.
- **Suggested fix:** Specify either (a) escape `"` and `\`, reject literal newlines, or (b) use YAML literal block scalars (`phase: |-`) or single-quoted scalars (which only need `''` doubling). Document the rule explicitly in §Schema.
- **Confidence:** High
- **Found by:** Security

### [I13] `.archive-declined` SHA-1 computation method is unspecified — invites unsafe shell
- **File:** `.claude/skills/roadmap/SKILL.md:230`
- **Bug:** Prose says "the SHA-1 of the H1 title" with no implementation guidance. Agents typically reach for `echo "$H1" | sha1sum`. If `H1` contains command substitution (e.g., a phase title authored with `$(…)` for any reason) and the agent doesn't quote correctly, that's an arbitrary-code path through the shell.
- **Impact:** The H1 title is contributor-controlled in a multi-user repo. Modest but real risk on shells that interpret `$(...)` or backticks.
- **Suggested fix:** Prescribe a method that doesn't pipe content through a shell command line. Either (a) compute via the agent's built-in capabilities (no shell), (b) write H1 to a temp file first then `sha1sum < tempfile`, or (c) use a heredoc with a quoted delimiter that disables interpolation.
- **Confidence:** Medium-High
- **Found by:** Security

### [I14] `git mv` lacks `--` separator (filename starting with `-` interpreted as flag)
- **File:** `.claude/skills/roadmap/SKILL.md:163, 229`
- **Bug:** None of the documented `git mv` invocations specify the `--` separator. A file in `docs/roadmap/` whose name starts with `-` would be parsed as a git option.
- **Impact:** Modest argument-injection risk if a malicious or careless file name lands in the directory. Also a hardening best practice.
- **Suggested fix:** Spell out `git mv -- <src> <dst>` everywhere shell mv is invoked.
- **Confidence:** Medium
- **Found by:** Security

## Suggestions

- **[S1]** Two examples in SKILL.md disagree about checklist pre-check state (lines 38-51 schema example shows steps 1-4 ticked; lines 449-466 step 2a creates with only 1, 2, 2a ticked). Risk: agent uses the more-prominent schema example as a template. Fix: rewrite the §Schema example to match the §2a creation state.
- **[S2]** CLAUDE.md doesn't mention `.claude/skills/roadmap/` (the project-local skill location). Add a short subsection covering the project-local skill's lifecycle (no marketplace, no version bump, edit-and-commit only).
- **[S3]** Resolution vocabulary duplicated in 4 places (lines 80, 541, 603, 728-735) — declare the Appendix authoritative and have the others link to it.
- **[S4]** Pushback / Alignment Category vocabularies duplicated and not authoritatively sourced (lines 541, 603, 706, 716) — same fix as S3.
- **[S5]** `last_updated` bump not spelled out at steps 4, 6, 8, 9, 10, 11 (the global rule at line 86 covers it, but uneven explicit reminders invite "step 4 didn't say to bump it" reasoning).
- **[S6]** §2a primary-name list inconsistent: detection (lines 247-263) checks only `main`/`master`; rejection (lines 354-385) treats `develop`/`trunk` as primary too. A `develop`-primary repo with no `origin/HEAD` falls through to the manual prompt at line 260.
- **[S7]** Stale-checklist threshold (line 184-185) is not the labeled "one-line constant" the design promised — value `30 days` lives inline in prose. Hoist to a labeled `**Stale threshold:** 30 days` block.
- **[S8]** §0 "abort run" node (line 116) is a `box`, but other terminals are `doublecircle`. Visual inconsistency.
- **[S9]** 6a/9a tick before user discussion can add new findings — provenance of user-added vs subagent-authored findings is lost. Consider a `source:` field per finding, or a one-sentence acknowledgement that post-tick additions count as user-authored.

## Plan Alignment

- **Implemented:** All 12 plan tasks landed (RED scenarios captured, migration done as `git mv` renames, Step 0 + checklist file creation + per-step update obligations + archive lifecycle + sub-checkbox semantics + literal transcription at step 10 + REFACTOR rationalization-table extension + end-to-end coherence pass). The §0 digraph in SKILL.md matches the design doc verbatim post-commit `99eebc3`. The archive-on-all-planned trigger correctly replaced the prior "all brainstormed → nothing to do" no-op. The single-PR override is documented in plan §PR scope.
- **Not yet implemented:** The stale-threshold "one-line constant" wording from design §3 isn't literally a labeled constant — see Suggestion S7.
- **Deviations:** None of consequence. Notable additions consistent with the design: `paad:pushback` failure-handling block adds the §0 cross-reference (plan Task 7 verbatim); REFACTOR rationalization-table row about merging partial findings (commit `d5bab34`).

## Review Metadata

- **Agents dispatched:** 6 specialists in parallel
  - Logic & Correctness (17 raw findings)
  - Edge Cases & Recovery (17 raw findings)
  - Contract & Integration (14 raw findings)
  - Plan Alignment (1 carry-forward + clean implementation report)
  - Security (5 raw findings)
  - Concurrency & State (6 raw findings)
- **Verifier:** confirmed/dropped each finding by reading actual file:line, deduplicated cross-specialist hits, assigned severity
- **Scope:** `.claude/skills/roadmap/SKILL.md` (primary, +397/-67 lines), `docs/roadmap/roadmap.md`, `docs/roadmap/plans/2026-05-02-roadmap-resume-checklists-design.md`, `docs/roadmap/plans/2026-05-02-roadmap-resume-checklists-plan.md`, `notes/roadmap-resume-baselines.md`, `CLAUDE.md`
- **Raw findings:** 60 (across 6 specialists, before dedup)
- **Verified findings:** 30 (7 Critical + 14 Important + 9 Suggestions)
- **Filtered out:** 30 (false positives, duplicates, prose-only ambiguity, intentional behavior)
- **Steering files consulted:** `CLAUDE.md` (one finding flagged: project-local skill not documented in steering)
- **Plan/design docs consulted:** `docs/roadmap/plans/2026-05-02-roadmap-resume-checklists-design.md`, `docs/roadmap/plans/2026-05-02-roadmap-resume-checklists-plan.md`, `notes/roadmap-resume-baselines.md`
