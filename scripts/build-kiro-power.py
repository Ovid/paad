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
`name:`/`description:` metadata is surfaced in POWER.md (a later task), not here.

This file is Task 2: steering files only. POWER.md aggregation is Task 3.
"""

import re
import sys
from pathlib import Path

# Make the shared body-cleaning core importable regardless of cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_body import clean_body  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "plugins" / "paad" / "skills"
STEERING_DIR = REPO_ROOT / "steering"

# Mirrors convert_skills.py's skip_names: these two skills are not emitted.
# `help` becomes POWER.md's index; `makefile` is intentionally omitted to keep
# the power's skill set identical to the legacy Kiro output.
SKIP_NAMES = {"help", "makefile"}

STEERING_FRONTMATTER = "---\ninclusion: manual\n---\n"

# A self-contained ```dot ... ``` fenced block. Used to protect digraphs from
# the `$ARGUMENTS` prose transform (digraphs are copied verbatim).
_DOT_BLOCK = re.compile(r"```dot\n.*?\n```", re.DOTALL)

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


def rewrite_arguments_to_scope_prompt(body):
    """Rewrite surviving prose `$ARGUMENTS` tokens into a scope prompt.

    Kiro manual steering files have no argument mechanism, so any `$ARGUMENTS`
    that survives `clean_body` (most live in excluded sections and are already
    gone) must prompt the user to state the scope in their chat message rather
    than imply automatic capture.

    Digraph `$ARGUMENTS` (inside ```dot blocks) is left untouched — digraphs are
    copied verbatim — so this protects fenced `dot` blocks before rewriting.
    """
    scope_prose = (
        "the path or scope you state in your chat message (for example, `src/`)"
    )

    # Protect ```dot blocks: stash them, rewrite, then restore.
    stash = []

    def _stash(match):
        stash.append(match.group(0))
        return f"\x00DOT{len(stash) - 1}\x00"

    protected = _DOT_BLOCK.sub(_stash, body)

    # Special-case the `If no `$ARGUMENTS` provided` idiom (the real vibe.md
    # phrasing): a blunt noun substitution yields the ungrammatical "If no the
    # path or scope ... provided". Rewrite the whole clause as a clean
    # conditional that still prompts the user for scope.
    protected = re.sub(
        r"If no `?\$ARGUMENTS`?\s+(?:is\s+|are\s+|was\s+)?provided",
        "If you don't state a scope in your chat message",
        protected,
    )

    # Replace any remaining `$ARGUMENTS` (optionally backtick-wrapped) with the
    # prose noun phrase.
    protected = re.sub(r"`?\$ARGUMENTS`?", scope_prose, protected)

    # Restore the digraphs verbatim.
    def _restore(match):
        return stash[int(match.group(1))]

    return re.sub(r"\x00DOT(\d+)\x00", _restore, protected)


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
    # Re-run the rewrite over the whole body to catch those. Idempotent: a
    # `#name` already rewritten is left unchanged.
    body = rewrite_cross_skill_refs(body)
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


if __name__ == "__main__":
    generate()
    print("Steering generation complete.")
