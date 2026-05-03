---
name: vibe
description: Use when making a small fix or quick change (1-3 files, same module) — bug fixes, typos, minor features, tweaks — where you want vibe-coding speed without the recklessness of skipping tests, duplicating existing code, or papering over deeper structural issues
---

**On invocation:** announce "Running paad:vibe v1.19.0" before anything else.

# Safe Vibe Coding

Quick fixes and small changes with guardrails. You get the speed of vibe coding without the recklessness — mandatory TDD, architecture awareness, and reusable component detection.

```dot
digraph vibe {
  "Task clear?" [shape=diamond];
  "Test infrastructure?" [shape=diamond];
  "Scope: how many files?" [shape=diamond];
  "Architecture smell?" [shape=diamond];
  "Reusable components found?" [shape=diamond];
  "RED: test result?" [shape=diamond];

  "Ask or clarify" [shape=box];
  "ASK: set up tests or skip TDD?" [shape=box];
  "WARN: may be bigger than a vibe task" [shape=box];
  "STOP: investigate deeper issues" [shape=box, style=bold];
  "Recommend using existing code" [shape=box];
  "STOP: feature may exist or test is wrong" [shape=box, style=bold];
  "STOP: unexpected failure, discuss" [shape=box, style=bold];
  "Proceed to GREEN" [shape=box];
  "Run pre-flight checks" [shape=box];

  "Task clear?" -> "Run pre-flight checks" [label="yes"];
  "Task clear?" -> "Ask or clarify" [label="no"];
  "Ask or clarify" -> "Task clear?";

  "Run pre-flight checks" -> "Test infrastructure?";
  "Test infrastructure?" -> "Scope: how many files?" [label="yes"];
  "Test infrastructure?" -> "ASK: set up tests or skip TDD?" [label="no"];
  "ASK: set up tests or skip TDD?" -> "Scope: how many files?";

  "Scope: how many files?" -> "Architecture smell?" [label="1-3 files"];
  "Scope: how many files?" -> "WARN: may be bigger than a vibe task" [label="4+ files"];
  "WARN: may be bigger than a vibe task" -> "Architecture smell?";

  "Architecture smell?" -> "STOP: investigate deeper issues" [label="simple task, complex impl"];
  "Architecture smell?" -> "Reusable components found?" [label="no smell"];

  "Reusable components found?" -> "Recommend using existing code" [label="yes"];
  "Reusable components found?" -> "RED: test result?" [label="no"];
  "Recommend using existing code" -> "RED: test result?";

  "RED: test result?" -> "STOP: feature may exist or test is wrong" [label="passes unexpectedly"];
  "RED: test result?" -> "STOP: unexpected failure, discuss" [label="fails unexpectedly"];
  "RED: test result?" -> "Proceed to GREEN" [label="fails as expected"];
}
```

## Step 1: Understand the Task

If no `$ARGUMENTS` provided, ask: "What needs fixing or changing?"

Once you have a task description:

- If the task is unclear, ask **one clarifying question at a time**
- Focus on: what should change, what should stay the same, edge cases
- Don't over-question simple tasks. "Fix the typo in the header" doesn't need a requirements session.

### Test infrastructure

Does this project have a test framework and runner? Look for:
- Test directories (`test/`, `tests/`, `spec/`, `__tests__/`)
- Test config files (`jest.config`, `vitest.config`, `pytest.ini`, `.rspec`, `phpunit.xml`, `Cargo.toml` with `[dev-dependencies]`, etc.)
- Existing test files

**If no test infrastructure exists:** tell the user. Ask: "There's no test setup in this project. Want me to set up a basic test framework first, or proceed without TDD?" If they choose to proceed without TDD, still follow GREEN and REFACTOR steps but skip RED.

### Existing tests in the affected area

Does the code being changed already have tests? If yes, note them — they'll inform your RED step and catch regressions. If no, that's fine but worth noting.

### Scope check

How many files and modules does this change likely touch?

- **1-3 files, same module:** good vibe territory. Proceed.
- **4+ files or crosses module boundaries:** warn the user: "This looks like it touches [N] files across [modules]. It might be bigger than a vibe task. Want to proceed, or would a more structured approach be better?"

### Architecture smell

If the task is conceptually simple (e.g., "only admin users can download finance reports") but investigation reveals it requires a lot of work to implement, **stop**. Investigate whether there are deeper architectural issues making the work harder than it should be. Discuss findings with the user before proceeding.

### Reusable components

If the task involves common functionality — toast notifications, modals, form validation, error handling, data formatting, API calls, permission checks, logging, etc. — **search the codebase first** for:

- Existing components or utilities that already do this
- Partial implementations someone started but didn't finish
- Patterns used elsewhere in the codebase for the same kind of thing

**If found:** tell the user what you found and recommend using/extending the existing code rather than building from scratch.

## Step 3: Implement (Red/Green/Refactor)

This is mandatory. Follow it strictly.

### RED — Write one failing test

Write a single test that defines the expected behavior for the change.

Run it. It should fail. If it doesn't:

- **If the test passes:** stop. The feature or fix may already exist, or your test may not be testing what you think. Tell the user what happened and ask how to proceed.
- **If the test fails in an unexpected way:** stop. The failure mode may reveal an unknown issue. Tell the user what you expected vs what happened and ask how to proceed.

Only proceed to GREEN when the test fails in the expected way.

### GREEN — Write minimal code to pass

Write the simplest code that makes the failing test pass. Resist the urge to:
- Add error handling for cases not covered by the test
- Build abstractions "while you're in there"
- Fix adjacent code that isn't broken
- Add features beyond what was asked

Run the test. It should pass. Run all existing tests in the affected area too — make sure nothing broke.

### REFACTOR — Improve while keeping tests green

Now clean up. This is the step AI skips unless told to, and it's where real quality comes from. Look for:

- **Duplicated logic** that should be extracted into a shared function
- **Hard-coded values** that belong in config or constants
- **Inconsistent patterns** where your new code doesn't match the conventions around it
- **Naming** that could be clearer
- **Dead code** your change made obsolete

Run all tests after refactoring. Everything must stay green.

### Repeat if needed

If the task involves multiple behaviors, repeat the red/green/refactor cycle for each. One test at a time, one behavior at a time.

## Step 4: Post-fix Summary

After the fix is complete, provide a brief summary:

- **What changed:** files modified, lines added/removed
- **Tests added:** the RED tests and what they verify
- **Refactoring done:** what was cleaned up in the REFACTOR step
- **Reusable components:** whether existing components were leveraged or new ones created

### Follow-up suggestions (only when genuinely relevant)

Suggest paad skills when the change warrants it. Don't suggest follow-ups for trivial fixes.

- If the change touched security-sensitive code (auth, permissions, input handling, secrets) → "Consider `` before merging — this touched security-sensitive code."
- If the change touched UI components → "Consider ` src/path/to/changed/files` to check accessibility."
- If the change felt significantly harder than expected → "This was harder than it should have been. Consider `` to investigate whether there are deeper structural issues."
