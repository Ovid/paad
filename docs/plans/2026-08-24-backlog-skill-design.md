# `/backlog` skill — design

*2026-08-24*

## Problem

`docs/FIX-BACKLOG.md` specified a backlog-lifecycle system — a multi-file
`paad/backlog/` split, a cold `archive/` tree, resolution-metadata schemas, a
CONFIRMED/RESOLVED/SUPERSEDED/UNCERTAIN taxonomy, context-budget doctrine, and
nine lifecycle test cases — hung off two skills, `/next-task` and
`/curate-backlog`, that were never built. None of that machinery exists. The
only backlog in the repo is the single flat file `paad/code-reviews/backlog.md`
that `/agentic-review` already writes (out-of-scope bugs, explicit-removal
lifecycle).

The spec is over-built for the reality. This design collapses it to **one skill,
`/backlog`, with two modes**, operating on the file that already exists.

## Decisions

| Fork | Choice |
|---|---|
| Resolved-item lifecycle | **Delete the entry.** The resolution note rides in the commit message that removes it. No `resolved.md`, no `archive/` tree, no metadata schema. `git log -- paad/code-reviews/backlog.md` is the archive. |
| File layout | **One flat file**, `paad/code-reviews/backlog.md`. No migration, no per-source split. |
| Clean mode | **Both** — re-verify each entry against HEAD (drop the fixed/gone), then dedupe/merge. |
| Next-item mode | **Fix end-to-end** — pick, fix, validate, then remove the entry. |
| Fix routing | **Bugs only in v1.** Drop the `/fix-architecture` branch until a skill actually writes architecture entries to this file. |

## Shape

One skill: `preview/paad/skills/backlog/SKILL.md`. Replaces the imagined
`/next-task` + `/curate-backlog`.

On invocation (after the announce line):

1. Backlog missing or empty → "Backlog is empty. Run `/agentic-review` to
   populate it." and stop.
2. Otherwise read it, show one line per entry (id, severity, file, one-line
   desc), and ask the routing question:

   ```
   Backlog: N items. What do you want to do?
     [1] Clean — re-verify against current code, drop the resolved, dedupe
     [2] Fix   — pick the next item and fix it end-to-end
   ```

`$ARGUMENTS`: `/backlog clean` / `/backlog fix` skip the menu; bare `/backlog`
shows it. Positional, no flags.

## Clean mode

**Pass A — verdict.** One `paad:paad-analyst` per entry (read-only) returns
`STILL-PRESENT` / `RESOLVED` / `GONE`, each with cited evidence (the lines it
read). Entries batched, analysts run in parallel — this is the "load only what
you need" concern, handled by dispatch fan-out instead of doctrine.

**Pass A′ — adversarial verification of removals only.** A false `RESOLVED`
deletes a still-real bug, so every `RESOLVED`/`GONE` candidate goes to a second,
independent `paad:paad-analyst` prompted to **refute the removal** ("prove this
bug is still present"):

- Verifier agrees it's gone → eligible for deletion.
- Verifier finds it still present → verdict flips to `STILL-PRESENT`, entry stays.
- Disagreement / can't confirm → entry stays. **Ambiguity never deletes.**

`STILL-PRESENT` verdicts need no verification — keeping an item is the safe
direction. This is the same find → independently-verify shape as
`/agentic-review`, scoped to the one irreversible action.

**Pass B — dedupe/merge.** Over the survivors, collapse entries describing the
same defect (same file+symbol+bug-class, or semantically equivalent). Merge
keeps the oldest `first_seen`, newest `last_seen`, one description. A merge that
loses an entry is recoverable from git, so it does not need the adversarial gate.

**Removal + archive.** Delete everything marked `RESOLVED`/`GONE` plus merge
losers, then commit with the resolution notes in the message:

```
backlog: clean — 3 resolved, 1 obsolete, 2 merged

resolved a1b2c3d4 Missing auth check (fixed at <sha>)
obsolete e5f6a7b8 Null deref in parser (symbol removed)
...
```

## Fix mode

**Pick.** Rank surviving entries by severity, then age (`first_seen`). Propose
the top one; user accepts or picks another. **One item per run** — no
batch-fixing.

**Fix.** Ordinary bug (what agentic-review produces today) → fix directly, or
via `/vibe` if it's a small same-module change. Per-fix commits.

**Validate — the removal gate.** Editing code is not evidence the bug is
resolved. Before touching the backlog:

1. Run the project's tests/checks (`make test`, or the repo's equivalent).
2. One independent `paad:paad-analyst` confirms the specific bug the entry
   described is now actually gone — the same adversarial refutation used in Clean.
3. Both pass → delete the entry, commit with the resolution note
   (`resolved <id> <desc> (fixed at <sha>)`).

Validation fails → entry stays, skill reports what's still wrong. A fix that
doesn't validate never silently removes its backlog item.

## Digraph coverage

`empty-check → menu → {clean: verdict → verify-removals → dedupe → commit}` /
`{fix: pick → fix → test+verify → remove-or-keep}`, with the two "stays on
ambiguity / failure" gates as explicit nodes.

## Fate of `docs/FIX-BACKLOG.md`

Delete it. It was the spec for the over-built version and describes machinery
(`archive/` tree, metadata schema) nobody should build. No downstream consumers.

## Plumbing checklist (implementation)

- `preview/paad/skills/backlog/SKILL.md` — frontmatter `name: backlog`,
  `description`, `metadata: internal: true`; announce line as first body line
  with `-preview` suffix; digraph after the intro, before the first `##`;
  `$ARGUMENTS` section.
- Every dispatched agent `subagent_type: paad:paad-analyst`, read-only (no
  Edit/Write on verify agents).
- `paad-help` — overview table row + detail section.
- `CHANGELOG.md` — `### Added` under `[Unreleased]`.
- Leave `README.md` alone until release.
- `make export && make test`; then drive for real with
  `claude --plugin-dir ./preview/paad`.
- No version bump here — that is the release's job.
