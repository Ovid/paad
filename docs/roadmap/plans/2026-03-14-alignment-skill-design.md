# Design: paad:alignment skill

**Date:** 2026-03-14
**Status:** Implemented

## Purpose

Checks that intent documents (requirements, specs, PRDs) and action documents (plans, tasks) are aligned. Finds coverage gaps, scope creep, and design mismatches, then rewrites all tasks in TDD red/green/refactor format.

## Key design decisions

1. **Flexible document discovery** — auto-detects from `.kiro/`, `specs/` (spec-kit), `docs/plans/`, `docs/specs/`, common filenames, or conversation history. Also accepts explicit file paths.
2. **Document classification** — automatically classifies documents as intent (what we want), action (what we'll do), or intermediate (design bridging the two).
3. **No fresh-session recommendation** — conversation history may contain the documents.
4. **Source control reality check** — same pattern as pushback; scan git history for conflicts before alignment analysis.
5. **Dependency-ordered issues** — root causes (missing requirements) before symptoms (missing tasks). Fixing upstream may resolve downstream.
6. **Mandatory TDD rewrite** — once aligned, all tasks are rewritten in red/green/refactor format. This is opinionated and not optional.

## Why TDD rewrite is mandatory

- **RED:** Writing a failing test first defines expected behavior. Occasionally reveals the feature already exists or that assumptions are wrong.
- **GREEN:** Minimal code forces simpler solutions. Less speculative "slop."
- **REFACTOR:** The step AI almost never does unless told. Catches duplication, hard-coded values, inconsistent patterns.

## Analysis categories (in dependency order)

1. Missing/unclear requirements (root causes)
2. Design gaps (if design docs exist)
3. Missing, orphaned, or out-of-scope tasks (symptoms)

## Scan locations for auto-detection

1. `.kiro/` — Kiro files
2. `specs/` — spec-kit (`SPECIFY_SPECS_DIR` env var)
3. `.specify/memory/constitution.md` — spec-kit constitution
4. `docs/plans/`, `docs/specs/` — common conventions
5. Repo root: `requirements.md`, `design.md`, `tasks.md`, `spec.md`, `plan.md`, `PRD.md`
6. Recently modified markdown files (fallback)
