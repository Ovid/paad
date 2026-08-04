# Templates and IDs

Distributable templates ship in this skill's `templates/` directory and are
copied to `kb-brain/templates/` on `init`. Humans and agents use the same
files.

## Common frontmatter

```yaml
---
id: F-001
type: finding
status: open
author: agent-parser-review
owner: task-lead
created: 2026-08-04
updated: 2026-08-04
related:
  - questions/Q-002-import-order.md
  - src/parser/imports.ts
---
```

Required: `id`, `type`, `status`, `author`, `created`, `updated`.

Add `owner`, `related`, `evidence`, `supersedes`, `amends`, `decision-owner`,
or `role: lead` where applicable.

## ID prefixes

Allocate the next numeric ID by inspecting the relevant directory — no shared
mutable counter file.

| Kind | Prefix |
|------|--------|
| Decision | `D-` |
| Finding | `F-` |
| Question | `Q-` |
| Failure | `X-` |
| Conflict | `C-` |
| Handoff | `H-` |
| Improvement | `I-` |
| Technical debt | `TD-` |
| Assumption | `A-` |
| Dependency | `DEP-` |
| Scope change | `SC-` |
| Amendment | `AM-` |
| Milestone | `M-` |

## Required templates

| File | Purpose |
|------|---------|
| `TASK.md` | Task card |
| `CONTEXT.md` | Compact shared context |
| `ASSIGNMENTS.md` | Lead-controlled assignments |
| `finding.md` | Finding / evidence |
| `decision.md` | Accepted decision |
| `question.md` | Open question |
| `failure.md` | Failure / abandoned approach |
| `conflict.md` | Conflicting positions |
| `handoff.md` | Handoff |
| `improvement.md` | Out-of-scope opportunity |
| `tech-debt.md` | Remediation liability |
| `assumption.md` | Strict-level assumption |
| `dependency.md` | Strict-level dependency |
| `scope-change.md` | Strict-level scope change |
| `PROMOTION.md` | Promotion tracking |
| `closeout.md` | Closeout |
| `amendment.md` | Post-seal correction |
| `BRIEF.md` | Human project brief |
| `MILESTONE.md` | Atomic milestone |
| `MILESTONE-SPEC.md` | Candidate milestone specification |

## Improvement body shape

```markdown
# <Improvement title>

## Observed during
...

## Observation
...

## Evidence
...

## Why it matters
...

## Possible direction
...

## Relationship to current work
...
```

## Conflict body shape

```markdown
# <Conflict title>

## Position A
...

## Position B
...

## Evidence
...

## Impact
...

## Required resolution
...

## Resolution
unresolved | resolved | deferred | blocked
```
