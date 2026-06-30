#!/usr/bin/env python3
"""Generate the Kiro power's `steering/` files from the PAAD skills.

Each in-scope `plugins/paad/skills/<name>/SKILL.md` becomes a
`steering/<name>.md` whose body is the source SKILL.md run through the SHARED
body-cleaning core (`skill_body.clean_body`) plus three POWER-SPECIFIC
transforms layered on top:

  1. Cross-skill refs `/paad:<name>` -> `#<name>` (injected as `clean_body`'s
     `paad_ref_transform`, *replacing* the legacy line-stripping — the line is
     kept, only the token is rewritten).
  2. Surviving prose `$ARGUMENTS` -> a prompt telling the user to state the
     scope in their chat message. Kiro slash commands have NO argument
     mechanism, so the prose must prompt, not imply auto-capture. Applied AFTER
     `clean_body` because it is power-specific, not part of the shared core.
  3. ```dot digraphs pass through verbatim — `clean_body` already preserves
     them, and transform #2 deliberately skips fenced `dot` blocks so digraph
     `$ARGUMENTS` node labels are not rewritten.

The source SKILL.md's own `name:`/`description:` frontmatter is STRIPPED; each
steering file is prefixed with the literal `---\ninclusion: manual\n---`
frontmatter as its first content (no leading blank line, no BOM). The
`name:`/`description:` metadata is surfaced in POWER.md, not here.

Running this script regenerates the whole Kiro power: the aggregated `POWER.md`
manifest at the repo root plus one `steering/<name>.md` per in-scope skill. The
`--check` mode regenerates both in memory and reports any on-disk file that has
drifted from what the generator would produce now (excluding the floating
provenance stamp), so `make check-kiro` enforces single-source-of-truth.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

# Make the shared body-cleaning core importable regardless of cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_body import clean_body  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "plugins" / "paad" / "skills"
STEERING_DIR = REPO_ROOT / "steering"
PLUGIN_JSON = REPO_ROOT / "plugins" / "paad" / ".claude-plugin" / "plugin.json"
SIDECAR = Path(__file__).resolve().parent / "kiro-keywords.yaml"
POWER_MD = REPO_ROOT / "POWER.md"

# Mirrors convert_skills.py's skip_names: these two skills are not emitted.
# `help` becomes POWER.md's index; `makefile` is intentionally omitted to keep
# the power's skill set identical to the legacy Kiro output.
SKIP_NAMES = {"help", "makefile"}

STEERING_FRONTMATTER = "---\ninclusion: manual\n---\n"

# A self-contained ```dot ... ``` fenced block. Used to protect digraphs from
# the cross-skill-ref and `$ARGUMENTS` transforms (digraphs are copied
# verbatim). The open fence tolerates trailing characters (e.g. a stray
# "```dot   " with trailing spaces) so such a block is still stashed rather than
# silently rewritten.
_DOT_BLOCK = re.compile(r"```dot[^\n]*\n.*?\n```", re.DOTALL)

# Leading YAML frontmatter (`---\n...\n---`) at the very start of a body.
# `clean_body` retains whatever precedes the first `##`, which includes the
# source SKILL.md's `name:`/`description:` frontmatter. Steering files replace
# that with their own `inclusion: manual` frontmatter, so we strip it here.
_LEADING_FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)


def rewrite_cross_skill_refs(text):
    """Power `paad_ref_transform`: rewrite `/paad:<name>` -> `#<name>`.

    Unlike the legacy `strip_paad_references`, this keeps the surrounding line
    and only rewrites the reference token, so cross-skill mentions become Kiro
    `#<name>` steering references.
    """
    return re.sub(r"/paad:([a-z0-9-]+)", r"#\1", text)


def strip_leading_frontmatter(body):
    """Remove the source SKILL.md's leading `---...---` frontmatter block.

    `clean_body` keeps the source's `name:`/`description:` frontmatter (it
    precedes the first `##`); steering files replace it with their own
    `inclusion: manual` frontmatter, so we drop the original here. The body then
    starts at the skill's `# Title` h1.
    """
    return _LEADING_FRONTMATTER.sub("", body, count=1)


def apply_outside_dot_blocks(text, transform):
    """Apply `transform` to `text` everywhere EXCEPT inside ```dot blocks.

    ```dot digraphs are copied verbatim, so any power transform that rewrites
    tokens (cross-skill refs, `$ARGUMENTS`) must skip them. This stashes each
    fenced `dot` block behind a NUL sentinel, runs `transform` on the remainder,
    then restores the blocks byte-for-byte.
    """
    # NUL is never valid in hand-authored markdown; if it appeared, the stash
    # sentinel would collide and `_restore` would fail opaquely. Fail loudly.
    assert "\x00" not in text, "input contains a NUL byte; not valid markdown"

    stash = []

    def _stash(match):
        stash.append(match.group(0))
        return f"\x00DOT{len(stash) - 1}\x00"

    protected = _DOT_BLOCK.sub(_stash, text)
    protected = transform(protected)

    def _restore(match):
        return stash[int(match.group(1))]

    return re.sub(r"\x00DOT(\d+)\x00", _restore, protected)


def _rewrite_arguments_tokens(text):
    """Rewrite `$ARGUMENTS` tokens in `text` (assumes dot blocks already removed).

    Most `$ARGUMENTS` lives in excluded sections and is already gone; this
    handles whatever survives in retained prose.
    """
    scope_prose = (
        "the path or scope you state in your chat message (for example, `src/`)"
    )

    # Special-case the `If no `$ARGUMENTS` provided` idiom (the real vibe.md
    # phrasing): a blunt noun substitution yields the ungrammatical "If no the
    # path or scope ... provided". Rewrite the whole clause as a clean
    # conditional that still prompts the user for scope.
    text = re.sub(
        r"If no `?\$ARGUMENTS`?\s+(?:is\s+|are\s+|was\s+)?provided",
        "If you don't state a scope in your chat message",
        text,
    )

    # Replace any remaining `$ARGUMENTS` (optionally backtick-wrapped) with the
    # prose noun phrase.
    return re.sub(r"`?\$ARGUMENTS`?", scope_prose, text)


def rewrite_arguments_to_scope_prompt(body):
    """Rewrite surviving prose `$ARGUMENTS` tokens into a scope prompt.

    Kiro manual steering files have no argument mechanism, so any `$ARGUMENTS`
    that survives `clean_body` (most live in excluded sections and are already
    gone) must prompt the user to state the scope in their chat message rather
    than imply automatic capture.

    Digraph `$ARGUMENTS` (inside ```dot blocks) is left untouched — digraphs are
    copied verbatim.
    """
    return apply_outside_dot_blocks(body, _rewrite_arguments_tokens)


def prepend_steering_frontmatter(body):
    """Prefix `body` with the literal `inclusion: manual` frontmatter.

    The result's first content is `---\\ninclusion: manual\\n---` — no leading
    blank line, no BOM — followed by exactly one blank line and then the body's
    `# Title`. Leading whitespace left by frontmatter-stripping is trimmed so the
    separator is never doubled.
    """
    return STEERING_FRONTMATTER + "\n" + body.lstrip("\n")


def build_steering_file(source_content, skill_name):
    """Return the full `steering/<skill_name>.md` content for one source skill.

    Pure (string in -> string out). The power transforms layer ON TOP of the
    shared `clean_body()` — section exclusion, path neutralization, and
    whitespace collapsing all come from `clean_body`; this function only adds
    the power-specific cross-ref / `$ARGUMENTS` / frontmatter handling.
    """
    body = clean_body(source_content, paad_ref_transform=rewrite_cross_skill_refs)
    body = strip_leading_frontmatter(body)
    # `clean_body` only applies `paad_ref_transform` to `##` sections, so a
    # `/paad:` in the pre-`##` intro (e.g. fix-architecture) would survive.
    # Re-run the rewrite over the whole body to catch those — but skip ```dot
    # blocks, which are copied verbatim. Idempotent: a `#name` already rewritten
    # is left unchanged.
    body = apply_outside_dot_blocks(body, rewrite_cross_skill_refs)
    body = rewrite_arguments_to_scope_prompt(body)
    return prepend_steering_frontmatter(body)


def _in_scope_skill_names(source_dir):
    return sorted(
        p.name
        for p in Path(source_dir).iterdir()
        if p.is_dir()
        and p.name not in SKIP_NAMES
        and (p / "SKILL.md").exists()
    )


def generate(source_dir=SOURCE_DIR, out_dir=STEERING_DIR):
    """Write one `steering/<name>.md` per in-scope skill into `out_dir`."""
    source_dir = Path(source_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for name in _in_scope_skill_names(source_dir):
        source = (source_dir / name / "SKILL.md").read_text(encoding="utf-8")
        (out_dir / f"{name}.md").write_text(
            build_steering_file(source, name), encoding="utf-8"
        )
        print(f"Wrote steering/{name}.md")


# ===========================================================================
# POWER.md aggregation (Task 3)
#
# POWER.md is the power's single manifest at the repo root. It aggregates the 7
# in-scope skills into one Kiro power:
#   * frontmatter — `name`/`version` READ from plugin.json (can't drift),
#     `keywords` = the curated sidecar `power:` list, the rest design constants.
#   * onboarding — SOURCED from `help/SKILL.md` so it can never drift from the
#     Claude Code help text.
#   * a generated "When to load steering files" routing list — one `#<name>`
#     entry per in-scope skill, derived from that skill's frontmatter.
#
# `build_power_md()` is PURE and deterministic (no git, no file I/O). The
# orchestrator `generate_power()` appends the git provenance stamp AFTER that
# deterministic content, so Task 4's drift check can compare the stamp-free body.
# ===========================================================================

# Design "Generated POWER.md shape" constants — these do NOT come from any file
# (unlike `name`/`version`/`keywords`), so they live as generator constants.
POWER_DISPLAY_NAME = "PAAD — Architecture, Review & Quality Skills"
POWER_DESCRIPTION = (
    "Multi-agent architecture analysis, code review, accessibility, and "
    "quality workflows."
)
POWER_AUTHOR = "Ovid"

# Frontmatter for one SKILL.md (`---\n...\n---`) at the very start of the file.
_SKILL_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def read_plugin_meta(plugin_json_path=PLUGIN_JSON):
    """Read `name` and `version` from plugin.json.

    POWER.md's `name`/`version` are sourced here so they can never drift from
    the Claude Code plugin manifest (the design's "version mirrors plugin.json").
    """
    data = json.loads(Path(plugin_json_path).read_text(encoding="utf-8"))
    return {"name": data["name"], "version": data["version"]}


def load_sidecar(sidecar_path=SIDECAR):
    """Parse the Kiro keyword sidecar (`kiro-keywords.yaml`) via PyYAML."""
    return yaml.safe_load(Path(sidecar_path).read_text(encoding="utf-8"))


def read_skill_frontmatter(source_content):
    """Parse a SKILL.md's leading `---...---` frontmatter into a dict.

    Used to derive each routing entry's `name`/`description` from the source
    skill (drift-proof — descriptions are never hand-copied into POWER.md).
    """
    match = _SKILL_FRONTMATTER.search(source_content)
    if not match:
        return {}
    return yaml.safe_load(match.group(1)) or {}


def missing_sidecar_entries(skill_names, sidecar):
    """Return in-scope skills with no entry in the sidecar's `skills:` map.

    Pure and testable: feed a sidecar missing an entry and assert the result.
    Sorted for deterministic warnings.
    """
    present = set((sidecar.get("skills") or {}).keys())
    return sorted(name for name in skill_names if name not in present)


def warn_missing_sidecar_entries(skill_names, sidecar):
    """Emit a stderr warning for any in-scope skill missing a sidecar entry.

    A newly added skill cannot ship without an explicit keyword decision: the
    warning forces the author to add a `skills:` entry (Design: "Edge cases").
    """
    missing = missing_sidecar_entries(skill_names, sidecar)
    if missing:
        print(
            "WARNING: skills missing from kiro-keywords.yaml `skills:` map: "
            + ", ".join(missing),
            file=sys.stderr,
        )
    return missing


def _power_frontmatter(plugin_meta, sidecar):
    """Build the POWER.md YAML frontmatter block (literal first content).

    `name`/`version` come from plugin.json; `keywords` is the sidecar `power:`
    list VERBATIM (not a union of per-skill keywords); the rest are constants.
    """
    keywords = ", ".join(sidecar["power"])
    return (
        "---\n"
        f"name: {plugin_meta['name']}\n"
        f"displayName: {POWER_DISPLAY_NAME}\n"
        f"description: {POWER_DESCRIPTION}\n"
        f"keywords: [{keywords}]\n"
        f"author: {POWER_AUTHOR}\n"
        f"version: {plugin_meta['version']}\n"
        "---\n"
    )


# Short Kiro-context framing appended after the help-sourced tagline. POWER.md's
# detailed skill directory is the generated "When to load steering files"
# routing list (frontmatter-derived, `#<name>`), NOT the verbatim Claude Code
# help overview — so the onboarding stays concise and Claude-Code-isms (the
# `/paad:` skill list, the `makefile` line) never leak into the power.
POWER_FRAMING = (
    "Each skill is exposed as a manual steering file the agent loads on "
    "demand. Pick the one that matches your request from the list below."
)


def _help_tagline(help_content):
    """Extract just the help OVERVIEW TAGLINE from `help/SKILL.md`.

    The tagline is the first non-empty line of the fenced overview block inside
    the `## Overview (no arguments)` section. Sourcing the tagline (rather than
    hand-writing it) keeps POWER.md's onboarding drift-proof, while DROPPING the
    rest of the verbatim overview block (the `/paad:` skill list + `makefile`
    line) that is Claude-Code-specific and wrong for the Kiro power context.

    Falls back to the first non-empty line of the content if the expected
    markers are absent (keeps the builder robust + deterministic).
    """
    after = help_content.split("## Overview (no arguments)", 1)
    region = after[1] if len(after) > 1 else help_content
    # Tolerate a language hint on the opening fence (e.g. ```text) and anchor to
    # the FIRST fence in the Overview region. `[^\n]*` mirrors `_DOT_BLOCK`'s
    # language tolerance; a bare-fence-only pattern would silently match the
    # WRONG fence if the help block ever gained a language hint, corrupting the
    # tagline into the literal `---` frontmatter marker.
    fence = re.search(r"```[^\n]*\n(.*?)\n```", region, re.DOTALL)
    block = fence.group(1) if fence else region
    for line in block.splitlines():
        if line.strip():
            return line.strip()
    return region.strip()


def _onboarding(help_content):
    """Build the trimmed, Kiro-appropriate onboarding.

    The help tagline (sourced verbatim, drift-proof) plus a short framing
    sentence — NOT the verbatim help overview block. The detailed skill listing
    is the generated routing list, so it is never duplicated here.
    """
    return _help_tagline(help_content) + "\n\n" + POWER_FRAMING


def _routing_list(source_dir):
    """Build the "When to load steering files" routing list.

    One entry per in-scope skill (sorted), each `**#<name>** — <description>`
    derived from that skill's frontmatter (drift-proof).
    """
    source_dir = Path(source_dir)
    lines = [
        "## When to load steering files",
        "",
        "Each skill is a manual steering file — load the one matching the "
        "user's request (type `/` in chat to pick it, or reference `#<name>`):",
        "",
    ]
    for name in _in_scope_skill_names(source_dir):
        source = (source_dir / name / "SKILL.md").read_text(encoding="utf-8")
        fm = read_skill_frontmatter(source)
        description = fm.get("description", "").strip()
        lines.append(f"- **#{name}** — {description}")
    return "\n".join(lines)


def build_power_md(source_dir, sidecar, plugin_meta, help_content):
    """Return the POWER.md content (PURE, deterministic, no git).

    Reads the in-scope SKILL.md files (via `_routing_list`) to derive the
    routing entries, but performs NO git calls and NO writes — given the same
    inputs it always returns byte-identical output.

    Composed of:
      1. frontmatter (name/version from plugin_meta, keywords from sidecar).
      2. onboarding sourced from `help_content`.
      3. a generated "When to load steering files" routing list.

    The provenance stamp is NOT included — the orchestrator appends it AFTER
    this content so Task 4's drift check can compare a stamp-free body.
    """
    frontmatter = _power_frontmatter(plugin_meta, sidecar)
    onboarding = _onboarding(help_content)
    routing = _routing_list(source_dir)

    return (
        frontmatter
        + "\n"
        + "# PAAD — Kiro Power\n"
        + "\n"
        + onboarding
        + "\n"
        + "\n"
        + routing
        + "\n"
    )


def git_short_sha():
    """Return the repo's current short commit SHA (orchestrator-only).

    Isolated behind a helper so the pure builder stays git-free and tests can
    monkeypatch it for a deterministic provenance stamp.
    """
    return subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def provenance_stamp(short_sha):
    """Return the provenance stamp line for `short_sha`.

    A single, clearly-separable HTML comment appended as POWER.md's FINAL line.
    Injecting it AFTER the comparable content lets Task 4's drift check exclude
    it.
    """
    return f"<!-- Generated from paad@{short_sha} by build-kiro-power -->"


# ===========================================================================
# Drift / idempotency (Task 4)
#
# The committed POWER.md's stamp embeds HEAD-at-generation-time, so it ALWAYS
# lags HEAD by one commit and a naive `git diff --exit-code` is forever dirty.
# The drift check therefore compares a STAMP-FREE view of POWER.md. The same
# `without_stamp` helper is shared by the idempotency test and the drift check
# so they cannot disagree (the REFACTOR seam), and the comparison itself is a
# PURE `find_drift(generated, ondisk)` over in-memory `{name: content}` maps.
# ===========================================================================

# Matches the provenance-stamp line anchored on the stable, content-free prefix
# (so a changed short SHA never registers as drift) AND on end-of-text (`\Z`):
# the stamp is contractually the FINAL line, so anchoring there means a body line
# that merely STARTS with the stamp literal mid-document is never stripped.
_STAMP_LINE = re.compile(
    r"<!-- Generated from paad@[0-9a-f]+ by build-kiro-power -->\n?\Z"
)


def without_stamp(text):
    """Return `text` with the provenance-stamp line removed.

    Shared by the idempotency test and the drift check: a POWER.md that differs
    from a freshly-generated one ONLY in its embedded short SHA must compare
    equal, because the committed stamp always lags HEAD by one commit. Text with
    no stamp is returned unchanged (idempotent).
    """
    return _STAMP_LINE.sub("", text)


def find_drift(generated, ondisk):
    """Return the sorted names of files that have really drifted.

    PURE comparison of two `{name: content}` maps (the freshly-generated
    contents vs. the on-disk contents). For each generated file:

      * POWER.md is compared with the provenance stamp normalized away
        (`without_stamp`), so a stamp-only delta is NOT drift.
      * Any other file is compared byte-for-byte.
      * A generated file missing entirely from `ondisk` counts as drift.

    Returns the drifted file names sorted (deterministic). An empty list means
    the on-disk tree matches what the generator would produce now.

    Orphans: any on-disk `steering/*.md` with no generator counterpart is also
    drift (the generators only WRITE, never DELETE, so a removed/renamed skill
    leaves a stale steering file the generator would never produce). POWER.md is
    always regenerated, so the orphan sweep is steering-only.
    """
    def _norm(name, content):
        return without_stamp(content) if name == "POWER.md" else content

    drifted = []
    for name, gen_content in generated.items():
        if name not in ondisk:
            drifted.append(name)
            continue
        if _norm(name, gen_content) != _norm(name, ondisk[name]):
            drifted.append(name)

    # Flag stale on-disk steering files the generator would never produce.
    for name in ondisk:
        if (
            name not in generated
            and name.startswith("steering/")
            and name.endswith(".md")
        ):
            drifted.append(name)

    return sorted(drifted)


def _load_power_inputs(source_dir):
    """Read the three POWER.md inputs: plugin meta, sidecar, and help content.

    Shared by `generate_power` (the writer) and `_generate_in_memory` (the drift
    check) so the two paths can never diverge in HOW they load inputs. PURE reads
    only — no warnings, no writes; those side-effects stay in `generate_power`.
    """
    source_dir = Path(source_dir)
    plugin_meta = read_plugin_meta()
    sidecar = load_sidecar()
    help_content = (source_dir / "help" / "SKILL.md").read_text(encoding="utf-8")
    return plugin_meta, sidecar, help_content


def _generate_in_memory(source_dir):
    """Return the `{relative-name: content}` map the generator WOULD write.

    Builds POWER.md (with the current provenance stamp) and every in-scope
    `steering/<name>.md` purely in memory — no writes — so the drift check never
    mutates the working tree.
    """
    source_dir = Path(source_dir)

    plugin_meta, sidecar, help_content = _load_power_inputs(source_dir)

    power_body = build_power_md(
        source_dir=source_dir,
        sidecar=sidecar,
        plugin_meta=plugin_meta,
        help_content=help_content,
    )
    power = power_body + "\n" + provenance_stamp(git_short_sha()) + "\n"

    generated = {"POWER.md": power}
    for name in _in_scope_skill_names(source_dir):
        source = (source_dir / name / "SKILL.md").read_text(encoding="utf-8")
        generated[f"steering/{name}.md"] = build_steering_file(source, name)
    return generated


def _read_ondisk(root, names):
    """Read the on-disk content for the generator's files PLUS every steering file.

    Returns a `{name: content}` map. The explicit `names` (the generator's
    outputs) are read so a missing one is reported as drift; in ADDITION, every
    actual `steering/*.md` under `root` is enumerated so a stale ORPHAN (a
    steering file with no generator counterpart) is visible to `find_drift`. A
    file that does not exist is simply omitted.
    """
    root = Path(root)
    ondisk = {}
    for name in names:
        path = root / name
        if path.exists():
            ondisk[name] = path.read_text(encoding="utf-8")

    # Enumerate the real steering tree so orphaned files (never (re)generated)
    # become visible — the generators only write, never delete.
    steering_dir = root / "steering"
    if steering_dir.is_dir():
        for path in sorted(steering_dir.glob("*.md")):
            name = f"steering/{path.name}"
            if name not in ondisk:
                ondisk[name] = path.read_text(encoding="utf-8")

    return ondisk


def check_drift(source_dir=SOURCE_DIR, root=REPO_ROOT):
    """Return the sorted names of committed power files that have drifted.

    Regenerates POWER.md + every steering file IN MEMORY from `source_dir`, reads
    the matching on-disk files under `root` (plus every on-disk `steering/*.md`
    so orphans are caught), and compares them with `find_drift` (excluding the
    provenance stamp). An empty list means the committed power is up to date; a
    non-empty list names the stale, hand-edited, or orphaned files.
    """
    generated = _generate_in_memory(source_dir)
    ondisk = _read_ondisk(root, generated.keys())
    return find_drift(generated, ondisk)


def generate_power(source_dir=SOURCE_DIR, out_path=POWER_MD):
    """Write POWER.md: the pure deterministic content + the provenance stamp.

    Loads plugin.json, the sidecar, and `help/SKILL.md`; warns about any
    in-scope skill missing a sidecar entry; builds the deterministic content;
    then appends the git provenance stamp as the final line and writes the file.
    """
    source_dir = Path(source_dir)
    out_path = Path(out_path)

    plugin_meta, sidecar, help_content = _load_power_inputs(source_dir)

    warn_missing_sidecar_entries(_in_scope_skill_names(source_dir), sidecar)

    content = build_power_md(
        source_dir=source_dir,
        sidecar=sidecar,
        plugin_meta=plugin_meta,
        help_content=help_content,
    )
    # Stamp is appended AFTER the comparable content (REFACTOR seam): one blank
    # line then the stamp as the clearly-separable final line.
    stamped = content + "\n" + provenance_stamp(git_short_sha()) + "\n"
    out_path.write_text(stamped, encoding="utf-8")
    print(f"Wrote {out_path.name}")


def _main(argv):
    """CLI entry point. `--check` reports drift; otherwise regenerate the power.

    `--check` exits non-zero (1) with a per-file message when the committed
    POWER.md / steering files are stale or hand-edited (ignoring the provenance
    stamp), and exits 0 when the tree is clean. The default (no args) regenerates
    the steering files and POWER.md.
    """
    if "--check" in argv:
        drifted = check_drift()
        if drifted:
            print(
                "DRIFT: the committed Kiro power is stale or hand-edited. "
                "Run `make kiro` to regenerate. Drifted files:",
                file=sys.stderr,
            )
            for name in drifted:
                print(f"  - {name}", file=sys.stderr)
            return 1
        print("Kiro power is up to date (no drift).")
        return 0

    generate()
    generate_power()
    print("Steering + POWER.md generation complete.")
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
