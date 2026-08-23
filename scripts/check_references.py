#!/usr/bin/env python3
"""Check that skill reference dispatches and reference files line up.

A SKILL.md that dispatches to references/ is only a router — the substance
lives in the files it names. Two ways that breaks, both silent:

  1. Dangling dispatch — a file names references/foo.md and no such file
     exists (renamed, deleted, typo). The skill runs until it tries to load
     a file that isn't there.
  2. Orphaned reference — a references/*.md nobody names. Either dead
     weight, or a dispatch line was dropped and the content is now unread.

Mentions are collected across the whole skill directory, not just SKILL.md:
a mode file legitimately dispatches to its own references (test-roadmap's
build/execute modes load break-it-check.md, not the router).
"""

import pathlib
import re
import sys

DEFAULT_SKILLS = pathlib.Path(__file__).resolve().parent.parent / "plugins/paad/skills"
MENTION = re.compile(r"references/([A-Za-z0-9._-]+\.md)")


def check(skill_dir):
    """Return a list of problem strings for one skill."""
    refs_dir = skill_dir / "references"
    on_disk = {p.name for p in refs_dir.glob("*.md")} if refs_dir.is_dir() else set()

    mentioned = {}
    for source in sorted(skill_dir.rglob("*.md")):
        for name in MENTION.findall(source.read_text(encoding="utf-8")):
            mentioned.setdefault(name, source.relative_to(skill_dir))

    problems = []
    for name, source in sorted(mentioned.items()):
        if name not in on_disk:
            problems.append(f"{source} dispatches to references/{name}, which does not exist")
    for name in sorted(on_disk - set(mentioned)):
        problems.append(f"references/{name} exists but nothing in the skill names it")
    return problems


def main():
    skills = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SKILLS
    if not skills.is_dir():
        print(f"FAIL: no skills directory at {skills} — this check cannot run.")
        return 1
    failed = False
    counted = 0
    for skill_dir in sorted(skills.iterdir()):
        if not skill_dir.is_dir():
            continue
        problems = check(skill_dir)
        counted += len(list((skill_dir / "references").glob("*.md"))) if (skill_dir / "references").is_dir() else 0
        for problem in problems:
            print(f"FAIL: {skill_dir.name}: {problem}")
            failed = True
    if failed:
        return 1
    print(f"{counted} skill reference file(s) resolve cleanly in {skills}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
