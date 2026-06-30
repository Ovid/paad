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
