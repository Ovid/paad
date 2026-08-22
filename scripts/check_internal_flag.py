#!/usr/bin/env python3
"""Check that project-local skills are flagged internal, the way the installer reads it.

`.claude/skills/` is not part of the paad plugin, but `npx skills add Ovid/paad`
searches it anyway — it is one of the per-agent project directories the installer
always looks in, alongside the plugin skills it resolves through marketplace.json.
The only thing keeping repo-only tooling out of a stranger's install is
`metadata.internal`, and the installer tests it as `metadata?.internal === true`.

That strict comparison is why this parses rather than greps:

  - the flag counts only under `metadata:`, so a grep for the bare line passes
    files where it sits under some other key and the installer ignores it;
  - indentation is free in YAML, and `metadata: {internal: true}` is the same
    mapping written inline, so a fixed-indent grep rejects valid files;
  - `internal: "true"` is a string. It is what the Agent Skills spec asks for —
    metadata is specified as "a map from string keys to string values" — and it
    is exactly what the installer's `=== true` rejects, so the skill would ship.
    The off-spec boolean is the one that works. Say so when it is wrong.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude/skills"
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---", re.S)


def internal_value(frontmatter):
    """Return the raw text of metadata.internal, or None if it is not there."""
    inline = re.search(r"^metadata:[ \t]*\{(.*)\}[ \t]*$", frontmatter, re.M)
    if inline:
        pair = re.search(r"\binternal[ \t]*:[ \t]*([^,}]+)", inline.group(1))
        return pair.group(1).strip() if pair else None

    lines = frontmatter.splitlines()
    for i, line in enumerate(lines):
        if not re.match(r"^metadata:[ \t]*$", line):
            continue
        for nested in lines[i + 1:]:
            if nested.strip() and not nested[:1].isspace():
                break  # dedented back to a sibling key; the mapping ended
            pair = re.match(r"^\s+internal[ \t]*:[ \t]*(.*?)[ \t]*$", nested)
            if pair:
                return pair.group(1)
    return None


def main():
    problems = []
    files = sorted(SKILLS.glob("*/SKILL.md"))
    for path in files:
        rel = path.relative_to(ROOT)
        match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
        if not match:
            problems.append(f"{rel}: no frontmatter block")
            continue
        value = internal_value(match.group(1))
        if value is None:
            problems.append(
                f"{rel}: no 'internal' key under 'metadata:'. Project-local skills are not "
                f"part of the plugin, but the npx installer searches .claude/skills/ — "
                f"without the flag this ships repo-only tooling to people who have no repo."
            )
        elif value != "true":
            problems.append(
                f"{rel}: metadata.internal is {value!r}, which the installer does not accept. "
                f"It tests `metadata?.internal === true`, so only the bare token true works — "
                f"a quoted \"true\" is a string and the skill would be installed."
            )

    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1
    print(f"{len(files)} project-local skill(s) carry metadata.internal: true.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
