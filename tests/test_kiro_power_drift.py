"""Tests for Task 4: idempotency + drift detection for the Kiro power.

The generator embeds a git provenance stamp (`<!-- Generated from paad@<sha> by
build-kiro-power -->`) as POWER.md's final line. Because the stamp captures
HEAD-at-generation-time, the committed POWER.md's stamp ALWAYS lags HEAD by one
commit, so a naive `git diff --exit-code -- POWER.md` is always dirty. The drift
check must therefore compare a STAMP-FREE view of POWER.md.

This module proves three things:

  * `without_stamp(text)` strips/normalizes the provenance stamp line, leaving
    all other content untouched. Two POWER.md bodies that differ ONLY in their
    stamp SHA compare equal once normalized.
  * `find_drift(generated, ondisk)` is a PURE comparison: identical -> no drift;
    stamp-only difference -> no drift; real content difference -> drift.
  * The generator is idempotent: regenerating produces the same stamp-free
    output (a regression guard — Tasks 2-3 already made the builders
    deterministic).
  * The end-to-end `check_drift(...)` reports drift when a generated file is
    hand-edited (the design's done-condition) and reports none on a clean tree.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

build_kiro_power = __import__("build-kiro-power")

SOURCE_DIR = REPO_ROOT / "plugins" / "paad" / "skills"

IN_SCOPE = [
    "agentic-a11y",
    "agentic-architecture",
    "agentic-review",
    "alignment",
    "fix-architecture",
    "pushback",
    "vibe",
]


# ---------------------------------------------------------------------------
# without_stamp: strips/normalizes the provenance stamp line
# ---------------------------------------------------------------------------

def test_without_stamp_removes_stamp_line():
    """The provenance stamp line is removed from the compared view."""
    text = "body line\n\n<!-- Generated from paad@abc1234 by build-kiro-power -->\n"
    assert "Generated from paad@" not in build_kiro_power.without_stamp(text)


def test_without_stamp_leaves_non_stamp_content_untouched():
    """Content that is not the stamp line survives normalization verbatim."""
    text = "# Title\n\nsome prose\n\n- a list item\n"
    assert build_kiro_power.without_stamp(text) == text


def test_without_stamp_equal_across_different_shas():
    """Two POWER.md bodies identical except for the stamp SHA compare EQUAL.

    This is the whole point: the committed stamp lags HEAD by one commit, so the
    drift check must treat a stamp-only delta as no drift.
    """
    a = "shared body\n\n<!-- Generated from paad@aaaaaaa by build-kiro-power -->\n"
    b = "shared body\n\n<!-- Generated from paad@bbbbbbb by build-kiro-power -->\n"
    assert build_kiro_power.without_stamp(a) == build_kiro_power.without_stamp(b)


def test_without_stamp_differs_when_real_content_differs():
    """A real body difference still differs after normalization."""
    a = "body ONE\n\n<!-- Generated from paad@aaaaaaa by build-kiro-power -->\n"
    b = "body TWO\n\n<!-- Generated from paad@aaaaaaa by build-kiro-power -->\n"
    assert build_kiro_power.without_stamp(a) != build_kiro_power.without_stamp(b)


def test_without_stamp_is_idempotent():
    """Normalizing already-normalized text changes nothing (no stamp to strip)."""
    text = "plain body with no stamp\n"
    once = build_kiro_power.without_stamp(text)
    assert build_kiro_power.without_stamp(once) == once


def test_without_stamp_only_strips_trailing_stamp_not_midbody():
    """The stamp is contractually the FINAL line: a mid-body line that merely
    starts with the stamp literal must NOT be stripped — only the real trailing
    stamp is removed."""
    text = (
        "<!-- Generated from paad@aaaaaaa by build-kiro-power -->\n"
        "real body content survives\n"
        "<!-- Generated from paad@bbbbbbb by build-kiro-power -->\n"
    )
    result = build_kiro_power.without_stamp(text)
    # The mid-body stamp-like line is preserved; only the trailing one is gone.
    assert result == (
        "<!-- Generated from paad@aaaaaaa by build-kiro-power -->\n"
        "real body content survives\n"
    )


# ---------------------------------------------------------------------------
# find_drift: pure comparison of {name: content} maps
# ---------------------------------------------------------------------------

def test_find_drift_identical_returns_empty():
    """Identical generated/on-disk maps -> no drift."""
    gen = {"POWER.md": "x\n", "steering/vibe.md": "y\n"}
    assert build_kiro_power.find_drift(gen, dict(gen)) == []


def test_find_drift_stamp_only_difference_returns_empty():
    """POWER.md differing ONLY in its stamp SHA is NOT drift."""
    gen = {
        "POWER.md": "body\n<!-- Generated from paad@aaaaaaa by build-kiro-power -->\n",
        "steering/vibe.md": "y\n",
    }
    ondisk = {
        "POWER.md": "body\n<!-- Generated from paad@bbbbbbb by build-kiro-power -->\n",
        "steering/vibe.md": "y\n",
    }
    assert build_kiro_power.find_drift(gen, ondisk) == []


def test_find_drift_content_difference_returns_filename():
    """A real content difference reports the drifted file name."""
    gen = {"POWER.md": "x\n", "steering/vibe.md": "GOOD\n"}
    ondisk = {"POWER.md": "x\n", "steering/vibe.md": "TAMPERED\n"}
    assert build_kiro_power.find_drift(gen, ondisk) == ["steering/vibe.md"]


def test_find_drift_power_md_real_difference_reported():
    """A real POWER.md difference (beyond the stamp) is reported as drift."""
    gen = {
        "POWER.md": "REAL body\n<!-- Generated from paad@aaaaaaa by build-kiro-power -->\n",
    }
    ondisk = {
        "POWER.md": "HAND-EDITED body\n<!-- Generated from paad@aaaaaaa by build-kiro-power -->\n",
    }
    assert build_kiro_power.find_drift(gen, ondisk) == ["POWER.md"]


def test_find_drift_missing_ondisk_file_is_drift():
    """A generated file absent from the on-disk map is drift (never silently
    passes — a deleted or never-written steering file must be caught)."""
    gen = {"POWER.md": "x\n", "steering/vibe.md": "y\n"}
    ondisk = {"POWER.md": "x\n"}
    assert build_kiro_power.find_drift(gen, ondisk) == ["steering/vibe.md"]


def test_find_drift_orphan_ondisk_steering_file_is_drift():
    """An on-disk steering file with NO generator counterpart is drift (the
    generators only write, never delete — orphans must be caught)."""
    gen = {"POWER.md": "x\n", "steering/vibe.md": "y\n"}
    ondisk = {
        "POWER.md": "x\n",
        "steering/vibe.md": "y\n",
        "steering/oldskill.md": "stale\n",
    }
    assert build_kiro_power.find_drift(gen, ondisk) == ["steering/oldskill.md"]


def test_find_drift_extra_nonsteering_ondisk_file_ignored():
    """An on-disk extra that is NOT under steering/ is not flagged — only
    orphaned steering files matter (POWER.md is always regenerated)."""
    gen = {"POWER.md": "x\n", "steering/vibe.md": "y\n"}
    ondisk = {
        "POWER.md": "x\n",
        "steering/vibe.md": "y\n",
        "README.md": "unrelated\n",
    }
    assert build_kiro_power.find_drift(gen, ondisk) == []


def test_find_drift_results_sorted():
    """Multiple drifted files are reported in deterministic sorted order."""
    gen = {"steering/b.md": "1\n", "steering/a.md": "1\n", "POWER.md": "1\n"}
    ondisk = {"steering/b.md": "X\n", "steering/a.md": "X\n", "POWER.md": "1\n"}
    assert build_kiro_power.find_drift(gen, ondisk) == [
        "steering/a.md",
        "steering/b.md",
    ]


# ---------------------------------------------------------------------------
# Idempotency: regenerating produces the same stamp-free output
# ---------------------------------------------------------------------------

def test_generator_is_idempotent_stamp_free(tmp_path, monkeypatch):
    """Running the generator twice yields stamp-free-identical POWER.md and
    byte-identical steering files. (Tasks 2-3 already made the builders
    deterministic; this is the regression guard.)"""
    # Generate once into out1, once into out2, with DIFFERENT fake SHAs to prove
    # the only allowed delta is the stamp.
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    out1.mkdir()
    out2.mkdir()

    monkeypatch.setattr(build_kiro_power, "git_short_sha", lambda: "1111111")
    build_kiro_power.generate(source_dir=SOURCE_DIR, out_dir=out1 / "steering")
    build_kiro_power.generate_power(source_dir=SOURCE_DIR, out_path=out1 / "POWER.md")

    monkeypatch.setattr(build_kiro_power, "git_short_sha", lambda: "2222222")
    build_kiro_power.generate(source_dir=SOURCE_DIR, out_dir=out2 / "steering")
    build_kiro_power.generate_power(source_dir=SOURCE_DIR, out_path=out2 / "POWER.md")

    power1 = (out1 / "POWER.md").read_text(encoding="utf-8")
    power2 = (out2 / "POWER.md").read_text(encoding="utf-8")
    assert build_kiro_power.without_stamp(power1) == build_kiro_power.without_stamp(
        power2
    )

    for name in IN_SCOPE:
        s1 = (out1 / "steering" / f"{name}.md").read_text(encoding="utf-8")
        s2 = (out2 / "steering" / f"{name}.md").read_text(encoding="utf-8")
        assert s1 == s2, f"steering/{name}.md not deterministic"


# ---------------------------------------------------------------------------
# check_drift end-to-end: clean tree passes, hand-edit fails (done-condition)
# ---------------------------------------------------------------------------

def _materialize_clean_tree(root, monkeypatch):
    """Generate a full power tree (POWER.md + steering/) under `root`."""
    monkeypatch.setattr(build_kiro_power, "git_short_sha", lambda: "abc1234")
    build_kiro_power.generate(source_dir=SOURCE_DIR, out_dir=root / "steering")
    build_kiro_power.generate_power(source_dir=SOURCE_DIR, out_path=root / "POWER.md")


def test_check_drift_clean_tree_reports_no_drift(tmp_path, monkeypatch):
    """A freshly generated tree has no drift, even with a different stamp SHA on
    re-generation (the stamp delta is excluded)."""
    _materialize_clean_tree(tmp_path, monkeypatch)
    # Re-check with a DIFFERENT SHA so POWER.md's stamp would differ.
    monkeypatch.setattr(build_kiro_power, "git_short_sha", lambda: "deadbee")
    assert build_kiro_power.check_drift(source_dir=SOURCE_DIR, root=tmp_path) == []


def test_check_drift_detects_hand_edited_steering_file(tmp_path, monkeypatch):
    """THE DONE-CONDITION: a deliberate hand-edit to a generated steering file
    makes the drift check FAIL (reports that file)."""
    _materialize_clean_tree(tmp_path, monkeypatch)
    tampered = tmp_path / "steering" / "vibe.md"
    tampered.write_text(
        tampered.read_text(encoding="utf-8") + "\nHAND-EDITED LINE\n",
        encoding="utf-8",
    )
    drift = build_kiro_power.check_drift(source_dir=SOURCE_DIR, root=tmp_path)
    assert "steering/vibe.md" in drift


def test_check_drift_detects_hand_edited_power_md(tmp_path, monkeypatch):
    """A hand-edit to POWER.md (beyond the stamp) is caught as drift."""
    _materialize_clean_tree(tmp_path, monkeypatch)
    power = tmp_path / "POWER.md"
    text = power.read_text(encoding="utf-8")
    # Tamper a real content line, NOT the stamp.
    power.write_text(text.replace("# PAAD — Kiro Power", "# TAMPERED TITLE"),
                     encoding="utf-8")
    drift = build_kiro_power.check_drift(source_dir=SOURCE_DIR, root=tmp_path)
    assert "POWER.md" in drift


def test_check_drift_detects_orphan_steering_file(tmp_path, monkeypatch):
    """A stale on-disk steering file the generator never produces is drift.

    The generators only WRITE, never DELETE, so removing/renaming a skill in
    `plugins/paad/skills/` leaves an orphan `steering/<old>.md` behind. That
    orphan means the committed power contains a file the generator would never
    produce — exactly the single-source-of-truth violation the drift check must
    catch.
    """
    _materialize_clean_tree(tmp_path, monkeypatch)
    orphan = tmp_path / "steering" / "oldskill.md"
    orphan.write_text(
        "---\ninclusion: manual\n---\n\n# Old Skill\n\nstale content\n",
        encoding="utf-8",
    )
    drift = build_kiro_power.check_drift(source_dir=SOURCE_DIR, root=tmp_path)
    assert "steering/oldskill.md" in drift
