# Security findings go to `paad/security/`

**Date:** 2026-09-12
**Branch:** `ovid/security`
**Status:** implemented, 10/10 agentic-review, 10/10 test-roadmap

## Problem

Developers run paad skills, commit the output, and push it to repositories
anyone can read. When the output is a security finding, the repository now
publishes its own attack map. `agentic-owasp` writes whole reports of live
weaknesses to `paad/owasp-reviews/` and only *argues* against committing them.
`test-roadmap` logs suspected bugs to `paad/test-roadmap/test-roadmap-findings.md`
and then instructs the agent to `git add` it. `agentic-review` puts
`Bug class: Security` entries in a backlog that is committed by design.
`agentic-architecture`, `pushback` and `agentic-dedup` all have a security
lens and write into their ordinary reports.

## Decision

Every security finding, from every skill, is written only under
`paad/security/`, a directory that ignores itself. Ordinary reports carry a
count and a pointer, nothing more, so they stay safe to commit.

## The shared paragraph

Skills have no include mechanism. Like the configuration paragraph, one
"Security findings" paragraph is copied verbatim into each of the six skills
that can produce a security finding: `agentic-owasp`, `agentic-review`,
`test-roadmap`, `agentic-architecture`, `pushback`, `agentic-dedup`.
`make check-security` enforces the copy.

The paragraph says four things.

1. **Definition.** A finding is security-related if reading it would help an
   attacker. Examples: the OWASP Top 10:2025 categories, plus anything in a
   payment, tenant-isolation, or secret-handling path. On the edge, treat it
   as security.
2. **Destination.** Security findings are written only under
   `paad/security/`, in `<skill>-<the skill's usual stamp>.md`. Before the
   first write of a run, the skill ensures `paad/security/.gitignore` exists
   containing a single `*`. It creates the file if absent and never rewrites
   it if present.
3. **The main report.** Where the finding would have gone, the report carries
   one line: `N security finding(s) written to paad/security/<file>`. No
   path, severity, symbol, or description.
4. **Post-Review block.** Emitted once. Mixed skills emit it only when N > 0;
   `agentic-owasp` emits it always.

   ```
   Security: N finding(s) in paad/security/<file> (new|updated).
   paad/security/.gitignore keeps the directory out of git. Deleting that file or `git add -f` bypasses it.
   Also list paad/security/ in your root .gitignore, or in .git/info/exclude to keep the rule local and unmentioned.
   If anything under paad/security/ was ever committed, ignoring it now does not remove it from history.
   paad/security/ is scratch, not state: it exists only on this machine, `git clean -x` deletes it, and nothing brings it back.
   ```

   The last line is a durability warning, not a leak warning. Measured against
   git 2.53.0: with the `*` ignore file, `git status` is clean, `git add -A`
   stages nothing, and an explicit `git add` of a file inside refuses without
   `-f`. `git clean -fd`, `git stash -u`, and branch checkout leave the
   directory intact; `git clean -fdx`/`-fdX` delete it; `git stash -a` stashes
   it and `stash pop` restores it; a new worktree does not contain it. A root
   `.gitignore` entry behaves identically on every one of those, so there is no
   safer placement, only the extra line for the developer who deletes the local
   ignore file.

The exporter already rewrites `paad/` to `.reviews/`, so Kiro, Antigravity
and Pi get `.reviews/security/` with the same ignore file. No generator change.

## Per-skill changes

- **agentic-owasp.** Every `paad/owasp-reviews/` path becomes
  `paad/security/`. Report: `paad/security/owasp-<scope>-<stamp>-<sha>.md`.
  Index stays OWASP's own at `paad/security/INDEX.md`, same schema, same
  structural guard. Proof scripts, today written "under the report directory", go
  under `paad/security/<report-stem>-proofs/`. The "why committing is a bad bet" passage
  collapses to the shared block plus one OWASP-specific line: a committed
  report ages into a false clearance. Cross-run reading checks both
  `paad/security/` and, if present, the old `paad/owasp-reviews/`.
