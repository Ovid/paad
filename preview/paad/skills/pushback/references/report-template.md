# Report Template — additional instructions

> **Read this file before writing the pushback report.** This is parent-side material for `/pushback` — the orchestrator (the agent that activated this skill) reads these instructions when it has been asked to write a separate pushback report. The report template below is binding for that deliverable.

**Report template:**

```markdown
# Pushback Review: <spec name or filename>

* **Date:** YYYY-MM-DD
* **Spec:** <file path or "conversation history">
* **Commit:** <current HEAD sha, or "N/A">

## Source Control Conflicts

<conflicts found, or "None — no conflicts with recent changes.">

## Issues Reviewed

### [1] <title>
- **Category:** <contradictions / feasibility / scope imbalance / omissions / ambiguity / security>
- **Severity:** <critical / serious / moderate / minor>
- **Issue:** <what's wrong>
- **Resolution:** <what the user decided>

(Repeat for each issue discussed.)

## Unresolved Issues

Issues not yet discussed (user stopped early). Listed for future reference.

### [N] <title>
- **Category:** ...
- **Severity:** ...
- **Issue:** ...
- **Suggested options:** ...

(Omit section if all issues were addressed.)

## Summary

- **Issues found:** N (plus K candidates dropped for lacking a defensible consequence)
- **Unresolved:** N - M   <!-- omit this line entirely when nothing is unresolved -->
- **Status:** <one or two sentences: what has to happen before implementation
  starts, and what can ride along. Not a verdict word.>
```
