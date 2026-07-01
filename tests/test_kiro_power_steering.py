"""Tests for the Kiro power steering-file generator (`scripts/build-kiro-power.py`).

Task 2 of the Kiro power work: turn each in-scope `plugins/paad/skills/<name>/SKILL.md`
into a `steering/<name>.md` file shaped as:

    ---
    inclusion: manual
    ---

    <transformed body, starting at the skill's `# Title` h1>

The generator layers three *power-specific* transforms on top of the shared
`clean_body()` core (it does NOT re-implement section exclusion / path
neutralization):

  1. cross-skill refs `/paad:<name>` -> `#<name>` (rewrite, not strip)
  2. surviving `$ARGUMENTS` in prose -> a prose "state the scope in chat" prompt
     (digraph `$ARGUMENTS` is left untouched — digraphs are copied verbatim)
  3. ```dot digraph blocks pass through verbatim

The orchestration writes exactly 7 files (all skills except `help`+`makefile`).
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

build_kiro_power = __import__("build-kiro-power")
build_steering_file = build_kiro_power.build_steering_file
generate = build_kiro_power.generate


SOURCE_DIR = REPO_ROOT / "plugins" / "paad" / "skills"


# ---------------------------------------------------------------------------
# build_steering_file() — the pure content builder
# ---------------------------------------------------------------------------

def test_first_line_is_frontmatter_open_then_inclusion_manual():
    """(c) The literal first content is `---` then `inclusion: manual` — no
    leading blank line, no BOM, and the source name:/description: frontmatter
    is stripped."""
    source = (
        "---\n"
        "name: example\n"
        "description: an example skill\n"
        "---\n\n"
        "# Example Title\n\nIntro prose.\n"
    )
    out = build_steering_file(source, "example")

    lines = out.splitlines()
    assert lines[0] == "---"
    assert lines[1] == "inclusion: manual"
    assert lines[2] == "---"
    # No leading blank / BOM.
    assert not out.startswith("\n")
    assert not out.startswith("﻿")
    # Source frontmatter stripped; body starts at the h1.
    assert "name: example" not in out
    assert "description: an example skill" not in out
    assert "# Example Title" in out


def test_exact_shape_one_blank_line_then_h1():
    """The required shape is exactly `---\\ninclusion: manual\\n---\\n\\n<h1>` —
    exactly one blank line between the frontmatter and the body's `# Title`,
    no doubled blank line."""
    source = (
        "---\nname: example\ndescription: an example skill\n---\n\n"
        "# Example Title\n\nIntro prose.\n"
    )
    out = build_steering_file(source, "example")

    assert out.startswith(
        "---\ninclusion: manual\n---\n\n# Example Title\n"
    ), repr(out[:80])


def test_cross_skill_refs_rewritten_to_anchor():
    """(d) `/paad:<name>` -> `#<name>` (rewrite the token, keep the line)."""
    source = (
        "---\nname: x\ndescription: d\n---\n\n"
        "# X\n\n## Body\n\nWhen done, run /paad:agentic-architecture for a deep look.\n"
    )
    out = build_steering_file(source, "x")

    assert "#agentic-architecture" in out
    assert "/paad:agentic-architecture" not in out
    # The surrounding line text is preserved (not stripped).
    assert "When done, run #agentic-architecture for a deep look." in out


def test_cross_skill_ref_in_intro_prose_rewritten():
    """`/paad:<name>` in the pre-`##` intro (which `clean_body` leaves untouched)
    must still be rewritten — the power applies the rewrite to the whole body,
    not just `##` sections. Mirrors fix-architecture's intro reference."""
    source = (
        "---\nname: x\ndescription: d\n---\n\n"
        "# X\n\nFlaws identified by `/paad:agentic-architecture` are fixed here.\n\n"
        "## Body\n\nMore prose.\n"
    )
    out = build_steering_file(source, "x")

    assert "/paad:agentic-architecture" not in out
    assert "`#agentic-architecture`" in out


def test_arguments_in_prose_rewritten_to_scope_prompt():
    """(d) A surviving prose `$ARGUMENTS` becomes a prompt telling the user to
    state the scope in their chat message."""
    source = (
        "---\nname: x\ndescription: d\n---\n\n"
        "# X\n\n## Body\n\nWith `$ARGUMENTS` you can target a file.\n"
    )
    out = build_steering_file(source, "x")

    assert "$ARGUMENTS" not in out
    assert "chat message" in out


