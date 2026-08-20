---
name: release
description: Cut a paad release — pick the semver bump from what is in [Unreleased], run make release, merge, tag, and verify the published plugin
---

## Start

Announce: **"Preparing a paad release…"**

Read @CLAUDE.md.

`make release` and `make tag` own everything mechanical: the changelog roll, the
version rewrite across four files and eleven announce lines, the export
regeneration, the full check suite, and the annotated tag. This skill owns the
parts a Makefile cannot decide — which number to bump to, whether a release is
wanted at all, and whether the thing users install actually works afterwards.

**Never hand-edit `plugin.json`, `marketplace.json`, `package.json`, a SKILL.md
announce line, or the changelog's version headings and link refs.** Those are
generated. If the generated result is wrong, fix the generator.

```dot
digraph release {
    "Read [Unreleased]" [shape=box];
    "Anything there?" [shape=diamond];
    "STOP — ask whether a release is wanted" [shape=box, style=bold];
    "Entries within the length rule?" [shape=diamond];
    "STOP — trim first, as its own commit" [shape=box, style=bold];
    "Propose MAJOR/MINOR/PATCH with reasoning" [shape=box];
    "User confirms version?" [shape=diamond];
    "On a branch?" [shape=diamond];
    "Create release branch" [shape=box];
    "make release VERSION=X.Y.Z" [shape=box];
    "Passed?" [shape=diamond];
    "STOP — report the failure and the half-applied state" [shape=box, style=bold];
    "Show the diff, get sign-off" [shape=box];
    "Commit, merge to main, push" [shape=box];
    "make tag" [shape=box];
    "Hand off in-app verification" [shape=doublecircle];

    "Read [Unreleased]" -> "Anything there?";
    "Anything there?" -> "STOP — ask whether a release is wanted" [label="empty"];
    "Anything there?" -> "Entries within the length rule?" [label="entries"];
    "Entries within the length rule?" -> "STOP — trim first, as its own commit" [label="no"];
    "Entries within the length rule?" -> "Propose MAJOR/MINOR/PATCH with reasoning" [label="yes"];
    "Propose MAJOR/MINOR/PATCH with reasoning" -> "User confirms version?";
    "User confirms version?" -> "Propose MAJOR/MINOR/PATCH with reasoning" [label="no"];
    "User confirms version?" -> "On a branch?" [label="yes"];
    "On a branch?" -> "Create release branch" [label="on main"];
    "On a branch?" -> "make release VERSION=X.Y.Z" [label="on a branch"];
    "Create release branch" -> "make release VERSION=X.Y.Z";
    "make release VERSION=X.Y.Z" -> "Passed?";
    "Passed?" -> "STOP — report the failure and the half-applied state" [label="no"];
    "Passed?" -> "Show the diff, get sign-off" [label="yes"];
    "Show the diff, get sign-off" -> "Commit, merge to main, push";
    "Commit, merge to main, push" -> "make tag";
    "make tag" -> "Hand off in-app verification";
}
```

## 1. Read what is actually unreleased

Read the `## [Unreleased]` section of `CHANGELOG.md`.

**If it is empty, stop and ask.** There is nothing to release. Do not invent a
version to bump to, and do not go hunting through `git log` for things that
should have been logged — an unrecorded change is a changelog bug to fix first,
as its own commit, not something to sweep into a release.

## 1.5. Check the entries against the length rule

CLAUDE.md sets it: **1–3 lines per entry, at most 8 for a new skill, ending in a
pointer to `paad:help` or README.** Once this section rolls into a version
heading it is published, and trimming it afterwards means editing released
history. Catch it here.

Read each bullet and ask what it is doing:

| In the entry | Verdict |
|---|---|
| What changed, who it affects, what to do | Keep |
| A pointer to `paad:help` or README | Keep |
| How the feature works internally — phases, agents, gates | Cut |
| Why the design is right, or what was rejected | Cut |
| Testing evidence, run counts, measured before/after | Cut |

The test from CLAUDE.md: **if it explains a mechanism, it is in the wrong file.**
That material is worth keeping — it belongs in the commit message, in README, or
in `paad:help`, all of which already exist. A changelog copy is a third copy that
has to be hand-synced and drifts.

Sanity check the size:

```bash
awk '/^## \[/{if(n)print len" lines  "n; n=$0; len=0; next} {len++} END{print len" lines  "n}' CHANGELOG.md | head -5
```

