# Report Template — additional instructions

> **Read this file before writing the Phase 5 report.** This is parent-side material for `/agentic-dedup` — the orchestrator (the agent that activated this skill) reads these instructions when entering the report-writing phase. The report template below is binding for the Phase 5 deliverable.

When interpolating specialist text into the template below, fence or
inline-escape any free-form agent output. Specialist findings can
contain backtick fences, HTML comments (`<!-- -->`), pipe characters,
or angle-bracketed pseudo-tags that would otherwise break the report's
Markdown structure. Either wrap the offending block in a fenced code
block (` ```text … ``` `) or replace internal triple-backticks with
quadruple-backtick fences. Do **not** paste agent output unmodified
into table cells.

```markdown
# Semantic Duplicate Code Hunt: <branch-or-scope>

* **Date:** YYYY-MM-DD HH:MM:SS
* **Model:** <the model you are running as — from your environment; "unknown" if unavailable>
* **PAAD version:** <plugin version from your on-invocation announce line>
* **Repository:** <repo root>
* **Scope:** <paths/modules/changed files/domain>
* **Commit:** <full-sha or "working tree">
* **Mode:** full scan / changed-code scan / type-constraint scan / domain scan

## Executive Summary

2-4 sentences summarizing the most important duplication risks, confidence level, and whether consolidation is recommended now or later.

## Findings by Severity

### Critical Issues

#### [C1] <canonical concept duplicated>
- **Canonical concept:** <plain-language rule/operation>
- **Duplicate locations:**
  - `path/to/file:line` — <symbol/name>
  - `path/to/file:line` — <symbol/name>
- **Why these are semantically duplicate:** <behavioral equivalence>
- **Important differences:** <differences, if any>
- **Impact:** <bug/divergence/security/compliance risk>
- **Suggested consolidation:** <specific refactoring or contract strategy>
- **Confidence:** High/Medium
- **Found by:** <specialist name(s)>

Or: None found.

### Important Issues

Same structure as Critical.

### Suggestions

One-line entries only unless detail is needed.

## Type and Constraint Equivalence Notes

For each verified type/schema/constraint duplicate or near-duplicate:

| Concept | Location A | Location B | Relationship | Risk | Recommendation |
|---------|------------|------------|--------------|------|----------------|
| <concept> | `path:line` | `path:line` | exact / overlap / subset / superset / drift | low/medium/high | <action> |

## Rejected Candidate Duplicates

List high-interest rejected candidates briefly. This section prevents future reviewers from rediscovering the same false positives.

| Candidate | Reason rejected |
|-----------|-----------------|
| `path:line` vs `path:line` | Similar structure but different domain contract |
| `path:line` vs `path:line` | Intentional bounded-context separation |

## Consolidation Strategy

Recommend one of:

- **Extract canonical domain function** — when duplicated logic is pure and shared across modules.
- **Extract policy object** — when duplicated logic represents business policy or authorization.
- **Extract shared schema/type** — when duplicated constraints represent the same data contract.
- **Generate from contract** — when duplication exists across API, DB, and client boundaries.
- **Add contract tests only** — when sharing code would create coupling but behavior must remain aligned.
- **Leave duplicated intentionally** — when similarity is superficial or boundaries are valuable.

Include a safe migration sequence if consolidation is recommended:

1. Add characterization tests covering both current implementations.
2. Document intentional behavior differences.
3. Extract or choose canonical implementation.
4. Migrate one caller at a time.
5. Keep compatibility wrappers if public APIs are involved.
6. Add regression tests for the edge cases that previously differed.

## Review Metadata

- **Agents dispatched:** <list with focus areas>
- **Files scanned:** <count>
- **Candidate pairs/groups discovered:** <count>
- **Verified findings:** <count>
- **Rejected candidates:** <count>
- **Generated/vendor paths excluded:** <list>
- **Steering files consulted:** <list or "none found">
- **Tests consulted:** <list or "none found">
```
