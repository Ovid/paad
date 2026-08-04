# Brief and milestone format

## Storage

```text
kb-brain/briefs/<brief-slug>/
├── BRIEF.md
├── INDEX.md
└── milestones/
    ├── M-001-<slug>.md
    └── ...

kb-brain/specs/<brief-slug>/
└── M-001-<slug>-spec.md
```

The human owns `BRIEF.md`. Agents may suggest amendments but must not silently
rewrite intent, outcomes, constraints, or non-goals.

## Brief template (product-level, implementation-light)

```markdown
# <Project or feature brief>

## Intended outcome
...

## Users and stakeholders
...

## Why it matters
...

## Constraints
...

## Non-goals
...

## Success at project level
...

## Known milestone ideas
...

## Open questions
...
```

Canonical copies: this skill's `templates/BRIEF.md` and
`kb-brain/templates/BRIEF.md` after init.

## Milestone records

Atomic files under `milestones/` with prefix `M-`. Status follows
`references/milestone-lifecycle.md`. Keep each milestone independently valuable
when possible.

## Index

`INDEX.md` lists milestone ID, title, status, and linked candidate spec path.
Regenerate when milestones or specs change (`kb_brain.py` brief helpers, or by
hand consistently with the table format).
