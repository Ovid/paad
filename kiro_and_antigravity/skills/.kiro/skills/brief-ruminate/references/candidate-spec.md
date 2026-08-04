# Candidate milestone specification

Status must be `review-needed`. Human approval section must remain unapproved
until a human changes it.

```markdown
# <Milestone title>

## Status
review-needed

## Brief linkage
<Brief path and milestone ID>

## Outcome
...

## Scope
...

## Non-goals
...

## User and system behaviour
...

## Constraints and controlling decisions
...

## Components and boundaries
...

## Data and interface implications
...

## Failure and recovery behaviour
...

## Security, privacy, accessibility, and operational concerns
...

## Dependencies
...

## Acceptance criteria
...

## Testing expectations
...

## Open questions
...

## Assumptions
...

## Evidence consulted
...

## Human approval
Unapproved candidate specification.
```

Canonical template: `templates/MILESTONE-SPEC.md`.

Tooling helper (never writes `approved-spec`):

```bash
python3 scripts/kb_brain.py brief-spec <brief-slug> <milestone-id>
```

## Stop conditions (leave unapproved)

Stop and record a blocker or open question in KBB when:

- the brief is contradictory or lacks a usable intended outcome
- a controlling decision is missing
- unresolved dependencies make a meaningful specification impossible
- the milestone overlaps another active owner's work and the boundary is unresolved
- the candidate would require inventing product behaviour
- the milestone is too large and the human has not accepted a proposed split

Do not ruminate indefinitely or rewrite the candidate without new evidence or
human direction.