def test_if_no_arguments_idiom_reads_grammatically():
    """The real vibe.md case `If no `$ARGUMENTS` provided, ask ...` must not
    produce the broken `If no the path or scope ... provided`. The
    `If no $ARGUMENTS provided` idiom is rewritten as a clean conditional."""
    source = (
        "---\nname: vibe\ndescription: d\n---\n\n"
        '# V\n\n## Step\n\nIf no `$ARGUMENTS` provided, ask: "What needs fixing?"\n'
    )
    out = build_steering_file(source, "vibe")

    assert "$ARGUMENTS" not in out
    assert "If no the path or scope" not in out
    assert "chat message" in out
    # The conditional still reads as a sentence: starts "If you don't ...".
    assert "If you don't state" in out


def test_dot_digraph_passes_through_verbatim():
    """(e) A ```dot block survives byte-for-byte, including any `$ARGUMENTS`
    node labels inside it (digraphs are copied verbatim)."""
    digraph = (
        "```dot\n"
        "digraph g {\n"
        '  "Has $ARGUMENTS?" [shape=diamond];\n'
        '  "Has $ARGUMENTS?" -> "Use that file" [label="yes"];\n'
        "}\n"
        "```"
    )
    source = (
        "---\nname: x\ndescription: d\n---\n\n"
        "# X\n\n" + digraph + "\n\n## Body\n\nProse here.\n"
    )
    out = build_steering_file(source, "x")

    assert digraph in out
    # The digraph's $ARGUMENTS labels are NOT rewritten to prose.
    assert '"Has $ARGUMENTS?"' in out


def test_cross_skill_ref_inside_dot_block_survives_verbatim():
    """A `/paad:<name>` reference INSIDE a ```dot block is copied verbatim
    (digraphs are not rewritten), while the SAME reference in normal prose is
    rewritten to `#<name>`. Guards against the whole-body `/paad:` rewrite
    leaking into digraphs."""
    digraph = (
        "```dot\n"
        "digraph g {\n"
        '  "Run /paad:agentic-review" [shape=box];\n'
        '  "Start" -> "Run /paad:agentic-review";\n'
        "}\n"
        "```"
    )
    source = (
        "---\nname: x\ndescription: d\n---\n\n"
        "# X\n\n" + digraph + "\n\n## Body\n\nWhen done, run /paad:agentic-review.\n"
    )
    out = build_steering_file(source, "x")

    # Inside the digraph: the /paad: ref is preserved verbatim.
    assert digraph in out
    assert '"Run /paad:agentic-review"' in out
    # In prose: the /paad: ref IS rewritten to the #anchor.
    assert "When done, run #agentic-review." in out


def test_dot_block_with_trailing_whitespace_fence_is_protected():
    """A ```dot open fence with trailing whitespace still stashes the block, so
    `/paad:` refs inside it survive verbatim. Guards against a fence written as
    "```dot   " silently dropping out of protection."""
    digraph = (
        "```dot   \n"  # trailing spaces on the open fence line
        "digraph g {\n"
        '  "Run /paad:agentic-review" [shape=box];\n'
        "}\n"
        "```"
    )
    source = (
        "---\nname: x\ndescription: d\n---\n\n"
        "# X\n\n" + digraph + "\n\n## Body\n\nWhen done, run /paad:agentic-review.\n"
    )
    out = build_steering_file(source, "x")

    # The whole block (trailing-space fence and all) is preserved verbatim.
    assert digraph in out
    assert '"Run /paad:agentic-review"' in out
    # Prose ref is still rewritten.
    assert "When done, run #agentic-review." in out


def test_excluded_sections_do_not_survive():
    """Layered on clean_body: orchestration-only sections are dropped."""
    source = (
        "---\nname: x\ndescription: d\n---\n\n"
        "# X\n\n"
        "## Pre-flight Checks\n\npreflight body\n\n"
        "## Input Resolution\n\nresolution body\n\n"
        "## Phase 1\n\nkept body\n"
    )
    out = build_steering_file(source, "x")

    assert "## Phase 1" in out
    assert "kept body" in out
    assert "## Pre-flight Checks" not in out
    assert "preflight body" not in out
    assert "## Input Resolution" not in out
    assert "resolution body" not in out


# ---------------------------------------------------------------------------
# generate() — the orchestration
# ---------------------------------------------------------------------------

def test_generate_produces_exactly_seven_steering_files(tmp_path):
    """(a) Exactly 7 steering/*.md are produced — not 8, not 9."""
    out_dir = tmp_path / "steering"
    generate(SOURCE_DIR, out_dir)

    produced = sorted(p.name for p in out_dir.glob("*.md"))
    assert len(produced) == 7, produced


