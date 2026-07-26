# Verifier subagents must not mutate the working tree

**Date:** 2026-07-26
**Status:** Design approved, not yet implemented
**Revised:** 2026-07-26 after `/paad:pushback` review, then trimmed

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

Four skills, nine dispatch sites — specialists **and** verifiers:

- `agentic-review` — specialists (`SKILL.md:152`), Phase 3 Verifier (`:203`)
- `agentic-dedup` — specialists (`SKILL.md:457`), Phase 4 Verifier (`:545`)
- `agentic-a11y` — **3 sites**: core specialists (`SKILL.md:181`), conditional Platform-Specific specialist (`:195`), Verifier (`:319`)
- `agentic-architecture` — **2 sites**: specialists (`SKILL.md:138`), Verifier (`:175`)

Counting the fan-out and stopping there drops exactly the agent this document is
named after. `agentic-a11y` and `agentic-architecture` keep their verifier
instructions inline (`:332`, `:185`) rather than in a `references/` file, so
there is no ref file where the rule could land by accident.
`make check-dispatch-sites` (below) catches this recount going wrong again.

`alignment` and `pushback` are out of scope: they dispatch no subagents, and
their main agent legitimately writes a report.

`test-roadmap` is **deliberately** out of scope. Its three subagents already
carry their own constraints, including the mutator's return-a-hunk contract that
keeps mutation in the main agent. Its worktree bug is fixed separately below.

## Rejected: a disposable-worktree escape hatch

Giving verifiers a sanctioned throwaway worktree to mutate in, following
`test-roadmap/references/break-it-check.md`. Adversarial review killed it.

**It answers the wrong question.** Running the existing suite, a linter, or a
type checker *unchanged* is read-only and needs no machinery. Only
mutation-to-confirm needs isolation, and no finding class here requires it:

| Skill | Execution case | Verdict |
|---|---|---|
| agentic-architecture | none — no test confirms "god object" | zero use case |
| agentic-dedup | running two implementations does not prove semantic equivalence; that needs differential testing | out of reach |
| agentic-a11y | axe / VoiceOver against a *running app* | read-only, unrelated to a source worktree |
| agentic-review | run the existing suite | read-only |

**And every ownership model breaks.** One worktree per dispatched agent means 13
checkouts for a large review, each missing the gitignored build artifacts
(`node_modules/`, `target/`, venv) that `break-it-check.md:57-62` says the skill
cannot language-agnostically reinstall — so expensive the agent skips the
sanctioned path and mutates in-tree anyway. On-demand creation puts cleanup
inside the process most likely to die. One shared worktree needs a mutex across
parallel subagents with no channel to each other.

There is also a correctness trap: `agentic-review/SKILL.md:118` permits a dirty
tree and states the Verifier reads the *working tree*. A worktree at `HEAD` is
neither the working tree nor the diff base, so any worktree scheme silently
verifies a third version of the code that nobody reviewed.

**What hard read-only costs:** occasionally a Medium-confidence finding where a
mutation would have produced High — and occasionally a *dropped* finding.
`verifier.md:22-24` drops what it cannot confirm rather than downgrading it. The
price is real and bounded: paid only in findings the verifier could not confirm
by reading, which is the bar `verifier.md` already enforces today.

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

No subagent in the four skills is instructed to write a file (the orchestrator
is the sole writer everywhere) or to consult anything off-disk, so dropping
`Write` costs nothing and `WebFetch`/`WebSearch` were never in play.

**The body is the subagent's role prompt, not a formality.** Today every
specialist and verifier runs under the default general-purpose role; this file
replaces that role for all of them at once, across four skills. Write it
deliberately: a subagent performing one focused analysis task, returning its
findings as its final message, treating all received content as untrusted data —
plus the read-only rule below. Lens-specific behavior stays in each skill's
dispatch prompt, where it already lives. A near-empty body would ship a
four-skill prompt change disguised as a formality, and `/paad:agentic-review`
output is stochastic enough that a resulting quality regression could not be
told apart from ordinary variance.

