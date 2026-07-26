---
name: agentic-architecture
description: Use when assessing the architectural health of a codebase — before a major refactor, when onboarding to an unfamiliar repo, after rapid growth, when planning a redesign, or to surface structural strengths and risks before they become expensive. Not for fixing what it finds, and not for reviewing a branch diff.
---

**On invocation:** announce "Running paad:agentic-architecture v1.21.0" before anything else.

# Agentic Architecture Analysis

Multi-agent architecture analysis of the current codebase. Dispatches specialist agents in parallel — each focused on a different architectural domain — verifies findings to filter false positives, and produces a balanced report of strengths and flaws with concrete evidence.

**Do NOT propose fixes.** This is diagnosis only.

**This is a technique skill.** Follow the phases in order. Do not skip verification.

**Pre-flight:**

```dot
digraph preflight {
  "Conversation has history?" [shape=diamond];
  "Proceed to Phase 1" [shape=box];
  "STOP: recommend new session" [shape=box, style=bold];

  "Conversation has history?" -> "STOP: recommend new session" [label="yes"];
  "Conversation has history?" -> "Proceed to Phase 1" [label="no"];
}
```

**Analysis flow:**

```dot
digraph analysis_flow {
  "Git repo?" [shape=diamond];
  "Scope size?" [shape=diamond];
  "Integration & Data specialist: distributed system?" [shape=diamond];
  "Confirmed by reading the actual code?" [shape=diamond];
  "Confidence >= 60?" [shape=diamond];
  "Concrete evidence present?" [shape=diamond];
  "Reported by multiple specialists?" [shape=diamond];

  "Repo name from git remote origin" [shape=box];
  "Repo name from top-level directory basename" [shape=box];
  "Recon: overview, structure, steering files, manifest" [shape=box];
  "Dispatch 5 specialists in parallel" [shape=box];
  "Partition files across 2 instances of each specialist" [shape=box];
  "Mark distributed-specific categories Not applicable" [shape=box];
  "Validate impact level and category assignment" [shape=box];
  "Merge duplicates, note the agreeing specialists" [shape=box];
  "DROP the finding" [shape=box];
  "Keep the finding" [shape=box];
  "Write report to paad/architecture-reviews/" [shape=box];
  "Report location, counts, 3-6 bullet summary" [shape=box];
  "STOP: diagnosis only — do NOT propose fixes" [shape=box, style=bold];

  "Git repo?" -> "Repo name from git remote origin" [label="yes"];
  "Git repo?" -> "Repo name from top-level directory basename" [label="no"];
  "Repo name from git remote origin" -> "Recon: overview, structure, steering files, manifest";
  "Repo name from top-level directory basename" -> "Recon: overview, structure, steering files, manifest";
  "Recon: overview, structure, steering files, manifest" -> "Scope size?";

  "Scope size?" -> "Dispatch 5 specialists in parallel" [label="small (<50) / medium (50-500)"];
  "Scope size?" -> "Partition files across 2 instances of each specialist" [label="large (500+ source files)"];
  "Partition files across 2 instances of each specialist" -> "Dispatch 5 specialists in parallel";
  "Dispatch 5 specialists in parallel" -> "Integration & Data specialist: distributed system?";
  "Integration & Data specialist: distributed system?" -> "Confirmed by reading the actual code?" [label="yes"];
  "Integration & Data specialist: distributed system?" -> "Mark distributed-specific categories Not applicable" [label="no"];
  "Mark distributed-specific categories Not applicable" -> "Confirmed by reading the actual code?";

  "Confirmed by reading the actual code?" -> "Confidence >= 60?" [label="yes — verifier per finding"];
  "Confirmed by reading the actual code?" -> "DROP the finding" [label="no"];
  "Confidence >= 60?" -> "Concrete evidence present?" [label="yes"];
  "Confidence >= 60?" -> "DROP the finding" [label="no"];
  "Concrete evidence present?" -> "Validate impact level and category assignment" [label="yes (path, symbol, excerpt)"];
  "Concrete evidence present?" -> "DROP the finding" [label="no"];
  "Validate impact level and category assignment" -> "Reported by multiple specialists?";
  "Reported by multiple specialists?" -> "Merge duplicates, note the agreeing specialists" [label="yes"];
  "Reported by multiple specialists?" -> "Keep the finding" [label="no"];
  "Merge duplicates, note the agreeing specialists" -> "Keep the finding";

  "Keep the finding" -> "Write report to paad/architecture-reviews/";
  "DROP the finding" -> "Write report to paad/architecture-reviews/" [label="counted under Filtered out"];
  "Write report to paad/architecture-reviews/" -> "Report location, counts, 3-6 bullet summary";
  "Report location, counts, 3-6 bullet summary" -> "STOP: diagnosis only — do NOT propose fixes";
}
```

