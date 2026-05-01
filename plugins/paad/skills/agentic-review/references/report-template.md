# Report Template — additional instructions

> **Read this file before writing the per-review report or updating the project backlog.** This is parent-side material for `/paad:agentic-review` Phase 4. The orchestrator (the agent that activated this skill) reads these instructions when entering the report-writing phase — there is no subagent dispatch for this phase. The empty-section rules, failure handling, report template, and backlog file shape below are binding for the Phase 4 deliverable.

**Empty-section rules:**

- If there are zero out-of-scope bug findings of any tier, omit the entire `## Out of Scope` section *and* its handoff block. Review Metadata still records `Out-of-scope findings: 0`.
- If there are zero out-of-scope additions, omit the entire `## Out-of-Scope Additions` section *and* its handoff block. Review Metadata still records `Out-of-scope additions: 0`.
- If there are zero in-scope findings of a tier but out-of-scope findings exist, write each empty in-scope tier section as `None found.` (existing convention) and write the Out of Scope section normally.
- When the Spec Compliance specialist's output begins with the `BAIL: spec-compliance` token (matched tolerantly per the verifier's "Specialist status detection" section), set `Intent sources consulted: none — Spec Compliance skipped` in metadata. No specialist can produce additions in this case (only Spec Compliance emits the OOSA signal, and it didn't run), so the `## Out-of-Scope Additions` section is empty; omit it.

**Failure handling:**

- If writing `paad/code-reviews/backlog.md` fails for any reason (permissions, disk, malformed existing file), surface the error to the user and write the per-review report anyway. The report is the authoritative deliverable; the backlog is a convenience layer.

**Report template:**

```markdown
# Agentic Code Review: <branch-name>

**Date:** YYYY-MM-DD HH:MM:SS
**Branch:** <branch> -> <base>
**Commit:** <full-sha>
**Files changed:** N | **Lines changed:** +X / -Y
**Diff size category:** Small / Medium / Large

## Executive Summary

2-3 sentences: overall assessment, highest-severity finding if any, general confidence level.

## Critical Issues

### [C1] <title>
- **File:** `path/to/file:line`
- **Bug:** What's wrong
- **Impact:** Why it matters
- **Suggested fix:** Concrete recommendation
- **Confidence:** High/Medium
- **Found by:** <specialist> (`<model>`)

(Repeat for each critical issue, or "None found.")

## Important Issues

(Same structure as Critical, or "None found.")

## Suggestions

One-line entries only. If empty, follow the Empty-section rules above.

## Out of Scope

> **Handoff instructions for any agent processing this report:** The findings below are
> pre-existing bugs that this branch did not cause or worsen. Do **not** assume they
> should be fixed on this branch, and do **not** assume they should be skipped.
> Instead, present them to the user **batched by tier**: one ask for all out-of-scope
> Critical findings, one ask for all Important, one for Suggestions. For each tier, the
> user decides which (if any) to address. When you fix an out-of-scope finding, remove
> its entry from `paad/code-reviews/backlog.md` by ID.

### Out-of-Scope Critical
#### [OOSC1] <title> — backlog id: `<id>`
- **File:** `path/to/file:line`
- **Bug:** What's wrong
- **Impact:** Why it matters
- **Suggested fix:** Concrete recommendation
- **Confidence:** High/Medium
- **Found by:** <specialist> (`<model>`)
- **Backlog status:** new | re-seen (first logged YYYY-MM-DD)

(Repeat for each, or "None found.")

### Out-of-Scope Important
(Same shape — IDs OOSI1, OOSI2, ...)

### Out-of-Scope Suggestions
(One-line entries; each carries a backlog id — IDs OOSS1, OOSS2, ...)

## Out-of-Scope Additions

> **Handoff instructions for any agent processing this report:** The entries below are code this branch added that the spec did not promise. They may be legitimate "while I'm here" fixes for issues exposed by this work, or scope creep that should live in a separate PR. Do **not** assume they should stay on this branch, and do **not** assume they should be reverted. Present them to the user **as a single batched ask**: "These M additions weren't promised by the spec — keep, split into a separate PR, or revert?" The user decides per item.
>
> Out-of-scope additions are flagged for this PR only — they do not persist to `paad/code-reviews/backlog.md`.

### [OOSA1] <title>
- **File:** `path/to/file:line`
- **Addition:** What was added that the spec did not promise
- **Suggested intent source:** What the agent treated as the spec (PR description / plan doc / commits / branch name)
- **Confidence:** High/Medium
- **Found by:** Spec Compliance (`<model>`)

(Repeat for each, or "None found.")

## Review Metadata

- **Agents dispatched:** <list with focus areas>
- **Scope:** <files reviewed — changed + adjacent>
- **Raw findings:** N (before verification)
- **Verified findings:** M (after verification)
- **Filtered out:** N - M
- **Out-of-scope findings:** N (Critical: a, Important: b, Suggestion: c)
- **Out-of-scope additions:** K
- **Backlog:** X new entries added, Y re-confirmed (see `paad/code-reviews/backlog.md`)
- **Steering files consulted:** <list or "none found">
- **Intent sources consulted:** <e.g., "PR description", "docs/plans/foo-design.md", "recent commit messages", or "none — Spec Compliance skipped">
```

## The Backlog File

`paad/code-reviews/backlog.md` is project-wide, append-only, and uses **explicit removal only** — agentic-review never auto-resolves entries. Created on first run if absent.

**Fixed header (preserved across all updates):**

```markdown
# Out-of-Scope Findings Backlog

> **These items were flagged by `/paad:agentic-review` as out of scope for the branch
> on which they were found.** They may be stale, may already have been fixed by other
> means, may no longer apply after refactors, or may simply have been judged not worth
> addressing. Verify each entry against the current code before acting on it. Entries
> are removed only when explicitly addressed — no automatic cleanup.

---
```

**Per-entry shape:**

```markdown
## `<id>` — <one-line title>
- **File (at first sighting):** `path/to/file:line`
- **Symbol:** `<function or class name, or `<file-scope>` for module-level code>`
- **Bug class:** Logic | Error Handling | Contract | Concurrency | Security | Spec Compliance
- **Description:** ...
- **Suggested fix:** ...
- **Confidence:** High | Medium
- **Found by:** <specialist> (`<model>`)
- **First seen:** YYYY-MM-DD on branch `<branch>` at `<short-sha>`
- **Last seen:** YYYY-MM-DD on branch `<branch>` at `<short-sha>`
- **Severity:** Critical | Important | Suggestion
```

**Update rule on re-discovery:** rewrite only the `Last seen` line. Everything else is immutable so the entry remains a stable historical record.

**Removal rule:** delete the entire `## <id> — <title>` block. No tombstones, no archive.

**ID format:** 8-char hex of `sha1(file + symbol + bug-class + first-seen-iso-date)`.

**Soft size warning:** when the active backlog reaches **≥ 200 active entries**, surface a warning in the post-review message so accumulation stays visible.
