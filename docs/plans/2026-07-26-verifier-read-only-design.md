# Verifier subagents must not mutate the working tree

**Date:** 2026-07-26
**Status:** Design approved, not yet implemented

## Problem

Verifier and specialist subagents in paad's multi-agent analysis skills have been
observed editing the developer's source code to test their findings — changing a
line and running tests to confirm a bug is real. This must never touch the
working tree.

Nothing in those skills forbids it. `agentic-review/references/verifier.md` says
"reject anything you cannot confirm by reading the code," but that is a quality
instruction, not a filesystem boundary. Every subagent is dispatched as prose
("using the Agent tool") with no `subagent_type`, so every one of them inherits a
default toolset that includes `Edit` and `Write`.

## Scope

Four skills dispatch subagents and need the fix:

- `agentic-review` — 6–12 parallel specialists (`SKILL.md:152`), Phase 3 Verifier (`:203`)
- `agentic-dedup` — specialists, Phase 4 Verifier
- `agentic-a11y` — 2 dispatch sites
- `agentic-architecture` — 1 dispatch site

`alignment` and `pushback` are out of scope: they dispatch no subagents, and their
main agent legitimately writes a report. The rule applies to subagent prompts only.

## Rejected: a disposable-worktree escape hatch

The first instinct was to give verifiers a sanctioned place to mutate — a throwaway
git worktree, following the prior art in
`test-roadmap/references/break-it-check.md`. Adversarial review killed it.

**It answers the wrong question.** Running the existing test suite, a linter, or a
type checker *unchanged* is read-only and needs no machinery. Only
mutation-to-confirm needs isolation, and no finding class in these four skills
requires it:

| Skill | Execution case | Verdict |
|---|---|---|
| agentic-architecture | none — no test confirms "god object" or "tight coupling" | zero use case |
| agentic-dedup | running two implementations does not prove semantic equivalence; that needs differential testing over an input domain | out of reach of this machinery |
| agentic-a11y | axe / VoiceOver against a *running app* | read-only, unrelated to a source worktree |
| agentic-review | run the existing suite | read-only |

**And every ownership model breaks.** One worktree per dispatched agent means 13
checkouts for a single large review (`agentic-review/SKILL.md:199` mandates 12
specialists plus the verifier), each missing the gitignored build artifacts
(`node_modules/`, `target/`, venv) that `break-it-check.md:57-62` says the skill
cannot language-agnostically reinstall — so expensive the agent skips the
sanctioned path and mutates in-tree anyway. One worktree per subagent, created on
demand, puts cleanup inside the process most likely to die, with no orchestrator
holding a handle to sweep. One shared worktree needs a mutex across parallel
subagents that have no channel to each other.

There is also a correctness trap: `agentic-review/SKILL.md:118` permits a dirty
tree and states the Verifier reads the *working tree*. A worktree checked out at
`HEAD` is neither the working tree nor the diff base, so any worktree scheme
silently verifies a third version of the code that nobody reviewed.

**What hard read-only costs:** a verifier occasionally reports Medium instead of
High confidence. `verifier.md` already has that gradation. That is the entire
price.

`break-it-check` keeps its worktree — mutation testing *is* its product.

## Design

### 1. A restricted agent definition

`plugins/paad/agents/paad-analyst.md`, sibling of `skills/`:

```markdown
---
name: paad-analyst
description: Read-only analysis subagent for paad's multi-agent skills...
tools: Read, Grep, Glob, Bash
---
```

The body stays short — this file exists for the `tools:` line. Behavior stays in
each skill's dispatch prompt, where it already lives.

Omitting `Edit`, `Write`, and `NotebookEdit` is the whole enforcement, and it is
mechanical: the harness never hands the subagent the tool, so no amount of budget
pressure recovers it. Dispatched as `subagent_type: paad-analyst`, which resolves
as `paad:paad-analyst` when installed from the marketplace — the same namespacing
`superpowers:code-reviewer` uses.

