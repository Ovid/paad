# Roadmap Resume Checklists — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `/roadmap` runs resumable across `/clear`s and session restarts by introducing a per-phase checklist file, a Step 0 resume-detection layer, an archive-on-all-planned lifecycle, and a one-time directory restructure under `docs/roadmap/`.

**Architecture:** All changes land in **one file**: `.claude/skills/roadmap/SKILL.md` (the personal `/roadmap` skill, not under `plugins/paad/skills/`). A one-time `git mv` migrates `docs/roadmap.md` and `docs/plans/` into `docs/roadmap/`. Behavior changes follow RED-GREEN-REFACTOR per `superpowers:writing-skills` — pressure scenarios first, then SKILL.md edits, then re-verify.

**Tech Stack:** Markdown (SKILL.md prose + checklist files), git for the migration, subagents (Task tool) for pressure scenarios. No code dependencies.

**Spec:** `docs/plans/2026-05-02-roadmap-resume-checklists-design.md` is the source of truth. This plan references its sections (§1, §2, §3, etc.) rather than duplicating prose.

**PR scope:** Single PR. CLAUDE.md normally suggests splitting refactor + features, but the user has explicitly opted for one bundled PR (blocking other work). Note this in the PR description.

---

## Pre-flight

### Task 0: Verify branch state

**Files:** none

**Step 1: Confirm clean working tree on the right branch**

```bash
git status
git branch --show-current
```

Expected: working tree clean, on `skill-roadmap-refuse-main` (the branch the design + pushback resolutions were committed to). If on `main`, stop and check out the working branch.

**Step 2: Confirm design doc is committed and readable**

```bash
ls docs/plans/2026-05-02-roadmap-resume-checklists-design.md
git log --oneline -3
```

Expected: file exists; HEAD shows the two pushback-resolution commits stacked on the design commit.

---

## RED Phase: Baseline pressure scenarios

The point of these is to capture *verbatim* what the current skill produces under interruption pressure, so the GREEN phase has a concrete failure to fix and the REFACTOR phase has a concrete rationalization vocabulary to plug.

### Task 1: Run baseline pressure scenarios against the current skill

**Files:**
- Create: `notes/roadmap-resume-baselines.md` (working notes, not committed long-term)

**Scenarios (run via Task() subagent dispatch, one per scenario):**

**Scenario A — Mid-pushback `/clear`:**
> "You're an agent partway through `/roadmap` step 6 (Pushback Review). Pushback raised three findings; the user has resolved finding #1 (`fixed-in-design`) and finding #2 (`dismissed-invalid`), and you're discussing finding #3. The user types `/clear`. Now they reinvoke `/roadmap`. Walk me through what you do, in order, and what you tell the user. Use the current SKILL.md at `.claude/skills/roadmap/SKILL.md`."

Expected baseline failure: agent has no way to know about the prior findings or where in step 6 it left off. It will likely either re-run the whole skill from step 1 or hallucinate a recovery path.

**Scenario B — Skip checklist update under time pressure:**
> "You're an agent executing `/roadmap`. You've just finished step 4 (brainstorming) and the design doc is written. The user says: 'Quick, what's next? I want to ship this before the meeting.' Walk me through what you do."

Expected baseline failure: no checklist exists today, so this scenario is mostly a control. The point is to verify the agent doesn't invent a checklist on its own — it should proceed straight to step 5.

**Scenario C — Subagent errors mid-pushback:**
> "You're an agent in `/roadmap` step 6. You invoke `paad:pushback`. It raises two findings, then errors before you can tell whether the findings list is complete. You retry once per the existing failure-handling section; the retry also fails. The user steps away. They come back tomorrow and reinvoke `/roadmap`. What do you do?"

Expected baseline failure: agent has no record of the partial findings or that pushback was invoked. The "mentally tracked" warning in the existing SKILL.md is exactly the gap.

**Step 1: Dispatch the three scenarios in parallel**

Use the Task tool, `subagent_type: general-purpose`. Each subagent should:
- Read `.claude/skills/roadmap/SKILL.md` first
- Receive the scenario prose verbatim
- Report: what they would do, in order, and what the user would see

**Step 2: Capture the verbatim outputs**

Append each subagent's output (or summary if too long) to `notes/roadmap-resume-baselines.md` under a `## Scenario X` heading. Note the specific rationalizations they used.

