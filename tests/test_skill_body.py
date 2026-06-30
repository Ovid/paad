"""Unit tests for the shared body-cleaning core (`scripts/skill_body.py`).

These tests pin the CURRENT behavior of `convert_skills.py`'s inline
body-cleaning logic so that the extracted, shared `clean_body()` function can
never silently diverge from it. The committed Kiro tree is the authoritative
snapshot of that behavior: each `.kiro/skills/<name>/SKILL.md` is exactly what
the inline logic produces for that skill today.
"""

from pathlib import Path

from conftest import REPO_ROOT

SOURCE_DIR = REPO_ROOT / "plugins" / "paad" / "skills"
KIRO_DIR = REPO_ROOT / "kiro_and_antigravity" / "skills" / ".kiro" / "skills"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_clean_body_reproduces_pushback_committed_output():
    """`clean_body()` must reproduce the committed pushback body exactly.

    pushback is the representative skill: it exercises section exclusion
    (`Input Resolution`), path neutralization (`paad/pushback-reviews/` ->
    `.reviews/pushback/`), and whitespace collapsing.
    """
    from skill_body import clean_body

    source = _read(SOURCE_DIR / "pushback" / "SKILL.md")
    expected = _read(KIRO_DIR / "pushback" / "SKILL.md")

    assert clean_body(source) == expected


def test_excluded_sections_constant_lists_the_four_headers():
    """The named constant is the single source of truth for dropped sections."""
    from skill_body import EXCLUDED_SECTIONS

    assert EXCLUDED_SECTIONS == [
        "Arguments",
        "Input Resolution",
        "Pre-flight Checks",
        "Document classification",
    ]
