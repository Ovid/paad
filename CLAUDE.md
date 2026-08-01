# CLAUDE.md — paad

## What this project is

This is a **Claude Code plugin marketplace** hosted at `github.com/Ovid/paad`. It distributes the `paad` plugin, which provides skills for architecture analysis, code quality, and development workflows.

After this file is read, announce "CLAUDE.md loaded."

Also, address me as "Ovid" for further verification that you have read this file.

## Project structure

```
paad/
├── package.json                        ← Pi package manifest
├── .claude-plugin/
│   └── marketplace.json           ← marketplace catalog (lists all plugins)
├── plugins/
│   └── paad/                      ← the "paad" plugin (namespace for all skills)
│       ├── .claude-plugin/
│       │   └── plugin.json        ← plugin manifest (name, version, metadata)
│       ├── agents/
│       │   └── paad-analyst.md    ← read-only subagent type (not a skill)
│       └── skills/
│           ├── agentic-a11y/
│           │   └── SKILL.md       ← /paad:agentic-a11y skill
│           ├── agentic-architecture/
│           │   └── SKILL.md       ← /paad:agentic-architecture skill
│           ├── agentic-review/
│           │   └── SKILL.md       ← /paad:agentic-review skill
│           ├── alignment/
│           │   └── SKILL.md       ← /paad:alignment skill
│           ├── fix-architecture/
│           │   └── SKILL.md       ← /paad:fix-architecture skill
│           ├── help/
│           │   └── SKILL.md       ← /paad:help skill
│           ├── makefile/
│           │   └── SKILL.md       ← /paad:makefile skill
│           ├── pushback/
│           │   └── SKILL.md       ← /paad:pushback skill
│           └── vibe/
│               └── SKILL.md       ← /paad:vibe skill
├── CLAUDE.md                      ← this file
└── README.md
```

## Key conventions

- **Marketplace name**: `paad`
- **Plugin name**: `paad` (so all skills are invoked as `/paad:<skill-name>`)
- **Skill naming**: skill folder names become the suffix after `paad:` — e.g., `skills/agentic-architecture/` → `/paad:agentic-architecture`
- **Versioning**: `package.json`, `marketplace.json`, and `plugin.json` use semver, plus every `SKILL.md` carries the plugin version inside its on-invocation announce line. Run `make bump-version VERSION=X.Y.Z` to update all manifests and skill announce lines at once; `make check-versions` and `make check-skill-versions` (run as part of `make test`) catch drift.
- **Changelog**: `CHANGELOG.md` tracks user-facing changes to the plugin, newest first. Land every user-facing change under `[Unreleased]` as you make it; the release rolls that section into a version. Repo-only churn (docs, `.claude/skills/`, README wording, design notes) doesn't need an entry. See "Releasing" for the rollover steps.
- **Validation**: run `claude plugin validate .` (marketplace) and `claude plugin validate ./plugins/paad` (plugin) before committing
- **Announce on invocation**: every `SKILL.md` must begin its body with the line `**On invocation:** announce "Running paad:<skill-name> v<version>" before anything else.` so users see which skill ran and which version produced the behavior. The literal version string must match `plugin.json`.
- **Announce the artifacts on completion**: any skill that writes or updates a file must end its run by listing every path it touched, one line per path marked new or updated, before the summary or next-step advice. Reports, indexes, backlogs, roadmaps, findings logs, and the developer's own spec/plan documents all count. Developers routinely miss that a run left an artifact in the repo, and an artifact nobody reads is the same as no artifact. Say it even when a single file changed and even when the user watched it happen. Skills that write nothing (`help`) are exempt.

## Adding a new skill

