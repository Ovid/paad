# Design: `.paadrc` and a single artifact root

**Date:** 2026-08-21
**Status:** SUPERSEDED — not implemented, and will not be

`.paadrc` was dropped. Open question 1 was settled by verification instead:
`npx skills@latest add Ovid/paad` works against this repository today. It
discovers skills through `.claude-plugin/marketplace.json` → `plugins/paad`,
copies whole skill directories verbatim (exec bits preserved), and installs to
70+ agents. So every install route except the hand-copy tree already agrees on
`paad/`, and the split this design existed to close is frozen rather than
growing. `kiro_and_antigravity/` keeps its `.reviews/` rewrites and is
deprecated in the README, with a migration table for anyone switching routes.

Two claims in the body are wrong and left standing for the record: nothing ever
wrote `.reports/`, and `make check-export-current` diffs only
`kiro_and_antigravity/` and `pi/`, so it would not have caught drift in a
script copied into `plugins/paad/skills/*/scripts/`.

**Touches:** every artifact-writing skill, `scripts/convert_skills.py`, `Makefile`, `README.md`, `CHANGELOG.md`

## Why

The Kiro and Antigravity export rewrites paad's output paths into `.reviews/`
and `.reports/`. A team running more than one AI IDE against the same
repository therefore gets its reports split across two directory trees
depending on which tool produced them, and neither tool looks where the other
writes. `paad/` is the only path all of them already agree on, because it is
what the plugin sources say.

Two changes follow from that. Artifacts default to `paad/` everywhere, on every
platform. And a `.paadrc` file at the repository root can move that root, for
teams whose layout wants the reports somewhere else.

The secondary goal is one install path outside Claude Code —
`npx skills@latest add Ovid/paad` — which the divergent output paths were an
obstacle to. That goal is **not** settled by this document; see Open questions.

## The config file

`.paadrc` at the repository root. One `key: value` per line.

```
artifact-root: docs/reviews
```

`artifact-root` is the only key. It replaces the leading `paad/` in every path
a skill writes: with the value above, `paad/code-reviews/…` becomes
`docs/reviews/code-reviews/…`. The subdirectory layout under the root does not
change and is not configurable.

Absent file, absent key, or empty value all mean `paad`.

The format is `key: value` rather than a bare path so that a second key can be
added later without a format migration. Nothing else is planned for it.

## The resolver

One POSIX `sh` script, `paadrc.sh`, copied into the `scripts/` directory of
every skill that writes artifacts.

```sh
#!/bin/sh
# Resolve a .paadrc key. Usage: scripts/paadrc.sh artifact-root
# Prints "<key>: <value>" on success — including when .paadrc is absent,
# in which case the built-in default is used. Any other output, or none,
# means the caller must resolve the key itself.
key="$1"
case "$key" in
  artifact-root) default="paad" ;;
  *) echo "paadrc: unknown key '$key'" >&2; exit 2 ;;
esac
value=$(sed -n "s/^[[:space:]]*$key[[:space:]]*:[[:space:]]*//p" .paadrc 2>/dev/null \
        | head -1 | sed 's/[[:space:]]*$//; s|/*$||')
[ -n "$value" ] || value="$default"
echo "$key: $value"
```

`.paadrc` is read relative to the working directory, which is the repository
being analyzed. The script's own location is irrelevant to what it reads.

### Why one script and not three

The rejected proposal was a shared `paad:paadrc` skill carrying node, Python,
and bash implementations, invoked by the other skills.

Skill-to-skill invocation is real — Claude Code documents itself doing it
(`skills.md:143`: a loaded skill's content gains an instruction to invoke
directory-qualified variants). What is not real is a *portable* way to ask.
The Agent Skills specification delegates activation to the client and defines
no mechanism, and every client picked a different one: Claude Code `/paad:x`,
Pi `/skill:x`, Kiro `/x`, Codex `@x` or `$x`, Antigravity a name-mention. One
skill body would have to spell out five ways to do one thing. Pi's own
documentation adds the reliability problem — "models don't always do this" —
and a config read that silently no-ops is worse than none.

Three language implementations answer a question that does not arise. Every
platform runs `scripts/` through a shell tool; where that tool is absent, node
and Python are equally unreachable. The language only matters when a shell
exists but the interpreter does not, and POSIX `sh` needs no interpreter beyond
the shell. One script, and it runs under dash, ash, and busybox.

### Detecting failure

The script always prints `artifact-root: <value>`, including when it falls back
to the default. The calling skill needs no theory about exit codes: if that
line did not come back, resolve the root without the script. A missing script,
a missing shell, a shell error, and empty output all collapse to the same
fallback.

`exit 2` on an unknown key is a bug in the calling skill, not a missing config,
and is deliberately loud.

## What each skill gets

A generated preamble, immediately after the announce line:

> **Artifact root:** run `paadrc.sh artifact-root` from this skill's `scripts/`
> directory. It prints `artifact-root: <path>`; use that path wherever this
> skill says `paad/`. If it prints anything else or nothing, read `.paadrc` at
> the repository root yourself and take the `artifact-root:` value; if there is
> no such file, use `paad/`.