## When NOT to Use This Skill

- **You already have a recent report** — re-running burns a session to regenerate what you have. Read the existing report in `paad/architecture-reviews/` and use `/paad:fix-architecture`, which handles staleness itself.
- **The scope is a handful of files** — architecture is about boundaries and relationships between components. Below that scale there's no structure to assess, and the report will pad.

## Arguments

`/paad:agentic-architecture` accepts optional `$ARGUMENTS`:

- `/paad:agentic-architecture` — analyze the entire repository
- `/paad:agentic-architecture src/` — scope the analysis to a specific directory (useful for monorepos or analyzing one service)
- `/paad:agentic-architecture packages/api/ packages/shared/` — analyze multiple directories together

When a path is provided, focus the analysis on that scope but still note dependencies on code outside the scope.

## Pre-flight Checks

1. **Context window:** If conversation has substantive history beyond invoking this skill, tell the user: "This analysis consumes significant context. Start a fresh session with `/paad:agentic-architecture` to avoid context rot." Stop and wait.

## Phase 1: Reconnaissance

Run these steps and collect results:

1. **Repo identification:**
   - Detect if this is a git repo (`git rev-parse`)
   - Determine repo name from `git remote get-url origin` (strip `.git`, take last segment) or basename of top-level directory
   - Set output filename accordingly

2. **Repo overview:**
   - Identify primary languages/frameworks
   - Identify key directories (`apps/`, `services/`, `packages/`, `src/`, `lib/`, etc.)
   - Estimate size: number of services/modules/packages

3. **Dependency & structure snapshot:**
   - Top-level modules/packages and their relationships
   - Quick import graph via heuristics (look for cross-layer imports, circular patterns)
   - Note positive structure signals (clean layering, bounded contexts)

4. **Scan for steering files:** `CLAUDE.md`, `AGENTS.md`, architecture docs, ADRs

5. **Estimate scope size:**
   - **Small:** <50 source files
   - **Medium:** 50-500 source files
   - **Large:** 500+ source files

6. **Build manifest:** source files grouped for specialists, annotated with module/package boundaries

**Steering file caveat:** Include in every agent prompt: "Steering files (CLAUDE.md, etc.) describe conventions but may be stale. If you find a contradiction between steering files and actual code, flag it as a finding."

## Phase 2: Specialist Analysis (Parallel)

Dispatch these agents simultaneously using the Agent tool. Each receives: the file manifest, repo overview, steering file contents, and their specialist focus.

### Specialists

