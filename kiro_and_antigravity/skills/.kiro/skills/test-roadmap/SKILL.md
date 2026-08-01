---
name: test-roadmap
description: >
  EXPERIMENTAL. Analyzes a repository and any existing test suite, grades
  existing tests for weakness, classifies mocks, emits a phased roadmap for
  building a test suite that catches real regressions, then executes those
  phases one at a time. Use when planning or building a test suite, assessing
  whether existing tests are worth anything, adding tests to a legacy codebase,
  or when the user mentions test coverage, test strategy, or weak tests. Not for
  reviewing a branch for bugs, and not for fixing the bugs it logs.
compatibility: Requires git
---

**On invocation:** announce "Running paad:test-roadmap v1.22.0" before anything else.

> **EXPERIMENTAL SKILL.** Its arguments, output paths, and behavior may
> change or be withdrawn in any release, including patch releases. It is not
> covered by the semver guarantees the other paad skills carry. Unlike every
> other paad skill, this one **writes code and commits it** — tests, one commit
> per phase, onto your working branch. Report rough edges at
> <https://github.com/Ovid/paad/issues>.

# test-roadmap

This file is the router. The routing itself stays dumb on purpose: one check,
two routes, nothing else. A couple of preconditions guard it first. All the
substance — grading, planning, writing tests, bug injection — lives in
`references/` and loads only once routing has picked a mode.

**Pre-flight and routing:**

```dot
digraph route {
  "Inside a git repo?" [shape=diamond];
  "STOP: needs a git checkout" [shape=box, style=bold];
  "Detached HEAD?" [shape=diamond];
  "origin/HEAD pointer resolves?" [shape=diamond];
  "Current branch == default branch?" [shape=diamond];
  "Name matches a well-known primary (main/master/trunk/develop/...)?" [shape=diamond];
  "ASK: is this your main development line?" [shape=diamond];
  "OFFER: create a working branch" [shape=box];
  "Developer agrees?" [shape=diamond];
  "STOP: never build on the primary branch" [shape=box, style=bold];
  "git switch -c <name>" [shape=box];
  ".reviews/test-roadmap/test-roadmap.md exists?" [shape=diamond];
  "Load references/build-test-roadmap.md (Detect, Grade, Plan, Critique, Write)" [shape=box];
  "Load references/execute-test-roadmap.md (next phase, break-it-check, commit)" [shape=box];

  "Inside a git repo?" -> "STOP: needs a git checkout" [label="no"];
  "Inside a git repo?" -> "Detached HEAD?" [label="yes"];
  "Detached HEAD?" -> "OFFER: create a working branch" [label="yes"];
  "Detached HEAD?" -> "origin/HEAD pointer resolves?" [label="no"];
  "origin/HEAD pointer resolves?" -> "Current branch == default branch?" [label="yes (authoritative)"];
  "origin/HEAD pointer resolves?" -> "Name matches a well-known primary (main/master/trunk/develop/...)?" [label="no"];
  "Current branch == default branch?" -> "OFFER: create a working branch" [label="yes"];
  "Current branch == default branch?" -> ".reviews/test-roadmap/test-roadmap.md exists?" [label="no"];
  "Name matches a well-known primary (main/master/trunk/develop/...)?" -> "OFFER: create a working branch" [label="yes"];
  "Name matches a well-known primary (main/master/trunk/develop/...)?" -> "ASK: is this your main development line?" [label="no"];
  "ASK: is this your main development line?" -> "OFFER: create a working branch" [label="yes / unsure"];
  "ASK: is this your main development line?" -> ".reviews/test-roadmap/test-roadmap.md exists?" [label="no"];
  "OFFER: create a working branch" -> "Developer agrees?";
  "Developer agrees?" -> "STOP: never build on the primary branch" [label="no"];
  "Developer agrees?" -> "git switch -c <name>" [label="yes"];
  "git switch -c <name>" -> ".reviews/test-roadmap/test-roadmap.md exists?";
  ".reviews/test-roadmap/test-roadmap.md exists?" -> "Load references/execute-test-roadmap.md (next phase, break-it-check, commit)" [label="yes"];
  ".reviews/test-roadmap/test-roadmap.md exists?" -> "Load references/build-test-roadmap.md (Detect, Grade, Plan, Critique, Write)" [label="no"];
}
```

## Before routing: confirm you're in a repo

