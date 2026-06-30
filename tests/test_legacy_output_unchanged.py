"""Regression guard: the refactor must not change `convert_skills.py`'s output.

The load-bearing invariant for Task 1 is that extracting `clean_body()` into
`scripts/skill_body.py` leaves the legacy Kiro/Antigravity generator producing
*byte-for-byte identical* output. This test proves that directly by running two
generators against the same source tree and comparing their full output:

  * the ORIGINAL generator, extracted verbatim from `git show HEAD:...`
  * the CURRENT (refactored) generator on disk

If they ever diverge, `clean_body()` no longer reproduces the original
behavior and this test fails.

Why compare original-vs-current rather than `git diff` against the committed
tree: the committed tree has a PRE-EXISTING drift (the `alignment` source was
edited without regenerating the tree), so a raw `git diff --exit-code` after
regeneration is non-empty regardless of this refactor. Comparing the two
generators isolates the refactor's effect from that unrelated drift, and the
original generator is the authoritative snapshot of "current behavior".
"""

import filecmp
import os
import shutil
import subprocess
import sys
from pathlib import Path

from conftest import REPO_ROOT

SCRIPTS_REL = "scripts/convert_skills.py"
SKILL_BODY_REL = "scripts/skill_body.py"
SOURCE_REL = "plugins/paad/skills"
TARGET_REL = "kiro_and_antigravity/skills"


def _run_generator(script_path, workdir):
    """Run a convert_skills.py copy in `workdir`, return CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(script_path)],
        cwd=workdir,
        capture_output=True,
        text=True,
    )


def _stage_workdir(tmp_path, name, convert_script_text):
    """Build an isolated repo-shaped workdir with source + a given generator.

    The current `scripts/skill_body.py` is always copied in because both the
    original and refactored generators must import the same shared module under
    test (the original generator pre-refactor had no import, so copying it is
    harmless for the original and required for the refactored one).
    """
    workdir = tmp_path / name
    scripts_dir = workdir / "scripts"
    scripts_dir.mkdir(parents=True)

    # Copy the full skills source tree (the generator reads from here).
    shutil.copytree(REPO_ROOT / SOURCE_REL, workdir / SOURCE_REL)

    # Provide the shared core so refactored imports resolve.
    shutil.copy2(REPO_ROOT / SKILL_BODY_REL, scripts_dir / "skill_body.py")

    # Write the generator under test.
    (scripts_dir / "convert_skills.py").write_text(
        convert_script_text, encoding="utf-8"
    )

    return workdir


def _dir_trees_equal(a, b):
    """Recursively assert two directory trees are byte-for-byte identical."""
    cmp = filecmp.dircmp(a, b)
    assert not cmp.left_only, f"only in {a}: {cmp.left_only}"
    assert not cmp.right_only, f"only in {b}: {cmp.right_only}"
    # filecmp's shallow=True can miss content changes with equal size/mtime;
    # force a full content comparison.
    _, mismatch, errors = filecmp.cmpfiles(
        a, b, cmp.common_files, shallow=False
    )
    assert not mismatch, f"content differs in {a} vs {b}: {mismatch}"
    assert not errors, f"comparison errors in {a} vs {b}: {errors}"
    for sub in cmp.common_dirs:
        _dir_trees_equal(Path(a) / sub, Path(b) / sub)


def test_refactored_generator_output_matches_original(tmp_path):
    """Refactored convert_skills.py must produce identical output to HEAD's."""
    original_text = subprocess.run(
        ["git", "show", f"HEAD:{SCRIPTS_REL}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    current_text = (REPO_ROOT / SCRIPTS_REL).read_text(encoding="utf-8")

    orig_wd = _stage_workdir(tmp_path, "original", original_text)
    cur_wd = _stage_workdir(tmp_path, "current", current_text)

    orig_run = _run_generator(orig_wd / "scripts" / "convert_skills.py", orig_wd)
    cur_run = _run_generator(cur_wd / "scripts" / "convert_skills.py", cur_wd)

    assert orig_run.returncode == 0, orig_run.stderr
    assert cur_run.returncode == 0, cur_run.stderr

    _dir_trees_equal(orig_wd / TARGET_REL, cur_wd / TARGET_REL)