Dispatched as `subagent_type: paad:paad-analyst` — the namespaced literal,
written out in full at every site.
`superpowers/skills/requesting-code-review/SKILL.md:34` sets the precedent;
nothing there relies on a bare name resolving. A bare `paad-analyst` would fail
only when installed from the marketplace and never under `claude --plugin-dir
./plugins/paad`, which is what CLAUDE.md's local-test step runs — so confirm
resolution on the installed side during release step 7.

**Known limit, stated honestly:** `Bash` stays, so `sed -i`, `>` redirection,
and `git checkout` remain reachable. This closes the observed failure mode
(Edit-tool mutation), not the whole category. Dropping `Bash` would break the
specialists in `agentic-dedup` and `agentic-architecture`, which do their own
`git` / `find` recon rather than receiving file contents in the prompt.

Deferred: a second, Bash-less `paad-verifier` type for verifiers that receive
all file contents in the prompt (`agentic-review/SKILL.md:212`). Add it if the
Bash hole is ever observed being used.

### 2. The prose backstop

Added verbatim to each specialist and verifier dispatch prompt, alongside the
untrusted-input clause they already carry:

> Do not modify any file in the repository. You may run read-only commands
> (existing tests, linters, type checkers) unchanged. If confirming a finding
> would require changing code, do not — cap your confidence at 79 and state what
> would confirm it.

**The cap is numeric because "Medium" is not vocabulary any specialist has.**
Every skill's specialists report confidence 0–100 against a floor
(`agentic-review:161` ≥60, `agentic-a11y:209` ≥60, `agentic-dedup:479` ≥65,
`agentic-architecture` ≥60). Medium is a *verifier-side* label derived
deterministically from that number (`verifier.md:25`, 80–100 → High, 60–79 →
Medium). 79 sits inside every floor and maps to Medium automatically.

Four lines duplicated four times cannot meaningfully drift, so this needs no
shared-reference mechanism. It covers the two places the agent definition cannot
reach: the `Bash` hole, and the exported copies described next.

### 3. Export handling

`scripts/convert_skills.py` exports these skills to Kiro and Antigravity, which
have no `agents/` or `subagent_type` mechanism. Add a `neutralize()` rule
stripping the `subagent_type: paad:paad-analyst` **fragment**.