1. Create `plugins/paad/skills/<skill-name>/SKILL.md` with frontmatter (`name`, `description`) and instructions
2. Add the on-invocation announce line as the very first line of the body (after the closing `---` of frontmatter): `**On invocation:** announce "Running paad:<skill-name> v<version>" before anything else.` — the version literal must match `plugin.json`
3. Consider `$ARGUMENTS` support — if the skill could benefit from user-provided scope (a file path, directory, branch name, etc.), add an Arguments section documenting usage. Users shouldn't need to remember flags; keep arguments positional and intuitive (e.g., `/paad:skillname path/to/scope`).
4. Add a graphviz digraph (```dot block) covering the skill's decision points and flow, placed immediately after the intro paragraphs and before the first `##` heading. The only exception is `paad:help`, which is a simple display skill. See "Digraph requirements" below.
5. Validate with `claude plugin validate ./plugins/paad`
6. Test locally with `claude --plugin-dir ./plugins/paad`
7. Bump the version with `make bump-version VERSION=X.Y.Z` (updates `package.json`, `plugin.json`, `marketplace.json`, and every SKILL.md announce line in one shot)
8. Update `README.md` to document the new skill under "Available Skills", including argument syntax in the heading
9. Add the new skill to `paad:help` — both the overview table and a detailed help section
10. Run `make test` to verify all checks pass (validate, version sync, skill-version announce, digraphs, help, README, frontmatter, references, dispatch sites)
11. Add the skill to `CHANGELOG.md` under `[Unreleased]` (`### Added`), then follow "Releasing" — step 7 above already did the version bump

## Modifying an existing skill

When changing a skill's behavior, arguments, or output, review `plugins/paad/skills/help/SKILL.md` and update the corresponding help text to match. Add a `CHANGELOG.md` entry under `[Unreleased]` if the change is visible to plugin users.

## Releasing

There is no build and no artifact upload. Users install from this repo via `/plugin marketplace add Ovid/paad`. Claude Code disables auto-update for third-party marketplaces by default, so most users pull a release by hand with `/plugin marketplace update paad` then `/plugin update paad@paad`; the ones who opted into auto-update get it in the background shortly after a session starts.

**The version bump is the release, not the merge.** Claude Code resolves a plugin's version from `plugin.json` first and uses it as the cache key for update detection: if the resolved version matches what a user already has, `/plugin update` and auto-update skip the plugin. Because `plugin.json` sets `version` explicitly, commits merged to `main` without a bump never reach an existing install. Merging is safe; shipping is the bump.

One leak in that: a *new* install clones the marketplace at `main`'s tip and gets whatever is there, version field notwithstanding. So user-facing work left unbumped on `main` reaches new users while existing ones stay behind, and both report the same version number. Don't leave it sitting — bump in the same cycle, or accept that "1.22.0" means two different things in the field. (Pinning the marketplace entry to a tag via a `git-subdir` source with `ref` would close this; the entry currently uses the relative-path form and does not.)

The changelog and tag are what make a release legible; the tag is a marker after the fact, not the delivery mechanism.

Release from a branch, never by committing to `main` directly.

**Use `/release`.** The project-local skill at `.claude/skills/release/SKILL.md` drives the whole sequence and owns the judgment calls the Makefile can't make. The steps below are what it does, and what to follow if you're releasing by hand.

1. **Pick the version.** Semver against what is in `[Unreleased]`: new skill or new user-facing behavior → minor; wording, digraph, or bug fixes only → patch. A renamed or removed skill is breaking — call it out in the changelog even though this project has stayed on `1.x`. If `[Unreleased]` is empty there is nothing to release — stop and ask.
2. **Cut it.** `make release VERSION=X.Y.Z` — one command, on a branch. It rolls the changelog (renames `## [Unreleased]` to `## [X.Y.Z] — <today>` using the system date, opens a fresh empty `[Unreleased]`, and rewrites both link refs), runs `make bump-version`, regenerates `kiro_and_antigravity/` and `pi/` via `make export`, then runs `make test`. It refuses on `main`, on a dirty tree, when `[Unreleased]` is empty, and when the version already has a section.

   Never hand-edit the generated pieces — `package.json`, `plugin.json`, `marketplace.json`, SKILL.md announce lines, changelog version headings, link refs, or anything under `kiro_and_antigravity/` and `pi/`. `make check-versions`, `check-skill-versions`, and `check-export-current` exist because drift happens. If the generated result is wrong, fix the generator.
3. **Read the output.** `make release` fails loudly; don't assume it passed. Review the diff before committing.
4. **Commit and merge.** `git commit -a -m "release: paad X.Y.Z"`, then merge the branch into `main` and push.
5. **Tag it.** On `main`, after the merge is pushed: `make tag`. It reads the version from `plugin.json`, builds the name as `paad--v` + version (double hyphen — it namespaces the plugin inside the marketplace repo), annotates, and pushes. It refuses if you're not on `main`, if the tree is dirty, if `main` is out of sync with `origin/main`, if the changelog has no matching section, or if the tag already exists.

   The tag goes on the merge commit because that's the tree users receive. Published tags don't get moved.
6. **Sanity-check the published side.** In Claude Code: `/plugin marketplace update paad` then `/plugin update paad@paad`, restart, and run any skill — the announce line should read `vX.Y.Z`. Cheapest way to catch a bump that never made it to `main`. This is the one step no target automates, because it happens in the app.

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