| Agent | Domain | Flaw types | Strength categories |
|-------|--------|-----------|-------------------|
| **Structure & Boundaries** | Module organization, responsibility distribution, domain modeling | 1 (global mutable state), 2 (god object), 9 (shotgun surgery), 10 (feature envy/anemic domain), 11 (low cohesion), 13 (inconsistent boundaries), 29 (utility dumping ground) | S1 (modular boundaries), S2 (cohesion), S13 (domain modeling), S14 (pragmatic abstractions) |
| **Coupling & Dependencies** | How components connect, abstraction quality, dependency direction | 3 (tight coupling), 4 (high/unstable deps), 5 (circular deps), 6 (leaky abstractions), 7 (over-abstraction), 8 (premature optimization), 23 (DI misuse), 27 (temporal coupling) | S3 (loose coupling), S4 (dependency direction), S5 (dep management hygiene) |
| **Integration & Data** | Service communication, data ownership, API contracts, resilience | 14 (distributed monolith), 15 (chatty calls), 16 (sync-only integration), 17 (no data ownership), 18 (shared database), 19 (lack of idempotency), 24 (inconsistent API contracts), 26 (poor transactional boundaries) | S6 (consistent API contracts), S12 (resilience patterns) |
| **Error Handling & Observability** | Error strategies, logging, config, side effects, business logic placement | 12 (hidden side effects), 20 (weak error handling), 21 (no observability), 22 (config sprawl), 25 (business logic in UI), 28 (magic numbers/strings), 34 (inconsistent error/logging) | S7 (robust error handling), S8 (observability), S9 (config discipline) |
| **Security & Code Quality** | Auth, secrets, dead code, test coverage | 30 (security as afterthought), 31 (dead code/unused deps), 32 (missing test coverage), 33 (hard-coded credentials) | S10 (security built-in), S11 (testability & coverage) |

### Agent prompt template

Each specialist agent prompt must include:
- The file manifest for their scope
- Repo overview and structure snapshot
- Steering file contents with the staleness caveat
- Their assigned flaw types and strength categories with descriptions
- Instruction: "You are an architecture specialist focused on [DOMAIN]. Find both **strengths** and **flaws** in the assigned categories. For each finding report: the category (flaw type number or strength category), file:line, a short label, 1-2 sentence explanation, concrete evidence (path, symbol, excerpt), impact level (High/Medium/Low), and your confidence (0-100). Only report findings with confidence >= 60. Validate every candidate by reading the actual code — do not infer from file names alone."

**Structure & Boundaries additional instruction:** "Look for: module-level mutable variables, singletons, static mutables; very large classes/files with high fan-in/fan-out; single logical changes requiring edits across many files; business logic in services while domain objects are just data bags; modules grouping unrelated behaviors; drifting responsibilities between layers; generic helper modules growing into grab-bags. Also look for the positive: clean module organization, high cohesion, strong domain modeling, pragmatic abstractions."

**Coupling & Dependencies additional instruction:** "Look for: concrete instantiations instead of abstractions, core depending on leaf modules, circular imports, abstractions requiring callers to know internals, excessive layers/interfaces for uncertain future needs, architecture optimized without evidence, DI obscuring control flow, components requiring specific call order. Also look for the positive: clean interfaces, stable dependency direction, minimal circular deps, consistent import conventions."

**Integration & Data additional instruction:** "Look for: microservices with heavy synchronous coupling, too many small network calls, everything requiring immediate responses, multiple services writing same data, services coupled through shared schemas, non-idempotent operations, API contracts without compatibility discipline, operations spanning systems without strategy. Also look for the positive: consistent API versioning, resilience patterns (timeouts, retries, circuit breakers, backpressure). If this is not a distributed system, mark distributed-specific categories as Not applicable."

**Error Handling & Observability additional instruction:** "Look for: functions doing more than signatures suggest, errors swallowed or over-generalized, missing logs/metrics/traces, scattered configs with unclear precedence, critical rules in frontend code, hard-coded magic values, inconsistent error/logging formats across services. Also look for the positive: consistent error taxonomy, structured logging with correlation IDs, centralized config, safe defaults."

**Security & Code Quality additional instruction:** "Look for: auth bolted on late, secrets in source, missing trust boundaries, unused packages/files/modules, unreachable code, stale feature flags, critical paths without tests. Also look for the positive: authN/Z patterns, secret management, least privilege, tests around critical paths, good test seams, deterministic tests."

**Refactor history instruction (include in all agent prompts):** "Before flagging a candidate flaw, use `git log --oneline` on the relevant files/directories to check whether the current code is the result of recent intentional work. A large file with many recent commits may be a completed refactor, not a neglected problem. Intentional design choices can still be flawed — check history to understand context, not to dismiss findings."

**Scaling for large codebases (500+ source files):** Partition files across 2 instances of each specialist.

## Phase 3: Verification

After all specialists complete, dispatch a single **Verifier** agent with all findings. The verifier:

1. For each finding, reads the actual current code at the referenced file:line
2. Confirms the strength or flaw exists and is accurately described
3. Drops false positives and findings below 60% confidence
4. Validates that the impact level (High/Medium/Low) is appropriate
5. Checks that the correct flaw type or strength category is assigned
6. Deduplicates findings flagged by multiple specialists (note which specialists agreed — cross-specialist agreement increases confidence)
7. Ensures every finding has concrete evidence (file path, symbol, excerpt) — drops findings without evidence

**Verifier prompt must include:** "You are verifying architecture findings. For each finding, read the actual code and confirm the strength or flaw exists. Be skeptical — file size alone doesn't make a god object, and many imports don't necessarily mean tight coupling. Check git history for context. A finding reported by multiple specialists is more likely real. Drop anything you cannot confirm by reading the code."

## Phase 4: Report

Write verified findings to `paad/architecture-reviews/<YYYY-MM-DD>-<git-repo-name>-architecture-report.md`.

Create the `paad/architecture-reviews/` directory if it doesn't exist.

**Report template:**

```markdown
# Architecture Report — <repo-name or current folder>

**Date:** YYYY-MM-DD
**Commit:** <full-sha>
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

## Flaw/Risk Type Reference

For specialist and verifier reference, the complete list of 34 flaw types:

1. Global mutable state
2. God object
3. Tight coupling
4. High/unstable dependencies
5. Circular dependencies
6. Leaky abstractions
7. Over-abstraction
8. Premature optimization
9. Shotgun surgery
10. Feature envy / anemic domain model
11. Low cohesion
12. Hidden side effects
13. Inconsistent boundaries
14. Distributed monolith
15. Chatty service calls
16. Synchronous-only integration
17. No clear ownership of data
18. Shared database across services
19. Lack of idempotency
20. Weak error handling strategy
21. No observability plan
22. Configuration sprawl
23. Dependency injection misuse
24. Inconsistent API contracts
25. Business logic in the UI
26. Poor transactional boundaries
27. Temporal coupling
28. Magic numbers/strings everywhere
29. "Utility" dumping ground
30. Security as an afterthought
31. Dead code / unused dependencies
32. Missing or inadequate test coverage for critical paths
33. Hard-coded credentials or secrets in source
34. Inconsistent error/logging conventions across services

## Strength Category Reference

S1. Clear modular boundaries
S2. High cohesion
S3. Loose coupling
S4. Dependency direction is stable
S5. Dependency management hygiene
S6. Consistent API contracts
S7. Robust error handling
S8. Observability present
S9. Configuration discipline
S10. Security built-in
S11. Testability & coverage
S12. Resilience patterns
S13. Domain modeling strength
S14. Simple, pragmatic abstractions

> If a category is not applicable due to repo nature (e.g., no networked services for S12), mark **Not applicable** and briefly explain.

## Common Mistakes

These patterns produce low-quality architecture analyses. Avoid them:

| Mistake | What to do instead |
|---------|-------------------|
| Single-agent analysis | Always dispatch 5 specialist agents in parallel — each architectural domain has unique concerns |
| Skipping verification | Always run verifier — file size and import count alone don't prove architectural problems |
| Inferring from names alone | Read the actual code — a file called `utils.py` might be well-organized, and `UserService` might be a god object |
| Ignoring git history | Check whether code is the result of recent intentional refactoring before flagging it |
| Proposing fixes | This is diagnosis only — describe what exists and why it matters, not what to do about it |
| Missing evidence | Every finding must include file:line, symbol name, and excerpt — unanchored findings are not actionable |
| Only reporting flaws | Strengths are equally important — they tell teams what to protect and what patterns to follow |
| Applying distributed system patterns to monoliths | Mark distributed-specific categories as Not applicable when reviewing a monolith |
| Counting lines as proof | A 500-line file might be perfectly cohesive; a 50-line file might violate single responsibility — analyze content, not metrics |

## Post-Analysis

After writing the report:
1. Tell the user the report location and finding counts (strengths and flaws by impact level)
2. Print a brief summary (3-6 bullet points) of the highest-impact strengths and risks
3. Do **not** propose fixes. The report is the deliverable.
