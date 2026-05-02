# Design: paad:vibe skill

**Date:** 2026-03-14
**Status:** Implemented

## Purpose

Safe vibe coding — quick fixes and small changes with TDD guardrails. Speed without recklessness.

## Key design decisions

1. **Accept task via `$ARGUMENTS` or ask** — `/paad:vibe fix the bug` or just `/paad:vibe`
2. **Pre-flight checks before any code** — test infrastructure, scope/complexity, architecture smells, reusable components
3. **Mandatory red/green/refactor** — not optional, even for "simple" fixes
4. **Stop on surprises** — if RED test passes or fails unexpectedly, stop and ask the user
5. **Architecture investigation** — if a simple task requires lots of work, investigate deeper issues before proceeding
6. **Reusable component search** — for common functionality (toasts, modals, form validation, etc.), search the codebase before building from scratch
7. **Post-fix summary with contextual follow-ups** — suggest agentic-review, a11y, or architecture only when genuinely relevant
8. **No alignment suggestion** — vibe coding often changes intent, so alignment checks would produce false positives

## Guardrails

- No test infrastructure → warn, ask how to proceed
- 4+ files or cross-module → warn, may not be a vibe task
- Simple task but hard work → investigate architecture
- Common functionality → search for existing components first
- Unexpected test behavior → stop and ask