def test_generate_skips_help_and_makefile(tmp_path):
    """(b) help.md and makefile.md are absent."""
    out_dir = tmp_path / "steering"
    generate(SOURCE_DIR, out_dir)

    produced = {p.name for p in out_dir.glob("*.md")}
    assert "help.md" not in produced
    assert "makefile.md" not in produced
    assert produced == {
        "agentic-a11y.md",
        "agentic-architecture.md",
        "agentic-review.md",
        "alignment.md",
        "fix-architecture.md",
        "pushback.md",
        "vibe.md",
    }


def test_generate_each_file_starts_with_frontmatter(tmp_path):
    """(c) applied to every real generated file: first lines are the
    `inclusion: manual` frontmatter with no leading blank."""
    out_dir = tmp_path / "steering"
    generate(SOURCE_DIR, out_dir)

    for f in out_dir.glob("*.md"):
        text = f.read_text(encoding="utf-8")
        lines = text.splitlines()
        assert lines[0] == "---", f.name
        assert lines[1] == "inclusion: manual", f.name
        assert lines[2] == "---", f.name
        assert not text.startswith("\n"), f.name
        assert not text.startswith("﻿"), f.name


# ---------------------------------------------------------------------------
# I-1: the ACCEPTED, deliberate digraph drop — guarded so it stays conscious
#
# `clean_body` copies ```dot digraphs verbatim, but ONLY within RETAINED
# sections. A digraph authored INSIDE an excluded section (e.g. `## Pre-flight
# Checks`) is dropped along with that whole section.
#
# In the real skills this splits the 7 steering files in two:
#   * alignment, pushback, vibe author their digraph in the INTRO (before the
#     first `##`), which is always retained -> their steering file KEEPS a
#     ```dot block.
#   * agentic-a11y, agentic-architecture, agentic-review, fix-architecture author
#     their digraph inside `## Pre-flight Checks` (an EXCLUDED section) -> their
#     steering file ships WITHOUT a ```dot block.
#
# This is ACCEPTED and deliberate (it matches the legacy Kiro output). It is NOT
# a bug — but it was silent. These two tests pin the current reality so any
# future change (a skill moving its digraph, or the exclusion set changing) is
# caught and must be a CONSCIOUS decision, not an accidental regression.
# ---------------------------------------------------------------------------

# Digraph authored in the retained intro -> steering file KEEPS a ```dot block.
_STEERING_WITH_DIGRAPH = ["alignment", "pushback", "vibe"]

# Digraph authored inside the excluded `## Pre-flight Checks` -> DROPPED.
_STEERING_WITHOUT_DIGRAPH = [
    "agentic-a11y",
    "agentic-architecture",
    "agentic-review",
    "fix-architecture",
]


def test_steering_files_with_intro_digraph_keep_the_dot_block(tmp_path):
    """Skills that author their digraph in the retained intro keep a ```dot block
    in their generated steering file."""
    out_dir = tmp_path / "steering"
    generate(SOURCE_DIR, out_dir)

    for name in _STEERING_WITH_DIGRAPH:
        text = (out_dir / f"{name}.md").read_text(encoding="utf-8")
        assert "```dot" in text, (
            f"{name}.md lost its digraph — it authors the digraph in the intro "
            f"(a retained section), so the ```dot block MUST survive. If this "
            f"changed, update this guard consciously."
        )


def test_steering_files_with_preflight_digraph_drop_the_dot_block(tmp_path):
    """ACCEPTED behavior: skills that author their digraph inside the EXCLUDED
    `## Pre-flight Checks` section ship WITHOUT a ```dot block — the digraph is
    dropped along with the excluded section. This matches the legacy Kiro output
    and is deliberate; the guard makes the drop conscious rather than silent."""
    out_dir = tmp_path / "steering"
    generate(SOURCE_DIR, out_dir)

    for name in _STEERING_WITHOUT_DIGRAPH:
        text = (out_dir / f"{name}.md").read_text(encoding="utf-8")
        assert "```dot" not in text, (
            f"{name}.md unexpectedly HAS a digraph. This skill authors its "
            f"digraph inside the excluded `## Pre-flight Checks` section, so the "
            f"steering file is expected to ship WITHOUT one (accepted, matches "
            f"legacy Kiro output). If the skill moved its digraph into a retained "
            f"section, that is a CONSCIOUS change — update this guard to match."
        )
