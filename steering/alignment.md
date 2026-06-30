---
inclusion: manual
---

# Alignment Check

Verifies that intent documents (requirements, specs, PRDs) and action documents (plans, tasks, implementation steps) are aligned. Finds gaps in both directions — unaddressed requirements and out-of-scope tasks — then rewrites all tasks in TDD red/green/refactor format.

**This skill does NOT recommend a fresh session.** The conversation history may contain the documents.

```dot
digraph alignment {
  "Has $ARGUMENTS?" [shape=diamond];
  "Conversation has docs?" [shape=diamond];
  "Found in common locations?" [shape=diamond];
  "Both sides found?" [shape=diamond];
  "Git repo?" [shape=diamond];
  "Source control conflicts?" [shape=diamond];

  "Classify files as intent/action" [shape=box];
  "Confirm with user" [shape=box];
  "Present candidates, ask user" [shape=box];
  "STOP: tell user what's missing" [shape=box, style=bold];
  "Skip Reality Check" [shape=box];
  "Present conflicts, resolve first" [shape=box];
  "Proceed to Alignment Analysis" [shape=box];

  "Has $ARGUMENTS?" -> "Classify files as intent/action" [label="yes"];
  "Has $ARGUMENTS?" -> "Conversation has docs?" [label="no"];
  "Conversation has docs?" -> "Confirm with user" [label="yes"];
  "Conversation has docs?" -> "Found in common locations?" [label="no"];
  "Found in common locations?" -> "Present candidates, ask user" [label="yes"];
  "Found in common locations?" -> "STOP: tell user what's missing" [label="no"];

  "Classify files as intent/action" -> "Both sides found?";
  "Confirm with user" -> "Both sides found?";
  "Present candidates, ask user" -> "Both sides found?";

  "Both sides found?" -> "Git repo?" [label="yes"];
  "Both sides found?" -> "STOP: tell user what's missing" [label="no"];

  "Git repo?" -> "Source control conflicts?" [label="yes"];
  "Git repo?" -> "Proceed to Alignment Analysis" [label="no"];
  "Source control conflicts?" -> "Present conflicts, resolve first" [label="yes"];
  "Source control conflicts?" -> "Proceed to Alignment Analysis" [label="no"];
  "Present conflicts, resolve first" -> "Proceed to Alignment Analysis";
}
```

## Phase 1: Reality Check (Source Control)

**Skip this phase if the project is not a git repository.**

Before analyzing document alignment, check whether recent codebase changes conflict with what the documents assume:

1. Run `git log --oneline -50 --since="2 weeks ago"` (whichever limit is reached first)
2. Read commit messages and, for relevant-looking commits, check the actual diffs
3. Compare against what the documents assume — do they reference code, APIs, schemas, infrastructure, or patterns that have recently been changed, removed, or replaced?
4. **If conflicts found:** present them upfront before any other analysis. For each conflict:
   - What the documents assume
   - What actually changed (commit SHA, date, summary)
   - Why this matters for alignment
   - Ask: "How do you want to handle this?" with options
5. **If no conflicts found:** say "No conflicts with recent changes" and move on

## Phase 2: Alignment Analysis

Perform three checks against the classified documents:

### 1. Requirements coverage

For every item in the intent documents, check whether at least one action item addresses it.

