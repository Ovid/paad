# Preview tree design

*2026-08-22*

## The problem

Merging to `main` ships. A new install runs `npx skills@latest add Ovid/paad`,
which clones `main` and takes whatever is there — the `plugin.json` version
field does not gate it. So work that lands on `main` before it has been driven
for real reaches users, and the only way to keep it away from them is to keep
it off `main`. Long-lived branches are the tax that follows, and they have made
releases hard.

The fix is to make `main` safe to merge into. A second tree, `preview/`, holds
work in progress. Nothing outside `plugins/` is reachable by either install
route, so `main` can carry unreleased skills indefinitely.

## The model

Two trees, one direction of flow.

```
preview/paad/                 all new work lands here; always ahead of, or equal to, plugins/
plugins/paad/                 what ships; written only by promotion, never hand-edited
kiro_and_antigravity/, pi/    generated from plugins/ only
```

The invariant is one-directional: **`plugins/` is always a past state of
`preview/`.** Promotion copies preview over plugins wholesale, and that is the
only way `plugins/` changes.

`preview/paad` is a byte-for-byte mirror of `plugins/paad`, including
`.claude-plugin/plugin.json` at the same depth. Promotion is then a directory
swap, with no special-casing for a file that lives somewhere else.

### The three markers

| | `preview/` | `plugins/` |
|---|---|---|
| announce line | `v1.31.0-preview` | `v1.31.0` |
| frontmatter | `metadata: internal: true` | absent |
| `plugin.json` version | `1.31.0-preview` | `1.31.0` |

Promotion strips all three.

The `-preview` suffix answers "which tree just ran?" in a transcript, which
matters when both are loaded. The `internal` flag is the safety gate.

## Why the flag is needed

Measured against `skills@1.5.23`, running the real installer over a repo copy
containing `preview/`:

- **Normal install: no leak.** `discoverSkills` resolves
  `.claude-plugin/marketplace.json` → `./plugins/paad` → `plugins/paad/skills`.
  Because that search finds skills, the whole-repo `findSkillDirs` sweep never
  runs. 14 skills installed, all from `plugins/`.
- **`--full-depth`: no leak either, but for a weaker reason.** That flag does
  sweep the whole repo. Preview's copies are dropped by `seenNames` dedup —
  `plugins/` is walked first, and the names collide.
- **`--full-depth` on a *new* skill: leaks.** A skill that exists only in
  preview has a name nothing has claimed, so dedup does not catch it. A
  throwaway `brandnew` skill in `preview/` was offered and installed.
- **With `metadata: internal: true`: does not leak.** The installer tests
  `metadata?.internal === true` and skips the skill. `brandnew` disappeared.

Dedup protects a skill only once it has already shipped, which is precisely
backwards from what preview is for. The flag is what actually closes it.

The bare token `true` is required. `internal: "true"` is a string and fails the
strict comparison, so the skill would ship — the same trap
`scripts/check_internal_flag.py` already documents for `.claude/skills/`.

**Verified:** `claude plugin validate` accepts both markers. Run against a
preview-shaped tree — `plugin.json` at `1.31.0-preview` and `metadata: internal:
true` on all 14 SKILL.md files — it passes. The prerelease suffix is valid semver
to it, and the frontmatter flag does not upset the manifest validator.

**Also verified:** Claude Code's `--plugin-dir` loader ignores
`metadata.internal`, so the local load route works with the flag in place.
Measured against `claude 2.1.241` with a two-skill probe plugin — `zzflagged`
carrying `metadata: internal: true`, `zzcontrol` carrying nothing. Both appear in
the available-skills list, and `ptest:zzflagged` invokes and runs. The probe's
`plugin.json` was at `1.30.2-preview`, so the prerelease suffix is accepted by the
loader too, not only by the validator.

That is the answer the design wants: the npx installer honors the flag (the
safety gate), Claude Code does not (so preview stays drivable). No stripping step
is needed in the local load route.

## Makefile

Preview's `plugin.json` carries the `-preview` suffix, and every per-skill check
already reads its version from `plugin.json`. Parameterize the checks on the
tree and the suffix falls out — no `-preview` literal anywhere in the Makefile.

```make
TREE       ?= plugins/paad
SKILLS_DIR := $(TREE)/skills
```

`test` runs the per-tree block twice through recursive make:

```make
test: check-versions validate check-readme check-export-...
	$(MAKE) tree-checks TREE=plugins/paad
	$(MAKE) tree-checks TREE=preview/paad

tree-checks: check-skill-names check-skill-versions check-digraphs \
             check-help check-frontmatter check-references \
             check-dispatch-sites check-announce
```

**Per-tree** — the eight above. `check-help` reads
`$(TREE)/skills/paad-help/SKILL.md`, so preview's help validates against
preview's skill list and travels with it at promotion.

`TREE` reaches only the shell loops written in the Makefile. Two of the eight
delegate to scripts that hardcode `plugins/paad/skills` and take no path
argument — `scripts/check_references.py` and `scripts/lint_digraphs.py` — so left
alone they check `plugins/` on both passes. `check-references` becomes a complete
no-op for preview; `check-digraphs` catches only a skill with no digraph at all,
never a malformed one. Both gain an optional path argument defaulting to
`plugins/paad/skills`, and the Makefile passes `$(SKILLS_DIR)`. Note that
`lint_digraphs.py`'s own "the check is a no-op" guard does not fire here — it
sees input, just the wrong tree's.

