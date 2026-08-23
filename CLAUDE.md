# CLAUDE.md — paad

## What this project is

This is a **Claude Code plugin marketplace** hosted at `github.com/Ovid/paad`. It distributes the `paad` plugin, which provides skills for architecture analysis, code quality, and development workflows.

After this file is read, announce "CLAUDE.md loaded."

Also, address me as "Ovid" for further verification that you have read this file.

## Project structure

`preview/paad/` is where all new work lands; `plugins/paad/` is what the marketplace distributes, and it is written only by promotion — see "The two trees" below. Everything else is scaffolding around them. `paad/code-reviews/` is committed output from paad's own skills. `.claude/skills/` holds project-local skills, which the marketplace does not carry but the npx installer does look in; the only thing keeping them out of an npx install is the `internal: true` flag documented under "Project-local skills" below. `package.json` is Pi's package manifest, not a Node one — this is not a JS project; it carries the version and the `pi.skills` path, and nothing else.

`kiro_and_antigravity/` and `pi/` are produced from `plugins/paad/` by `make export` — from the shipped tree only, so preview work does not reach them until it is promoted. Everything in them is generated — edit the source or the generator, never the output. README deprecates copying straight out of `kiro_and_antigravity/` in favor of `npx skills@latest add Ovid/paad`, but the route still works and is still documented, so a stale export on `main` is wrong content shipped to real users.

## The two trees

Merging used to ship. `npx skills@latest add Ovid/paad` clones `main` and takes what is there — `plugin.json`'s version field does not gate it — so anything merged before it had been driven for real reached users, and keeping it away from them meant keeping it off `main`. Long-lived branches were the tax, and they made releases hard.

`preview/paad/` fixes that by making `main` safe to merge into:

```
preview/paad/                 all new work lands here; always ahead of, or equal to, plugins/
plugins/paad/                 what ships; written only by promotion, never hand-edited
kiro_and_antigravity/, pi/    generated from plugins/ only
```

The invariant runs one way: **`plugins/` is always a past state of `preview/`.** `make promote` copies preview over plugins wholesale and that is the only way `plugins/` changes. `preview/paad` is a byte-for-byte mirror including `.claude-plugin/plugin.json` at the same depth, so promotion is a directory swap with nothing special-cased.

Three markers separate the trees, and promotion strips all three:

| | `preview/` | `plugins/` |
|---|---|---|
| announce line | `v1.31.0-preview` | `v1.31.0` |
| frontmatter | `metadata: internal: true` | absent |
| `plugin.json` version | `1.31.0-preview` | `1.31.0` |

The `-preview` suffix answers "which tree just ran?" in a transcript, which matters when both are loaded. The `internal` flag is the safety gate: a normal `npx` install never reaches `preview/` at all, but `--full-depth` sweeps the whole repo, and the `seenNames` dedup that catches preview's copies only protects a skill that has *already shipped* — precisely backwards from what preview is for. A preview-only skill has a name nothing has claimed, so without the flag it is offered and installed. The bare token `true` is required; `internal: "true"` is a string and fails the installer's `=== true`.

Claude Code does **not** honor the flag, which is what keeps preview drivable: `claude --plugin-dir ./preview/paad` lists and runs flagged skills normally (measured against `claude 2.1.241`, and the `-preview` version suffix loads fine too). So the npx installer gates and Claude Code does not — exactly the split this needs.

**Never hand-edit `plugins/`**, hotfixes included. The edit does not survive: `make release` opens with `make promote`, whose `rsync -a --delete` copies the pre-fix preview straight over it. Nothing catches that — the tree is committed so the dirty guard passes, and the result is self-consistent so every check passes. The release ships and the changelog announces a fix that is not in it. A hotfix branches from a release tag, where the two trees are equal by construction, so there is nothing to skip: edit `preview/`, run `make release` unchanged, cherry-pick forward onto `main`.

One thing preview does not cover: `scripts/convert_skills.py` has no preview stage, so a generator change alters `kiro_and_antigravity/` and `pi/` the moment it merges, with only `check-export-*` behind it. Preview guards skill content, not the export pipeline.

### Which checks run per tree

`make test` runs the eight per-skill checks once for each tree, through recursive make on `TREE`:

**Per-tree** — `check-skill-names`, `check-skill-versions`, `check-digraphs`, `check-help`, `check-frontmatter`, `check-references`, `check-dispatch-sites`, `check-announce`. Each reads its version out of `$(TREE)/.claude-plugin/plugin.json`, so the `-preview` suffix falls out of the tree rather than appearing as a literal anywhere in the Makefile. `check-help` reads preview's own `paad-help`, so it validates against preview's skill list and travels with it at promotion.

**Plugins only, once** — `check-versions`, `validate`, `check-readme`, and the three `check-export-*`. README documents the shipped set, so a preview-only skill is *tolerated* there, not required — its entry gets written on the release branch before `make release` runs, as its own commit. `check-versions` additionally asserts preview's version is the shipped one plus `-preview`.

`make tree-checks TREE=preview/paad` runs one tree's block on its own.

## Key conventions

- **Marketplace name**: `paad`
- **Plugin name**: `paad`. Skills are reachable by their bare name (`/pushback`); the `/paad:<skill-name>` form also works and is only needed to disambiguate against another plugin. Skill prose uses the bare form so the pointers work outside Claude Code.
- **Skill naming**: the skill folder name is the skill name — e.g. `skills/agentic-architecture/` → `/agentic-architecture`, fully qualified `/paad:agentic-architecture`. The help skill is `paad-help`, not `help`, because `/help` is a Claude Code builtin.
- **Versioning**: `package.json`, `marketplace.json` (the `plugins[0].version` field — `metadata.version` is the marketplace's own and stays put), and `plugin.json` use semver, plus every `SKILL.md` carries the plugin version inside its on-invocation announce line. `make bump-version VERSION=X.Y.Z` updates all of them at once across both trees — plain in `plugins/`, `-preview`-suffixed in `preview/` — and `make release` runs it. Don't invoke it by hand outside a release. `make check-versions` and `make check-skill-versions` (part of `make test`) catch drift.
- **Changelog**: `CHANGELOG.md` tracks user-facing changes to the plugin, newest first. Land every user-facing change under `[Unreleased]` as you make it; the release rolls that section into a version. Repo-only churn (docs, `.claude/skills/`, README wording, design notes) doesn't need an entry. See "Releasing" for the rollover steps.

  **Entry length: 1–3 lines. A new skill gets at most 8, and ends with a pointer to `paad:paad-help` or README.** A changelog entry answers one question — *does this release affect me, and do I need to do anything?* Say what changed, who it hits, and what to do about it. Nothing else.

  What does **not** go in an entry: how the feature works internally, why the design is right, the alternatives rejected, the phases or agents it dispatches, the evidence behind it, run counts from testing. That material is real and worth keeping — it belongs in the commit message, in README (why it works this way), or in `paad:paad-help` (how to use it). Putting it in the changelog makes a third copy that has to be hand-synced with the other two, and drifts.

  The test: if you're explaining a mechanism, you're in the wrong file. If a reader would have to scroll to find out whether the release affects them, it's too long. Some past sections run to 200 lines — those are the mistake, not the precedent.
- **Verification**: `make export && make test` before committing. It regenerates `kiro_and_antigravity/` and `pi/` from the plugin sources, then runs every check — including `claude plugin validate` on the marketplace and the plugin. Never hand-edit anything it generates; if the output is wrong, fix the generator.
- **Announce on invocation**: every `SKILL.md` must begin its body with the line `**On invocation:** announce "Running paad:<skill-name> v<version>" before anything else.` so users see which skill ran and which version produced the behavior. The literal version string must match `plugin.json`.
- **Announce the artifacts on completion**: any skill that writes or updates a file must end its run by listing the **artifacts** it touched — reports, indexes, backlogs, roadmaps, findings logs, and the developer's own spec/plan documents — one line per path marked new or updated, before the summary or next-step advice.

  The test is visibility, not file type. A developer never sees a report land in `paad/`, so it gets named. The source file they asked you to change is the work they are already watching, and on a large run enumerating it buries the artifact that needed saying. **Source and test files therefore need only a count and a pointer to the diff** — `12 source files changed across 3 modules (see git diff)`. Naming them individually is allowed when there are only a few, never required.

  Developers routinely miss that a run left an artifact in the repo, and an artifact nobody reads is the same as no artifact. Say it even when a single file changed and even when the user watched it happen. Skills that write nothing (`paad-help`, `rethink`) are exempt — `make check-announce` holds the same two.

## Adding a new skill

`make export && make test` owns the mechanical half — validate, version sync, announce lines, digraph lint, help and README coverage, frontmatter, references, dispatch sites, export currency. Run it and fix what it reports; the steps below are only the parts it can't decide for you.

1. Create `preview/paad/skills/<skill-name>/SKILL.md` — never under `plugins/` — with frontmatter (`name` matching the folder, `description`, and `metadata: internal: true`) and instructions
2. Add the on-invocation announce line as the very first line of the body (after the closing `---` of frontmatter): `**On invocation:** announce "Running paad:<skill-name> v<version>" before anything else.` — the version literal must match the tree's own `plugin.json`, so in `preview/` it carries the `-preview` suffix
3. Consider `$ARGUMENTS` support — if the skill could benefit from user-provided scope (a file path, directory, branch name, etc.), add an Arguments section documenting usage. Users shouldn't need to remember flags; keep arguments positional and intuitive (e.g., `/skillname path/to/scope`).
4. Add a graphviz digraph (```dot block) covering the skill's decision points and flow, placed immediately after the intro paragraphs and before the first `##` heading. The only exception is `paad:paad-help`, which is a simple display skill. See "Digraph requirements" below.
5. If the skill dispatches subagents for analysis, dispatch every one of them as `subagent_type: paad:paad-analyst` — the analysis agent in `plugins/paad/agents/`. Specialists and verifiers must not carry `Edit`, `Write`, or `NotebookEdit`; subagents have been observed editing source code to test whether a finding was real.
6. Document it in `preview/paad/skills/paad-help/SKILL.md` — both the overview table and a detailed help section. **Leave `README.md` alone until the release**: README describes what users can install, and the entry belongs on the release branch as its own commit before `make release` runs
7. Add a `### Added` entry under `[Unreleased]` in `CHANGELOG.md`
8. Run `make export && make test`, then drive the skill for real: `claude --plugin-dir ./preview/paad`

**Don't bump the version here.** The bump is the release — run `/release` when the work is ready to ship. See "Releasing".

## Modifying an existing skill

Edit the SKILL.md **in `preview/paad/skills/`**, then run `make export && make test`. If the change alters behavior, arguments, or output, update the matching help text in `preview/paad/skills/paad-help/SKILL.md`. If it's visible to plugin users, add a `CHANGELOG.md` entry under `[Unreleased]`. The version is the release's job, not this edit's.

## Releasing

There is no build and no artifact upload. Claude Code users install from this repo via `/plugin marketplace add Ovid/paad`; everyone else runs `npx skills@latest add Ovid/paad`, which clones the repo at `main` and has no version key at all. That route used to make merging equivalent to shipping; `preview/` is what closed it. Both routes now read `plugins/paad`, and `plugins/paad` changes only at promotion, so **merging to `main` is safe and the release is `make release`** — for every route. Claude Code disables auto-update for third-party marketplaces by default, so most users pull a release by hand from the `/plugin` panel — **Installed** → **paad** → **Update now** — or with `claude plugin update paad@paad` from a shell; the ones who opted into auto-update get it in the background shortly after a session starts. The panel action refreshes the marketplace catalog itself before checking.

**The version bump is the release, not the merge.** Claude Code resolves a plugin's version from `plugin.json` first and uses it as the cache key for update detection: if the resolved version matches what a user already has, both a manual update and auto-update skip the plugin. Because `plugin.json` sets `version` explicitly, commits merged to `main` without a bump never reach an existing install. Merging is safe; shipping is the bump.

One leak used to sit under that: a *new* install clones the marketplace at `main`'s tip and gets whatever is there, version field notwithstanding, so unbumped user-facing work on `main` reached new users while existing ones stayed behind on the same version number. Preview closes it structurally rather than procedurally — `main`'s tip only ever carries the last promoted state of `plugins/`, however much unreleased work is queued in `preview/`. (Pinning the marketplace entry to a tag via a `git-subdir` source with `ref` would pin the Claude Code route too; the entry uses the relative-path form and does not.)

The changelog and tag are what make a release legible; the tag is a marker after the fact, not the delivery mechanism.

Release from a branch, never by committing to `main` directly. Work merges to `main` as it is finished, unbumped and unpromoted, and accumulates in `preview/` until someone decides to ship — that decision is a release branch, `make release`, and one merge. The old rule about releasing from *the branch that carries the work* is no longer load-bearing, because there is no longer a window where `main` holds something a new install would pick up early.

**Use `/release`.** The project-local skill at `.claude/skills/release/SKILL.md` drives the whole sequence and owns the judgment calls the Makefile can't make — which number to bump to, whether a release is wanted at all, and the in-app verification afterwards. Read it if you're releasing by hand.

## Digraph requirements

Every skill (except `paad:paad-help`) must include at least one graphviz digraph (`\`\`\`dot` block) that visualizes the skill's decision points and flow. Digraphs must be:

- **Complete** — every decision point, stop condition, and branching path in the prose must appear in the digraph
- **Accurate** — node labels, edge labels, and flow must match the prose exactly. If the prose changes, the digraph must be updated to match.
- **Relevant** — digraphs exist to prevent the agent from skipping safety gates or misordering steps. Focus on decision points where the agent could cause damage by skipping ahead, not on linear sequences that are obvious from the prose.
- **In the same place in every skill** — all of a skill's digraphs go immediately after the intro paragraphs, before the first `##` heading, each introduced by a one-line bold label (`**Pre-flight:**`, `**Session flow:**`). Never inside the section they describe. An agent reading any SKILL.md finds the control flow in the same position every time, and reads it before the prose that details it.

When modifying a skill's flow, check that the digraph still matches. When reviewing a skill, cross-reference the digraph against the prose.

`make check-digraphs` runs `scripts/lint_digraphs.py` against whichever tree it was invoked for (it takes the skills directory as an argument, defaulting to `plugins/paad/skills`), parsing each block with graphviz (skipped if graphviz isn't installed) and rejects `shape=` attached to an edge statement, declared-but-unused nodes, nodes used in an edge but never declared, and any digraph placed after the first `##` heading. It cannot check completeness or accuracy against the prose — that stays a review job.

## Important rules

- Do NOT put `skills/`, `commands/`, or `agents/` inside `.claude-plugin/` — only `plugin.json` or `marketplace.json` go there
- Skill files must be named `SKILL.md` (uppercase) inside a folder whose name becomes the skill name
- Plugin sources in `marketplace.json` use paths relative to the marketplace root (start with `./`)
- Keep marketplace.json plugin descriptions in sync with plugin.json descriptions

## Project-local skills under `.claude/skills/`

The repo also hosts **project-local** skills at `.claude/skills/<name>/SKILL.md` (`roadmap`, `release`). These are **not** part of the `paad` plugin and follow a different lifecycle:

- **Not distributed, but only because they say so** — they are picked up automatically by Claude Code when it runs in this working directory, and there is no marketplace, no `claude plugin validate` step, no `plugin.json`, no version field. What actually keeps them out of an npx install is `metadata: internal: true` in the frontmatter. The installer searches `.claude/skills/` directly — it is one of the per-agent project directories it always looks in, alongside the plugin skills it resolves through `.claude-plugin/marketplace.json` — and honors the flag by skipping any skill that carries it. Without it, repo-only tooling is offered to people who have no repo. (Verified against `skills` 1.5.23; the whole-repo walk people assume happens is a fallback that runs only when the targeted search finds nothing.) **Every new project-local skill needs that flag** — `make check-frontmatter` fails without it, via `scripts/check_internal_flag.py`, which now polices all three trees at once: required under `.claude/skills/` and `preview/paad/skills/`, and *forbidden* under `plugins/paad/skills/`, where a flag that survived promotion would make a shipped skill silently invisible to every installer:

  ```yaml
  ---
  name: roadmap
  description: …
  metadata:
    internal: true
  ---
  ```
- **No `make bump-version` impact** — `make bump-version` rewrites `package.json`, `plugin.json`, `marketplace.json`, and every `plugins/paad/skills/*/SKILL.md` announce line. Project-local SKILL.md files are skipped on purpose. They have no announce-line version, no `paad:<name>` namespace.
- **Almost no `make test` checks** — check-digraphs / check-help / check-readme / check-skill-versions walk the plugin trees and enforce nothing here. The one exception is `check-frontmatter`, which asserts the `internal: true` flag above.
- **Edit-and-commit, plus the flag** — change the SKILL.md, commit, you're done. No version bump, no help table edit, no README entry, no `paad:paad-help` cross-reference. The `internal: true` flag is the only thing you must not forget.
- **Naming** — invoke as `/<name>` (no `paad:` prefix), because they're not in a plugin. `/roadmap`, not `/paad:roadmap`.

When reviewing or modifying a `.claude/skills/<name>/SKILL.md`, do not chase the paad-plugin conventions (announce lines, version literals, help / README cross-references). They don't apply here.
