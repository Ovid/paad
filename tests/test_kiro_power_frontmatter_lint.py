"""Tests for Task 5: frontmatter-first lint for the Kiro power.

Kiro has ONE hard rule about steering files and POWER.md: the YAML frontmatter
must be the LITERAL first content of the file — `---` on line 1, no leading
blank line, no leading whitespace, no UTF-8 BOM before it — with a closing `---`
delimiter and parseable YAML between. Kiro silently ignores a steering file whose
frontmatter is not the first thing in the file, so a single stray blank line
disables a skill with no error.

This module proves three things:

  * `frontmatter_first_violation(text)` is a PURE check: it returns `None` for a
    file whose frontmatter is the literal first content, and a human-readable
    reason string for every way that can be violated (leading blank line, BOM,
    missing/un-terminated block, non-`---` first line, unparseable YAML).
  * The REAL committed `steering/*.md` + `POWER.md` all pass the lint (they were
    generated correctly).
  * The end-to-end `lint_frontmatter_first(root)` FAILS on a file with a leading
    blank line (the design's done-condition) without touching the real tree, and
    PASSES on a clean generated tree.

REFACTOR seam: the lint reuses the SAME leading-frontmatter matcher the generator
uses to PARSE source frontmatter (`read_skill_frontmatter`), so "what we write
and parse as valid frontmatter" and "what we lint" share one definition.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

build_kiro_power = __import__("build-kiro-power")

SOURCE_DIR = REPO_ROOT / "plugins" / "paad" / "skills"

# Sourced from the generator so it can never silently drift from the actual
# in-scope skill set (a skill added/removed in plugins/paad/skills is reflected
# automatically).
IN_SCOPE = build_kiro_power._in_scope_skill_names(SOURCE_DIR)

VALID = "---\ninclusion: manual\n---\n\n# Title\n\nbody\n"


# ---------------------------------------------------------------------------
# frontmatter_first_violation: pure check over a single file's text
# ---------------------------------------------------------------------------

def test_valid_frontmatter_first_returns_none():
    """`---` on line 1 with a closing `---` and parseable YAML -> no violation."""
    assert build_kiro_power.frontmatter_first_violation(VALID) is None


def test_leading_blank_line_is_violation():
    """A blank line before `---` disables the steering file in Kiro -> violation."""
    text = "\n" + VALID
    reason = build_kiro_power.frontmatter_first_violation(text)
    assert reason is not None
    assert reason  # non-empty, human-readable reason


def test_leading_whitespace_is_violation():
    """Leading whitespace before `---` (so line 1 is not exactly `---`) -> violation."""
    text = "   " + VALID
    assert build_kiro_power.frontmatter_first_violation(text) is not None


def test_bom_prefix_is_violation():
    """A UTF-8 BOM before `---` means `---` is not the literal first content."""
    text = "﻿" + VALID
    assert build_kiro_power.frontmatter_first_violation(text) is not None


def test_missing_closing_delimiter_is_violation():
    """An un-terminated frontmatter block (no closing `---`) -> violation."""
    text = "---\ninclusion: manual\n\n# Title\n\nbody\n"
    assert build_kiro_power.frontmatter_first_violation(text) is not None


def test_first_line_not_dashes_is_violation():
    """A first line that is not `---` (e.g. an h1) -> violation."""
    text = "# Title\n\nbody\n"
    assert build_kiro_power.frontmatter_first_violation(text) is not None


def test_unparseable_yaml_is_violation():
    """A leading `---...---` block whose body is not parseable YAML -> violation."""
    text = "---\n: : not valid : yaml :\n---\n\n# Title\n"
    assert build_kiro_power.frontmatter_first_violation(text) is not None


def test_scalar_yaml_frontmatter_is_violation():
    """A leading block whose YAML parses to a SCALAR (not a mapping) -> violation.

    `---\\njust a scalar\\n---` is parseable YAML but not usable frontmatter; real
    steering/POWER frontmatter is always a YAML mapping (`name:`, `inclusion:`)."""
    text = "---\njust a scalar\n---\n\n# Title\n"
    assert build_kiro_power.frontmatter_first_violation(text) is not None


def test_list_yaml_frontmatter_is_violation():
    """A leading block whose YAML parses to a LIST (not a mapping) -> violation."""
    text = "---\n- a\n- b\n---\n\n# Title\n"
    assert build_kiro_power.frontmatter_first_violation(text) is not None


# ---------------------------------------------------------------------------
# Integration: the REAL committed power files all pass the lint
# ---------------------------------------------------------------------------

def test_committed_power_md_passes_lint():
    """The committed POWER.md has frontmatter as its literal first content."""
    text = (REPO_ROOT / "POWER.md").read_text(encoding="utf-8")
    assert build_kiro_power.frontmatter_first_violation(text) is None


def test_committed_steering_files_pass_lint():
    """Every committed steering/*.md has frontmatter as its literal first content."""
    for name in IN_SCOPE:
        text = (REPO_ROOT / "steering" / f"{name}.md").read_text(encoding="utf-8")
        assert build_kiro_power.frontmatter_first_violation(text) is None, name


def test_real_committed_tree_lint_passes():
    """End-to-end: the lint over the REAL committed tree reports no violations."""
    assert build_kiro_power.lint_frontmatter_first(root=REPO_ROOT) == []


# ---------------------------------------------------------------------------
# lint_frontmatter_first end-to-end: clean tree passes, bad file fails
# ---------------------------------------------------------------------------

def _materialize_clean_tree(root, monkeypatch):
    """Generate a full power tree (POWER.md + steering/) under `root`."""
    monkeypatch.setattr(build_kiro_power, "git_short_sha", lambda: "abc1234")
    build_kiro_power.generate(source_dir=SOURCE_DIR, out_dir=root / "steering")
    build_kiro_power.generate_power(source_dir=SOURCE_DIR, out_path=root / "POWER.md")


def test_lint_clean_tree_reports_no_violations(tmp_path, monkeypatch):
    """A freshly generated tree passes the frontmatter-first lint."""
    _materialize_clean_tree(tmp_path, monkeypatch)
    assert build_kiro_power.lint_frontmatter_first(root=tmp_path) == []


def test_lint_detects_leading_blank_line_in_steering(tmp_path, monkeypatch):
    """THE DONE-CONDITION: a steering file with a leading blank line before its
    frontmatter is flagged by the lint (naming that file)."""
    _materialize_clean_tree(tmp_path, monkeypatch)
    bad = tmp_path / "steering" / "vibe.md"
    bad.write_text("\n" + bad.read_text(encoding="utf-8"), encoding="utf-8")
    violations = build_kiro_power.lint_frontmatter_first(root=tmp_path)
    assert any("steering/vibe.md" in v for v in violations), violations


def test_lint_detects_leading_blank_line_in_power_md(tmp_path, monkeypatch):
    """A POWER.md with a leading blank line before its frontmatter is flagged."""
    _materialize_clean_tree(tmp_path, monkeypatch)
    bad = tmp_path / "POWER.md"
    bad.write_text("\n" + bad.read_text(encoding="utf-8"), encoding="utf-8")
    violations = build_kiro_power.lint_frontmatter_first(root=tmp_path)
    assert any("POWER.md" in v for v in violations), violations


def test_lint_results_sorted(tmp_path, monkeypatch):
    """Multiple violations are reported in deterministic sorted order."""
    _materialize_clean_tree(tmp_path, monkeypatch)
    for name in ("vibe.md", "alignment.md"):
        bad = tmp_path / "steering" / name
        bad.write_text("\n" + bad.read_text(encoding="utf-8"), encoding="utf-8")
    violations = build_kiro_power.lint_frontmatter_first(root=tmp_path)
    files = [v.split(":", 1)[0] for v in violations]
    assert files == sorted(files)
