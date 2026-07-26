# break-it-check — the mandatory anti-theater gate

**This gate is mandatory. No phase latches without it.** Execute mode's step 4
is `break-it-check`, invoked between "write the tests for this phase" and
"write `Landed:` and commit" — nothing skips it, and nothing writes `Landed:`
without it passing.

It discharges *"the test suite should fail loudly when you fix bugs."* For
each behavior named on the phase's `Catches:` line: inject that bug into a
**disposable copy** of the production code, confirm the new test goes red,
discard the copy.

The mechanism is adapted from `verification-before-completion/SKILL.md:84-88`:

```
Write → Run (pass) → Inject bug → Run (MUST FAIL) → Discard copy → Run (pass)
```

with two inversions from that skill: there is no fix to revert — the bug is
**injected** into working code — and the injection happens in a throwaway
`git worktree`, so nothing in the developer's tree is ever at risk (Inviolate
#2: production code is never permanently modified).

**When you tell the developer what you're doing, use plain words — never
"break-it-check," "the gate," "mutation," or "latch"** (see
`references/test-pushback.md § Talking to the developer`). For example: *"Before
I call these tests done, I'll make sure they actually work — I'll slip one
realistic bug into a throwaway copy of the code and confirm the tests catch it,
then throw the copy away. Your real code is never touched."* What each possible
result means for the developer is spelled out in *Explaining results*, below.

## Protocol

Six steps, in order. The order is load-bearing — steps 1 and 2 each protect
against a failure mode that only shows up if they run first.

1. **Sweep, then create one worktree for the phase.** First fix this run's
   identity. Generate it **once**, at the first `break-it-check` of the
   session:

   ```
   echo "$(date +%Y%m%d-%H%M%S)-$$"
   ```

   Record the literal it prints (e.g. `20260726-141133-48217`) and reuse that
   exact string as `<run-id>` for every phase for the rest of the session — the
   timestamp keeps it legible, the shell PID separates two sessions started in
   the same second. Never regenerate it per phase: the sweep below is scoped by
   it, and a run that changes its own id stops recognizing its own strands.

   Then reclaim any strand left by a crashed or aborted prior run:

   - `git worktree prune` — reclaims only records whose checkout directory is
     already gone; it cannot touch a live worktree.
   - Enumerate `git worktree list --porcelain` and force-remove a worktree
     **iff both hold: its path contains a `paad-test-roadmap-<id>` directory
     segment, and that `<id>` is your run-id.**

   Both arms are load-bearing and they guard against different neighbors. The
   **`paad-test-roadmap-` segment** is what keeps the sweep off the developer's
   own worktrees — this is **not** "remove all worktrees"; a developer may have
   a hand-made worktree checked out elsewhere on the same repo, and this sweep
   must never touch it. The **run-id** is what keeps the sweep off a
   *concurrent* `test-roadmap` session, which is the likelier collision for a
   skill whose pre-flight tells developers to start a fresh session: the segment
   alone identifies "worktrees this skill made," not "worktrees belonging to
   *my* run," so a sibling session's sweep would force-remove a live worktree
   out from under a running mutation. Because the run-id is embedded in the
   path, both arms are answerable from `git worktree list` output alone.

   **Match on that path segment, not on a `${TMPDIR:-/tmp}/…` string you
   construct.** The two never compare equal: git records the *resolved*
   absolute path, and on macOS `$TMPDIR` and `/tmp` both live behind symlinks
   (`/var/folders/…` is printed as `/private/var/folders/…`, `/tmp` as
   `/private/tmp`), while `$TMPDIR` itself already ends in `/`, so the
   constructed string also carries a doubled slash the record does not have. A
   constructed-prefix test silently matches nothing, which fails in the worst
   direction available: the sweep becomes a no-op and the leak it exists to
   close stays open all session.

   Scoping by run-id does mean a strand left by a *dead* session is no longer
   force-removed by the next session's sweep. That is the deliberate trade, and
   it costs nothing: the strand sits in `$TMPDIR`, which the OS reclaims, and
   once the directory is gone the unscoped `git worktree prune` above clears
   the leftover `.git/worktrees/` record. **Do not add an age or mtime arm to
   reclaim it sooner.** The worktree is created once and reused across the
   baseline plus one mutation per `Catches:` behavior, and a directory's mtime
   only moves when entries are added or removed — so a phase grinding through a
   slow suite crosses any threshold you pick and gets force-removed
   mid-mutation, which is the exact failure the run-id scoping exists to
   prevent, merely rescheduled onto a timer.

   Then create the phase's worktree: `git worktree add
   "${TMPDIR:-/tmp}/paad-test-roadmap-<run-id>/<phase>" HEAD`.

   The destination is named, not incidental. Nothing this gate creates may land
   in the working tree: a second full checkout under the repo root is visible to
   test discovery, linters, the `find`/`grep` recon in this plugin's own skills,
   and `git status` — and the skill cannot exempt it, because it does not edit
   the developer's `.gitignore`. `.git/` used to satisfy that property, but it
   **hard-fails wherever `.git` is a *file* rather than a directory** — a `git
   worktree` checkout, a submodule, a `--separate-git-dir` repo — with `fatal:
   could not create leading directories of '.git/…/.git': Not a directory`.
   Those shapes are not hypothetical here; `agentic-dedup`'s pre-flight already
   detects two of the three (submodule, and `git worktree add` checkout).
   `$TMPDIR` keeps the nothing-in-the-working-tree property, behaves identically
   in all three of those repo shapes, keeps a fixed path segment for the sweep
   to match on, and lets the OS reclaim anything a crash leaks.

   This worktree is **reused across the baseline run and every mutation in
   the phase** — one worktree per phase, not one per mutation. That reuse is
   structural, not an optimization to skip if time-pressed: a fresh checkout
   excludes gitignored artifacts (no `node_modules/`, `target/`, no venv), and
   the skill cannot know, language-agnostically, what install command would
   repopulate them or how long it takes. Paying that cost once per phase
   instead of once per mutation is the only mitigation available that doesn't
   require hardcoding an ecosystem's build tooling.

2. **Copy the phase's new test files into the worktree, *then* mutate.**
   Never the other way around. In colocated-test ecosystems — Rust's
   `#[cfg(test)] mod tests` is the reproduced case — the test file *is* the
   production file. If the mutation were applied first and the test copied
   in second, the copy would silently overwrite the mutation: the test would
   stay green, and the gate would misread a mutation that was never actually
   applied as a theater test. Copy-then-mutate is the only order that can't
   erase its own injected bug.

