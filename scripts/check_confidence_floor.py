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
  python3 scripts/check_confidence_floor.py [scan-root]

Defaults to scanning plugins/paad/skills/. The optional positional arg
exists to support fixture-driven tests.
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
    if len(argv) > 2:
        print("Usage: check_confidence_floor.py [scan-root]", file=sys.stderr)
        return 1
    scan_root = Path(argv[1]) if len(argv) == 2 else DEFAULT_SCAN_ROOT

    if not scan_root.is_dir():
        print(f"FAIL: scan root not found: {scan_root}", file=sys.stderr)
        return 1

    matches: list[tuple[Path, str, int]] = []
    for md in sorted(scan_root.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        for pat in FLOOR_PATTERNS:
            for m in re.finditer(pat, text):
                try:
                    matches.append((md, pat, int(m.group(1))))
                except (ValueError, IndexError):
                    continue

    if not matches:
        print(
            "FAIL: no confidence-floor sites matched. Either FLOOR_PATTERNS "
            "are stale or all floor sites were removed.",
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
