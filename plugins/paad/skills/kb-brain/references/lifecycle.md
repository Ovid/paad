# Lifecycle: start, close, seal, amend, check

## Start

1. Ensure `kb-brain/` exists (`init` if not).
2. Resolve repository default level from `AGENTS.md` or `.default-level`.
3. Refuse levels below the repo default without explicit human approval.
4. Allocate `YYYY-MM-DD-<slug>` (append `-2`, … on collision).
5. Create level-appropriate files and directories from templates.
6. Regenerate workspace `INDEX.md`, `work/ACTIVE.md`, and repo `INDEX.md`.

## Final cleanup (before close)

The lead may:

- remove empty placeholders and accidental duplicates
- repair metadata and broken links
- update statuses, ownership, and final context
- remove accidentally captured secrets or sensitive transient output
- complete `PROMOTION.md` and `CLOSEOUT.md`
- regenerate indexes and run validation

Do **not** erase substantive failures, disagreements, abandoned approaches, or
evidence to make history look cleaner.

## Closure flow

```text
active work
→ final cleanup
→ durable knowledge promotion
→ closeout generation
→ index regeneration
→ validation
→ seal creation
→ move to work/closed/
→ immutable
```

Closed workspace retains its atomic structure and adds:

```text
CLOSEOUT.md
SEAL.json
amendments/
```

## SEAL.json

SHA-256 hashes of every historical workspace file at closure, **excluding**:

- `SEAL.json` itself
- generated `INDEX.md`
- files under `amendments/`

`kb-check` reports mutation, removal, or rename of sealed files. It may
regenerate `INDEX.md` and accept new valid amendment files without invalidating
the seal.

## Amendments

Never edit, rename, or delete original sealed records. Create:

```text
kb-brain/work/closed/<task-id>/amendments/AM-NNN-<slug>.md
```

An amendment must identify what it corrects, clarifies, or supersedes; explain
why; link new evidence; and state impact. Regenerated indexes visibly mark
amended records.

## kb-check validates

- expected top-level section names
- required workspace files for the selected level
- valid YAML frontmatter and required fields
- unique IDs within their scope
- valid relative links where deterministically checkable
- task ownership / lead-only metadata consistency
- blockers consistent between `TASK.md` and generated `ACTIVE.md`
- closed workspace seal hashes
- amendment references point at an existing sealed record
- no original closed file changed, removed, or renamed
- no obvious secret patterns in files being sealed
- indexes regenerable cleanly

Report all safe-to-collect errors in one run; do not stop at the first issue.
