# Milestone lifecycle

```text
brief
→ incubating
→ ready-for-expansion
→ expanding
→ review-needed
→ approved-spec
→ planned
→ in-progress
→ completed
→ superseded
```

## Who may advance which states

| Transition | Actor |
|------------|-------|
| through `review-needed` | `brief-ruminate` / agents |
| to `approved-spec` | **human only** |
| `planned` and beyond | separate planning / implementation workflows |

## After human approval (separate invocations)

```text
approved specification
→ pushback
→ implementation planning
→ alignment
→ implementation
→ agentic-review
```

Do **not** auto-run or modify those skills from `brief-ruminate`.

## Selection guidance

When choosing the next milestone:

- Prefer independently valuable outcomes that are sufficiently unblocked.
- Do not select solely because a milestone appears first in the list.
- If oversized, propose a split; do not rewrite the brief automatically.
- If blocked on a missing controlling decision, ownership overlap, or invented
  behaviour, stop and record the blocker rather than guessing.