**Plugins only, run once** — `check-versions`, `validate`, `check-readme`, and
the three `check-export-*`. README documents the shipped set; a preview-only
skill is tolerated there, not required.

Its README entry gets written on the release branch **before `make release`
runs**, as its own commit — not in the promotion commit. That commit is made
after `make release` has finished, and `make release` ends in `make test`, which
runs `check-readme` against the freshly promoted `plugins/`. A skill promoted
without its README entry fails there, with the rsync, the changelog roll and both
trees' version strings already written, and `make release` unable to re-run
against the dirty tree it just created. Writing the entry first costs nothing and
merges with the release, so README never advertises a skill nobody can install.

**`check_internal_flag.py`** grows two rules beyond its `.claude/skills/` pass:
require the flag on every `preview/paad/skills/*/SKILL.md`, and forbid it on
every `plugins/paad/skills/*/SKILL.md`. The second rule catches a botched
promotion — a shipped skill still wearing its safety flag would be silently
invisible to every installer.

**`bump-version`** gains a second pass writing `$(VERSION)-preview` to preview's
`plugin.json` and `v$(VERSION)-preview` to preview's announce lines.
`check-versions` asserts the two forms agree.

**`validate`** adds `claude plugin validate preview/paad`. Measured: it passes
on a `1.31.0-preview` manifest, so the fallback once reserved for a rejected
suffix — a plain version in preview's `plugin.json` with the suffix carried as a
Makefile variable — is not needed.

## Promotion and release

```make
promote:  ## Copy preview/ over plugins/ and strip the preview markers
	@<refuse if git status is dirty>
	rsync -a --delete preview/paad/ plugins/paad/
	python3 scripts/promote.py
```

The dirty-tree guard keeps the resulting diff reviewable. `--delete` is
deliberate: a skill removed from preview is removed from the shipped set.

`scripts/promote.py` is small because `bump-version` does the version half. It
strips `internal: true` from frontmatter, dropping an empty `metadata:` key with
it, reusing the frontmatter parsing already written for
`check_internal_flag.py`.

The version literals resolve themselves. After the rsync, `plugins/` announces
`v1.30.2-preview` and its `plugin.json` says the same. `bump-version` reads
`old_ver` per tree, so its existing sed matches that string and rewrites it to
plain `v1.31.0`, while preview's pass rewrites `1.30.2-preview` →
`1.31.0-preview`. No new substitution logic.

`make release` gains one step at the front:

```
branch + dirty guards → make promote → roll_changelog →
bump-version (both trees) → export → test → commit, merge, tag
```

`/release` gains a step describing what promotion did and directing the user to
read `git diff plugins/` before committing. That diff is the release's actual
payload and the last moment to catch something unintended.

### Accepted limitations

**Hotfixes go through preview like everything else.** A hotfix branches from the
release tag, and at a release tag `preview/` and `plugins/` are equal by
construction — preview's queue lives on `main`, which that branch does not
include. There is nothing to skip: edit `preview/`, run `make release` unchanged,
cherry-pick forward onto `main` afterwards.

Hand-editing `plugins/` stays forbidden with no exception, because an exception
would be destroyed by its own release. `make release` begins with `make promote`,
whose `rsync -a --delete preview/paad/ plugins/paad/` would copy the pre-fix
preview straight over the hand edit. Nothing catches it: the tree is committed so
the dirty guard passes, and the result is self-consistent so every check passes.
The release ships, the changelog announces the fix, and the fix is not in it.

**The generator has no preview stage.** A change to
`scripts/convert_skills.py` alters `kiro_and_antigravity/` and `pi/` output the
moment it merges, with only `check-export-*` behind it. Preview covers skill
content, not the export pipeline. The alternative doubles the generated output
to guard a file that changes rarely.

## Migrating the current branch

1. **Move the work into preview.** `preview/paad` is already byte-identical to
   this branch's `plugins/paad`. Add the three markers: relocate `plugin.json`
   to `preview/paad/.claude-plugin/`, set its version to `1.30.2-preview`, add
   `-preview` to all 14 announce lines, add `metadata: internal: true` to all 14
   SKILL.md files.

2. **Leave the shipped tree alone, and release it.** `plugins/` already carries
   `paad-help`, and this branch's Makefile is written for the post-rename world —
   `check-help`, `check-digraphs`, `check-announce` and `check-readme` all
   hardcode `paad-help` by name. Reverting `plugins/` to `main` puts `help/` back
   underneath those checks and fails all four; measured, not predicted. So
   `paad-help` ships in the release that lands this design.

   No deprecation stub is kept. `/help` was never reachable as a paad skill — it
   is Claude Code's builtin, which is why the rename happened — so a stub would
   serve only people who typed the fully qualified `/paad:help`, and the changelog
   already tells them what it became. It would also cost three check exemptions
   and a hand-written SKILL.md, since the rename deleted the directory rather than
   leaving one to keep. README needs no change: it already documents `/paad-help`.

3. **CLAUDE.md.** Its `paad-help` conventions stay as written — `paad-help` ships
   in this release. It gains a preview section: the two-tree model, the three
   markers, "never hand-edit `plugins/`", and the per-tree vs plugins-only check
   split.

Unchanged by these steps: `scripts/check_internal_flag.py`,
`scripts/convert_skills.py`, `.claude/skills/`, `docs/`, `paad/code-reviews/`,
and `CHANGELOG.md`'s `[Unreleased]` entries — still correctly unreleased.
