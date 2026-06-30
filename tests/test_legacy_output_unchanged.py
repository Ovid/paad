"""Golden-output regression guard for the shared body-cleaning core.

The load-bearing invariant for Task 1 is that the extracted `clean_body()`
reproduces `convert_skills.py`'s legacy per-skill body output EXACTLY. We prove
that against the committed Kiro tree, which is the authoritative golden output:
each `kiro_and_antigravity/skills/.kiro/skills/<name>/SKILL.md` is exactly what
the generator produces for that source skill today.

For every in-scope source skill (all `plugins/paad/skills/*/SKILL.md` except
the `skip_names` `help` and `makefile`), this asserts:

    clean_body(<source SKILL.md>) == <committed .kiro SKILL.md>

This is read-only (no subprocess, no tree mutation, no artifacts), and it
covers every path replacement and section exclusion across ALL skills — not
just one representative. Unlike a `git show HEAD` comparison, it can genuinely
fail if `clean_body()` ever diverges from the committed golden output.
"""

import pytest

from conftest import REPO_ROOT
from skill_body import clean_body

SOURCE_DIR = REPO_ROOT / "plugins" / "paad" / "skills"
KIRO_DIR = REPO_ROOT / "kiro_and_antigravity" / "skills" / ".kiro" / "skills"

# Mirrors convert_skills.py's skip_names: these skills are not emitted to the
# Kiro tree and so have no golden output to compare against.
SKIP_NAMES = {"help", "makefile"}


def _in_scope_skill_names():
    names = sorted(
        p.name
        for p in SOURCE_DIR.iterdir()
        if p.is_dir()
        and p.name not in SKIP_NAMES
        and (p / "SKILL.md").exists()
    )
    assert names, "no in-scope source skills found — test setup is wrong"
    return names


def test_in_scope_skills_have_committed_golden_output():
    """Sanity: every in-scope source skill has a committed .kiro counterpart.

    Guards against the golden comparison silently covering nothing if the tree
    layout changes.
    """
    for name in _in_scope_skill_names():
        assert (KIRO_DIR / name / "SKILL.md").exists(), (
            f"missing committed golden output for in-scope skill {name!r}"
        )


@pytest.mark.parametrize("name", _in_scope_skill_names())
def test_clean_body_matches_committed_golden_output(name):
    """clean_body(source) must byte-equal the committed .kiro golden output."""
    source = (SOURCE_DIR / name / "SKILL.md").read_text(encoding="utf-8")
    golden = (KIRO_DIR / name / "SKILL.md").read_text(encoding="utf-8")

    assert clean_body(source) == golden, (
        f"clean_body() output for {name!r} no longer matches the committed "
        f"Kiro golden output; the shared core has diverged from the legacy "
        f"generator behavior."
    )
