# Out-of-Scope Findings Backlog

> **These items were flagged by `/paad:agentic-review` as out of scope for the branch
> on which they were found.** They may be stale, may already have been fixed by other
> means, may no longer apply after refactors, or may simply have been judged not worth
> addressing. Verify each entry against the current code before acting on it. Entries
> are removed only when explicitly addressed — no automatic cleanup.

---

## `0965bef0` — Report-filename convention is stated three ways; the announce template and paad-help both disagree with the writer rule
- **File (at first sighting):** `plugins/paad/skills/agentic-review/SKILL.md:258`
- **Symbol:** `## Post-Review`
- **Bug class:** Contract
- **Description:** The writer rule at `agentic-review:224` is `paad/code-reviews/BRANCH-YYYY-MM-DD-HH-MM-SS-SHA.md`. `agentic-review:258`, the Post-Review artifacts-announce block the orchestrator copies as its template, shows `paad/code-reviews/review-2026-08-01-10-42-13.md` — no branch segment, no sha, and a literal `review-` prefix the rule never produces. `paad-help:217` documents `paad/code-reviews/BRANCH-TIMESTAMP.md`, dropping the sha. The example is what a sloppy run imitates when naming the file.
- **Suggested fix:** Make the `:258` example `new      paad/code-reviews/my-branch-2026-08-01-10-42-13-a1b2c3d.md` and `paad-help:217` read `paad/code-reviews/BRANCH-TIMESTAMP-SHA.md`.
- **Confidence:** Medium
- **Found by:** Contract & Integration (`claude-opus-5[1m]`)
- **First seen:** 2026-08-21 on branch `ovid/install` at `64d261f`
- **Last seen:** 2026-08-21 on branch `ovid/install` at `64d261f`
- **Severity:** Suggestion