3. **Baseline run.** Run the phase's own tests, unmutated, in the worktree.
   They **must pass**, and the result must be **stable across two runs**. See
   the *Failure table* below for what each way of failing this step means —
   do not proceed past a baseline that isn't clean green and stable.

4. **Per behavior on `Catches:`, inject one mutation via a blind mutator
   subagent.** The subagent receives:

   - the `Catches:` behavior text,
   - the production file,
   - the worktree path,
   - the operator list (below),

   and explicitly **not the test**. It returns one hunk. The main agent
   applies the **first** hunk returned, runs the phase's own tests, and
   checks for red. There is no re-rolling for a more convenient hunk — see
   *Constrained mutation* for why.

   Blinding the subagent to the test is the point: a subagent that can see
   the test could tune the mutation to whatever the test happens to check,
   which reintroduces the exact failure mode this gate exists to catch — the
   same author writing both the test and the thing meant to indict it.

5. **`git worktree remove --force`.** `--force` is required, not optional —
   the worktree is unclean by construction (the copied-in test is untracked,
   the injected mutation is a tracked-file modification), and a bare
   `git worktree remove` refuses an unclean worktree, telling you to pass
   `--force`. There is nothing to restore, nothing to stage, no fence to
   satisfy first: this is only the fast path. Step 1's sweep is the
   guarantee — see *Why a disposable worktree* below.

6. **Commit only after the check passes** — and after execute mode's step 5
   clean-run gate also passes — on the developer's real tree. This gate proves
   the phase's tests catch a bug; that one proves they run clean in the full
   suite on the branch. Both precede the commit. The operator name(s) used here
   are echoed to the transcript and recorded on the phase's `Landed:` line as
   provenance.

**"Run the test" means the phase's own tests, not the whole suite**, at every
step above. Mutating production code *should* break unrelated tests — that's
expected, not signal — so there's no reason to run the full suite here, and a
legacy suite's pre-existing failures stay out of frame.

## Constrained mutation

The injected mutation is not free-form. It is a single change drawn from a
named operator set, and the subagent must **declare which operator by
name** when it returns its hunk:

- flip a comparison (`<` ↔ `<=`, `==` ↔ `!=`)
- off-by-one a boundary
- negate a condition
- alter a constant
- drop a state transition

**Explicitly banned, regardless of operator name:**

- an early `return` / `raise` / `throw` at function entry
- removing a whole function body

These two are banned by shape, not by judgment call, because they are
sledgehammers: either one makes *any* test go red — including a theater test
like `assert result is not None` — which would let a genuinely worthless test
pass the gate for the wrong reason. "Keep the mutation small" is a
rationalizable instruction; "no early return at function entry" is a concrete
line an agent cannot talk itself around. Requiring the operator to be named
turns a dishonest mutation into an affirmative written claim instead of a
silent choice.

**If the first hunk leaves the test green, that is the theater row in the
table below — rewrite the test. Do not re-roll the mutation.** Re-rolling
would let the main agent shop for a hunk that happens to turn the test red,
which quietly restores the identity the blind-mutator subagent exists to
break: one author controlling both the test and the thing meant to indict
it. A test that survives one honest, named mutation attempt on the behavior
it claims to cover has already told you what it needs to tell you.

## Failure table

Five outcomes. Each is a different failure of a different precondition the
gate depends on, and each has one correct action — never "fix the code" and
never "latch anyway."

