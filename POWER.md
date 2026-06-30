---
name: paad
displayName: PAAD — Architecture, Review & Quality Skills
description: Multi-agent architecture analysis, code review, accessibility, and quality workflows.
keywords: [architecture, code review, accessibility, requirements, code quality]
author: Ovid
version: 1.11.0
---

# PAAD — Kiro Power

paad — impractical tools for software architecture, code quality, and development workflows.

Each skill is exposed as a manual steering file the agent loads on demand. Pick the one that matches your request from the list below.

## When to load steering files

Each skill is a manual steering file — load the one matching the user's request (type `/` in chat to pick it, or reference `#<name>`):

- **#agentic-a11y** — Comprehensive multi-agent accessibility audit of user-facing code — supports web, mobile (iOS/Android/React Native/Flutter), desktop, CLI, and games — dispatches specialists for screen readers, vision, motor, cognitive, and multimedia concerns, verifies findings, and produces an actionable report with WCAG 2.2 AA/AAA ratings
- **#agentic-architecture** — Multi-agent architecture analysis — dispatches specialists for structure, coupling, integration, error handling, and security, verifies findings, and produces a comprehensive report of strengths and flaws with evidence
- **#agentic-review** — Use when reviewing current branch for bugs before pushing or merging, when wanting a thorough multi-agent review of local changes, or when preparing work for human review
- **#alignment** — Check that requirements, designs, and implementation plans are aligned — finds coverage gaps, scope creep, and design mismatches, then rewrites tasks in TDD red/green/refactor format
- **#fix-architecture** — Guided fixing of architectural flaws from an agentic-architecture report — validates findings, writes tests, applies fixes with developer approval, and tracks status in the report
- **#pushback** — Push back on specs, PRDs, requirements, and design documents — finds unrelated features, oversized scope, contradictions, feasibility issues, scope imbalance, omissions, ambiguity, and security concerns, with source control reality checks
- **#vibe** — Safe vibe coding with TDD guardrails — for small fixes and quick changes where you want speed but not recklessness. Enforces red/green/refactor, checks for architecture issues, reusable components, and test infrastructure before diving in.

<!-- Generated from paad@4c71a8f by build-kiro-power -->
