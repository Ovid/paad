# Report template — parent-side instructions

> This is parent-side material for `paad:agentic-architecture` (Phase 4 report writing). Unlike specialist refs, no subagent reads this — the orchestrator reads it itself when entering Phase 4. The orchestrator handles output path computation and `mkdir -p paad/architecture-reviews/`; this file is the binding template for what to write into that file.

## Verbatim from SKILL.md

```markdown
# Architecture Report — <repo-name or current folder>

**Date:** YYYY-MM-DD
**Commit:** <full-sha> (append the literal token ` [working tree dirty]` if `git status --porcelain` was non-empty at run-time; do **not** embed the porcelain output, file paths, or per-file status — those are pending changes the user did not ask to publish)
**Languages:** <primary languages/frameworks>
**Key directories:** <list>
**Scope:** <full repo or specific paths>

## Repo Overview

Brief description of the codebase: what it does, how it's structured, approximate size.

## Strengths

Ranked by impact (High/Medium/Low), 5–15 items:

### [S-ID] <Strength label>
- **Category:** <S1-S14 category name>
- **Impact:** High / Medium / Low
- **Explanation:** 1-2 sentences
- **Evidence:** `path:line-range` (`symbol`), excerpt: "short excerpt"
- **Found by:** <specialist name(s)>

## Flaws/Risks

Ranked by impact (High/Medium/Low), 10–25 items:

### [F-ID] <Flaw label>
- **Category:** <flaw type 1-34 name>
- **Impact:** High / Medium / Low
- **Explanation:** 1-2 sentences
- **Evidence:** `path:line-range` (`symbol`), excerpt: "short excerpt"
- **Found by:** <specialist name(s)>

## Coverage Checklist

### Flaw/Risk Types 1–34
| # | Type | Status | Finding |
|---|------|--------|---------|
| 1 | Global mutable state | Observed / Not observed / Not assessed | #F-ID or — |
(continue for all 34)

### Strength Categories S1–S14
| # | Category | Status | Finding |
|---|----------|--------|---------|
| S1 | Clear modular boundaries | Observed / Not observed / Not assessed / Not applicable | #S-ID or — |
(continue for all 14)

## Hotspots

Top 3 files/directories to review:
1. `path/` — brief why (can include risk hotspots and strong core hotspots)
2. ...
3. ...

## Next Questions

Up to 5 questions to guide follow-up investigation. Questions only — no suggested solutions.

## Analysis Metadata

- **Agents dispatched:** <list with focus areas>
- **Scope:** <files analyzed>
- **Raw findings:** N (before verification)
- **Verified findings:** M (after verification)
- **Filtered out:** N - M
- **By impact:** X high, Y medium, Z low
- **Steering files consulted:** <list or "none found">
```
