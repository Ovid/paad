# CLAUDE.md — paad

## What this project is

This is a **Claude Code plugin marketplace** hosted at `github.com/Ovid/paad`. It distributes the `paad` plugin, which provides skills for architecture analysis, code quality, and development workflows.

After this file is read, announce "CLAUDE.md loaded."

Also, address me as "Ovid" for further verification that you have read this file.

## Project structure

```
paad/
├── .claude-plugin/
│   └── marketplace.json           ← marketplace catalog (lists all plugins)
├── plugins/
│   └── paad/                      ← the "paad" plugin — the only distributed thing here
│       ├── .claude-plugin/
│       │   └── plugin.json        ← plugin manifest (name, version, metadata)
│       ├── agents/
│       │   └── paad-analyst.md    ← read-only subagent type (not a skill)
│       └── skills/
│           ├── agentic-review/
│           │   ├── SKILL.md       ← one folder per skill → /paad:agentic-review
│           │   └── references/    ← optional; loaded on demand by the skill
│           └── <one folder per skill>
├── kiro_and_antigravity/          ← GENERATED export (Kiro / Cursor / Antigravity)
├── pi/                            ← GENERATED export (Pi agent)
├── package.json                   ← Pi package manifest (version + pi.skills path)
├── scripts/
│   ├── convert_skills.py          ← generates kiro_and_antigravity/ and pi/
│   ├── check_references.py
│   ├── lint_digraphs.py
│   └── roll_changelog.py
├── Makefile                       ← every check, plus the release sequence
├── .claude/skills/                ← project-local skills (/roadmap, /release) — not distributed
├── paad/code-reviews/             ← committed output from paad's own skills
├── docs/, notes/                  ← plans, roadmap, design notes
├── CHANGELOG.md
├── CLAUDE.md                      ← this file
└── README.md
```

`kiro_and_antigravity/` and `pi/` are produced from `plugins/paad/` by `make export`. Everything in them is generated — edit the source or the generator, never the output. README tells non-Claude-Code users to copy straight out of `kiro_and_antigravity/`, so a stale export on `main` is wrong content shipped to real users.

## Key conventions

