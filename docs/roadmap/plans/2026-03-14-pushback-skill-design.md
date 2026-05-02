# Design: paad:pushback skill

**Date:** 2026-03-14
**Status:** Implemented

## Purpose

A spec/PRD/requirements critic that pushes back on plans before work begins. Finds contradictions, feasibility issues, scope imbalance, omissions, ambiguity, and security concerns — with source control reality checks.

## Key design decisions

1. **Format-agnostic** — works on any kind of spec document (PRD, user stories, design docs, brainstorm output, plain English), not tied to EARS or any specific format
2. **No fresh-session recommendation** — conversation history may be the spec itself
3. **Source control reality check first** — git history is scanned upfront for conflicts with spec assumptions; showstoppers surface before other analysis
4. **Severity-ordered, one issue at a time** — most impactful first; user can stop when satisfied
5. **Flexible output** — user chooses: update spec in-place or write separate report to `paad/pushback-reviews/`
6. **No flags** — just `/paad:pushback` or `/paad:pushback path/to/file.md`

## Input resolution order

1. `$ARGUMENTS` file path
2. Conversation history (confirm with user)
3. Common file locations (`docs/plans/`, `docs/specs/`, `requirements.md`, `PRD.md`, `spec.md`)
4. Ask the user

## Analysis categories (in severity-ranked order)

1. Contradictions
2. Feasibility (given current codebase)
3. Scope imbalance
4. Omissions
5. Ambiguity
6. Security concerns

## Follow-up items

- All existing paad skills (a11y, agentic-review, architecture) should accept `$ARGUMENTS` for customization (e.g., scoping to specific directories, output path overrides)
