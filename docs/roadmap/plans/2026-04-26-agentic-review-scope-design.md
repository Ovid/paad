# `/paad:agentic-review` — Scope Constraint Design

**Date:** 2026-04-26
**Status:** Design (brainstormed, not yet implemented)
**Targets:** `plugins/paad/skills/agentic-review/SKILL.md`

> **Amendments since original design:**
> - The Plan Alignment specialist was replaced with a richer **Spec Compliance** specialist that emits Missing / Deviation / Out-of-scope-addition categories.
> - A separate `## Out-of-Scope Additions` report section was added for findings the branch added but the spec didn't promise; these are ephemeral (no backlog persistence) and surface a per-PR keep / split / revert decision per item.
> - The live behavior is in `plugins/paad/skills/agentic-review/SKILL.md`; this doc reflects the original scope-classification design only and notes deltas inline.

## Problem

`/paad:agentic-review` deliberately expands review scope beyond changed lines (callers/callees one level deep, full module on small diffs) so specialists can catch integration bugs. This expansion is also the source of a recurring failure mode:

- Re-running the review on the same branch keeps surfacing findings *outside* the branch's scope.
- The user, treating all findings as actionable, fixes those out-of-scope bugs on the current branch.
- The branch grows; the next re-run pulls in even more adjacent files (because the just-fixed files are now changed); more out-of-scope findings surface; the cycle repeats.
- Result: branch explosion. Also: the out-of-scope findings *are* often important and shouldn't simply be dropped.

The design constrains the problem by classifying every finding as **in-scope** or **out-of-scope** for the current branch, surfacing both clearly, and persisting the out-of-scope ones to a project-wide backlog so they aren't lost.

## Definitions

**In-scope** for the current branch means: this branch's changes either *caused* the bug or *worsened* it (made it more likely to fire, expanded its blast radius, removed a guard that was masking it, added a new caller into broken code, etc.). Pre-existing bugs that the branch does not reach differently are **out-of-scope**, even when they live in files the branch touches.

## Mechanism

Classification is **hybrid blame + reasoning**:

1. **Blame default.** Every finding's `file:line` is checked against a pre-computed touched-lines map derived from `git diff base...HEAD`. If the line falls within a touched range → tentatively **in-scope**. Otherwise → tentatively **out-of-scope**.
2. **Reasoning promotion.** For tentatively out-of-scope findings only, the verifier asks: "Does this branch's diff cause this bug to fire when it didn't before, or measurably increase its probability/blast radius?" If yes → promote to **in-scope**. If the bug is purely pre-existing and the branch doesn't reach it differently → confirmed **out-of-scope**.
3. **Cosmetic-touch demotion.** A finding on touched lines defaults to in-scope, but the verifier may demote to out-of-scope when **both** of the following hold: (a) the branch's edits to those specific lines are purely cosmetic (whitespace, comment additions, line splits, identifier renames that don't change semantics), and (b) the bug itself is purely pre-existing — the cosmetic touch did not introduce, expose, or alter the bug's behavior. If either condition fails (semantic edit on the line, or the touch interacts with the bug), the finding stays in-scope. This carve-out closes the gap where reformatting a buggy line would otherwise force the user to fix unrelated pre-existing bugs on the current branch.

Out-of-scope findings are **semantically deduped** by the verifier against a **file-filtered slice** of `paad/code-reviews/backlog.md`. Before invoking the verifier, the orchestrator pre-filters the backlog to entries whose `File (at first sighting)` path matches a file in the current review's manifest (changed + adjacent). Only that subset is passed in. Match → emit an update directive (`{id, last_seen, branch, sha}`). No match → mint a new entry with a stable 8-char hex ID hashed from `file + symbol + bug-class + first-seen-iso-date`. When the unfiltered backlog crosses **200 active entries**, the post-review message also surfaces a soft warning ("backlog has N active entries — consider triaging") so accumulation stays visible.

Backlog **lifecycle is explicit-removal only** — agentic-review never auto-resolves entries. Downstream agents (or the user) delete the `## <id> — <title>` block when an item is addressed. `git log` on the file is the audit trail.

## Skill changes

### Phase 1 (Reconnaissance) — additions

- Build a **touched-lines map**: from `git diff base...HEAD`, produce `{file → [line ranges]}` covering every line the branch added or modified. This map becomes part of the verifier's input. Construction rules:
  - **Keys are current-HEAD paths.** Files are recorded under the path they have at HEAD, not at base.
  - **Renamed files** are keyed by the new path; the line ranges cover lines modified in the new file. The old path is not retained.
  - **Newly added files** include all lines (1..end) — every line is touched.
  - **Pure deletions** contribute no entries (no current line exists to anchor a finding to).
  - When a path filter argument is supplied (e.g., `/paad:agentic-review main src/auth/`), the touched-lines map is filtered to that scope, matching the manifest.
