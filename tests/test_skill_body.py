"""Focused unit tests for the shared body-cleaning core (`scripts/skill_body.py`).

These pin the individual transform behaviors of `clean_body()` on small,
self-contained inputs (no file I/O), documenting the core's contract:

  * which sections survive (EXCLUDED_SECTIONS),
  * `paad/...` path neutralization (including the bare `paad/` fallback),
  * the legacy `/paad:` line-stripping default,
  * the injectable `paad_ref_transform` seam for the future power generator.

The full-tree golden comparison against the committed Kiro output lives in
`test_legacy_output_unchanged.py`; this file isolates each rule so a failure
points at a specific transform.
"""

from skill_body import EXCLUDED_SECTIONS, clean_body


def test_excluded_sections_constant_lists_the_four_headers():
    """The named constant is the single source of truth for dropped sections."""
    assert EXCLUDED_SECTIONS == [
        "Arguments",
        "Input Resolution",
        "Pre-flight Checks",
        "Document classification",
    ]


def test_excluded_sections_are_dropped_kept_sections_survive():
    content = (
        "# Title\n\nIntro.\n\n"
        "## Arguments\n\nargs body\n\n"
        "## Input Resolution\n\nresolution body\n\n"
        "## Pre-flight Checks\n\npreflight body\n\n"
        "## Document classification\n\nclass body\n\n"
        "## Phase 1\n\nkept body\n"
    )
    out = clean_body(content)

    assert "## Phase 1" in out
    assert "kept body" in out
    for dropped in ("## Arguments", "args body", "## Input Resolution",
                    "resolution body", "## Pre-flight Checks", "preflight body",
                    "## Document classification", "class body"):
        assert dropped not in out


def test_known_paad_paths_are_neutralized():
    content = (
        "# T\n\n## Body\n\n"
        "Write to paad/pushback-reviews/x.md and paad/code-reviews/y.md "
        "and paad/architecture-reviews/z.md and paad/alignment-reviews/w.md.\n"
    )
    out = clean_body(content)

    assert ".reviews/pushback/x.md" in out
    assert ".reviews/code/y.md" in out
    assert ".reviews/architecture/z.md" in out
    assert ".reviews/alignment/w.md" in out
    assert "paad/" not in out


def test_bare_paad_path_falls_back_to_reviews():
    """The catch-all `paad/` -> `.reviews/` replacement (not covered by pushback)."""
    content = "# T\n\n## Body\n\nSee paad/something-else/file.md here.\n"
    out = clean_body(content)

    assert ".reviews/something-else/file.md" in out
    assert "paad/" not in out


def test_legacy_strip_removes_paad_reference_lines():
    content = (
        "# T\n\n## Body\n\n"
        "Keep this line.\n"
        "Follow up with /paad:agentic-review when done.\n"
        "Keep this too.\n"
    )
    out = clean_body(content)

    assert "Keep this line." in out
    assert "Keep this too." in out
    assert "/paad:" not in out
    assert "agentic-review" not in out


def test_paad_ref_transform_is_injectable():
    """The /paad: handling is a seam: a custom transform replaces the default."""
    content = "# T\n\n## Body\n\nSee /paad:vibe for details.\n"

    def rewrite_to_anchor(body):
        import re
        return re.sub(r'/paad:([a-z0-9-]+)', r'#\1', body)

    out = clean_body(content, paad_ref_transform=rewrite_to_anchor)

    assert "#vibe" in out
    assert "/paad:" not in out
