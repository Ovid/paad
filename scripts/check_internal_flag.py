#!/usr/bin/env python3
"""Check `metadata.internal` across all three skill trees, the way the installer reads it.

Two trees must carry the flag and one must not:

  - `.claude/skills/` is not part of the paad plugin, but `npx skills add Ovid/paad`
    searches it anyway — it is one of the per-agent project directories the installer
    always looks in, alongside the plugin skills it resolves through marketplace.json.
  - `preview/paad/skills/` holds work that has merged but not shipped. A normal
    install never reaches it, but `--full-depth` sweeps the whole repo, and dedup
    against the shipped names only protects a skill that has already shipped —
    precisely backwards from what preview is for. The flag is what actually closes it.
  - `plugins/paad/skills/` is the shipped set and must NOT carry it. A skill promoted
    while still wearing its safety flag is silently invisible to every installer, so
    the botched promotion looks like a successful one.

The only thing keeping repo-only or unreleased work out of a stranger's install is
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
REQUIRE = [ROOT / ".claude/skills", ROOT / "preview/paad/skills"]
FORBID = [ROOT / "plugins/paad/skills"]
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---", re.S)


def metadata_block(lines, i):
    """Return (end, indent) for the mapping nested under the `metadata:` line at index i.

    `end` is exclusive and stops after the last indented, non-blank line. A blank
    line is legal inside a YAML mapping and does not close it — terminating on one
    is what let this check and `promote.py` disagree about where the block ended,
    so the boundary is defined here once and imported by both. When they disagree
    the result is not a refusal but a corrupted file every check then reports clean.

    `indent` is the block's own leading whitespace. A key nested deeper belongs to
    a child mapping, and the installer's `metadata?.internal` does not reach it.
    """
    end = i + 1
    indent = None
    j = i + 1
    while j < len(lines):
        line = lines[j]
        if line.strip():
            if not line[:1].isspace():
                break  # dedented back to a sibling key; the mapping ended
            if indent is None:
                indent = line[: len(line) - len(line.lstrip())]
            end = j + 1
        j += 1
    return end, (indent if indent is not None else "")


def scalar(raw):
    """Strip a trailing YAML comment. `#` opens one only at the start or after space."""
    return re.sub(r"(?:\A|(?<=\s))#.*\Z", "", raw).strip()


def internal_value(frontmatter):
    """Return the raw text of metadata.internal, or None if it is not there."""
    inline = re.search(r"^metadata:[ \t]*\{(.*)\}[ \t]*$", frontmatter, re.M)
    if inline:
        # anchored: `x-internal:` is a different key, and the installer reads it as one
        pair = re.search(r"(?:\A|,)[ \t]*internal[ \t]*:[ \t]*([^,}]*)", inline.group(1))
        return scalar(pair.group(1)) if pair else None

    lines = frontmatter.splitlines()
    for i, line in enumerate(lines):
        if not re.match(r"^metadata:[ \t]*$", line):
            continue
        end, indent = metadata_block(lines, i)
        if not indent:
            continue
        for nested in lines[i + 1:end]:
            pair = re.match(rf"^{re.escape(indent)}internal[ \t]*:[ \t]*(.*)$", nested)
            if pair:
                return scalar(pair.group(1))
    return None


def self_test():
    """The boundary cases that decide whether this check and promote.py agree."""
    # the ordinary nested and inline spellings
    assert internal_value("name: v\nmetadata:\n  internal: true") == "true"
    assert internal_value("name: v\nmetadata: {internal: true}") == "true"

    # a blank line is legal inside a YAML mapping and does not end it
    assert internal_value("name: v\nmetadata:\n\n  internal: true") == "true"

    # a trailing comment is not part of the value; YAML reads this as boolean true
    assert internal_value("metadata:\n  internal: true  # keeps it out of npx") == "true"

    # a hash with no leading space is part of the scalar, not a comment
    assert internal_value("metadata:\n  internal: a#b") == "a#b"

    # only a direct child of metadata counts — the installer reads metadata?.internal
    assert internal_value("metadata:\n  extra:\n    internal: true") is None

    # ...and only the key named exactly internal, not one that merely ends in it
    assert internal_value("metadata: {x-internal: true}") is None
    assert internal_value("metadata:\n  x-internal: true") is None

    # the off-spec quoted form must be reported, not silently accepted
    assert internal_value('metadata:\n  internal: "true"') == '"true"'

    # absent, and a sibling key that is not under metadata at all
    assert internal_value("name: v\ndescription: d") is None
    assert internal_value("internal: true\nmetadata:\n  owner: ovid") is None

    print("self-test passed.")
    return 0


def scan(tree, problems):
    """Yield (relative path, raw metadata.internal value) for each SKILL.md in tree."""
    files = sorted(tree.glob("*/SKILL.md"))
    if not files:
        problems.append(f"{tree.relative_to(ROOT)}: no SKILL.md found — this check cannot run.")
    for path in files:
        rel = path.relative_to(ROOT)
        match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
        if not match:
            problems.append(f"{rel}: no frontmatter block")
            continue
        yield rel, internal_value(match.group(1))


def main():
    if "--self-test" in sys.argv:
        return self_test()

    problems = []
    flagged = 0
    for tree in REQUIRE:
        for rel, value in scan(tree, problems):
            if value is None:
                problems.append(
                    f"{rel}: no 'internal' key under 'metadata:'. Skills in this tree are not "
                    f"part of the shipped plugin, but the npx installer can still reach them — "
                    f"without the flag this ships unreleased or repo-only tooling to strangers."
                )
            elif value != "true":
                problems.append(
                    f"{rel}: metadata.internal is {value!r}, which the installer does not accept. "
                    f"It tests `metadata?.internal === true`, so only the bare token true works — "
                    f"a quoted \"true\" is a string and the skill would be installed."
                )
            else:
                flagged += 1

    shipped = 0
    for tree in FORBID:
        for rel, value in scan(tree, problems):
            if value is not None:
                problems.append(
                    f"{rel}: carries metadata.internal ({value!r}), which the shipped tree must "
                    f"never have. Promotion strips it; this one survived, and a flagged skill is "
                    f"silently skipped by every installer — the release would ship it invisible."
                )
            else:
                shipped += 1

    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1
    print(f"{flagged} unshipped skill(s) carry metadata.internal: true; {shipped} shipped skill(s) carry none.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
