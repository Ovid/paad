# Report Template — additional instructions

> **Read this file before writing the alignment report.** This is parent-side material for `/alignment` — the orchestrator (the agent that activated this skill) reads these instructions when it has been asked to write a separate alignment report. The report template below is binding for that deliverable.

**Report template:**

```markdown
# Alignment Review: <topic or project name>

* **Date:** YYYY-MM-DD
* **Model:** <the model you are running as — from your environment; "unknown" if unavailable>
* **PAAD version:** <plugin version from your on-invocation announce line>
* **Commit:** <current HEAD sha, or "N/A">

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