- **Marketplace name**: `paad`
- **Plugin name**: `paad` (so all skills are invoked as `/paad:<skill-name>`)
- **Skill naming**: skill folder names become the suffix after `paad:` — e.g., `skills/agentic-architecture/` → `/paad:agentic-architecture`
- **Versioning**: `package.json`, `marketplace.json` (the `plugins[0].version` field — `metadata.version` is the marketplace's own and stays put), and `plugin.json` use semver, plus every `SKILL.md` carries the plugin version inside its on-invocation announce line. `make bump-version VERSION=X.Y.Z` updates all of them at once, and `make release` runs it — don't invoke it by hand outside a release. `make check-versions` and `make check-skill-versions` (part of `make test`) catch drift.
- **Changelog**: `CHANGELOG.md` tracks user-facing changes to the plugin, newest first. Land every user-facing change under `[Unreleased]` as you make it; the release rolls that section into a version. Repo-only churn (docs, `.claude/skills/`, README wording, design notes) doesn't need an entry. See "Releasing" for the rollover steps.
- **Verification**: `make export && make test` before committing. It regenerates `kiro_and_antigravity/` and `pi/` from the plugin sources, then runs every check — including `claude plugin validate` on the marketplace and the plugin. Never hand-edit anything it generates; if the output is wrong, fix the generator.
- **Announce on invocation**: every `SKILL.md` must begin its body with the line `**On invocation:** announce "Running paad:<skill-name> v<version>" before anything else.` so users see which skill ran and which version produced the behavior. The literal version string must match `plugin.json`.
- **Announce the artifacts on completion**: any skill that writes or updates a file must end its run by listing the **artifacts** it touched — reports, indexes, backlogs, roadmaps, findings logs, and the developer's own spec/plan documents — one line per path marked new or updated, before the summary or next-step advice.

  The test is visibility, not file type. A developer never sees a report land in `paad/`, so it gets named. The source file they asked you to change is the work they are already watching, and on a large run enumerating it buries the artifact that needed saying. **Source and test files therefore need only a count and a pointer to the diff** — `12 source files changed across 3 modules (see git diff)`. Naming them individually is allowed when there are only a few, never required.

  Developers routinely miss that a run left an artifact in the repo, and an artifact nobody reads is the same as no artifact. Say it even when a single file changed and even when the user watched it happen. Skills that write nothing (`help`) are exempt.

## Adding a new skill

`make export && make test` owns the mechanical half — validate, version sync, announce lines, digraph lint, help and README coverage, frontmatter, references, dispatch sites, export currency. Run it and fix what it reports; the steps below are only the parts it can't decide for you.

1. Create `plugins/paad/skills/<skill-name>/SKILL.md` with frontmatter (`name` matching the folder, `description`) and instructions
2. Add the on-invocation announce line as the very first line of the body (after the closing `---` of frontmatter): `**On invocation:** announce "Running paad:<skill-name> v<version>" before anything else.` — the version literal must match `plugin.json`
3. Consider `$ARGUMENTS` support — if the skill could benefit from user-provided scope (a file path, directory, branch name, etc.), add an Arguments section documenting usage. Users shouldn't need to remember flags; keep arguments positional and intuitive (e.g., `/paad:skillname path/to/scope`).
4. Add a graphviz digraph (```dot block) covering the skill's decision points and flow, placed immediately after the intro paragraphs and before the first `##` heading. The only exception is `paad:help`, which is a simple display skill. See "Digraph requirements" below.
5. If the skill dispatches subagents for analysis, dispatch every one of them as `subagent_type: paad:paad-analyst` — the read-only agent in `plugins/paad/agents/`. Specialists and verifiers must not carry `Edit`, `Write`, or `NotebookEdit`; subagents have been observed editing source code to test whether a finding was real.
6. Document it in `README.md` under "Available Skills" (argument syntax in the heading) and in `paad:help` — both the overview table and a detailed help section
7. Add a `### Added` entry under `[Unreleased]` in `CHANGELOG.md`
8. Run `make export && make test`, then drive the skill for real: `claude --plugin-dir ./plugins/paad`

**Don't bump the version here.** The bump is the release — run `/release` when the work is ready to ship. See "Releasing".

## Modifying an existing skill

Edit the SKILL.md, then run `make export && make test`. If the change alters behavior, arguments, or output, update the matching help text in `plugins/paad/skills/help/SKILL.md`. If it's visible to plugin users, add a `CHANGELOG.md` entry under `[Unreleased]`. The version is the release's job, not this edit's.

## Releasing

There is no build and no artifact upload. Users install from this repo via `/plugin marketplace add Ovid/paad`. Claude Code disables auto-update for third-party marketplaces by default, so most users pull a release by hand from the `/plugin` panel — **Installed** → **paad** → **Update now** — or with `claude plugin update paad@paad` from a shell; the ones who opted into auto-update get it in the background shortly after a session starts. The panel action refreshes the marketplace catalog itself before checking.

**The version bump is the release, not the merge.** Claude Code resolves a plugin's version from `plugin.json` first and uses it as the cache key for update detection: if the resolved version matches what a user already has, both a manual update and auto-update skip the plugin. Because `plugin.json` sets `version` explicitly, commits merged to `main` without a bump never reach an existing install. Merging is safe; shipping is the bump.

One leak in that: a *new* install clones the marketplace at `main`'s tip and gets whatever is there, version field notwithstanding. So user-facing work left unbumped on `main` reaches new users while existing ones stay behind, and both report the same version number. The fix is procedural and it's below: release from the branch that carries the work, so `main` never holds an unbumped user-facing change. (Pinning the marketplace entry to a tag via a `git-subdir` source with `ref` would close it properly; the entry currently uses the relative-path form and does not.)

The changelog and tag are what make a release legible; the tag is a marker after the fact, not the delivery mechanism.

Release from a branch, never by committing to `main` directly — and release from *the branch that carries the unreleased work*. Commit the feature, run `make release` on that same branch, then merge once. That is what "bump in the same cycle" means: you still don't bump as you edit, you bump as the last commit before the merge. Merging user-facing work to `main` ahead of its bump is what opens the leak above, because `main`'s tip is what a new install clones.

**Use `/release`.** The project-local skill at `.claude/skills/release/SKILL.md` drives the whole sequence and owns the judgment calls the Makefile can't make. The steps below are what it does, and what to follow if you're releasing by hand.

1. **Pick the version.** Semver against what is in `[Unreleased]`: new skill or new user-facing behavior → minor; wording, digraph, or bug fixes only → patch. A renamed or removed skill is breaking — call it out in the changelog even though this project has stayed on `1.x`. If `[Unreleased]` is empty there is nothing to release — stop and ask.
2. **Cut it.** `make release VERSION=X.Y.Z` — one command, on a branch. It rolls the changelog (renames `## [Unreleased]` to `## [X.Y.Z] — <today>` using the system date, opens a fresh empty `[Unreleased]`, and rewrites both link refs), runs `make bump-version`, regenerates `kiro_and_antigravity/` and `pi/` via `make export`, then runs `make test`. It refuses on `main`, on a dirty tree, when `[Unreleased]` is empty, and when the version already has a section.

   Never hand-edit the generated pieces — `package.json`, `plugin.json`, `marketplace.json`, SKILL.md announce lines, changelog version headings, link refs, or anything under `kiro_and_antigravity/` and `pi/`. `make check-versions`, `check-skill-versions`, and `check-export-current` exist because drift happens. If the generated result is wrong, fix the generator.
3. **Read the output.** `make release` fails loudly; don't assume it passed. Review the diff before committing.

   `make release` mutates before it verifies, so a failure at `make test` leaves the changelog rolled and the version bumped. That work is good — keep it. Fix what the check reported, run `make export && make test`, then commit. Don't re-run `make release`: it refuses on the now-dirty tree, and `roll_changelog.py` refuses a second time on a version that already has a section. To abandon the release instead, `git checkout -- .` before anything else. Fixing the cause and re-verifying is not the hand-editing the next step forbids.
4. **Commit and merge.** `git commit -a -m "release: paad X.Y.Z"`, then merge the branch into `main` and push.
5. **Tag it.** On `main`, after the merge is pushed: `make tag`. It reads the version from `plugin.json`, builds the name as `paad--v` + version (double hyphen — it namespaces the plugin inside the marketplace repo), annotates, and pushes. It refuses if you're not on `main`, if the tree is dirty, if `main` is out of sync with `origin/main`, if the changelog has no matching section, or if the tag already exists.

   The tag goes on the merge commit because that's the tree users receive. Published tags don't get moved.
6. **Sanity-check the published side.** In Claude Code: `/plugin` → **Installed** → **paad** → **Update now**, restart, and run any skill — the announce line should read `vX.Y.Z`. Cheapest way to catch a bump that never made it to `main`. This is the one step no target automates, because it happens in the app. Use the panel action; a check run against a plugin that was never actually updated reads the old version and reports a false alarm.

This project does not use GitHub Releases (`gh release create`) — the tag is the record. Don't add one unless Ovid asks.

## Digraph requirements

Every skill (except `paad:help`) must include at least one graphviz digraph (`\`\`\`dot` block) that visualizes the skill's decision points and flow. Digraphs must be:

- **Complete** — every decision point, stop condition, and branching path in the prose must appear in the digraph
- **Accurate** — node labels, edge labels, and flow must match the prose exactly. If the prose changes, the digraph must be updated to match.
- **Relevant** — digraphs exist to prevent the agent from skipping safety gates or misordering steps. Focus on decision points where the agent could cause damage by skipping ahead, not on linear sequences that are obvious from the prose.
- **In the same place in every skill** — all of a skill's digraphs go immediately after the intro paragraphs, before the first `##` heading, each introduced by a one-line bold label (`**Pre-flight:**`, `**Session flow:**`). Never inside the section they describe. An agent reading any SKILL.md finds the control flow in the same position every time, and reads it before the prose that details it.

When modifying a skill's flow, check that the digraph still matches. When reviewing a skill, cross-reference the digraph against the prose.

`make check-digraphs` runs `scripts/lint_digraphs.py`, which parses each block with graphviz (skipped if graphviz isn't installed) and rejects `shape=` attached to an edge statement, declared-but-unused nodes, nodes used in an edge but never declared, and any digraph placed after the first `##` heading. It cannot check completeness or accuracy against the prose — that stays a review job.

## Important rules

- Do NOT put `skills/`, `commands/`, or `agents/` inside `.claude-plugin/` — only `plugin.json` or `marketplace.json` go there
- Skill files must be named `SKILL.md` (uppercase) inside a folder whose name becomes the skill name
- Plugin sources in `marketplace.json` use paths relative to the marketplace root (start with `./`)
- Keep marketplace.json plugin descriptions in sync with plugin.json descriptions

## Project-local skills under `.claude/skills/`

The repo also hosts **project-local** skills at `.claude/skills/<name>/SKILL.md` (`roadmap`, `release`). These are **not** part of the `paad` plugin and follow a different lifecycle:

- **Not distributed** — they live in this repo only and are picked up automatically by Claude Code when it runs in this working directory. There is no marketplace, no `claude plugin validate` step, no `plugin.json`, no version field.
- **No `make bump-version` impact** — `make bump-version` rewrites `package.json`, `plugin.json`, `marketplace.json`, and every `plugins/paad/skills/*/SKILL.md` announce line. Project-local SKILL.md files are skipped on purpose. They have no announce-line version, no `paad:<name>` namespace.
- **No `make test` checks** — the Makefile's check-frontmatter / check-digraphs / check-help / check-readme / check-skill-versions targets all walk `plugins/paad/skills/`. They do not enforce anything against `.claude/skills/`.
- **Edit-and-commit only** — change the SKILL.md, commit, you're done. No version bump, no help table edit, no README entry, no `paad:help` cross-reference.
- **Naming** — invoke as `/<name>` (no `paad:` prefix), because they're not in a plugin. `/roadmap`, not `/paad:roadmap`.

When reviewing or modifying a `.claude/skills/<name>/SKILL.md`, do not chase the paad-plugin conventions (announce lines, version literals, help / README cross-references). They don't apply here.