Every other `paad/…` mention in the skill — prose, digraph nodes, sample output
— stays literal. Substituting a placeholder throughout would be a much larger
diff and would make the digraphs and examples harder to read for no behavioral
gain.

Nine skills write artifacts and get both the preamble and the script:
`agentic-a11y`, `agentic-architecture`, `agentic-dedup`, `agentic-owasp`,
`agentic-review`, `alignment`, `fix-architecture`, `pushback`, `test-roadmap`.

`help` writes nothing but documents the paths; it gets a prose mention of
`.paadrc` and no script. `handoff`, `vibe`, `rethink`, and `makefile` are
unaffected.

## Generation and drift

`plugins/paad/shared/paadrc.sh` is the single source. `convert_skills.py`
copies it into each writing skill's `scripts/` directory, and
`make check-export-current` fails if a copy drifts. This is the pattern the
repository already runs for the Kiro, Antigravity, and Pi outputs.

The copies are generated and committed, because Pi and Claude Code load
straight out of `plugins/paad/skills/` — a script that only existed after a
build step would not be there when they look.

`convert_skills.py` currently copies only `references/`. It needs to copy
`scripts/` on the same terms, or the Kiro export ships skills whose preamble
points at a file that is not there. The prose fallback would cover it, but
silently, which is the failure this design is trying to avoid.

## Export changes

Delete the five path rewrites in `neutralize_paths()`
(`scripts/convert_skills.py:80-86`):

```python
text = text.replace("paad/architecture-reviews/", ".reviews/architecture/")
text = text.replace("paad/code-reviews/", ".reviews/code/")
text = text.replace("paad/pushback-reviews/", ".reviews/pushback/")
text = text.replace("paad/alignment-reviews/", ".reviews/alignment/")
text = re.sub(r"(?<!Ovid/)paad/", ".reviews/", text)
```

That is the whole of the `.reviews/` problem. Everything else those functions
do — stripping `subagent_type:` fragments and `/paad:` command references —
stays, because those genuinely have no meaning outside Claude Code.

The catch-all regex also carried a `(?<!Ovid/)` guard so that
`github.com/Ovid/paad` survived. With the rewrites gone the guard goes too.

One check blocks the deletion and has to go with it. `check-export-frontmatter`
(`Makefile:247`) fails any exported `description:` containing `paad/`, and
`fix-architecture`'s description names `paad/architecture-reviews/` in its first
sentence. It passes today only because `neutralize_description()` also calls
`neutralize_paths()`. Under this design a `paad/` path in an exported
description is the correct output, not a leak, so drop that `case` from the
check. The other three rules it enforces — non-empty name, non-empty
description, no `/paad:` command — are unaffected.

## Split out: the export frontmatter bug

`neutralize()` runs over the YAML frontmatter and deletes descriptions from the
Kiro export. It was filed here as a bug fixed in passing. It is not in passing —
it affects four skills by two distinct causes, plus an inverse leak in the
Antigravity wrappers, and it shares no line of `convert_skills.py` with the
changes above.

It got its own spec, `2026-08-21-export-frontmatter-fix.md`, and shipped in
paad 1.30.2 — before this design was implemented. That fix is why the rewrites
above now live in `neutralize_paths()` rather than `neutralize()`, and why
`check-export-frontmatter` exists to be amended.

## Verification

- `make check-artifact-root` — every artifact-writing skill carries the
  preamble and a `scripts/paadrc.sh`; the copies match the shared source.
- `make check-export-current` already catches a stale export.
- A `demo`/self-check for `paadrc.sh` itself: absent file, present key, absent
  key, trailing slash, trailing whitespace, unknown key.
- Drive at least one writing skill for real on a repository with a `.paadrc`
  and one without.

## Out of scope

- Per-skill output overrides. One root, one layout beneath it.
- Configuring anything other than the artifact root.
- Migrating existing `.reviews/` directories. Users who have them keep them;
  the next run writes to `paad/`.

## Open questions

1. **Does `npx skills@latest add Ovid/paad` work against this repository's
   layout?** Unverified. The skills live under `plugins/paad/skills/`, not at
   the repository root, and whether that installer finds them, and whether it
   carries `scripts/` across, has not been checked. This is the goal behind the
   whole change and it is the next thing to settle.
2. **Does the Kiro/Antigravity export still need to exist** once a single
   install path works? If the installer handles those platforms, the export is
   dead weight — but it also strips `/paad:` references those platforms cannot
   use, so retiring it is not a pure deletion.
3. **How does a skill address its own `scripts/` directory** on each platform?
   The specification says relative paths from the skill root, but the working
   directory is the repository being analyzed. The prose fallback makes a wrong
   guess harmless rather than fatal, but if this proves unreliable in practice
   the script buys nothing over prose alone, and Option 3 from the design
   conversation becomes the right answer.
