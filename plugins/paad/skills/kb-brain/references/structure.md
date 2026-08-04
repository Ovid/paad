# KB-Brain structure

## Top-level layout

```text
kb-brain/
├── README.md
├── INDEX.md
├── decisions/
├── architecture/
├── domains/
├── runbooks/
├── gotchas/
├── briefs/
├── specs/
├── plans/
├── reviews/
├── learnings/
├── open-questions/
├── agents/
├── improvements/
├── tech-debt/
│   ├── LEDGER.md
│   └── closed/
├── templates/
└── work/
    ├── ACTIVE.md
    ├── active/
    └── closed/
```

Do not create empty atomic records during init.

## Permanent section meanings

| Section | Meaning |
|---------|---------|
| `decisions/` | Accepted ADR-style decisions with owner and evidence |
| `architecture/` | Mutable notes refining or challenging stable `docs/` — always link back |
| `domains/` | Product and business domain knowledge |
| `runbooks/` | Recurring procedures not yet stable documentation |
| `gotchas/` | Sharp edges, false starts, reliable warnings |
| `briefs/` | Human-owned briefs and atomic milestone records |
| `specs/` | Active working specifications, including candidate milestone expansions |
| `plans/` | Implementation plans tied to approved specs |
| `reviews/` | Review outputs worth preserving beyond their session |
| `learnings/` | Post-hoc lessons and retrospectives |
| `open-questions/` | Unresolved questions; agents may add evidence, never invent answers |
| `agents/` | Repository-specific agent behaviour and coordination notes |
| `improvements/` | One atomic file per noticed gap or opportunity |
| `tech-debt/` | Open debt + `LEDGER.md`; resolved entries move to `closed/` |

`docs/` is the stable architecture / accepted documentation source of truth.
Do not duplicate it under `kb-brain/`.

## Workspace levels

Repository default is selected in `AGENTS.md` (recommended `standard`). A task
may raise its level. Lowering below the repository default requires explicit
human approval.

### minimal

Required: task scope and status, compact context, ownership, final handoff,
durable findings selected for promotion.

### standard (default)

Adds: assignments, findings and evidence, questions, failures and abandoned
approaches, confirmed decisions, conflicts, handoffs, promotion tracking.

### strict

Adds: explicit assumptions, dependency records, decision ownership, scope-change
records, mandatory evidence references, detailed conflict handling, completion
and promotion checks.

All levels use focused files and atomic record directories — never a single
append-only workspace journal.

## Active workspace layout

```text
kb-brain/work/active/<task-id>/
├── TASK.md
├── INDEX.md
├── CONTEXT.md
├── ASSIGNMENTS.md          # standard + strict
├── PROMOTION.md
├── decisions/
├── findings/
├── questions/
├── failures/
├── conflicts/
├── handoffs/
├── assumptions/            # strict
├── dependencies/           # strict
└── scope-changes/          # strict
```

Task ID format: `YYYY-MM-DD-<short-slug>`. On collision append `-2`, `-3`, …

## File responsibilities

- **`TASK.md`** — authoritative task card: objective, scope, non-goals,
  completion criteria, workspace level, lead owner, lifecycle status, current
  focus, blockers, controlling brief/spec/issue/plan links.
- **`INDEX.md`** — generated. Lists atomic records by type, status, owner, and
  relationship. Marks amendments on closed workspaces.
- **`CONTEXT.md`** — compact shared working memory. Keep brief; link detail.
- **`ASSIGNMENTS.md`** — lead-controlled assignments, boundaries, dependencies,
  status.
- **`PROMOTION.md`** — durable information that must move to permanent KBB
  sections or stable `docs/` before closure.

## ACTIVE.md

`kb-brain/work/ACTIVE.md` is generated from task workspace metadata. It
contains only: active task ID and link, status, workspace level, lead/owner,
objective, current focus, blockers. **Do not list conflicts.** Do not hand-edit
narrative that can drift — regenerate via `kb_brain.py index`.