**Step 3: Identify the rationalizations to plug**

Read back the three captures and list each distinct rationalization (e.g., "I'll just re-run pushback from scratch, the user will tell me which findings are still open"). This list seeds the rationalization table additions in the REFACTOR phase.

**Step 4: Commit the baseline notes**

```bash
git add notes/roadmap-resume-baselines.md
git commit -m "RED: capture baseline failures of /roadmap under interruption"
```

(The `notes/` directory is untracked-by-convention working area; check `.gitignore`. If `notes/` is gitignored, just leave the file uncommitted as a working artifact and skip the commit.)

---

## GREEN Phase: Migration + SKILL.md edits

Five commits, each a logical chunk. Apply in order.

### Task 2: Migrate to `docs/roadmap/` layout

**Files:**
- Create: `docs/roadmap/` (directory)
- Move: `docs/roadmap.md` → `docs/roadmap/roadmap.md`
- Move: `docs/plans/` → `docs/roadmap/plans/`

**Step 1: Verify pre-conditions**

```bash
ls docs/roadmap.md docs/plans/
ls docs/roadmap/ 2>/dev/null  # should not exist yet
```

Expected: the source paths exist; the destination doesn't.

**Step 2: Create the destination skeleton**

```bash
mkdir -p docs/roadmap
```

(The `archive/` and `decisions/` subdirs are created lazily — only when first used.)

**Step 3: Run the moves**

```bash
git mv docs/roadmap.md docs/roadmap/roadmap.md
git mv docs/plans docs/roadmap/plans
```

**Step 4: Verify post-conditions**

```bash
git status
ls docs/roadmap/roadmap.md docs/roadmap/plans/
ls docs/plans 2>/dev/null  # should not exist
```

Expected: git status shows two renames; new locations populated; old locations gone.

**Step 5: Verify the design + plan files moved correctly**

```bash
ls docs/roadmap/plans/2026-05-02-roadmap-resume-checklists-design.md
ls docs/roadmap/plans/2026-05-02-roadmap-resume-checklists-plan.md
```

(This plan file moves with everything else.)

**Step 5b: Verify `<!-- plan: ... -->` comments still resolve**

The design (§1) asserts that the `<!-- plan: foo.md -->` comments in `roadmap.md` use bare filenames and keep resolving correctly under the new location. Verify it:

```bash
grep -oE '<!-- plan: [^ ]+ -->' docs/roadmap/roadmap.md \
  | sed -E 's/<!-- plan: (.+) -->/\1/' \
  | while read filename; do
      test -f "docs/roadmap/plans/$filename" \
        && echo "OK: $filename" \
        || echo "MISSING: $filename"
    done
```

Expected: every line begins with `OK:`. Any `MISSING:` line means a comment in the roadmap points at a file that doesn't exist — fix the comment (or write the missing design doc) before continuing. This same verification logic is what the in-skill auto-migrate (§3) should mirror for other projects, so the bash above is also the reference implementation.

**Step 6: Commit**

```bash
git commit -m "Restructure: move docs/roadmap.md and docs/plans/ under docs/roadmap/"
```

### Task 3: Update path references in SKILL.md

**Files:**
- Modify: `.claude/skills/roadmap/SKILL.md`

**Step 1: Find all occurrences**

```bash
grep -n 'docs/roadmap\.md\|docs/plans/\|docs/roadmap-decisions/' .claude/skills/roadmap/SKILL.md
```

Expected: ~5–10 matches across the file (the §Read the Roadmap step, §Step 5 prose, §Decision Log Entry Schema, etc.).

**Step 2: Apply edits**

For each match, replace per this map:

| Old | New |
|---|---|
| `docs/roadmap.md` | `docs/roadmap/roadmap.md` |
| `docs/plans/` | `docs/roadmap/plans/` |
| `docs/roadmap-decisions/` | `docs/roadmap/decisions/` |

Use the Edit tool. Some occurrences are inside example code blocks — apply the same rewrite there.

**Step 3: Re-grep to verify zero matches remain**

```bash
grep -n 'docs/roadmap\.md\|docs/plans/\|docs/roadmap-decisions/' .claude/skills/roadmap/SKILL.md
```

