# PR1 Implementation Plan — Extract Spec Compliance specialist to `references/`

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move the Spec Compliance specialist's ~30-line additional-instructions block out of `plugins/paad/skills/agentic-review/SKILL.md` into `references/specialists/spec-compliance.md`, dispatched on demand. Establish the structural guardrail (`scripts/extracted-refs.tsv`, `scripts/check_extracted_refs.sh`, `make check-extracted-refs`) that all subsequent extractions reuse. Verify behavior is preserved against a known-history fixture commit.

**Architecture:** Parent `SKILL.md` keeps a thin Spec Compliance entry in the specialist table; the dispatch prompt instructs the subagent to read `references/specialists/spec-compliance.md` for its full instructions. Structural guardrail (manifest TSV + check script + Makefile target) catches accidental regressions across this and future extractions. Behavioral test = run `/paad:agentic-review` against a fixture commit and verify the Spec Compliance section of the report matches a written behavioral checklist.

**Tech Stack:** bash, awk, GNU make, the existing paad plugin layout (`plugins/paad/skills/agentic-review/`), git for fixture checkout, `/paad:agentic-review` itself for behavioral verification.

**Branching:** All work lands as commits on the current branch `ovid/skill-breakdown` per `notes/convert-skills.md` working-branch decision. No per-task feature branches.

