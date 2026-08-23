#!/usr/bin/env python3
"""Strip the preview markers from the shipped tree after `make promote` rsyncs it.

`make promote` copies `preview/paad/` wholesale over `plugins/paad/`, so the
shipped tree arrives wearing all three preview markers. Two of them are versions
and `make bump-version` rewrites those on its own — it reads each tree's current
version out of its own `plugin.json`, so `1.30.2-preview` is just the string it
substitutes from. The third is `metadata: internal: true`, which no version pass
would ever touch, and which must not survive: the installer tests
`metadata?.internal === true` and silently skips a flagged skill, so a shipped
skill still carrying it is invisible to every install.

Removing the key can empty the `metadata:` mapping it sat under. A bare
`metadata:` with nothing nested is a null value, not an empty map, so the whole
line goes with it when nothing else is left.

Both YAML spellings are handled — the nested block that the migration writes, and
the inline `metadata: {internal: true}` that `check_internal_flag.py` also accepts.
Handling only the one we write would let a hand-authored inline flag ride into a
release, where `check_internal_flag.py` would catch it — but not until the rsync,
the changelog roll and both trees' version strings were already written.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHIPPED = ROOT / "plugins/paad/skills"
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---", re.S)


def strip_internal(text):
    """Return text with metadata.internal removed, dropping an emptied metadata key."""
    match = FRONTMATTER.match(text)
    if not match:
        return text

    lines = match.group(1).splitlines()
    kept = []
    i = 0
    while i < len(lines):
        line = lines[i]

        inline = re.match(r"^metadata:[ \t]*\{(.*)\}[ \t]*$", line)
        if inline:
            pairs = [p.strip() for p in inline.group(1).split(",") if p.strip()]
            pairs = [p for p in pairs if not re.match(r"^internal[ \t]*:", p)]
            if pairs:
                kept.append("metadata: {" + ", ".join(pairs) + "}")
            i += 1
            continue

        if re.match(r"^metadata:[ \t]*$", line):
            block = []
            j = i + 1
            while j < len(lines) and lines[j].strip() and lines[j][:1].isspace():
                block.append(lines[j])
                j += 1
            block = [b for b in block if not re.match(r"^\s+internal[ \t]*:", b)]
            if block:
                kept.append(line)
                kept.extend(block)
            i = j
            continue

        kept.append(line)
        i += 1

    return text[:match.start(1)] + "\n".join(kept) + text[match.end(1):]


def self_test():
    """Each spelling, plus the cases that must be left alone."""
    def fm(body):
        return f"---\n{body}\n---\n\nBody text.\n"

    # the nested block the migration writes: key and its emptied parent both go
    assert strip_internal(fm("name: vibe\nmetadata:\n  internal: true")) == fm("name: vibe")

    # a metadata mapping with other keys keeps the mapping, loses only internal
    assert strip_internal(
        fm("name: vibe\nmetadata:\n  internal: true\n  owner: ovid")
    ) == fm("name: vibe\nmetadata:\n  owner: ovid")

    # a key after the mapping is a sibling, not part of it, and must survive
    assert strip_internal(
        fm("name: vibe\nmetadata:\n  internal: true\ndescription: d")
    ) == fm("name: vibe\ndescription: d")

    # inline spelling, emptied and not
    assert strip_internal(fm("name: vibe\nmetadata: {internal: true}")) == fm("name: vibe")
    assert strip_internal(
        fm("name: vibe\nmetadata: {internal: true, owner: ovid}")
    ) == fm("name: vibe\nmetadata: {owner: ovid}")

    # a file that never had the flag is returned untouched
    clean = fm("name: vibe\ndescription: d")
    assert strip_internal(clean) == clean

    # a body mentioning internal: true is not frontmatter and must not be edited
    prose = fm("name: vibe") + "\nSet `internal: true` to hide a skill.\n"
    assert strip_internal(prose) == prose

    print("self-test passed.")
    return 0


def main():
    if "--self-test" in sys.argv:
        return self_test()

    files = sorted(SHIPPED.glob("*/SKILL.md"))
    if not files:
        print(f"FAIL: no SKILL.md found under {SHIPPED} — the rsync did not land.")
        return 1

    stripped = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        promoted = strip_internal(text)
        if promoted != text:
            path.write_text(promoted, encoding="utf-8")
            stripped += 1

    print(f"Promoted {len(files)} skill(s); stripped the internal flag from {stripped}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