Expected: zero matches (or only in comments documenting the *old* layout, which we'd need to flag separately).

**Step 4: Commit**

```bash
git add .claude/skills/roadmap/SKILL.md
git commit -m "/roadmap: point at docs/roadmap/ layout"
```

### Task 4: Add the checklist schema + obligations sections

**Files:**
- Modify: `.claude/skills/roadmap/SKILL.md` — add a new top-level section `## Per-Phase Checklist File` near the top (between `## Start` and the existing `## 1. Read the Roadmap`).

**Step 1: Draft the section**

The section content: copy the schema, field rules, sub-checkbox rules, and "Checklist update obligations" + rationalization table from §2 and §5 of the design doc. Use it verbatim — the design IS the spec for this prose.

Structure:
```
## Per-Phase Checklist File

[short overview paragraph: what it is, where it lives, when it's updated]

### Filename
[from design §2]

### Schema
[verbatim YAML + markdown example from design §2]

### Field rules
[verbatim from design §2]

### Update obligations
[from design §5: "every step ends with..."]

### Rationalization table
[from design §5]

### Verification before ticking
[from design §5]

### Brainstorming non-resumability
[from design §5]
```

**Step 2: Insert the section**

Use the Edit tool to insert after the `## Start` block and before the existing `## 1. Read the Roadmap` heading.

**Step 3: Sanity-check by re-reading the inserted block**

```bash
sed -n '/^## Per-Phase Checklist File$/,/^## /p' .claude/skills/roadmap/SKILL.md
```

(Or just Read the file and inspect.)

Expected: the whole new section is present, formatted correctly, with the schema example unmodified.

**Step 4: Commit**

```bash
git add .claude/skills/roadmap/SKILL.md
git commit -m "/roadmap: add checklist file schema and update obligations"
```

### Task 5: Add Step 0 (resume detection + auto-migration)

**Files:**
- Modify: `.claude/skills/roadmap/SKILL.md` — insert a new `## 0. Resume Detection` section before the existing `## 1. Read the Roadmap`.

**Step 1: Draft the section content**

Copy from §3 of the design:
- Opening paragraph ("a new step that runs before everything else")
- The graphviz digraph (verbatim)
- "Layout migration (first thing step 0 checks)" prose + the prompt block
- "Scan scope" sentence
- "Branch verification" table
- "Multiple candidates" paragraph
- "Stale-checklist threshold" paragraph
- "Jumping to the right step" + the two-mode recovery list for steps 6/9

**Step 2: Insert the section**

Insert between `## Per-Phase Checklist File` (added in Task 4) and `## 1. Read the Roadmap`.

**Step 3: Update the top-of-file announce line**

The existing skill begins with `Announce: **"Checking roadmap for next unplanned phase…"**`. Step 0 changes the entry behavior. Update to:

```
Announce: **"Checking for in-progress runs and roadmap layout…"**
```

This goes before Step 0 fires.

**Step 4: Verify by re-reading the new section**

Read the file; confirm the digraph renders as a code block (triple backticks + `dot` language tag), all sub-headings are present, and the section ordering is: Start → Per-Phase Checklist File → 0. Resume Detection → 1. Read the Roadmap.

**Step 5: Commit**

```bash
git add .claude/skills/roadmap/SKILL.md
git commit -m "/roadmap: add Step 0 (resume detection + auto-migration)"
```

### Task 5.5: Modify Step 2a to create the checklist file

This is the load-bearing wire-up: without it, every other checklist task is inert (no file to update, scan, or resume).

**Files:**
- Modify: `.claude/skills/roadmap/SKILL.md` — Step 2a section.

**Step 1: Locate the insertion point**

Step 2a's existing flow ends with `git checkout -b '<name>'` succeeding. The checklist-creation prose goes immediately after that success path, before the skill proceeds to step 3.

**Step 2: Append a "Create the run checklist" sub-section to Step 2a**

Insert prose along these lines (use the schema from §Per-Phase Checklist File added in Task 4 as the canonical reference; this section just specifies *when* to write the file):

> #### Create the run checklist
>
> After `git checkout -b` succeeds, write a new checklist file to:
>
> ```
> docs/roadmap/plans/<YYYY-MM-DD>-<phase-slug>-checklist.md
> ```
>
> where `<YYYY-MM-DD>` is today's date and `<phase-slug>` is the slug derived from the phase title (per the §Per-Phase Checklist File filename rule — same rule used for the branch name above; reuse the slug, do not re-derive).
>
> Populate the frontmatter:
>
> ```yaml
> ---
> phase: "<full Phase N: Title text from the roadmap heading>"
> phase_slug: <phase-slug>
> branch: <branch name created above>
> roadmap: docs/roadmap/roadmap.md
> started: <YYYY-MM-DD>
> last_updated: <YYYY-MM-DD>
> design_file: null
> plan_file: null
> decision_log: null
> ---
> ```
>
> Initialize the body with:
> - The H1: `# <full phase title> — Run Checklist`
> - The `## Steps` block (all 11 step boxes including the `6a` and `9a` sub-checkboxes), with steps **1, 2, and 2a pre-checked** (the work to reach this point is done).
> - Empty `## Pushback Findings` and `## Alignment Findings` sections, each with the placeholder line `(populated during step N, transcribed by step 10)`.

**Step 3: Verify by re-reading Step 2a**

Confirm the creation procedure appears after the `git checkout -b` success path and before any reference to step 3.

**Step 4: Commit**

```bash
git add .claude/skills/roadmap/SKILL.md
git commit -m "/roadmap: create the run checklist file at step 2a"
```

### Task 6: Wire checklist updates into Steps 1–5, 7, 8, 11

**Files:**
- Modify: `.claude/skills/roadmap/SKILL.md` — append a checklist-update directive at the end of each of these steps' prose.

**Step 1: For each of steps 1, 2, 3, 4, 5, 7, 8, 11, add the appropriate update directive at the end of the step's section**

Map (from design §6):

| Step | Directive to append |
|---|---|
| 1 | "Tick `- [x] 1. Read roadmap` and bump `last_updated`." |
| 2 | "Tick `- [x] 2. Identified next unplanned phase` and bump `last_updated`. *Note:* if step 2 detects 'every phase has a `<!-- plan: ... -->` comment,' do NOT tick — instead invoke the archive lifecycle (Task 8 / §4 of the design) before continuing." |
| 3 | "Tick `- [x] 3. Extract phase context` and bump `last_updated`." |
| 4 | "After the design doc is written, **verify it exists and is non-empty** (`test -s <path>`); if either check fails, surface to the user and stop. Then set `design_file: <path>` in the checklist frontmatter and tick `- [x] 4. Brainstorm → design saved`." |
| 5 | "After updating roadmap.md, tick `- [x] 5. Record plan filename in roadmap` and bump `last_updated`." |
| 7 | "Tick `- [x] 7. CLAUDE.md review` after the discussion concludes, regardless of whether CLAUDE.md was edited." |
| 8 | "After the plan doc is written, **verify it exists and is non-empty** (`test -s <path>`); if either check fails, surface to the user and stop. Then set `plan_file: <path>` in the checklist frontmatter and tick `- [x] 8. Write implementation plan`." |
| 11 | "After announce, tick `- [x] 11. Announce completion`. The checklist is now fully ticked and serves as the historical record of the run." |

**Note:** Step 2a is handled separately by Task 5.5 (it creates the checklist; the linear tick-after-step pattern doesn't apply).

**Step 2: Apply the edits**

Use the Edit tool, one edit per step.

**Step 3: Verify**

Read each modified step section; confirm the directive is present at the end.

**Step 4: Commit**

```bash
git add .claude/skills/roadmap/SKILL.md
git commit -m "/roadmap: wire checklist updates into linear steps"
```

### Task 7: Update Steps 6, 9, 10 (sub-checkbox semantics + transcription)

**Files:**
- Modify: `.claude/skills/roadmap/SKILL.md` — Steps 6, 9, 10 sections.

**Step 1: Step 6 (Pushback)**

Replace the existing "Instrumentation for the decision log" sub-section with the prose from design §6 step 6:

> Replace "mentally track each issue" with: for each issue pushback raises, append a finding entry to the checklist's `## Pushback Findings` section with `Severity`, `Category`, `Summary` (one paragraph written *now* while the context is fresh — this is the prose step 10 will copy verbatim), `Status: open`, and `Resolution: _(pending)_`. When the pushback subagent returns cleanly, tick `6a. Pushback returned all findings`. When discussion closes a finding, flip `Status: closed` and write the resolution using the closed vocabulary. Tick top-level step 6 only when **both** 6a is checked AND every finding has `Status: closed`.

Keep the existing "Failure handling" sub-section. Add to it: "If pushback fails on retry, leave the (possibly partial) findings in `## Pushback Findings` as-is. The 6a sub-checkbox stays unchecked, which signals a future resume to wipe the section and re-invoke pushback per §3 (resume detection)."

**Step 2: Step 9 (Alignment)**

Same pattern as step 6, against `## Alignment Findings` and `9a. Alignment returned all findings`.

**Step 3: Step 10 (Decision log)**

Update the prose to read:

> Transcribe `## Pushback Findings` and `## Alignment Findings` from the checklist into the decision log file. Transcription is a literal copy of every finding minus the `Status:` line (decision log entries are always closed by definition). Severity counts in the decision log frontmatter come from counting the checklist's findings — single source of truth eliminates the "mentally tracked counts don't sum" reconciliation hazard the prior version of this skill warned about. After the decision log is written, **verify it exists and is non-empty** (`test -s <path>`); if either check fails, surface to the user and stop. Then set `decision_log: <path>` in the checklist frontmatter and tick step 10.

Keep the "stop and reconcile" guidance from the existing decision-log frontmatter section (severity counts must sum to total) — but reword to apply against checklist counts, not in-head counts.

**Step 4: Verify each step section reads coherently**

Read steps 6, 9, 10 end-to-end. Make sure the new directives are consistent with the §Per-Phase Checklist File schema added in Task 4.

**Step 5: Commit**

```bash
git add .claude/skills/roadmap/SKILL.md
git commit -m "/roadmap: sub-checkbox semantics for pushback/alignment + literal transcription at step 10"
```

### Task 8: Add archive lifecycle (replace Step 2's "all phases brainstormed" no-op)

**Files:**
- Modify: `.claude/skills/roadmap/SKILL.md` — Step 2 prose, plus a new sub-section.

**Step 1: Locate the existing no-op**

Step 2 currently says:
> If **all** phases have plan comments, announce:
> > **All roadmap phases have been brainstormed.** Nothing to do.
> …and stop.

**Step 2: Replace with the archive prompt flow**

Insert from design §4:

> If **all** phases have plan comments, the roadmap is fully planned. Surface the archive prompt:
>
> > All phases of this roadmap have been planned. Archive to `docs/roadmap/archive/<slug>/` and start fresh? `yes` / `no` / `later`
>
> Parse the response (case-insensitive, leniently as the §2a accept-grammar):
>
> - **`yes`** — derive `<slug>` from the roadmap.md H1 title using the existing slug rule. Run `git mv` to move every entry under `docs/roadmap/` (excluding `archive/` itself) into `docs/roadmap/archive/<slug>/`. Then write a fresh stub `docs/roadmap/roadmap.md` (a minimal H1 + empty Phase Structure table — the user fills it in). Announce: "Archived to `docs/roadmap/archive/<slug>/`. Start a new roadmap by editing `docs/roadmap/roadmap.md`." Stop.
> - **`no`** — write a marker file `docs/roadmap/.archive-declined` containing the SHA-1 of the H1 title. On future runs, if the marker file exists and matches the current H1 hash, skip the archive prompt entirely. Announce the no-op and stop.
> - **`later`** — leave everything in place; do not write a marker. Announce the no-op and stop.

**Step 3: Add the §0 / resume detection cross-reference**

In §0's "Layout migration" sub-section, add a sentence: "Once layout migration succeeds and resume detection finds no in-progress checklist, fall through to step 1 → step 2; the archive prompt fires from step 2 if applicable."

**Step 4: Verify**

Read step 2's section. Confirm the archive prompt text matches the design and the parser logic is concrete enough to implement (yes / no / later with the marker-file behavior on no).

**Step 5: Commit**

```bash
git add .claude/skills/roadmap/SKILL.md
git commit -m "/roadmap: archive-on-all-planned lifecycle"
```

---

## GREEN Verification

### Task 9: Re-run baseline scenarios against the updated skill

**Files:**
- Append to `notes/roadmap-resume-baselines.md` (or its committed equivalent)

**Step 1: Re-dispatch the three scenarios from Task 1 against the *new* SKILL.md**

Same prompts, same subagent type. Each subagent reads the *current* `.claude/skills/roadmap/SKILL.md` (which now includes the checklist machinery).

**Step 2: For each scenario, document expected vs actual**

| Scenario | Expected with new skill |
|---|---|
| A — Mid-pushback `/clear` | Step 0 detects the in-progress checklist; finds 6a checked + open finding #3; resumes discussion of finding #3 only. Findings #1 and #2 stay closed with their resolutions visible. |
| B — Skip checklist update under time pressure | Agent updates the checklist before announcing/proceeding to step 5; cites the rationalization table if it tries to skip. |
| C — Subagent errors mid-pushback | Step 0 detects the in-progress checklist; sees 6a unchecked; wipes `## Pushback Findings` and re-invokes pushback. Does not silently resume from partial findings. |

**Step 3: If any scenario still fails, capture the new rationalization for REFACTOR.**

**Step 4: If all pass, commit the verification notes**

```bash
git add notes/roadmap-resume-baselines.md
git commit -m "GREEN: verify /roadmap recovery under the same baseline scenarios"
```

(Skip the commit if `notes/` is gitignored.)

---

## REFACTOR Phase

### Task 10: Extend the rationalization table from new failure modes

**Files:**
- Modify: `.claude/skills/roadmap/SKILL.md` — the `## Per-Phase Checklist File` → `### Rationalization table` sub-section.

**Step 1: For each NEW rationalization captured in Task 9, add a row**

Format matches the existing table:

```
| "<verbatim excuse the agent used>" | <terse reality check, mirroring the §5 examples> |
```

**Step 2: If Task 9 found zero new rationalizations, skip this task**

Note in the commit message that the rationalization table was sufficient as-shipped.

**Step 3: Re-run only the scenarios that produced new rationalizations**

Verify the additions plug the holes.

**Step 4: Commit**

```bash
git add .claude/skills/roadmap/SKILL.md
git commit -m "/roadmap: extend rationalization table from REFACTOR-cycle findings"
```

(Skip if no changes.)

### Task 11: End-to-end coherence pass

**Files:**
- Read-only: `.claude/skills/roadmap/SKILL.md`

**Step 1: Read the full updated SKILL.md top to bottom**

Check for:
- The new sections appear in this order: Start → Per-Phase Checklist File → 0. Resume Detection → 1. Read the Roadmap → … → 11. Announce Completion → Appendix.
- No surviving references to the old `docs/plans/` or `docs/roadmap.md` paths (re-run the grep from Task 3).
- The Status / Resolution vocabularies in the checklist schema match the decision log appendix exactly.
- The flowchart in Step 0 renders (triple-backtick `dot` block, balanced braces).
- The cross-reference in Step 8 (archive lifecycle) → Step 0 (layout migration) is present.

**Step 2: If issues found, fix them in a single follow-up commit**

Don't refactor for style; only fix actual breakage.

**Step 3: Optionally render the flowchart**

```bash
# from the writing-skills directory
~/.claude/plugins/cache/superpowers-marketplace/superpowers/4.0.0/skills/writing-skills/render-graphs.js .claude/skills/roadmap
```

Inspect the SVG to confirm the digraph is well-formed. Skip if the script isn't available.

**Step 4: No commit needed unless fixes were applied.**

---

## Wrap-up

### Task 12: Open the PR

**Files:** none

**Step 1: Push the branch**

```bash
git push -u origin skill-roadmap-refuse-main
```

**Step 2: Open the PR**

```bash
gh pr create --title "Roadmap resume checklists + docs/roadmap/ restructure" --body "..."
```

PR body MUST mention:
- The single-PR override is deliberate (blocks other work; explicit user decision)
- Summary of the 5 design issues resolved during pushback (link to the design doc)
- The migration is reversible via `git mv` if needed
- The Step 0 layout-migration prompt means other projects on the legacy layout get a one-time migration prompt the next time they invoke `/roadmap` (not silently broken)

**Step 3: Verify the PR diff matches expectations**

```bash
gh pr diff
```

Spot-check that the SKILL.md changes match the design and that the file moves are tracked as renames.

---

## Done

After Task 12, the implementation is complete. Suggested follow-ups (not in scope of this PR):

- Run `/roadmap` against Phase 2 of `docs/roadmap/roadmap.md` (agentic-architecture references) using the new flow as the first real-world test.
- Consider promoting `/roadmap` into `plugins/paad/skills/roadmap/` so the paad plugin distributes it (would require adding the announce line, digraph, version bump).