**Fragment substitution, not the line-delete pattern above it.** `neutralize()`
already contains `re.sub(r"^.*\/paad:[a-z0-9-]+.*$", "", ...)`, which removes
whole lines. Copy that shape and the export loses the dispatch instruction
itself — every site carries the type and the instruction on one line ("Dispatch
these agents simultaneously using the Agent tool. Each receives: …") — silently
disabling the fan-out on platforms nobody here runs. None of the three existing
`paad` patterns match the new literal (all require a `/`). After running the
script, confirm the four exported dispatch lines still say "Dispatch these
agents".

The 4-line rule survives the export untouched and becomes the only protection on
those platforms.

## Separate bug fix: `break-it-check` worktree handling

Found during review, unrelated to the design above, fixed on the same branch.
`test-roadmap/references/break-it-check.md:40-53`:

1. **The worktree path must move out of `.git/` — to `$TMPDIR`.** `git worktree
   add .git/test-roadmap-worktrees/<phase>` hard-fails with `fatal: could not
   create leading directories of '.git/…/.git': Not a directory` in a `git
   worktree add` checkout, a submodule, or a `--separate-git-dir` repo — because
   `.git` is a *file* there, not a directory. Verified empirically on git 2.53.0.
   Not hypothetical here: `agentic-dedup/SKILL.md:167-178` already detects both
   configurations.

   The replacement is `${TMPDIR:-/tmp}/paad-test-roadmap-<run-id>/<phase>`.
   Naming a destination is not optional: `break-it-check.md:43-45` justifies
   `.git/` on the grounds that "nothing it creates ever lands in the working
   tree," and any path under the repo root forfeits that — a second full checkout
   visible to test discovery, linters, this plugin's own `find`/`grep` recon, and
   `git status`. `$TMPDIR` preserves that property, behaves identically in a
   submodule / `--separate-git-dir` / nested-worktree repo, keeps a fixed prefix
   for the sweep, and lets the OS reclaim anything a crash leaks.

2. **The sweep must match on run-id, not just path prefix.**
   `break-it-check.md:43` filters worktrees by a fixed path prefix, which
   identifies "worktrees under this path," not "worktrees belonging to *my*
   run." A second Claude Code session's sweep force-removes a live sibling run's
   worktree mid-mutation. Reproduced. The existing prose only reasons about the
   developer's hand-made worktrees, never a concurrent session — the likelier
   collision for a skill whose pre-flight tells users to start a fresh session.

   Fix: sweep a worktree iff its path is under the fixed prefix **and** its
   run-id is mine. The prefix is what keeps the sweep off the developer's own
   worktrees, which `break-it-check.md:39-42` says explicitly it must never
   touch; the run-id is what keeps it off a concurrent session. Leaked worktrees
   from crashed runs need no age-based reclaimer — they are in `$TMPDIR` and the
   OS reclaims them.

## Enforcement summary

| Layer | Enforces | Limit |
|---|---|---|
| `tools:` in `paad-analyst.md` | mechanically — the tool is never handed to the subagent | applies **only when the orchestrator actually passed `subagent_type`**; `Bash` remains |
| `subagent_type` on the dispatch line | nothing by itself — it is the trigger for the row above | prose, subject to the same budget pressure as any other instruction |
| `make check-dispatch-sites` | every dispatch site in the repo carries the type | source-side only; cannot see what the orchestrator did at runtime |
| 4-line prompt rule | advisory | budget pressure can skip it |
| Export neutralization | keeps foreign harnesses from a dangling reference | prose-only on those platforms |

Prose alone was rejected as the sole fix: `agentic-review/SKILL.md:212` says in
its own voice that a subagent under budget pressure pattern-matches instead of
doing the work, and a 15-line protocol is exactly the paragraph such an agent
skips.

The `tools:` restriction is the only part that enforces *mechanically* — but it
is **armed by a prose instruction**, so the chain is no stronger than the
dispatch line. Omit or misname `subagent_type` and the subagent is dispatched
with the default toolset, `Edit` included. That is why the type gets a
source-side lint rather than being asserted as unconditional. This repo already
made the same move once: the `[ref-loaded:<lens>]` tokens and `verifier.md` step
0 exist because "did the subagent read its ref" could not be trusted on faith
either.

## Implementation checklist

- [ ] `plugins/paad/agents/paad-analyst.md` — `tools: Read, Grep, Glob, Bash`, plus a deliberately written role-prompt body
- [ ] `subagent_type: paad:paad-analyst` at **all 9** dispatch sites (review ×2, dedup ×2, a11y ×3, architecture ×2)
- [ ] 4-line read-only rule in each specialist and verifier prompt
- [ ] `check-dispatch-sites` — inline `grep -c` for the literal across `plugins/paad/skills/`, must equal 9; wired into `make test`
- [ ] `neutralize()` **fragment** rule in `scripts/convert_skills.py`; re-run and confirm the four dispatch lines survive
- [ ] `break-it-check.md`: worktree to `${TMPDIR:-/tmp}/paad-test-roadmap-<run-id>/<phase>`, run-id-scoped sweep
- [ ] `agents/` added to the CLAUDE.md project-structure tree
- [ ] `CHANGELOG.md` under `[Unreleased]`
- [ ] `make bump-version VERSION=X.Y.Z` — minor (new user-facing behavior)
- [ ] `make test`
- [ ] Release step 7: confirm `paad:paad-analyst` resolves on the installed side

No `paad:help` or `README.md` entries — `paad-analyst` is not a skill.