A section running past ~40 lines for a normal release is the signal. Sections in
this file's history run to 200 lines; those are the mistake, not the precedent.

**If entries are too long, stop and say so.** Trimming is its own commit *before*
the release, exactly like a missing entry is — not a silent edit during it, and
not something to fold into the release commit. Propose the shortened text, get
sign-off, commit it, then start again at step 1.

## 2. Propose the version

Semver against what is in `[Unreleased]`, not against how much work it felt like:

| Change | Bump |
|---|---|
| A new skill, or new user-facing behavior in an existing one | MINOR |
| Wording, digraph, or bug fixes only | PATCH |
| A renamed or removed skill | breaking — say so explicitly |

paad has stayed on `1.x`. A breaking change still gets called out in the
changelog even if the major does not move; raise it and let Ovid decide.

State your reasoning and the proposed number, then **wait for confirmation.**
Do not proceed on a version you picked unilaterally.

Note for the experimental skills (`agentic-dedup`, `test-roadmap`): their
arguments and output may change in any release including a patch, so a breaking
change to one of them does not force a major.

## 3. Cut it

Confirm you are on a branch, not `main` — `make release` refuses on `main`, but
say so before running rather than after.

Release from the branch that already carries the unreleased work, so the feature
and its bump merge together. `main` holding user-facing work that has not been
bumped is the leak CLAUDE.md describes under "Releasing": a new install clones
`main`'s tip and gets it, while existing installs stay behind on the same version
number. If the work is already merged and there is no such branch, cut one off
`main` and say that the window is open until it lands.

```bash
make release VERSION=X.Y.Z
```

That single command rolls the changelog with today's real date, opens a fresh
`[Unreleased]`, fixes both link refs, rewrites every version string, regenerates
`kiro_and_antigravity/` and `pi/`, and runs `make test`.

**If it fails, stop and report the failure.** Do not hand-patch around it. A
failing check at this point means either the release is not ready or a generator
is wrong, and both need a decision from Ovid.

Report the state along with the failure, because it is not clean: `make release`
mutates before it verifies, so a failure at `make test` leaves the changelog
rolled and every version string bumped. Say so, and say that re-running
`make release` will not work — it refuses on the now-dirty tree, and
`roll_changelog.py` refuses a second time on a version that already has a
section. Once Ovid has decided and the cause is fixed, the way forward is
`make export && make test` and then commit; the way out is `git checkout -- .`,
which discards the roll and the bump together. Neither is the hand-patching this
step forbids — that means editing the generated output to make a check pass.

## 4. Show the work before committing

Show the diff — at minimum the changelog section boundary and the version
strings. Get sign-off, then commit:

```bash
git commit -a -m "release: paad X.Y.Z"
```

## 5. Merge and tag

Merge the branch into `main` and push. Ovid uses `git-done`; plain
`git checkout main && git merge --no-ff <branch> && git push` works too.

Then, **on `main`, after the merge is pushed:**

```bash
make tag
```

It reads the version from `plugin.json`, refuses if you are not on a synced
`main`, if the tree is dirty, if the changelog has no matching section, or if the
tag already exists — then annotates and pushes.

The tag goes on the merge commit because that is the tree users receive. Never
move a published tag; if the wrong commit got tagged, ask Ovid before doing
anything about it.

## 6. Hand off the verification you cannot do

You cannot run this part — it happens in Ovid's Claude Code session. Tell him to:

1. `/plugin` → **Installed** → **paad** → **Update now**
2. Restart Claude Code
3. Run any skill and confirm the announce line reads `vX.Y.Z`

This is the cheapest way to catch a bump that never made it to `main`.

Step 1 refreshes the marketplace catalog itself before it checks for a new
version. It is the panel action and nothing else — if the plugin never actually
updated, the version check at step 3 reads the *old* version and reports a
release that shipped fine as broken.

Then report what shipped: the version, the tag, the commit it points at, and a
one-line summary of the changelog section.

## What this skill does not do

- **No GitHub Release.** The tag is the record. Do not run `gh release create`
  unless Ovid asks.
- **No `[Unreleased]` housekeeping.** If a change is missing from the changelog,
  that is a separate commit before the release, not a silent addition during it.
- **No version invention.** Step 2 ends in a question, always.
