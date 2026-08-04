# Routing and write rules

## Durability test

> Will this information materially help a future developer understand, decide,
> avoid a failure, or continue unfinished work?

If **no** — keep it in session context; do not create a file.

If **yes** — route by intent:

| Intent | Destination |
|--------|-------------|
| Accepted choice and rationale | `decisions/` |
| Mutable architectural reasoning | `architecture/` (link to stable `docs/`) |
| Product/domain fact | `domains/` |
| Recurring procedure | `runbooks/` |
| Sharp edge or false start | `gotchas/` |
| Unresolved decision | `open-questions/` |
| Out-of-scope opportunity | `improvements/` |
| Remediation liability | `tech-debt/` + update `LEDGER.md` |
| Task-specific evidence or working state | current workspace |
| Stable accepted documentation | propose/perform promotion to `docs/`, then link from KBB |

Avoid duplicates: search indexes and relevant titles first. Append evidence to
an active compatible record when the conclusion, scope, owner, and lifecycle
match; otherwise create a new record.

## Agent permissions

### Sub-agents may append

- findings and evidence
- questions
- failures and abandoned approaches
- conflicts
- handoffs
- suggested improvements
- technical debt

### Lead-only (or human task owner)

- task scope or non-goals
- task lifecycle status
- assignments and ownership
- confirmed decisions
- blocker disposition
- conflict resolution status
- workspace closure and sealing

Prefer `role: lead` (and `decision-owner` where applicable) on privileged
records. `kb-check` flags confirmatory decisions/scope-changes that lack lead
ownership metadata.

## Conflict protocol

Conflicting findings are recorded, never overwritten. When a conflict pertains
to current work, address it in-session. The lead records one of:

- `resolved` — evidence or human decision establishes the controlling conclusion
- `deferred` — real but outside the bounded task; record why and where next
- `blocked` — cannot safely continue; add the blocker to `TASK.md` (surfaces in
  `ACTIVE.md`)

Unrelated conflicts remain recorded and do not block the current assignment.

## AGENTS.md installation snippet

Provide this (or equivalent) when initializing KBB in a repository:

```markdown
## KB-Brain

Use the `kb-brain` skill for section routing, templates, workspace lifecycle, and write rules.

Every PAAD-managed task uses a focused shared workspace under:

`kb-brain/work/active/<task-id>/`

Repository workspace level: `standard`

Supported levels:

- `minimal` — scope, status, ownership, handoff, and durable findings
- `standard` — findings, questions, decisions, failures, conflicts, and handoffs
- `strict` — standard plus evidence, assumptions, dependencies, ownership, and scope-change tracking

A task may raise its level. Lowering below the repository level requires explicit human approval.

Sub-agents may append findings, evidence, questions, failures, conflicts, and handoffs.

Only the lead agent or human task owner may change task scope, lifecycle status, assignments, blockers, confirmed decisions, or conflict resolution state.

Conflicting findings must be recorded rather than overwritten. Address conflicts during the session when they affect current work.

Agents may autonomously:

- add one file per gap under `kb-brain/improvements/`;
- track smoothing or remediation work under `kb-brain/tech-debt/`;
- update `kb-brain/tech-debt/LEDGER.md`;
- move resolved debt into `kb-brain/tech-debt/closed/`;
- promote durable task knowledge into the appropriate permanent KBB section.

Use the provided templates for human- and agent-authored records.

Bulk content ingress from existing documentation is a dedicated operation. Do not copy architecture documentation into KBB unprompted.

Closed workspaces are immutable. Add corrections or later findings as explicit amendments.
```