| Outcome | Meaning | Action |
|---|---|---|
| Baseline red (fails unmutated, run alone) — but green in a full-suite run | **Order dependence**, not a mischaracterization: the test relies on state another test sets up. The isolated gate cannot judge it. | **Surface it. The phase cannot use the isolated gate as-is.** Do not latch, do not "fix" the code. |
| Baseline red (fails unmutated) — and also red in a full-suite run | The test does not describe current behavior — **mischaracterization**. | **Rewrite the test.** Do not fix the code, do not latch. |
| Baseline result unstable across two runs | The test is **flaky** — its verdict is noise, so the gate cannot judge it. | **Surface it.** Do not latch. |
| No code path implements this `Catches:` behavior (no valid site to inject) | The phase was planned against code that has since moved or vanished. | **Phase invalidated — re-plan it.** Do not latch. |
| Mutation applied, test stayed green | **Theater** — the test does not catch what the phase claims. | **Rewrite the test.** Do not latch. Do not re-roll the mutation. |

**"Run the test" in every row above means the phase's own tests, not the
whole suite.** The order-dependence and flaky rows exist because the
isolated gate silently *depends on* the phase's tests being isolable and
deterministic — this table is where those two preconditions get checked,
and where a violation of either gets named and surfaced rather than papered
over. Naming the violation is the whole of this gate's engagement with
suite health; it detects the two failure modes, it does not repair them.

The "no code path" row is the design's staleness detector: a bug cannot be
injected into a code path that has moved or vanished, and no phase latches
without passing this gate — so a stale plan gets caught here, not silently
latched against a `Produces:` path that no longer means what it once did.

## Explaining results to the developer

The table's labels — "theater," "mischaracterization," "order dependence,"
"flaky," "invalidated" — are for the agent. Tell the developer what the result
means for their tests, in plain words (§ Talking to the developer):

| Outcome | What to say to the developer |
|---|---|
| Mutation applied, test stayed green (*theater*) | *"These tests still passed after I deliberately broke the code they're supposed to check, so they aren't actually testing that behavior. I'll rewrite them so they catch it."* |
| Baseline red, also red in full suite (*mischaracterization*) | *"These tests disagree with how the code behaves right now. Since the job here is to pin down current behavior, I'll fix the tests to match what the code actually does."* |
| Baseline red alone, green in full suite (*order dependence*) | *"These tests only pass when run together with others — run on their own they fail — so I can't confirm them in isolation. That's worth cleaning up before relying on them."* |
| Baseline unstable across two runs (*flaky*) | *"These tests give different results on repeat runs, so I can't trust the outcome yet. They need to be made reliable first."* |
| No code path implements `Catches:` (*invalidated*) | *"The code this set of tests was planned around has moved or been removed, so the plan for it is out of date and I'll redo it."* |

## Why a disposable worktree, not an in-tree mutation

An earlier draft mutated the developer's working tree directly and protected
it with an elaborate write-fence: a whole-tree `git status --porcelain`
snapshot compared before and after each mutation, plus a
`git add`-before-`git checkout` staging dance to survive `git checkout`'s
restore-from-index behavior. Roughly forty lines of protocol existed solely
to make an in-tree mutation survivable — and it still had a window: a crash,
context exhaustion, or a `--watch` runner mid-mutation could leave altered
production code on disk, caught only on the *next* run, after the developer
already had it in front of them.

The worktree deletes the problem instead of fencing it. The mutated copy is
disposable, so there is no invariant left to protect: no snapshot
comparison, no staging, no path-based fence — and the colocated-test hazard
that broke every such fence (in Rust/Zig/D the test file *is* under `src/`)
becomes irrelevant, because you're mutating a copy you're about to throw
away regardless.

The same kind of crash the write-fence could not survive can still strand
the **worktree itself** — the disposable checkout, plus its
`.git/worktrees/` record — on any exit that skips step 5: a failure-table
short-circuit, context exhaustion, a `--watch` runner, a hard kill. That is
hygiene, not a safety gap — the developer's tree is never touched either
way, so Inviolate #2 holds regardless of whether step 5 ever runs — but the
leak this time is closed the way the write-fence's window was **not**: on
the next entry, never on the current exit. Step 1's sweep (`git worktree
prune`, plus a force-remove filtered to test-roadmap's own path segment
**and** this run's id) runs on the one path a crash cannot skip — the start
of the next phase — so a strand left by a short-circuited phase dies when
the session next enters the gate, instead of persisting for the rest of the
run. A strand left by a session that died outright is out of the run-id
sweep's reach by design (step 1) and is reclaimed instead by `$TMPDIR` plus
the unscoped `prune`. On-exit removal (step 5) is only the fast path;
the sweep is the guarantee, because no on-exit cleanup survives a crash this
design already declined to trust once.

The cost, stated honestly: a fresh worktree starts with no `node_modules/`,
no `target/`, no venv, no `_build/`. Some ecosystems need a full dependency
install before their tests can even run, and that can cost minutes. This
skill cannot know the install command stack-agnostically, so the mitigation
here is structural, not a lookup table — one worktree per phase, reused
across every mutation in that phase (protocol step 1) — never a built-in
per-language command table.
