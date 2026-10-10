# Report Template — additional instructions

> **Read this file before writing the accessibility audit report.** This is parent-side material for `/agentic-a11y` Phase 4. The orchestrator (the agent that activated this skill) reads these instructions when entering the report-writing phase — there is no subagent dispatch for this phase. The report template below is binding for the Phase 4 deliverable.

**Report template:**

```markdown
# Accessibility Audit: <project-name>

* **Date:** YYYY-MM-DD HH:MM:SS
* **Model:** <the model you are running as — from your environment; "unknown" if unavailable>
* **PAAD version:** <plugin version from your on-invocation announce line>
* **Commit:** <full-sha>
* **Platform(s):** <detected platforms>
* **Tech stack:** <frameworks, libraries, engines>
* **Files audited:** N
* **Existing a11y tooling:** <list or "none found">
* **Conformance target:** WCAG 2.2 AA via WCAG2ICT (AAA noted as recommendations)
* **Platform guidelines referenced:** <e.g., Apple HIG Accessibility, Material Design Accessibility, Xbox Accessibility Guidelines, or "N/A">

## Executive Summary

2-3 sentences: overall accessibility posture, highest-severity findings, estimated conformance level (A / partial AA / AA / partial AAA).

## Impact Summary by User Group

Brief summary of how the codebase affects each group:
- **Screen reader users:** <1-2 sentences>
- **Low-vision users:** <1-2 sentences>
- **Colorblind users:** <1-2 sentences>
- **Motor-impaired users (keyboard/switch/sip-and-puff):** <1-2 sentences>
- **Cognitive and learning disabilities:** <1-2 sentences>
- **Deaf and hard-of-hearing users:** <1-2 sentences>
- **Vestibular and photosensitive users:** <1-2 sentences>

## Critical Issues (Complete Barriers)

### [C1] <title>
- **File:** `path/to/file:line`
- **Platform:** <which platform this applies to>
- **Barrier:** What's wrong
- **Criterion:** <WCAG criterion or platform guideline> — Level <A/AA>
- **Affects:** Who is blocked and how
- **Fix:** Concrete code-level recommendation
- **Confidence:** High/Medium
- **Found by:** <specialist name(s)>

(Repeat for each critical issue, or "None found.")

## Serious Issues (Major Difficulty)

(Same structure as Critical, or "None found.")

## Moderate Issues (Friction)

(Same structure, or "None found.")

## Minor Issues & AAA Recommendations

One-line entries with criterion reference. Omit section if none.
Mark AAA items with [AAA] prefix.

## Conformance Checklist

For each WCAG principle, list criteria checked and their status. For non-web platforms, criteria are interpreted via WCAG2ICT. Mark criteria that do not apply to the detected platform as "N/A" with brief explanation.

### Perceivable
| Criterion | Level | Status | Finding |
|-----------|-------|--------|---------|
| 1.1.1 Non-text Content | A | Pass / Fail / Partial / N/A / Not assessed | #ID or — |
(continue for all Perceivable criteria assessed)

### Operable
(same table format)

### Understandable
(same table format)

### Robust
(same table format)

### Platform-Specific Guidelines
| Guideline | Status | Finding |
|-----------|--------|---------|
| <e.g., Apple HIG: Dynamic Type> | Pass / Fail / Partial | #ID or — |
(list platform-specific guidelines checked beyond WCAG, or omit section if web-only)

## Quick Wins

Top 5 fixes that would have the largest positive impact for the least effort. Each entry: what to fix, which findings it addresses, estimated effort (small/medium/large).

## Audit Metadata

- **Agents dispatched:** <list with focus areas>
- **Platform(s) detected:** <list>
- **Scope:** <files audited>
- **Raw findings:** N (before verification)
- **Verified findings:** M (after verification)
- **Filtered out:** N - M
- **By severity:** X critical, Y serious, Z moderate, W minor
- **By conformance level:** X Level A, Y Level AA, Z Level AAA
- **Steering files consulted:** <list or "none found">
- **Existing a11y tooling:** <list or "none found">
```
