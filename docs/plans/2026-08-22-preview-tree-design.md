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

**Known unknown:** whether Claude Code ignores `metadata.internal` when loading
`preview/paad` as a plugin. Verify when wiring up the local load route. If it
chokes, strip the flag in that step rather than dropping it from the design.

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

**Plugins only, run once** — `check-versions`, `validate`, `check-readme`, and
the three `check-export-*`. README documents the shipped set; a preview-only
skill is tolerated there, not required. Its README entry gets written in the
promotion commit, which is where it stops being a lie to users.

**`check_internal_flag.py`** grows two rules beyond its `.claude/skills/` pass:
require the flag on every `preview/paad/skills/*/SKILL.md`, and forbid it on
every `plugins/paad/skills/*/SKILL.md`. The second rule catches a botched
promotion — a shipped skill still wearing its safety flag would be silently
invisible to every installer.

**`bump-version`** gains a second pass writing `$(VERSION)-preview` to preview's
`plugin.json` and `v$(VERSION)-preview` to preview's announce lines.
`check-versions` asserts the two forms agree.

**`validate`** adds `claude plugin validate preview/paad`. A prerelease string
is valid semver and should pass. If it rejects the suffix, that is the one
finding that forces a fallback: a plain version in preview's `plugin.json`, and
the suffix reintroduced as a Makefile variable.

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

**Hotfixes cannot skip preview's unreleased work.** Promoting drags everything
along. The escape hatch is ordinary: branch from the release tag, edit
`plugins/` directly there — the only place hand-editing is legitimate — release,
then cherry-pick into preview. No new machinery; just never on `main`.

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

2. **Revert the shipped tree.**

   ```
   git checkout main -- plugins/
   make export
   ```

   `plugins/` gets `help/` back; `preview/` keeps `paad-help/`. Both trees stay
   self-consistent because `check-help` is per-tree.

3. **README, by hand.** Keep the npx-installation rewrite — it is independent of
   `plugins/` and a real improvement. Restore the two `/paad-help` mentions to
   `/paad:help` so `check-readme` passes against the shipped `help` skill. They
   flip back in the promotion commit that ships `paad-help`.

4. **CLAUDE.md.** Its `paad-help` conventions become forward-looking statements
   about preview. It gains a preview section: the two-tree model, the three
   markers, "never hand-edit `plugins/`", and the per-tree vs plugins-only check
   split.

Unchanged on the branch: `scripts/check_internal_flag.py`,
`scripts/convert_skills.py`, `.claude/skills/`, `docs/`, `paad/code-reviews/`,
and `CHANGELOG.md`'s `[Unreleased]` entries — still correctly unreleased.
