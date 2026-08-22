# Out-of-Scope Findings Backlog

> **These items were flagged by `/paad:agentic-review` as out of scope for the branch
> on which they were found.** They may be stale, may already have been fixed by other
> means, may no longer apply after refactors, or may simply have been judged not worth
> addressing. Verify each entry against the current code before acting on it. Entries
> are removed only when explicitly addressed — no automatic cleanup.

---

## `abaa9522` — Single-argument shape heuristic routes every slash-containing branch name to the path-filter arm
- **File (at first sighting):** `plugins/paad/skills/agentic-review/SKILL.md:110`
- **Symbol:** `## Arguments`
- **Bug class:** Error Handling
- **Description:** Line 110: with exactly one argument, an argument containing `/` is treated as a path filter against `main`. Every conventional branch name (`feature/login`, `origin/main`, this repo's own `ovid/install`) therefore becomes a path filter. That arm has no existence check, and the only empty-manifest guard (pre-flight 4, line 119) evaluates the diff unfiltered, before the argument applies. So `agentic-review origin/main` scopes the manifest to a directory that does not exist, dispatches six specialists at zero files, and reports clean. Sibling skills `agentic-dedup:136` and `agentic-owasp:302` both explicitly bless `origin/main` as a valid base.
- **Suggested fix:** Reorder the test so existence decides, not shape: try `git rev-parse --verify` on the argument first (success = base branch), then `test -e` (success = path filter), and stop with the offending value if neither resolves. Independently, move the empty-manifest check after the path filter is applied, or add a second check there.
- **Confidence:** High
- **Found by:** Error Handling & Edge Cases (`claude-opus-5[1m]`)
- **First seen:** 2026-08-21 on branch `ovid/install` at `64d261f`
- **Last seen:** 2026-08-21 on branch `ovid/install` at `64d261f`
- **Severity:** Important

## `46d97ae3` — Unresolvable base ref is reported to the user as "No changes to review on this branch"
- **File (at first sighting):** `plugins/paad/skills/agentic-review/SKILL.md:119`
- **Symbol:** `## Pre-flight Checks`
- **Bug class:** Error Handling
- **Description:** Pre-flight 4 (line 119) stops with "No changes to review on this branch." when `git diff BASE...HEAD` returns no output, and enumerates only two causes: zero commits ahead, or already merged. A base ref that does not resolve (typo, deleted branch, unfetched tag) makes git fail on stderr with empty stdout, which satisfies the guard. `agentic-review` contains no `rev-parse` and no ref validation. Siblings `agentic-owasp:311` and `agentic-dedup:142` both verify the ref and surface the offending value.
- **Suggested fix:** Port the sibling rule: before pre-flight 4, run `git rev-parse --verify 'BASE'^{commit}` and stop with the offending value on failure. At minimum, amend line 119 to key on git's exit status rather than on stdout being empty.
- **Confidence:** Medium
- **Found by:** Error Handling & Edge Cases (`claude-opus-5[1m]`)
- **First seen:** 2026-08-21 on branch `ovid/install` at `64d261f`
- **Last seen:** 2026-08-21 on branch `ovid/install` at `64d261f`
- **Severity:** Important

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