- Findings are classified by their **anchor line** only (the `file:line` reported by the specialist). Multi-line bugs whose anchor line happens to be untouched are caught by reasoning-promotion in Phase 3, not by an expanded blame check.

Everything else in Phase 1 stays as-is (diff stats, manifest construction, callers/callees one level, plan/steering scan, infrastructure-pair scan).

### Phase 2 (Specialist Review) — additions

- Each specialist's prompt is appended with: *"Include the model name you are running as in every finding under a `model:` field."* This carries through to the report so the user knows which model produced each finding.

Specialist lenses, scopes, and dispatch behavior were unchanged at design time. (Subsequently amended: the Plan Alignment specialist was replaced with Spec Compliance — see amendments at top.)

### Phase 3 (Verification) — expanded responsibilities

The verifier now does, in order:

1. (existing) Read code at each finding's location; drop false positives and findings below 60% confidence.
2. (existing) Assign severity (Critical / Important / Suggestion) and dedupe across specialists.
3. **(new) Classify** each finding as `in-scope` or `out-of-scope` using the hybrid blame + reasoning + cosmetic-demotion rules above. Touched-lines map is provided as input.
4. **(new) Backlog dedup** for out-of-scope findings only. A **pre-filtered slice** of `paad/code-reviews/backlog.md` is provided as input — only entries whose `File (at first sighting)` path matches a file in the manifest. For each out-of-scope finding, the verifier decides:
   - **Match** → emit `{id, last_seen, branch, sha}` update directive.
   - **No match** → mint a new entry (with a fresh ID).

Verifier output to Phase 4 is two lists:

- In-scope findings (with severity).
- Out-of-scope findings (with severity, backlog ID, and `new` vs `re-seen` flag).

### Phase 4 (Report) — new section + new metadata

In-scope sections (`## Critical Issues`, `## Important Issues`, `## Suggestions`) are unchanged structurally; they now implicitly mean "in-scope." A new section is inserted *after* Suggestions and *before* the (then-named) Plan Alignment section. (Plan Alignment was subsequently replaced by Spec Compliance, which emits its own `## Out-of-Scope Additions` section after this `## Out of Scope` section — see amendments at top.):

```markdown
## Out of Scope

> **Handoff instructions for any agent processing this report:** The findings below are
> pre-existing bugs that this branch did not cause or worsen. Do **not** assume they
> should be fixed on this branch, and do **not** assume they should be skipped.
> Instead, present them to the user **batched by tier**: one ask for all out-of-scope
> Critical findings, one ask for all Important, one for Suggestions. For each tier, the
> user decides which (if any) to address. When you fix an out-of-scope finding, remove
> its entry from `paad/code-reviews/backlog.md` by ID.

### Out-of-Scope Critical
### [OOSC1] <title> — backlog id: `<id>`
- **File:** `path/to/file:line`
- **Bug:** ...
- **Impact:** ...
- **Suggested fix:** ...
- **Confidence:** High/Medium
- **Found by:** <specialist> (`<model>`)
- **Backlog status:** new | re-seen (first logged YYYY-MM-DD)

### Out-of-Scope Important
(same shape — IDs OOSI1, OOSI2, ...)

### Out-of-Scope Suggestions
(one-line entries; each carries a backlog id — IDs OOSS1, OOSS2, ...)
```

The handoff block above is human-readable guidance for any downstream agent processing the report — its prose may evolve across skill versions. The **stable contract** downstream tooling depends on is the structured per-finding fields and stable backlog IDs, not the prose wording.

In-scope finding entries also gain a `Found by: <specialist> (<model>)` field.

**Review Metadata** gains two new lines:

```markdown
- **Out-of-scope findings:** N (Critical: a, Important: b, Suggestion: c)
- **Backlog:** X new entries added, Y re-confirmed (see paad/code-reviews/backlog.md)
```

### Backlog file: `paad/code-reviews/backlog.md`

Project-wide, append-only, explicit removal. Created on first run if absent.

**Fixed header (preserved across all updates):**

```markdown
# Out-of-Scope Findings Backlog

> **These items were flagged by `/paad:agentic-review` as out of scope for the branch
> on which they were found.** They may be stale, may already have been fixed by other
> means, may no longer apply after refactors, or may simply have been judged not worth
> addressing. Verify each entry against the current code before acting on it. Entries
> are removed only when explicitly addressed — no automatic cleanup.

---
```

**Per-entry shape:**

