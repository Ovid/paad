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
│   └── paad/                      ← the "paad" plugin (namespace for all skills)
│       ├── .claude-plugin/
│       │   └── plugin.json        ← plugin manifest (name, version, metadata)
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
- **Versioning**: both `marketplace.json` and `plugin.json` use semver, plus every `SKILL.md` carries the plugin version inside its on-invocation announce line. Run `make bump-version VERSION=X.Y.Z` to update all three places at once; `make check-skill-versions` (run as part of `make test`) catches drift.
- **Validation**: run `claude plugin validate .` (marketplace) and `claude plugin validate ./plugins/paad` (plugin) before committing
- **Announce on invocation**: every `SKILL.md` must begin its body with the line `**On invocation:** announce "Running paad:<skill-name> v<version>" before anything else.` so users see which skill ran and which version produced the behavior. The literal version string must match `plugin.json`.

## Adding a new skill

1. Create `plugins/paad/skills/<skill-name>/SKILL.md` with frontmatter (`name`, `description`) and instructions
2. Add the on-invocation announce line as the very first line of the body (after the closing `---` of frontmatter): `**On invocation:** announce "Running paad:<skill-name> v<version>" before anything else.` — the version literal must match `plugin.json`
3. Consider `$ARGUMENTS` support — if the skill could benefit from user-provided scope (a file path, directory, branch name, etc.), add an Arguments section documenting usage. Users shouldn't need to remember flags; keep arguments positional and intuitive (e.g., `/paad:skillname path/to/scope`).
4. Add a graphviz digraph (```dot block) covering the skill's decision points and flow. The only exception is `paad:help`, which is a simple display skill. See "Digraph requirements" below.
5. Validate with `claude plugin validate ./plugins/paad`
6. Test locally with `claude --plugin-dir ./plugins/paad`
7. Bump the version with `make bump-version VERSION=X.Y.Z` (updates `plugin.json`, `marketplace.json`, and every SKILL.md announce line in one shot)
8. Update `README.md` to document the new skill under "Available Skills", including argument syntax in the heading
9. Add the new skill to `paad:help` — both the overview table and a detailed help section
10. Run `make test` to verify all checks pass (validate, version sync, skill-version announce, digraphs, help, README, frontmatter)

## Modifying an existing skill

When changing a skill's behavior, arguments, or output, review `plugins/paad/skills/help/SKILL.md` and update the corresponding help text to match.

## Digraph requirements

Every skill (except `paad:help`) must include at least one graphviz digraph (`\`\`\`dot` block) that visualizes the skill's decision points and flow. Digraphs must be:

- **Complete** — every decision point, stop condition, and branching path in the prose must appear in the digraph
- **Accurate** — node labels, edge labels, and flow must match the prose exactly. If the prose changes, the digraph must be updated to match.
- **Relevant** — digraphs exist to prevent the agent from skipping safety gates or misordering steps. Focus on decision points where the agent could cause damage by skipping ahead, not on linear sequences that are obvious from the prose.

When modifying a skill's flow, check that the digraph still matches. When reviewing a skill, cross-reference the digraph against the prose.

`make check-digraphs` runs `scripts/lint_digraphs.py`, which parses each block with graphviz (skipped if graphviz isn't installed) and rejects node attributes attached to edge statements, declared-but-unused nodes, and nodes used in an edge but never declared. It cannot check completeness or accuracy against the prose — that stays a review job.

## Important rules

- Do NOT put `skills/`, `commands/`, or `agents/` inside `.claude-plugin/` — only `plugin.json` or `marketplace.json` go there
- Skill files must be named `SKILL.md` (uppercase) inside a folder whose name becomes the skill name
- Plugin sources in `marketplace.json` use paths relative to the marketplace root (start with `./`)
- Keep marketplace.json plugin descriptions in sync with plugin.json descriptions

## Project-local skills under `.claude/skills/`

The repo also hosts **project-local** skills at `.claude/skills/<name>/SKILL.md` (e.g. `.claude/skills/roadmap/SKILL.md`). These are **not** part of the `paad` plugin and follow a different lifecycle:

- **Not distributed** — they live in this repo only and are picked up automatically by Claude Code when it runs in this working directory. There is no marketplace, no `claude plugin validate` step, no `plugin.json`, no version field.
- **No `make bump-version` impact** — `make bump-version` rewrites `plugin.json`, `marketplace.json`, and every `plugins/paad/skills/*/SKILL.md` announce line. Project-local SKILL.md files are skipped on purpose. They have no announce-line version, no `paad:<name>` namespace.
- **No `make test` checks** — the Makefile's check-frontmatter / check-digraphs / check-help / check-readme / check-skill-versions targets all walk `plugins/paad/skills/`. They do not enforce anything against `.claude/skills/`.
- **Edit-and-commit only** — change the SKILL.md, commit, you're done. No version bump, no help table edit, no README entry, no `paad:help` cross-reference.
- **Naming** — invoke as `/<name>` (no `paad:` prefix), because they're not in a plugin. `/roadmap`, not `/paad:roadmap`.

When reviewing or modifying a `.claude/skills/<name>/SKILL.md`, do not chase the paad-plugin conventions (announce lines, version literals, help / README cross-references). They don't apply here.