**Source-of-truth design:** `docs/plans/2026-05-01-agentic-review-references-pilot-design.md`. This plan is the bite-sized task list for the first extraction (PR1 in the design's eight-extraction roadmap).

---

## Pre-flight check before starting

Confirm `git status` is clean and `git branch --show-current` returns `ovid/skill-breakdown`. If either fails, stop and surface to the user.

---

### Task 1: Pick fixture commit(s)

This is research only — no code changes, no commit. Goal: identify ≥1 commit on this repo's history that, when reviewed by `/paad:agentic-review`, would exercise Spec Compliance behaviors. Ideally find both:

- **Behaviors fixture** — a commit where Spec Compliance produces *something* (a Missing finding, a Deviation, an out-of-scope addition with the `category: out-of-scope-addition` tag, or a retro-edited-spec contradiction).
- **Bail-out fixture** — a commit with no inferable intent source (no PR description, no plan doc, no descriptive commit message), so Spec Compliance outputs `Spec compliance: skipped — no intent source identified`.

**Files:**
- Modify: `notes/convert-skills.md` — fill in "### Fixtures used" subsection under the "Fixture strategy" heading.

**Step 1: Survey candidate commits**

Run:
```bash
git log --oneline --all | head -80
```

Look for commits whose subject mentions agentic-review or skills, with a non-trivial diff. Recent agentic-review work (e.g., `83aa677` "agentic-review: plug Phase 2/3 contract gaps") is a strong candidate for the behaviors fixture because it's a real change against the published agentic-review design doc (`docs/plans/2026-04-26-agentic-review-scope-design.md`), so an intent source exists for the specialist to compare against.

**Step 2: Narrow to two candidates**

For each candidate, run:
```bash
git show --stat <SHA>
gh pr view <PR-number> --json title,body 2>/dev/null || echo "no PR for this commit"
```

Pick:
- Behaviors fixture: a commit with a real intent source (PR description, plan doc, or rich commit body) AND non-trivial code changes.
- Bail-out fixture: a small typo-fix or one-liner commit with no PR and no descriptive body.

**Step 3: Record fixtures in notes/convert-skills.md**

Edit `notes/convert-skills.md`. Under the existing `### Fixtures used` heading, replace the placeholder line with:

```markdown
### Fixtures used

- **PR1 behaviors fixture:** `<SHA>` — `<one-line subject>`. Intent
  source: `<PR description / plan doc path / commit body>`. Expected
  Spec Compliance behaviors: `<list, e.g. Missing finding for X,
  out-of-scope addition for Y>`.
- **PR1 bail-out fixture:** `<SHA>` — `<one-line subject>`. No intent
  source. Expected Spec Compliance behavior: skipped output.
```

**Step 4: Commit notes update**

```bash
git add notes/convert-skills.md
git commit -m "$(cat <<'EOF'
notes: record PR1 fixture commits for Spec Compliance extraction

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Capture baseline behavior

For each fixture, run `/paad:agentic-review` with the *current* (inline-instructions) skill, save the Spec Compliance section of the report, and write a behavioral checklist describing what we expect to preserve after extraction.

**Files:**
- Create: `notes/baselines/PR1-spec-compliance-behaviors.md`
- Create: `notes/baselines/PR1-spec-compliance-bailout.md`
- Create: `notes/baselines/PR1-spec-compliance-checklist.md`

**Step 1: Create the baselines directory**

```bash
mkdir -p notes/baselines
```

**Step 2: Run agentic-review against the behaviors fixture**

The fixture commit lives on this repo's history but the working branch is `ovid/skill-breakdown`. Don't check it out destructively. Use a temporary branch:

```bash
git checkout -b pr1-fixture-behaviors <SHA-from-Task-1>
```

Then in a Claude Code session in this repo, invoke `/paad:agentic-review`. Wait for it to complete and write its report under `paad/code-reviews/`. Confirm the report exists.

**Step 3: Capture the Spec Compliance section verbatim**

The report won't be structured by specialist (the verifier merges all findings). Instead, identify which findings were *Found by: Spec Compliance* and copy them — plus any "Spec compliance: skipped" line if present — into `notes/baselines/PR1-spec-compliance-behaviors.md` along with the report path.

Template:
```markdown
# PR1 Baseline — Spec Compliance behaviors fixture

Fixture commit: <SHA>
Report file: paad/code-reviews/<filename>.md
Captured: <date> with paad v1.14.0 (current inline-instructions version).

## Findings attributed to Spec Compliance

(verbatim copy of every entry whose `Found by:` line names Spec Compliance)
```

**Step 4: Run agentic-review against the bail-out fixture**

Switch to the bail-out fixture:

```bash
git checkout -B pr1-fixture-bailout <SHA-of-bailout-fixture>
```

Run `/paad:agentic-review`. Confirm the Spec Compliance section says "skipped" or contains no findings attributed to Spec Compliance.

**Step 5: Capture the bail-out baseline**

Create `notes/baselines/PR1-spec-compliance-bailout.md` with the same template, recording the skipped-or-empty behavior.

**Step 6: Write the behavioral checklist**

Create `notes/baselines/PR1-spec-compliance-checklist.md`. This is what we'll re-verify after extraction. Use this template:

```markdown
# PR1 Spec Compliance behavioral checklist

After extraction, re-running /paad:agentic-review against the same
fixtures must produce output that satisfies every item below. If any
item fails after the green step, the extraction is broken.

## Behaviors fixture (<SHA>)

- [ ] Spec Compliance attributes at least one finding (or report
      explicitly notes Spec Compliance ran without findings — verify
      against baseline).
- [ ] (Behavior 1, e.g.) "out-of-scope addition" with
      `category: out-of-scope-addition` tag routed to
      `## Out-of-Scope Additions` section.
- [ ] (Behavior 2, e.g.) Missing finding pointing at concrete artifact
      named in the spec.
- [ ] (Behavior 3, e.g.) intent source listed in Review Metadata
      matches the source listed in the baseline.
- [ ] No "Implemented" / "Not yet implemented" lists in the report (the
      specialist drops these per its instructions).

## Bail-out fixture (<SHA>)

- [ ] Spec Compliance produces no findings attributed to it, OR
      Review Metadata includes "Spec Compliance skipped — no intent
      source identified".
```

Fill in the parenthesized "(Behavior N)" items based on what actually appeared in `notes/baselines/PR1-spec-compliance-behaviors.md` — they are not generic, they're the specific findings the inline version produced on this fixture.

**Step 7: Return to the working branch and clean up**

```bash
git checkout ovid/skill-breakdown
git branch -D pr1-fixture-behaviors pr1-fixture-bailout
```

**Step 8: Commit baselines**

```bash
git add notes/baselines/
git commit -m "$(cat <<'EOF'
notes: capture PR1 Spec Compliance baselines and behavioral checklist

Baseline behavior recorded against fixtures <SHA1> (intent source
present) and <SHA2> (bail-out). The behavioral checklist is the
acceptance criteria for the extraction in PR1.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Build structural guardrail infrastructure

Set up the manifest TSV, the check script, and wire it into `make test`. The manifest starts empty (header only). With no rows, the check passes trivially — this is the "infrastructure-only" commit.

**Files:**
- Create: `scripts/extracted-refs.tsv`
- Create: `scripts/check_extracted_refs.sh`
- Modify: `Makefile` — add `check-extracted-refs` target, wire into `test` dependency list.

**Step 1: Create the manifest with a header only**

Create `scripts/extracted-refs.tsv` with this content (header line is a comment, no data rows yet):

```
# skill	ref-path-relative-to-skill	sentinel-phrase
```

The columns are tab-separated. `#` lines are comments. Data rows are added in Task 4.

**Step 2: Create the check script**

Create `scripts/check_extracted_refs.sh` with the following content (executable):

```bash
#!/usr/bin/env bash
# Verify each row in scripts/extracted-refs.tsv represents a correctly
# extracted reference: ref file exists, sentinel moved out of SKILL.md
# into the ref file, and SKILL.md dispatch references the ref path.
set -euo pipefail

MANIFEST="scripts/extracted-refs.tsv"
SKILLS_ROOT="plugins/paad/skills"

if [ ! -f "$MANIFEST" ]; then
    echo "FAIL: manifest not found at $MANIFEST"
    exit 1
fi

fail=0
row=0
while IFS=$'\t' read -r skill ref_path sentinel; do
    # skip blanks and comments
    case "$skill" in
        ''|'#'*) continue ;;
    esac
    row=$((row + 1))
    skill_md="$SKILLS_ROOT/$skill/SKILL.md"
    ref_file="$SKILLS_ROOT/$skill/$ref_path"

    if [ ! -f "$skill_md" ]; then
        echo "FAIL [row $row, $skill]: SKILL.md not found at $skill_md"
        fail=1
        continue
    fi
    if [ ! -f "$ref_file" ]; then
        echo "FAIL [row $row, $skill]: ref file not found at $ref_file"
        fail=1
        continue
    fi
    if grep -qF -- "$sentinel" "$skill_md"; then
        echo "FAIL [row $row, $skill]: sentinel still present in SKILL.md ('$sentinel')"
        fail=1
    fi
    if ! grep -qF -- "$sentinel" "$ref_file"; then
        echo "FAIL [row $row, $skill]: sentinel missing from ref file ('$sentinel')"
        fail=1
    fi
    if ! grep -qF -- "$ref_path" "$skill_md"; then
        echo "FAIL [row $row, $skill]: ref path '$ref_path' not referenced anywhere in SKILL.md"
        fail=1
    fi
done < "$MANIFEST"

if [ "$fail" -eq 1 ]; then
    exit 1
fi

echo "All $row extracted reference(s) verified."
```

Make it executable:

```bash
chmod +x scripts/check_extracted_refs.sh
```

**Step 3: Add the Makefile target**

Open `Makefile`. Find the `.PHONY` line and the `test:` target.

Append `check-extracted-refs` to the `.PHONY` declaration:

```makefile
.PHONY: help test validate check-versions check-skill-versions check-digraphs check-help check-readme check-frontmatter check-extracted-refs bump-version
```

Append `check-extracted-refs` to the `test:` target's dependency list (after `check-frontmatter`):

```makefile
test: validate check-versions check-skill-versions check-digraphs check-help check-readme check-frontmatter check-extracted-refs ## Run all checks
	@echo "All checks passed."
```

Add the new target definition near the other `check-*` targets:

```makefile
check-extracted-refs: ## Check every row in scripts/extracted-refs.tsv represents a correctly extracted reference
	@bash scripts/check_extracted_refs.sh
```

**Step 4: Run `make test` to confirm green**

```bash
make test
```

Expected: passes. The `All 0 extracted reference(s) verified.` message confirms the new check ran (zero rows, but the script executed).

**Step 5: Commit infrastructure**

```bash
git add scripts/extracted-refs.tsv scripts/check_extracted_refs.sh Makefile
git commit -m "$(cat <<'EOF'
build: add extracted-refs structural guardrail (manifest + check + make target)

Adds the manifest at scripts/extracted-refs.tsv and the verification
script at scripts/check_extracted_refs.sh, wired into 'make test' as
'check-extracted-refs'. Manifest starts empty; subsequent commits add
one row per extraction.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Extract Spec Compliance to `references/`

This is the actual extraction. Inside this task we run a structural-red → green → behavioral-green sequence; only the final state lands as a commit.

**Files:**
- Create: `plugins/paad/skills/agentic-review/references/specialists/spec-compliance.md`
- Modify: `plugins/paad/skills/agentic-review/SKILL.md` — remove the Spec Compliance additional-instructions block (currently lines 169-200), add a one-line dispatch reference in its place.
- Modify: `scripts/extracted-refs.tsv` — add the Spec Compliance row.

**Step 1: Add the manifest row (structural red)**

Edit `scripts/extracted-refs.tsv`. Append this tab-separated line:

```
agentic-review	references/specialists/spec-compliance.md	Internal spec contradictions (retro-edited specs)
```

**Step 2: Run `make test` and confirm it FAILS**

```bash
make test
```

Expected output includes:
```
FAIL [row 1, agentic-review]: ref file not found at plugins/paad/skills/agentic-review/references/specialists/spec-compliance.md
```

This confirms the structural test discriminates. If it passes, stop and investigate — the manifest row isn't being read correctly.

**Step 3: Create the references file**

Create the directory:

```bash
mkdir -p plugins/paad/skills/agentic-review/references/specialists
```

Create `plugins/paad/skills/agentic-review/references/specialists/spec-compliance.md`. Copy the content from the current `SKILL.md` lines 169-200 verbatim, but reformat the leading `**Spec Compliance additional instructions:**` declaration into a top-level `# Spec Compliance — additional instructions` heading:

```markdown
# Spec Compliance — additional instructions

> **Read this file before producing findings.** You are the Spec Compliance specialist dispatched by `/paad:agentic-review` Phase 2. Your standing instructions in the parent `SKILL.md` cover the inputs you receive and the basic finding-report format. This file covers the Spec Compliance lens specifically.

Establish intent first. Identify the source of intent in priority order:
1. Explicit spec file passed via `$ARGUMENTS`.
2. PR description (via `gh pr view --json title,body` if the branch has an open PR).
3. Plan/design docs found in Phase 1 reconnaissance (`docs/plans/`, `aidlc-docs/`, etc.).
4. Recent commit messages on the branch since base.
5. Branch name.

Use the most specific source available. Prefer recent and specific (PR description > plan doc > commits > branch name). When sources contradict, name the contradiction.

Produce findings in exactly three categories:
1. **Missing** — spec called for X, diff doesn't deliver X. Format as a regular finding (`file:line`, severity Critical/Important/Suggestion). The verifier routes these through the in-scope severity ladder.
2. **Deviation** — diff implements X but contradicts the spec (different shape, opposite behavior, wrong invariant, missing default). Same format and routing.
3. **Out-of-scope addition** — diff adds substantive new code the spec did not promise. Tag the finding with `category: out-of-scope-addition` so the verifier routes it to the report's Out-of-Scope Additions section. Do not decide whether the addition is justified ("while I'm here" fix) or scope creep — flag and let the user decide.

Two failure modes worth special attention:

(a) **Missing artifacts.** When the spec names a concrete code artifact — a constant in a `STRINGS` or similar named table, a type, an exported function, a route, a config key, a string literal, a file — verify the artifact appears in the diff. Grep the diff for the named symbol; if absent or referenced but never defined/added, flag as Missing. Classic example: spec writes "use `STRINGS.error.somekey`" but no `somekey` is added to the strings table.

(b) **Internal spec contradictions (retro-edited specs).** Specs sometimes get edited to ratify implementation choices, leaving residual contradictions between the spec's algorithm/code block (recently edited to match code) and its surrounding prose, named invariants, or string tables (older, describing original intent). When the algorithm block describes behavior X but the prose, "Key invariants," or named strings/types describe behavior Y, treat that contradiction as a deviation from original intent. Surface both readings to the user — let them decide which is canonical.

Do not report:
- "Implemented" lists (the diff IS the implementation).
- "Not yet implemented" multi-PR pending items (partial implementation across PRs is expected).

Scale rigor to diff size (from Phase 1's classification):
- Small (<50 lines): one-line summary unless something is wrong. Default: "Spec compliance: clean."
- Medium (50–500 lines): full deviation analysis; expect 0–3 findings.
- Large (500+ lines): full deviation analysis; expect 0–8 findings, partition focus by feature area.

Bail out cleanly when no intent can be inferred. If no source yields a clear statement of what this PR was supposed to do, output "Spec compliance: skipped — no intent source identified" and stop. Do not invent intent from the diff itself.
```

**Step 4: Remove the inline block from SKILL.md and add the dispatch reference**

In `plugins/paad/skills/agentic-review/SKILL.md`, replace the block from `**Spec Compliance additional instructions:**` (currently around line 169) through the end of the bail-out paragraph (currently around line 200) with this one-paragraph dispatch reference:

```markdown
**Spec Compliance additional instructions:** Before producing findings, the Spec Compliance specialist reads `references/specialists/spec-compliance.md` (relative to this skill's directory). That file covers intent-source priority, the three finding categories (Missing / Deviation / Out-of-scope addition with `category: out-of-scope-addition` tag routing), the two attention-grade failure modes (missing artifacts, retro-edited spec contradictions), drop rules, diff-size scaling, and the no-intent-source bail-out. The dispatch prompt for the Spec Compliance specialist must include the instruction: "Read `references/specialists/spec-compliance.md` from this skill's directory before producing findings; treat its instructions as binding."
```

**Step 5: Run `make test` and confirm it now PASSES**

```bash
make test
```

Expected: all checks pass, including `All 1 extracted reference(s) verified.`

If it fails, debug:
- "ref file not found" → check the file was created at the right path.
- "sentinel still present in SKILL.md" → the inline block wasn't fully removed; grep `SKILL.md` for "Internal spec contradictions" and remove the residual.
- "sentinel missing from ref file" → the content didn't make it into the ref file verbatim; check copy-paste.
- "ref path not referenced in SKILL.md" → the dispatch paragraph doesn't include the literal string `references/specialists/spec-compliance.md`; add it.

**Step 6: Commit the extraction**

Commit the structural-green state (manifest row + ref file + SKILL.md dispatch update) before behavioral verification. Behavioral verification needs Task 3 and Task 4 commits to exist as named SHAs we can cherry-pick.

```bash
git add scripts/extracted-refs.tsv plugins/paad/skills/agentic-review/SKILL.md plugins/paad/skills/agentic-review/references/specialists/spec-compliance.md
git commit -m "$(cat <<'EOF'
agentic-review: extract Spec Compliance specialist to references/

The Spec Compliance specialist's ~30-line additional-instructions block
moved out of SKILL.md into references/specialists/spec-compliance.md;
the parent dispatch instructs the subagent to read the ref before
producing findings. Manifest row added; structural guardrail green.

Behavioral verification follows in the next commits via the
fixture-parent-as-base procedure documented in the PR1 plan.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

Capture the SHA for use in Steps 7-9:

```bash
TASK4_SHA=$(git rev-parse HEAD)
TASK3_SHA=$(git rev-parse HEAD~1)
```

(`HEAD~1` is correct because Task 3 was the previous commit on this branch.)

**Step 7: Behavioral verification — set up the behaviors fixture verification branches**

The mechanism: build a *verify-base* branch that has the fixture's parent + our infrastructure + our extraction, then a *verify-fixture* branch that adds the fixture commit on top. Running `/paad:agentic-review verify-base` from the verify-fixture branch makes the diff under review = only the fixture's changes, with our extracted skill active in the working tree.

Replace `<behaviors-fixture-SHA>` with the SHA from Task 1.

```bash
# Create verify-base: fixture's parent + our infrastructure + our extraction
git checkout -B pr1-verify-behaviors-base <behaviors-fixture-SHA>^
git cherry-pick "$TASK3_SHA" "$TASK4_SHA"

# Create verify-fixture: verify-base + the fixture commit
git checkout -B pr1-verify-behaviors
git cherry-pick <behaviors-fixture-SHA>
```

If any cherry-pick conflicts, stop and surface to the user. The conflict shouldn't normally happen — Task 3 and Task 4 touch files orthogonal to most fixture commits — but if the fixture commit itself touches `agentic-review/SKILL.md` there will be overlap and we need to resolve carefully (the fixture's changes to SKILL.md must survive on top of our extracted layout).

**Step 8: Run agentic-review against the behaviors fixture**

In a Claude Code session opened with `claude --plugin-dir ./plugins/paad` (so the working-tree skill is loaded, not the cached install), invoke:

```
/paad:agentic-review pr1-verify-behaviors-base
```

Passing `pr1-verify-behaviors-base` as `$ARGUMENTS` makes that the review base. The diff under review is just the fixture commit's changes. Wait for the run to complete and write its report under `paad/code-reviews/`.

Open the report and verify each item in the *Behaviors fixture* section of `notes/baselines/PR1-spec-compliance-checklist.md` is satisfied. Pay particular attention to:

- Findings attributed to Spec Compliance match (in kind and roughly in count) the baseline captured in Task 2.
- Any out-of-scope addition appears in `## Out-of-Scope Additions` with the correct routing (the `category: out-of-scope-addition` tag did its work).
- Review Metadata's `Intent sources consulted:` line names the same source the baseline named.

**Step 9: Run agentic-review against the bail-out fixture**

Replace `<bailout-fixture-SHA>` with the bail-out SHA from Task 1.

```bash
git checkout -B pr1-verify-bailout-base <bailout-fixture-SHA>^
git cherry-pick "$TASK3_SHA" "$TASK4_SHA"
git checkout -B pr1-verify-bailout
git cherry-pick <bailout-fixture-SHA>
```

Then in Claude Code (`--plugin-dir ./plugins/paad`):

```
/paad:agentic-review pr1-verify-bailout-base
```

Verify the bail-out checklist item is satisfied: Spec Compliance produces no findings attributed to it, OR Review Metadata includes "Spec Compliance skipped — no intent source identified".

**Step 10: Return to the working branch and clean up**

```bash
git checkout ovid/skill-breakdown
git branch -D pr1-verify-behaviors-base pr1-verify-behaviors pr1-verify-bailout-base pr1-verify-bailout
```

If verification failed at Step 8 or 9, surface to the user with: which fixture, which checklist items missed, and the offending output. Do **not** proceed to Task 5 until all items are green. The Task 4 extraction commit stays on `ovid/skill-breakdown` regardless — debugging happens by amending or follow-up commits, not by reverting.

---

### Task 5: Lock conventions, refactor, bump version

The extraction is functionally green. This task records the verified subagent-path-resolution mechanism in `notes/convert-skills.md`, tightens the dispatch prompt if possible, and bumps the plugin version.

**Files:**
- Modify: `notes/convert-skills.md` — fill in the "Subagent path resolution" answer and add a "Conventions established" entry.
- Optionally: `plugins/paad/skills/agentic-review/SKILL.md` — tighten the dispatch paragraph (if the verification revealed scaffolding the ref now duplicates).
- Modify: `plugins/paad/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, every `SKILL.md` (via `make bump-version`).

**Step 1: Update path-resolution answer in notes**

Open `notes/convert-skills.md`. Replace the `## Subagent path resolution — open question for pilot` section's "Possibilities (1)/(2)/(3)" closing paragraph with the verified answer based on Task 4 Step 8/9 observations. Examples:

- If the subagent successfully read the relative path: "**Verified mechanism: relative paths from SKILL.md root work for subagents.** The dispatch prompt instructs the subagent to read `references/specialists/spec-compliance.md` and the subagent resolves it correctly."
- If it required absolute path: "**Verified mechanism: parent must resolve to absolute path.** The dispatch prompt computed the absolute path via `<mechanism>` and embedded it in the subagent's prompt."

**Step 2: Add convention entry**

Under `## Conventions established by the pilot` in `notes/convert-skills.md`, append:

```markdown
### Dispatch prompt template (PR1)

Established by PR1 (Spec Compliance). Subsequent extractions copy this
shape verbatim, swapping the lens name and ref path:

> **<Lens> additional instructions:** Before producing findings, the
> <Lens> specialist reads `references/specialists/<lens>.md` (relative
> to this skill's directory). The dispatch prompt must include:
> "Read `references/specialists/<lens>.md` from this skill's directory
> before producing findings; treat its instructions as binding."

The reference file itself starts with a `# <Lens> — additional
instructions` heading and a brief role-statement quote.
```

**Step 3: Tighten dispatch prompt if helpful**

Re-read the dispatch paragraph in `SKILL.md`. If any phrasing is duplicated between SKILL.md and the ref file, prefer the ref. Edit and re-run `make test` (must stay green).

**Step 4: Bump version**

Current version is 1.14.0. PR1 is a feature change (refactor with behavior preservation), so bump minor:

```bash
make bump-version VERSION=1.15.0
```

This updates `plugin.json`, `marketplace.json`, and the announce line in every `SKILL.md`.

**Step 5: Run full test suite**

```bash
make test
```

Expected: all checks pass, including `check-extracted-refs`.

**Step 6: Commit**

```bash
git add notes/convert-skills.md plugins/paad/skills/agentic-review/SKILL.md plugins/paad/.claude-plugin/plugin.json .claude-plugin/marketplace.json plugins/paad/skills/
git commit -m "$(cat <<'EOF'
agentic-review: lock PR1 conventions and bump to 1.15.0

Records verified subagent path-resolution mechanism in
notes/convert-skills.md and the dispatch-prompt template that
PRs 2-8 reuse. Plugin version bumped to 1.15.0.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Done criteria for PR1

All of the following hold simultaneously:

- `make test` is green on `ovid/skill-breakdown`.
- `notes/baselines/PR1-spec-compliance-checklist.md` items are all checked off (verified during Task 4 Step 8/9).
- `notes/convert-skills.md` "Subagent path resolution" section is no longer open — the verified mechanism is recorded.
- `plugins/paad/.claude-plugin/plugin.json` reads `1.15.0`.
- `git log --oneline ovid/skill-breakdown` shows the four commits in order:
  1. `notes: record PR1 fixture commits...`
  2. `notes: capture PR1 Spec Compliance baselines...`
  3. `build: add extracted-refs structural guardrail...`
  4. `agentic-review: extract Spec Compliance specialist...`
  5. `agentic-review: lock PR1 conventions and bump to 1.15.0`

PRs 2–6 (other specialists) reuse this plan as a template, swapping the lens name and ref path. PR7 (verifier) and PR8 (report template) get their own plans because they target different dispatch sites.
