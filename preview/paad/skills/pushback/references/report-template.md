# Report Template — additional instructions

> **Read this file before writing the pushback report.** This is parent-side material for `/pushback` — the orchestrator (the agent that activated this skill) reads these instructions when it has been asked to write a separate pushback report. The report template below is binding for that deliverable.

**Report template:**

```markdown
# Pushback Review: <spec name or filename>

* **Date:** YYYY-MM-DD
* **Model:** <the model you are running as — from your environment; "unknown" if unavailable>
* **PAAD version:** <plugin version from your on-invocation announce line>
* **Spec:** <file path or "conversation history">
* **Commit:** <current HEAD sha, or "N/A">

## Source Control Conflicts

<conflicts found, or "None — no conflicts with recent changes.">

## Warrant

**Upstream document:** <path or description, or "none — traced against this document's own stated goals">

| # | Requirement (quoted) | Traces to (quoted upstream line) | Verdict | Owner |
|---|---|---|---|---|

**Counts:** traced N / derived K / amplified M / untraced J

<How the raised rows were resolved, or "every requirement traces to the upstream document".>

## Simplifications

Over-engineering found in the simplicity pass and what replaced it.

| # | Location | Cut this | Use this instead | Ruling | Revisit when |
|---|----------|----------|------------------|--------|--------------|

**Proposed N / accepted M / rejected K / deferred J — net: −X requirements**

Rejected rows carry the user's reason in their own terms; deferred rows carry the
trigger that brings them back. Keep this section across rounds rather than
rewriting it: a spec that is offered eight cuts a round and accepts one is
ratcheting upward, which is invisible across three conversations and obvious in
one table.

<or "None — solution fits the problem.">

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
- **Requirements that do not trace to the upstream document:** N untraced, M amplified — of those raised: cut N, narrowed M, deferred K, kept J
- **Requirements with no named owner:** N
- **Simplification cuts proposed / accepted:** N / M
- **Unresolved:** N - M   <!-- omit this line entirely when nothing is unresolved -->
- **Status:** <one or two sentences: what has to happen before implementation
  starts, and what can ride along. Not a verdict word.>
```
