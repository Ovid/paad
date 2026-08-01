#!/usr/bin/env python3
"""Roll CHANGELOG.md's [Unreleased] section into a dated release section.

Usage: python3 scripts/roll_changelog.py X.Y.Z

Renames `## [Unreleased]` to `## [X.Y.Z] — <today>`, opens a fresh empty
`## [Unreleased]` above it, and updates the link refs at the bottom. Refuses
to run when there is nothing to release or when the version already has a
section, so `make release` fails before it rewrites any manifest.

The date comes from the system clock rather than an argument on purpose: the
release checklist used to say "use today's real date (check it; don't guess)",
which is advice a script can simply obey.
"""

import re
import sys
from datetime import date
from pathlib import Path

CHANGELOG = Path("CHANGELOG.md")
COMPARE = "https://github.com/Ovid/paad/compare/paad--v{}...HEAD"
TAG_URL = "https://github.com/Ovid/paad/releases/tag/paad--v{}"

# Matches a version heading: "## [1.22.0] — 2026-07-26" or "## [Unreleased]"
HEADING = re.compile(r"^## \[([^\]]+)\]", re.MULTILINE)


def fail(message):
    sys.exit(f"FAIL: {message}")


def main():
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} X.Y.Z")
    version = sys.argv[1]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail(f"VERSION must be in X.Y.Z form (got {version})")

    text = CHANGELOG.read_text(encoding="utf-8")

    headings = list(HEADING.finditer(text))
    if not headings:
        fail(f"{CHANGELOG}: no '## [version]' headings found")
    if headings[0].group(1) != "Unreleased":
        fail(f"{CHANGELOG}: first section is [{headings[0].group(1)}], expected [Unreleased]")
    if any(h.group(1) == version for h in headings):
        fail(f"{CHANGELOG} already has a [{version}] section — is this version already rolled?")

    # Body runs from the end of the [Unreleased] heading to the next heading.
    body_start = headings[0].end()
    body_end = headings[1].start() if len(headings) > 1 else len(text)
    if not text[body_start:body_end].strip():
        fail(
            "[Unreleased] is empty — there is nothing to release. Land the change "
            "under [Unreleased] first, or stop and ask whether a release is wanted."
        )

    today = date.today().isoformat()
    text = (
        text[: headings[0].start()]
        + f"## [Unreleased]\n\n## [{version}] — {today}"
        + text[headings[0].end() :]
    )

    # Link refs at the bottom. [Unreleased] compares against the new tag; the
    # new version gets its own line directly beneath it, newest-first like the
    # sections above.
    unreleased_ref = re.compile(r"^\[Unreleased\]:.*$", re.MULTILINE)
    if not unreleased_ref.search(text):
        fail(f"{CHANGELOG}: no '[Unreleased]:' link ref to update")
    text = unreleased_ref.sub(
        f"[Unreleased]: {COMPARE.format(version)}\n[{version}]: {TAG_URL.format(version)}",
        text,
        count=1,
    )

    CHANGELOG.write_text(text, encoding="utf-8")
    print(f"Rolled [Unreleased] into [{version}] — {today}")


if __name__ == "__main__":
    main()