**Known limit, stated honestly:** `Bash` stays, so `sed -i`, `>` redirection, and
`git checkout` remain reachable. This closes the observed failure mode (Edit-tool
mutation), not the whole category. Dropping `Bash` would break the specialists in
`agentic-dedup` and `agentic-architecture`, which do their own `git` / `find`
recon rather than receiving file contents in the prompt.

Deferred: a second, Bash-less `paad-verifier` type for verifiers that receive all
file contents in the prompt (`agentic-review/SKILL.md:212`). Add it if the Bash
hole is ever observed being used.

### 2. The prose backstop

Added verbatim to each specialist and verifier dispatch prompt in the four skills,
alongside the untrusted-input clause they already carry:

> Do not modify any file in the repository. You may run read-only commands
> (existing tests, linters, type checkers) unchanged. If confirming a finding
> would require changing code, do not — report it at Medium confidence and state
> what would confirm it.

Four lines duplicated four times cannot meaningfully drift, so this needs no
shared-reference mechanism, sync script, or `make` target. (There is no cross-skill
reference mechanism anyway — `scripts/check_references.py` enforces per-skill
`references/`.) The rule covers the two places the agent definition cannot reach:
the `Bash` hole, and the exported copies described next.

### 3. Export handling

`scripts/convert_skills.py` exports these skills to Kiro and Antigravity, which
have no `agents/` or `subagent_type` mechanism. Add a `neutralize()` rule
stripping `subagent_type: paad-analyst` from dispatch lines, so exported skills
don't instruct a foreign harness to use an agent type that doesn't exist there.
The 4-line rule survives the export untouched and becomes the only protection on
those platforms.

## Separate bug fix: `break-it-check` worktree handling

Found during review, unrelated to the design above, fixed on the same branch.
`test-roadmap/references/break-it-check.md:40-53`:

1. **The worktree path must move out of `.git/`.** `git worktree add
   .git/test-roadmap-worktrees/<phase>` hard-fails with `fatal: could not create
   leading directories of '.git/…/.git': Not a directory` in a `git worktree add`
   checkout, a submodule, or a `--separate-git-dir` repo — because `.git` is a
   *file* there, not a directory. Verified empirically on git 2.53.0. This is not
   hypothetical for this project: `agentic-dedup/SKILL.md:167-178` already detects
   both configurations and records them in Review Metadata.

2. **The sweep must stop being prefix-only.** `break-it-check.md:43` filters
   worktrees by a fixed path prefix, which identifies "worktrees under this path,"
   not "worktrees belonging to *my* run." A second Claude Code session's sweep
   force-removes a live sibling run's worktree mid-mutation. Reproduced. The
   existing prose only reasons about the developer's hand-made worktrees, never a
   concurrent session — which is the likelier collision for a skill whose
   pre-flight tells users to start a fresh session. Fix: per-run unique suffix,
   and sweep by mtime age rather than prefix alone.

## Enforcement summary

| Layer | Enforces | Limit |
|---|---|---|
| `tools:` in `paad-analyst.md` | mechanically — tool is never handed to the subagent | `Bash` remains |
| 4-line prompt rule | advisory | budget pressure can skip it |
| Export neutralization | keeps foreign harnesses from a dangling reference | prose-only on those platforms |

Prose alone was rejected as the sole fix: `agentic-review/SKILL.md:212` says in
its own voice that a subagent under budget pressure pattern-matches instead of
doing the work, and a 15-line protocol is exactly the paragraph such an agent
skips. The `tools:` restriction is the only part that actually enforces.

## Implementation checklist

- [ ] `plugins/paad/agents/paad-analyst.md`
- [ ] `subagent_type: paad-analyst` at all dispatch sites in the four skills
- [ ] 4-line read-only rule in each specialist and verifier prompt
- [ ] `neutralize()` rule in `scripts/convert_skills.py`
- [ ] `break-it-check.md`: worktree out of `.git/`, run-scoped + mtime sweep
- [ ] `agents/` added to the CLAUDE.md project-structure tree
- [ ] `CHANGELOG.md` under `[Unreleased]`
- [ ] `make bump-version VERSION=X.Y.Z` — minor (new user-facing behavior)
- [ ] `make test`

No `paad:help` or `README.md` entries — `paad-analyst` is not a skill.