```markdown
## `<id>` — <one-line title>
- **File (at first sighting):** `path/to/file:line`
- **Symbol:** `<function or class name>`
- **Bug class:** Logic | Error Handling | Contract | Concurrency | Security
- **Description:** ...
- **Suggested fix:** ...
- **Confidence:** High | Medium
- **Found by:** <specialist> (`<model>`)
- **First seen:** YYYY-MM-DD on branch `<branch>` at `<short-sha>`
- **Last seen:** YYYY-MM-DD on branch `<branch>` at `<short-sha>`
- **Severity:** Critical | Important | Suggestion
```

**Update rule on re-discovery:** rewrite only the `Last seen` line for that entry. Everything else is immutable so the entry remains a stable historical record.

**Removal rule:** delete the entire `## <id> — <title>` block. No tombstones, no archive.

**ID format:** 8-char hex of `sha1(file + symbol + bug-class + first-seen-iso-date)`.

### Post-review message — updated

After writing the report, tell the user in this order:

1. Report path and counts: `Critical: N (in-scope) / X (out-of-scope), Important: …, Suggestion: …`.
2. Backlog state: `Backlog: X new entries added, Y re-confirmed, Z total active.`
3. **Security disclosure warning** (only when this run added one or more `Bug class: Security` entries to the backlog): list the count, the affected files, and the line: *"`paad/code-reviews/backlog.md` is committed to this repository by default. If this repo is public or shared outside your team, decide whether to commit these security entries before pushing — you can `.gitignore` the file before the next run or remove specific entries from the current file. Note: if the backlog was already committed in a previous run, `.gitignore` alone does not remove entries from git history — you must rewrite history (e.g. `git filter-repo`) or accept the leak."*
4. **Backlog-size soft warning** (only when total active entries ≥ 200): *"Backlog has N active entries — consider triaging stale items."*
5. Pointer to `superpowers:receiving-code-review` for in-scope fixes, with: *"For out-of-scope findings, the report includes batched-ask handoff instructions; any agent following them will prompt you tier-by-tier and remove backlog entries by ID as items are fixed."*
6. Do not auto-fix anything. (Unchanged.)

## Edge cases

- **Backlog file missing.** First run creates `paad/code-reviews/backlog.md` with the header block and proceeds.
- **No out-of-scope findings.** Omit the entire `## Out of Scope` section *and* the handoff block. Metadata still records `Out-of-scope findings: 0`.
- **No in-scope findings but out-of-scope exists.** Write in-scope sections as `None found.` (consistent with current behavior); write the Out-of-Scope section normally.
- **Backlog write fails.** Surface the error and write the report anyway. The report is the authoritative deliverable; the backlog is a convenience layer.
- **Empty diff.** Covered by existing pre-flight.
- **Renamed files.** Findings on the new path are classified normally against the touched-lines map. The orchestrator does not attempt to translate findings between old and new paths — specialists already work against current code.
- **Newly added files.** Every line is touched; all findings on these files default in-scope (subject to the cosmetic-touch demotion rule, which will rarely apply since the lines are new).
- **Multi-line bugs.** Anchor-line classification is the rule; reasoning-promotion handles cases where the anchor sits on an unchanged line but the bug genuinely involves the branch's edits.
- **Path filter argument.** When a path filter is supplied, the touched-lines map is filtered to that scope and the manifest is filtered to that scope — both consistent.
- **Repository visibility / sensitive findings.** `paad/code-reviews/backlog.md` is committed by default; users in public repos who want different handling are warned at write-time when Security-class entries are added (see Post-review message step 3) and may `.gitignore` the file or redact specific entries.

## Common Mistakes — additions

| Mistake | What to do instead |
|---------|-------------------|
| Treating out-of-scope findings as fixable on this branch | They are pre-existing — surface them, batch the ask, and let the user decide per tier |
| Dropping out-of-scope findings on the floor | They go in the report's Out of Scope section AND in `backlog.md` — never silently discarded |

## Out-of-scope for this design

Deliberately excluded to keep the change tractable:

- **Auto-resolve / stale archive of backlog entries** — considered and rejected. Explicit removal only; downstream agents (or the user) handle removal when items are addressed.
- **Cross-branch dedup of in-scope findings** — only out-of-scope findings touch the backlog.
- **One-by-one ask for Critical out-of-scope** — initially considered; superseded by uniform batched-ask across all tiers.
- **Verifier-driven backlog garbage collection** — agentic-review never deletes backlog entries.
- **Atomic backlog writes / crash safety** — markdown file, low corruption risk in practice; if needed later, write-temp-then-rename can be added without changing the design.
- **Re-classifying severity on re-discovery** — backlog entries store severity at first sighting and are immutable except for `Last seen`. The current report reflects current severity; the backlog reflects history.
- **8-char ID collision risk** — birthday paradox bites near 10K entries; not a practical concern at expected backlog sizes.
- **Default-by-policy security handling** (e.g., automatic `.gitignore` for security entries, two-file split) — rejected in favor of public-by-default plus a write-time warning so users can decide per run.
