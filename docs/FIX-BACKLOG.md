## Active backlog size and resolved-item lifecycle

The files under:

```text
paad/backlog/
```

must represent **active unresolved work only**.

Do not allow resolved, obsolete, superseded, or otherwise non-actionable findings to accumulate indefinitely in the active backlog files. These files will be read by `/next-task`, `/curate-backlog`, and potentially other PAAD skills, so uncontrolled growth wastes context and eventually makes the backlog itself expensive to use.

When an item is fixed or determined no longer to apply, remove it from the active backlog immediately.

### Historical information

Prefer one of these approaches, in this order:

1. **Git history only**, if it provides sufficient traceability.
2. If retaining explicit resolution metadata is useful, move resolved entries into a cold archive such as:

```text
paad/
    backlog/
        code-review.md
        architecture.md
        security.md
        ...
        archive/
            2026-08.md
            2026-09.md
```

The exact archive structure may differ if another layout better fits PAAD's existing conventions.

The critical rule is:

> Archive data is cold historical state, not working context.

`/next-task`, normal backlog-producing skills, and routine `/curate-backlog` runs MUST NOT load archive files by default.

Archive files should only be inspected when the user explicitly asks about historical findings, prior resolutions, recurrence, or similar history-dependent questions.

Do not maintain a single ever-growing `resolved.md` file. That merely relocates the context-window problem.

### Resolution metadata

If an archive is implemented, a resolved entry should preserve only useful historical information, such as:

* stable finding ID
* short description
* originating skill
* first seen
* last confirmed
* resolution date
* resolution status/reason
* relevant commit/SHA where practical

Do not copy large amounts of obsolete code context, analysis, or evidence into the archive unless there is a concrete reason to retain it. Git already preserves much of that history.

For example:

```markdown
### 7fa24c10 — Missing authorization check

Source: agentic-review
First seen: 2026-06-12
Last confirmed: 2026-08-19
Resolved: 2026-08-23
Resolution: Fixed
Commit: de91a23
```

Keep archived entries compact.

---

## Curation outcomes and movement

`/curate-backlog` should use outcomes conceptually equivalent to:

```text
CONFIRMED
RESOLVED
SUPERSEDED
UNCERTAIN
```

Their effect on active state should be:

### CONFIRMED

Keep the item in the active backlog and update its confirmation metadata.

### RESOLVED

Remove the item from the active backlog immediately.

If PAAD implements a cold archive, write a compact resolution record there. Otherwise rely on Git history.

### SUPERSEDED

Do not retain both the obsolete and replacement forms in the active backlog.

Replace/update the active finding so that the backlog describes the **current** problem.

If historical archiving is implemented, the obsolete version may be recorded there as superseded.

### UNCERTAIN

Keep the item active because PAAD lacks sufficient evidence to remove it safely.

Mark it clearly as requiring revalidation or human attention.

The active backlog must always describe PAAD's best current understanding of unresolved work, rather than becoming an append-only history.

---

## Backlog writes after remediation

Any PAAD skill that actually fixes or invalidates a known backlog item should update backlog state as part of completing that work.

For example:

```text
/next-task
    ↓
user selects finding 7fa24c10
    ↓
finding is fixed
    ↓
tests/validation confirm fix
    ↓
7fa24c10 removed from active backlog
```

Do not require the user to remember to run `/curate-backlog` merely to remove an item that PAAD itself has just successfully fixed.

However, removal must happen only after sufficient validation. Merely editing the relevant code is not evidence that the finding has been resolved.

Where an existing remediation skill such as `/fix-architecture` resolves a known backlog entry, that skill should remove or update the corresponding active finding once its own validation succeeds.

---

## Context-budget requirement

Treat backlog context size as an explicit design constraint.

When implementing `/next-task`, `/curate-backlog`, and backlog-producing skills:

* load only active backlog files needed for the operation
* do not load historical archives by default
* avoid repeatedly embedding large original reports inside backlog entries
* reference historical reports by path where practical rather than duplicating them
* keep backlog entries concise while retaining enough evidence for later revalidation
* use deterministic repository inspection before sending large amounts of source code to a model
* avoid loading every active finding's full evidence when only a subset needs semantic analysis

If an individual active backlog file becomes large despite containing only unresolved findings, consider processing entries incrementally or in batches rather than loading the entire file into model context.

The goal is that backlog management remains useful even in a long-lived repository with years of PAAD history.

---

## Add to tests and validation

Also test the lifecycle explicitly:

* fixing an item removes it from the active backlog
* curation of a resolved item removes it from active state
* superseding an item does not leave both versions active
* an uncertain item remains active
* archived/resolved items are not loaded by `/next-task`
* archived/resolved items are not loaded during routine `/curate-backlog`
* remediation skills remove known backlog entries only after successful validation
* repeated fixing/curation does not create duplicate archive records
* large historical archives do not materially affect normal backlog operations