`compatibility: Requires git` above means this skill needs a working git
checkout — build mode fans out grading subagents against the tree as it
stands, and execute mode's `break-it-check` gate runs bug injection in a
disposable `git worktree`. If the current directory isn't inside a git repo,
say so and stop before loading either mode file.

## Before routing: confirm you're on a working branch

This skill commits as it goes — build mode commits the roadmap, execute mode
commits each phase's tests — all onto the branch you are on right now. A
half-built test suite landing on the developer's main development line is exactly
what this check prevents, the same spirit as running a code review on a feature
branch rather than on `main`. So before routing, confirm the current branch is a
*working* branch, not the primary one.

Identify the primary branch from repo signals, in order — stop at the first that
decides:

1. **Detached HEAD** — `git symbolic-ref -q HEAD` prints nothing. There is no
   branch for the suite to accumulate on at all; treat it like being on the
   primary branch and offer a working branch (below).
2. **The repo's own default-branch pointer** — `git symbolic-ref -q --short
   refs/remotes/origin/HEAD` resolves to e.g. `origin/main`; strip the remote
   prefix for the default branch name. If the current branch (`git symbolic-ref
   -q --short HEAD`) equals it, you are on the primary branch. This is the
   authoritative signal and needs no built-in list of names.
3. **No such pointer** (a local-only repo, or one where it was never set) — fall
   back to the well-known primary names: `main`, `master`, `trunk`, `develop`,
   `devel`, and the like — **examples, not a closed list**, the same stance
   Stage 1 takes on manifests. If the current branch name matches one, treat it
   as primary. If it matches none *and* step 2 could not confirm, **ask the
   developer once, in plain words**, whether this is their main development line —
   never silently proceed on a branch that might be it. Being wrong toward asking
   costs a keystroke; being wrong toward building on the main line is the harm
   this check exists to prevent.

**When the current branch is the primary one (or HEAD is detached), do not route
yet.** Say why in plain words — *"I build the test suite up commit by commit, and
you don't want those landing on your main branch while it's half-done, so let's
put them on a working branch"* — then offer to make one: propose a name
(`test-roadmap` is a fine default), and on the developer's OK run `git switch -c
<name>` (or `git checkout -b <name>` on older git) and continue to routing. If
they decline, stop — never build or execute on the primary branch.

This is the skill's **one** branch: a single working branch, created at
invocation only when needed. It is **not** a per-phase branch — execute mode
still commits every phase onto whatever working branch you are on, and the suite
accumulates there (see `references/execute-test-roadmap.md § What execute mode
writes`). Both mode files assume this check has already passed and never re-run
it; the guard lives here, once.

## Route

```
.reviews/test-roadmap/test-roadmap.md exists?  →  load references/execute-test-roadmap.md
                       absent  →  load references/build-test-roadmap.md
```

That is the entire routing logic — one file existence check, two branches.
`.reviews/test-roadmap/test-roadmap.md` is the roadmap this skill itself writes at the end of
build mode, so its presence is exactly the signal that a previous run already
did Detect/Grade/Plan/Critique/Write and there is a phased plan to execute
against. Its absence means this is either the first run against this repo, or
a run after that file was deleted — either way, build it.

If it ever grows a third condition, that is a signal something has been put
in the wrong place — take it back to `build-test-roadmap.md` or
`execute-test-roadmap.md`, not to this file.

This router never loads `references/break-it-check.md`,
`references/test-pushback.md`, or `references/test-theater.md` directly.
Those three are loaded by whichever of the two mode files needs them, at the
point in their own protocol that needs them — not from here.

## Entering build mode

Before build mode can plan anything, it needs to know what it's planning
for. The first thing it does — Stage 1, Detect — is identify the stack from
manifests and config rather than assumption (`package.json`,
`pyproject.toml`, `go.mod`, `Cargo.toml`, `Gemfile`, and so on: examples, not
a closed table), then determine how tests are invoked and what test files
already exist. The skill must never hardcode a language; where it needs a
per-ecosystem fact, it looks for the signal in the repo instead of consulting
a built-in list.

The full five-stage protocol — Detect, Grade, Plan, Critique, Write — lives
in `references/build-test-roadmap.md`. Load it now if
`.reviews/test-roadmap/test-roadmap.md` is absent.

## Entering execute mode

Load `references/execute-test-roadmap.md` now if `.reviews/test-roadmap/test-roadmap.md`
exists. It reads that file's `## Decisions` section once, selects the next
phase per the completion protocol, and gets on with writing tests — it does
not re-detect or re-ask anything build mode already settled.
