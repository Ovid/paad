#!/usr/bin/env python3
"""Verify the confidence-floor literal is consistent across all sites.

The floor (currently 60) gates whether specialist findings are reported
at all. It appears in specialist dispatch prompts, verifier instructions,
per-specialist drop-rule definitions, and cap-confidence clauses. A
silent desync between any of those sites would invalidate findings
without warning. This check enforces all matches resolve to the same
integer.

Patterns are deliberately narrow phrasings — they must capture the floor
itself, not band lower bounds (e.g., '60-79 -> Medium') or score-range
descriptors (e.g., 'confidence (0-100)') that are conceptually distinct.

Usage:
  python3 scripts/check_confidence_floor.py [--strict] [scan-root]

Defaults to scanning plugins/paad/skills/. The optional positional arg
exists to support fixture-driven tests.

`--strict` additionally requires every pattern in FLOOR_PATTERNS to
match at least once across the scan tree. A zero-match pattern is the
drift this checker is meant to detect — but synthetic fixtures
deliberately exercise a subset of patterns, so the strict assertion
is opt-in. The real-codebase invocation in the Makefile passes it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Each pattern's capture group must equal the operational floor. Add new
# phrasings here as the prompts evolve.
FLOOR_PATTERNS: list[str] = [
    r"confidence >= (\d+)\b",
    r"below (\d+)% confidence",
    r"confidence is below (\d+)\b",
    r"[Cc]ap confidence at (\d+)\b",
    r"[Dd]rop findings below (\d+)\b",
]

DEFAULT_SCAN_ROOT = Path("plugins/paad/skills")


def main(argv: list[str]) -> int:
    args = list(argv[1:])
    strict = False
    if "--strict" in args:
        strict = True
        args.remove("--strict")
    if len(args) > 1:
        print("Usage: check_confidence_floor.py [--strict] [scan-root]", file=sys.stderr)
        return 1
    scan_root = Path(args[0]) if args else DEFAULT_SCAN_ROOT

    if not scan_root.is_dir():
        print(f"FAIL: scan root not found: {scan_root}", file=sys.stderr)
        return 1

    matches: list[tuple[Path, str, int]] = []
    for md in sorted(scan_root.rglob("*.md")):
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            # An unreadable or non-UTF-8 file under the scan root is a real
            # operator problem (permissions, corruption, accidentally
            # tracked binary), not a clean "no floor here" — fail loudly.
            print(f"FAIL: cannot read {md}: {exc}", file=sys.stderr)
            return 1
        for pat in FLOOR_PATTERNS:
            for m in re.finditer(pat, text):
                # The capture group `(\d+)` guarantees a digit-only match,
                # so int() conversion cannot fail. If FLOOR_PATTERNS is
                # ever changed to allow non-digit captures, that change
                # owns adding the type guard.
                matches.append((md, pat, int(m.group(1))))

    if not matches:
        print(
            "FAIL: no confidence-floor sites matched. Either FLOOR_PATTERNS "
            "are stale or all floor sites were removed.",
            file=sys.stderr,
        )
        return 1

    # Per-pattern minimum-match guard (opt-in via --strict): every
    # pattern in FLOOR_PATTERNS must have matched at least once across
    # the scan tree. A pattern that no longer matches anything is
    # itself the drift this checker is meant to detect — silently
    # passing it would let stale patterns accumulate until the checker
    # becomes vacuous. Off by default because synthetic fixtures
    # legitimately exercise a subset of patterns.
    if strict:
        unmatched_patterns = [
            pat for pat in FLOOR_PATTERNS
            if not any(p == pat for _, p, _ in matches)
        ]
        if unmatched_patterns:
            print(
                "FAIL: one or more FLOOR_PATTERNS matched zero sites — "
                "pattern rot or sites removed:",
                file=sys.stderr,
            )
            for pat in unmatched_patterns:
                print(f"  {pat!r}", file=sys.stderr)
            print(
                "If a pattern is intentionally retired, remove it from "
                "FLOOR_PATTERNS; if a site was renamed, update the pattern.",
                file=sys.stderr,
            )
            return 1

    distinct = sorted({v for _, _, v in matches})
    if len(distinct) > 1:
        print(
            f"FAIL: confidence floor inconsistent across sites: found values {distinct}",
            file=sys.stderr,
        )
        for path, pat, val in matches:
            print(f"  {path}: {val} (matched '{pat}')", file=sys.stderr)
        return 1

    print(f"Confidence floor consistent across {len(matches)} sites: {distinct[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
