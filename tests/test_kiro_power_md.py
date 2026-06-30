"""Tests for the Kiro power POWER.md aggregator (`scripts/build-kiro-power.py`).

Task 3 of the Kiro power work: emit a single `POWER.md` at the repo root that
aggregates the 7 in-scope skills into one Kiro power manifest. Shape:

    ---
    name: paad                 # from plugin.json "name"
    displayName: ...           # generator constant
    description: ...           # generator constant
    keywords: [...]            # = sidecar `power:` list, VERBATIM
    author: Ovid               # generator constant
    version: 1.11.0            # from plugin.json "version"
    ---

    <onboarding sourced from help/SKILL.md>
    <"When to load steering files" routing list, one per in-scope skill>

The PURE builder `build_power_md(...)` is deterministic (no git, no file I/O).
The orchestrator reads the git short SHA and appends a provenance stamp AFTER
the deterministic content so Task 4's drift check can exclude it.
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

# The 7 in-scope skills (all except help + makefile).
IN_SCOPE = [
    "agentic-a11y",
    "agentic-architecture",
    "agentic-review",
    "alignment",
    "fix-architecture",
    "pushback",
    "vibe",
]

# The known help-overview tagline. Proves onboarding is sourced from help/SKILL.md.
HELP_TAGLINE = (
    "paad — impractical tools for software architecture, code quality, "
    "and development workflows."
)


def _real_sidecar():
    return build_kiro_power.load_sidecar(SCRIPTS_DIR / "kiro-keywords.yaml")


def _real_plugin_meta():
    return build_kiro_power.read_plugin_meta(
        REPO_ROOT / "plugins" / "paad" / ".claude-plugin" / "plugin.json"
    )


def _real_help_content():
    return (SOURCE_DIR / "help" / "SKILL.md").read_text(encoding="utf-8")


def _build_real():
    return build_kiro_power.build_power_md(
        source_dir=SOURCE_DIR,
        sidecar=_real_sidecar(),
        plugin_meta=_real_plugin_meta(),
        help_content=_real_help_content(),
    )


# ---------------------------------------------------------------------------
# (a) frontmatter: name/displayName/description/keywords/author/version
# ---------------------------------------------------------------------------

def test_frontmatter_is_literal_first_content():
    """The literal first content is `---` on line 1 — no leading blank, no BOM."""
    out = _build_real()
    assert out.startswith("---\n"), repr(out[:40])
    assert not out.startswith("\n")
    assert not out.startswith("﻿")
    lines = out.splitlines()
    assert lines[0] == "---"


def test_frontmatter_has_all_required_keys():
    """(a) frontmatter has name/displayName/description/keywords/author/version."""
    out = _build_real()
    # Frontmatter is the block between the first two `---` lines.
    fm = out.split("---\n", 2)[1]
    for key in ("name:", "displayName:", "description:", "keywords:",
                "author:", "version:"):
        assert key in fm, f"{key} missing from frontmatter:\n{fm}"


def test_name_and_version_sourced_from_plugin_json():
    """(a) name + version mirror plugin.json (can't drift)."""
    meta = _real_plugin_meta()
    assert meta["name"] == "paad"
    assert meta["version"] == "1.11.0"

    out = _build_real()
    fm = out.split("---\n", 2)[1]
    assert "name: paad" in fm
    assert f"version: {meta['version']}" in fm


def test_displayName_description_author_are_design_constants():
    """(a) displayName/description/author are the design's fixed constants."""
    out = _build_real()
    fm = out.split("---\n", 2)[1]
    assert ("displayName: PAAD — Architecture, Review & Quality Skills"
            in fm)
    assert ("description: Multi-agent architecture analysis, code review, "
            "accessibility, and quality workflows.") in fm
    assert "author: Ovid" in fm


# ---------------------------------------------------------------------------
# (b) onboarding is SOURCED from help/SKILL.md (not hand-written)
# ---------------------------------------------------------------------------

def test_onboarding_sourced_from_help_tagline_present():
    """(b) A known phrase from help/SKILL.md appears verbatim, proving the
    onboarding is sourced from help, not hand-written."""
    out = _build_real()
    assert HELP_TAGLINE in out


def test_onboarding_tracks_help_content_change():
    """(b) Onboarding is derived from the passed help_content, not a literal
    baked into the builder — a changed help tagline flows into POWER.md."""
    sentinel = "ZZZ-UNIQUE-HELP-TAGLINE-SENTINEL-ZZZ"
    fake_help = (
        "---\nname: help\ndescription: d\n---\n\n"
        "# paad Help\n\n## Overview (no arguments)\n\n"
        "```\n" + sentinel + "\n\nAvailable skills:\n```\n"
    )
    out = build_kiro_power.build_power_md(
        source_dir=SOURCE_DIR,
        sidecar=_real_sidecar(),
        plugin_meta=_real_plugin_meta(),
        help_content=fake_help,
    )
    assert sentinel in out


def test_onboarding_falls_back_when_help_markers_absent():
    """If help_content lacks the expected `## Overview` / fence markers, the
    builder degrades gracefully (no crash) and still emits a valid POWER.md."""
    fake_help = "no overview marker, no fence, just plain text\n"
    out = build_kiro_power.build_power_md(
        source_dir=SOURCE_DIR,
        sidecar=_real_sidecar(),
        plugin_meta=_real_plugin_meta(),
        help_content=fake_help,
    )
    assert out.startswith("---\n")
    assert "no overview marker" in out
    # Routing list is still appended.
    assert "## When to load steering files" in out


# ---------------------------------------------------------------------------
# (c) keywords == curated sidecar `power:` list, NOT a union of skill keywords
# ---------------------------------------------------------------------------

def test_keywords_equal_sidecar_power_list_verbatim():
    """(c) keywords == sidecar `power:` list verbatim."""
    sidecar = _real_sidecar()
    out = _build_real()
    fm = out.split("---\n", 2)[1]
    expected = "keywords: [" + ", ".join(sidecar["power"]) + "]"
    assert expected in fm, f"expected {expected!r} in:\n{fm}"


def test_keywords_are_not_union_of_per_skill_keywords():
    """(c) keywords are the NARROW curated list, not the union of every skill's
    per-skill keywords."""
    sidecar = _real_sidecar()
    out = _build_real()
    fm = out.split("---\n", 2)[1]
    # `a11y` only appears in the per-skill list, never in the curated `power:`
    # list — its presence would prove a union leaked in.
    union = {kw for kws in sidecar["skills"].values() for kw in kws}
    assert "a11y" in union  # sanity: it IS in the union
    assert "a11y" not in sidecar["power"]  # sanity: not in curated list
    keywords_line = [ln for ln in fm.splitlines() if ln.startswith("keywords:")][0]
    assert "a11y" not in keywords_line


# ---------------------------------------------------------------------------
# (d) missing sidecar entry emits a warning
# ---------------------------------------------------------------------------

def test_missing_sidecar_entries_returns_missing_names():
    """(d) The testable detector returns in-scope skills absent from the
    sidecar's `skills:` map."""
    sidecar = {"power": ["x"], "skills": {"agentic-a11y": ["a11y"]}}
    missing = build_kiro_power.missing_sidecar_entries(
        ["agentic-a11y", "vibe", "pushback"], sidecar
    )
    assert missing == ["pushback", "vibe"]


def test_missing_sidecar_entries_empty_when_all_present():
    """(d) Real sidecar covers every in-scope skill — no missing entries."""
    missing = build_kiro_power.missing_sidecar_entries(IN_SCOPE, _real_sidecar())
    assert missing == []


def test_warn_missing_sidecar_entries_prints_to_stderr(capsys):
    """(d) The warning fires (to stderr) when an in-scope skill is missing."""
    sidecar = {"power": ["x"], "skills": {"agentic-a11y": ["a11y"]}}
    build_kiro_power.warn_missing_sidecar_entries(["agentic-a11y", "vibe"], sidecar)
    captured = capsys.readouterr()
    assert "vibe" in captured.err
    assert captured.out == ""  # warning goes to stderr, not stdout


def test_warn_missing_sidecar_entries_silent_when_complete(capsys):
    """(d) No warning when every in-scope skill has a sidecar entry."""
    build_kiro_power.warn_missing_sidecar_entries(IN_SCOPE, _real_sidecar())
    captured = capsys.readouterr()
    assert captured.err == ""


# ---------------------------------------------------------------------------
# "When to load steering files" routing list (generated from frontmatter)
# ---------------------------------------------------------------------------

def test_routing_list_has_all_seven_in_scope_skills():
    """One `#<name>` routing entry per in-scope skill (the 7)."""
    out = _build_real()
    for name in IN_SCOPE:
        assert f"#{name}" in out, f"routing entry for {name} missing"


def test_routing_entries_use_skill_frontmatter_descriptions():
    """Routing descriptions are derived from each skill's frontmatter
    description (drift-proof), not hand-written."""
    out = _build_real()
    # A distinctive fragment from agentic-architecture's real description.
    assert "Multi-agent architecture analysis" in out
    # A distinctive fragment from vibe's real description.
    assert "Safe vibe coding with TDD guardrails" in out


def test_help_and_makefile_not_in_routing_list():
    """help + makefile are excluded from the routing list."""
    out = _build_real()
    assert "#help" not in out
    assert "#makefile" not in out


# ---------------------------------------------------------------------------
# Determinism + purity of the builder
# ---------------------------------------------------------------------------

def test_build_power_md_is_deterministic():
    """The pure builder produces byte-identical output across calls."""
    assert _build_real() == _build_real()


def test_build_power_md_has_no_provenance_stamp():
    """The PURE builder emits NO git provenance stamp — that is appended by the
    orchestrator AFTER the comparable content."""
    out = _build_real()
    assert "Generated from paad@" not in out


def test_routing_entries_sorted_deterministically():
    """Routing entries appear in sorted order (deterministic)."""
    out = _build_real()
    positions = [out.index(f"**#{name}**") for name in sorted(IN_SCOPE)]
    assert positions == sorted(positions), "routing entries not in sorted order"


# ---------------------------------------------------------------------------
# Helpers: provenance stamp + version read
# ---------------------------------------------------------------------------

def test_provenance_stamp_shape():
    """The provenance stamp is a single HTML comment line naming the short SHA."""
    stamp = build_kiro_power.provenance_stamp("abc1234")
    assert stamp == "<!-- Generated from paad@abc1234 by build-kiro-power -->"


def test_read_plugin_meta_reads_name_and_version():
    """read_plugin_meta surfaces name + version from plugin.json."""
    meta = build_kiro_power.read_plugin_meta(
        REPO_ROOT / "plugins" / "paad" / ".claude-plugin" / "plugin.json"
    )
    assert meta["name"] == "paad"
    assert meta["version"] == "1.11.0"


# ---------------------------------------------------------------------------
# Orchestrator: writes POWER.md with the stamp appended after content
# ---------------------------------------------------------------------------

def test_generate_power_writes_file_with_stamp_appended(tmp_path, monkeypatch):
    """The orchestrator writes POWER.md = pure content + provenance stamp, with
    the stamp on its own separable FINAL line (after the comparable content)."""
    monkeypatch.setattr(build_kiro_power, "git_short_sha", lambda: "deadbee")
    out_path = tmp_path / "POWER.md"
    build_kiro_power.generate_power(source_dir=SOURCE_DIR, out_path=out_path)

    text = out_path.read_text(encoding="utf-8")
    pure = _build_real()
    stamp = build_kiro_power.provenance_stamp("deadbee")
    # Pure content is a prefix; the stamp is the clearly-separable final line.
    assert text.startswith(pure)
    assert text.rstrip().endswith(stamp)
    assert text.rstrip().splitlines()[-1] == stamp