- **agentic-review.** Security specialist and `references/security.md`
  unchanged. The verifier applies the shared paragraph's definition to every
  finding it sees and retags a qualifying one to `Bug class: Security`,
  whichever specialist found it — an off-by-one in a refund calculation is a
  security finding under the definition even though the Logic specialist found
  it. The orchestrator then routes by bug class alone, no second judgment: it
  writes `Bug class: Security` findings, in scope and out, to
  `paad/security/code-review-<branch>-<stamp>-<sha>.md`. Security backlog
  entries go to `paad/security/backlog.md`, same schema and IDs. The
  pre-filter reads both backlogs and hands the verifier one merged slice. The
  existing step-4 security warning is replaced by the shared block. The
  backlog lifecycle prose ("`git log` on the file is the audit trail") is
  scoped to the committed backlog: security entries have no history and no
  sharing across clones, so a teammate's run mints its own IDs and the
  "re-confirmed" count in Post-Review means re-confirmed on this machine.
- **backlog.** Clean and Fix read both `paad/code-reviews/backlog.md` and
  `paad/security/backlog.md`, and write each entry back to the file it came
  from. Without this, security entries have no consumer. The printed commit
  command covers only the committed backlog; edits to the security backlog are
  reported in the artifact list and never committed.
- **test-roadmap.** Findings that pass the disclosure test go to
  `paad/security/test-roadmap-findings.md` instead of the normal findings
  log. The build-mode `git add` list and the execute-mode commit invariant
  gain one sentence: never `git add -f` anything under `paad/security/`.
  Post-Review names the security log with no description. The
  roadmap's pointer to a routed entry is a count line only, and the test that
  pins it is named for input and outcome, never for the weakness, since both
  are committed.
- **agentic-architecture, pushback, agentic-dedup.** Qualifying findings go to
  `paad/security/<skill>-<stamp>.md`; the main report keeps count and pointer;
  Post-Review emits the block when N > 0. For pushback the rule covers the
  pushback report only. A requirement the user agrees to add to their spec
  ("this endpoint must require auth") is a requirement, not a finding, and is
  theirs to commit; Phase 3 writes it into the spec as it does today.
- **Digraphs.** Each of the six gains one node for the split, since it is a
  gate the agent could skip.

## Migration (warn-only)

Nothing is edited automatically. The goal is to keep this change small.

- **OWASP reports.** A run that finds `paad/owasp-reviews/` adds one
  Post-Review line: move it under `paad/security/`; a committed copy stays in
  history. Prior reports are read from both locations, so nothing breaks if
  the developer never moves it.
- **Backlog entries.** `agentic-review` reads `Bug class: Security` entries
  from the old `paad/code-reviews/backlog.md` for dedup but never edits that
  file. A finding that matches one is copied into `paad/security/backlog.md`
  under its original ID, so the ID survives the move. Post-Review says how
  many were copied and tells the developer to delete the committed copies,
  and how many unmatched legacy entries remain to move by hand.
  `/backlog` Clean mode finishes the migration: a committed entry whose ID is
  also in the security backlog is a merge-loser it deletes in Pass B.
- **This repo.** Move the local untracked `paad/owasp-reviews/` under
  `paad/security/` by hand first, then swap the root `.gitignore`'s single
  `paad/owasp-reviews/` line for `paad/security/`. In that order: the other order
  leaves live findings visible to `git add -A` in between.
- **Nothing else moves.** Non-security reports, the roadmap, the analysis
  file and the ordinary findings log stay where they are and stay
  committable.

## Checks, docs, verification

- `make check-security` joins the per-tree block: the six skills carry the
  shared paragraph verbatim, and `paad/security/` appears only in an explicit
  allowlist — the six, `paad-help` (documents it), and `backlog` (consumes
  it). Any other skill mentioning the path fails. Same skip rule as
  `check-config` for a shipped tree that predates it.
- `paad-help` gains a short "Security findings" note and updated artifact
  lines for the six skills and `backlog`. README changes land on the release branch.
  Changelog: one `### Changed` entry, three lines, under `[Unreleased]`.
- Verification: drive `agentic-review` and `test-roadmap` against a scratch
  repo with a planted injection bug, ten runs each, pass is ten of ten. Three
  runs pass a one-in-five routing miss about half the time, and a miss here is
  the leak. Pass means the main report has only the count-and-pointer line,
  the security file has the finding, and `git status` shows nothing under
  `paad/security/`.