- Flag requirements with no corresponding tasks
- Flag requirements only partially covered (e.g., happy path has a task but error handling doesn't)
- Note which requirements are well-covered

### 2. Scope compliance

For every item in the action documents, check whether it traces back to a stated requirement.

- Flag tasks that don't map to any requirement (scope creep or gold-plating)
- Flag tasks that seem to address implied but unstated requirements (may be legitimate — ask)
- Note tasks that are clearly in scope

### 3. Design alignment (only if intermediate design docs exist)

Check both directions:
- Does the design address all requirements?
- Do the tasks implement the design, or do they bypass it?
- Flag design decisions that aren't reflected in tasks
- Flag tasks that contradict or ignore the design

## Phase 3: Issue Presentation

Present issues **dependency-ordered** so that fixing upstream problems first may resolve downstream ones:

1. **Missing or unclear requirements** first (root causes) — a missing requirement explains why there's no task for it and no design for it
2. **Design gaps** second (if design docs exist) — a design gap may explain why tasks are missing or wrong
3. **Missing, orphaned, or out-of-scope tasks** last (symptoms) — these often resolve when upstream issues are fixed

### For each issue

- State the specific documents and sections that are misaligned
- Explain the nature of the misalignment (missing coverage, out of scope, design gap)
- Assign severity: **Critical** / **Important** / **Minor**
- Present concrete options from best to worst, with recommendation
- Wait for the user's response before presenting the next issue

The user can say "good enough" or "stop" at any point.

### Analysis guidance

- **Read the codebase.** Don't just compare documents — check whether what they describe matches the actual code.
- **Understand intent.** A requirement that says "user authentication" and a task that says "implement login flow" are aligned even if the wording differs. Match on meaning, not keywords.
- **Respect intentional omissions.** If a requirement is explicitly marked as out of scope or future work, don't flag missing tasks for it.
- **Flag implicit requirements.** If a task requires infrastructure or capabilities not mentioned in requirements (e.g., tasks assume a message queue but requirements never mention async processing), flag the gap.

## Phase 4: Resolution

After all issues are addressed (or user says "good enough"):

### Step 1: Update documents

Ask: **"Would you like me to update the documents to reflect our alignment decisions, or write a separate alignment report?"**

**If updating documents:**
- Apply agreed changes to the original files
- Add missing requirements, remove out-of-scope tasks, fill design gaps
- Don't touch items that weren't discussed

**If writing a report:**
Write to `.reviews/alignment/<YYYY-MM-DD>-<topic>-alignment.md`.

Create the `.reviews/alignment/` directory if it doesn't exist.

**Report template:**

```markdown
# Alignment Review: <topic or project name>

**Date:** YYYY-MM-DD
**Commit:** <current HEAD sha, or "N/A">

## Documents Reviewed

- **Intent:** <file paths or "conversation history">
- **Action:** <file paths or "conversation history">
- **Design:** <file paths, or "none">

## Source Control Conflicts

<conflicts found, or "None — no conflicts with recent changes.">

## Issues Reviewed

### [1] <title>
- **Category:** <missing coverage / out of scope / design gap>
- **Severity:** <critical / important / minor>
- **Documents:** <which documents are misaligned>
- **Issue:** <what's wrong>
- **Resolution:** <what the user decided>

(Repeat for each issue discussed.)

## Unresolved Issues

(Issues not yet discussed. Omit section if all were addressed.)

## Alignment Summary

- **Requirements:** N total, M covered, K gaps
- **Tasks:** N total, M in scope, K orphaned
- **Design items:** N total, M aligned (if applicable)
- **Status:** <aligned / needs further work>
```

**If documents came from conversation history:**
Ask: "The documents aren't saved to files yet. Where should I write them?" Suggest a reasonable path based on project structure.

### Step 2: TDD task rewrite (when applicable)

Once alignment is confirmed, check whether tasks should be rewritten in red/green/refactor format. **Skip this step if:**

- Tasks are already in red/green/refactor format
- Tasks don't involve code implementation (e.g., infrastructure provisioning, documentation, design work, data migrations, manual processes)

If neither condition applies, rewrite action items in red/green/refactor format — it produces better implementations.

**Why this works:**

- **RED — Write a failing test first.** Defines expected behavior before writing code. Occasionally the test passes immediately, revealing that the feature already exists or that assumptions are wrong. More commonly, the test fails in unexpected ways that highlight unknown issues in the codebase. Both outcomes are valuable information you'd otherwise miss.

- **GREEN — Write minimal code to pass.** Forces simpler solutions. The AI looks at the problem more directly instead of over-engineering. Less speculative code means less "slop."

- **REFACTOR — Clean up what you just wrote.** This is the step AI almost never does unless explicitly told to. It catches duplicated code that should be extracted, hard-coded values that belong in config, inconsistent patterns that should be consolidated, and other small issues that compound over time.

**Format for each task:**

```markdown

### Task: <task name>

**Requirement:** <which requirement this addresses>

#### RED
- Write a test that: <what the test asserts>
- Expected failure: <how and why it should fail>
- If it passes unexpectedly: <what that would mean>

#### GREEN
- Implement: <minimal implementation to pass the test>
- Constraints: keep it simple — no anticipatory abstractions

#### REFACTOR
- Look for: <specific refactoring opportunities>
  - Duplicated logic to extract
  - Hard-coded values to move to config
  - Patterns to consolidate with existing code
  - Naming improvements
```

Rewrite the tasks in the action document in-place, or write to a new file if the user prefers.
