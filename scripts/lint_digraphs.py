#!/usr/bin/env python3
"""Lint the graphviz digraphs embedded in plugins/paad/skills/*/SKILL.md.

check-digraphs only proves a ```dot fence exists. These rules catch the
defects that fence check cannot see:

  1. shape= attached to an edge statement. Graphviz silently accepts and
     ignores it, so a decision node keeps rendering as an ellipse and nobody
     notices. (style= is deliberately not checked — it is a legal edge
     attribute: style=dashed, style=bold.)
  2. nodes declared with attributes but never used in any edge — a dead
     node left behind when the flow around it was rewritten.
  3. nodes used in an edge but never declared — they render unstyled, so a
     stop condition looks like an ordinary step.
  4. digraphs that are not all up front. Every skill puts its digraphs
     immediately after the intro, before the first '## ' heading, so an
     agent always finds the control flow in the same place.

If graphviz is installed, each block is also parsed with `dot`. When it
isn't, that check is skipped rather than failing the build.
"""

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

SKILLS = pathlib.Path(__file__).resolve().parent.parent / "plugins/paad/skills"
BLOCK = re.compile(r"```dot\n(.*?)```", re.S)
DECL = re.compile(r'^\s*"([^"]+)"\s*\[', re.M)
# Matched as two halves so chained edges ("a" -> "b" -> "c") count b as both.
EDGE_SOURCE = re.compile(r'"([^"]+)"\s*(?=->)')
EDGE_TARGET = re.compile(r'->\s*"([^"]+)"')
SHAPE_ON_EDGE = re.compile(r"\[[^\]]*\bshape\s*=")


def lint(block):
    """Return a list of problem strings for one dot block."""
    problems = []

    if "digraph" not in block:
        problems.append("block contains no digraph")

    # Statements, not lines — an edge statement may wrap before its [attrs].
    for statement in block.split(";"):
        if "->" in statement and SHAPE_ON_EDGE.search(statement):
            problems.append(
                "shape= on an edge statement (graphviz ignores it): "
                + " ".join(statement.split())
            )

    declared = set(DECL.findall(block))
    used = set(EDGE_SOURCE.findall(block)) | set(EDGE_TARGET.findall(block))

    for node in sorted(declared - used):
        problems.append(f'declared but never used in an edge: "{node}"')
    for node in sorted(used - declared):
        problems.append(f'used in an edge but never declared: "{node}"')

    return problems


def misplaced(text):
    """Return the count of dot blocks that fall after the first '## ' heading."""
    heading = re.search(r"^## ", text, re.M)
    if not heading:
        return 0
    return sum(1 for m in re.finditer(r"^```dot$", text, re.M) if m.start() > heading.start())


def parses(block):
    """Return dot's stderr if it rejects the block, else None."""
    with tempfile.NamedTemporaryFile("w", suffix=".dot", delete=False) as handle:
        handle.write(block)
        path = handle.name
    try:
        result = subprocess.run(
            ["dot", "-Tcanon", path], capture_output=True, text=True
        )
        if result.returncode != 0 or result.stderr:
            return (result.stderr or "dot exited non-zero").strip()
        return None
    finally:
        pathlib.Path(path).unlink()


def self_test():
    """The three rules, each against the real defect that motivated it."""
    # 1. the makefile bug: shape= on an edge statement
    bad_edge = 'digraph g {\n "a" [shape=box];\n "a" -> "b" [shape=diamond];\n "b" [shape=box];\n}'
    assert any("on an edge statement" in p for p in lint(bad_edge)), lint(bad_edge)

    # ...including when the statement wraps before its attribute list
    wrapped = 'digraph g {\n "a" [shape=box];\n "b" [shape=box];\n "a" -> "b"\n   [shape=diamond];\n}'
    assert any("on an edge statement" in p for p in lint(wrapped)), lint(wrapped)

    # style= IS legal on an edge and must not be flagged
    dashed = 'digraph g {\n "a" [shape=box];\n "b" [shape=box];\n "a" -> "b" [style=dashed];\n}'
    assert lint(dashed) == [], lint(dashed)

    # a chained edge marks the middle node as used, not orphaned
    chain = 'digraph g {\n "a" [shape=box];\n "b" [shape=box];\n "c" [shape=box];\n "a" -> "b" -> "c";\n}'
    assert lint(chain) == [], lint(chain)

    # 2. the alignment bug: declared node with no edges
    orphan = 'digraph g {\n "a" [shape=box];\n "b" [shape=box];\n "c" [shape=box];\n "a" -> "b";\n}'
    assert any('"c"' in p and "never used" in p for p in lint(orphan)), lint(orphan)

    # 3. an edge naming a node that was never declared
    undeclared = 'digraph g {\n "a" [shape=box];\n "a" -> "b";\n}'
    assert any('"b"' in p and "never declared" in p for p in lint(undeclared)), lint(undeclared)

    # a clean block trips nothing
    good = 'digraph g {\n "a" [shape=diamond];\n "b" [shape=box];\n "a" -> "b" [label="yes"];\n}'
    assert lint(good) == [], lint(good)

    # 4. placement: digraphs belong above the first '## ' heading
    up_front = "# Skill\n\nIntro.\n\n```dot\ndigraph g {}\n```\n\n## Arguments\n\nText.\n"
    assert misplaced(up_front) == 0, misplaced(up_front)
    buried = "# Skill\n\nIntro.\n\n## Process\n\n```dot\ndigraph g {}\n```\n"
    assert misplaced(buried) == 1, misplaced(buried)

    print("self-test passed.")
    return 0


def main():
    if "--self-test" in sys.argv:
        return self_test()

    have_dot = shutil.which("dot") is not None
    failures = 0
    blocks = 0

    for skill in sorted(SKILLS.glob("*/SKILL.md")):
        text = skill.read_text()

        late = misplaced(text)
        if late:
            print(
                f"FAIL: {skill.parent.name}: {late} digraph(s) after the first '## ' "
                "heading — all digraphs go immediately after the intro"
            )
            failures += late

        for index, block in enumerate(BLOCK.findall(text)):
            blocks += 1
            problems = lint(block)
            if have_dot:
                error = parses(block)
                if error:
                    problems.append(f"graphviz rejected the block: {error}")
            for problem in problems:
                print(f"FAIL: {skill.parent.name} digraph[{index}]: {problem}")
                failures += 1

    if failures:
        print(f"{failures} digraph problem(s) found.")
        return 1

    if not blocks:
        print(f"FAIL: no digraphs found under {SKILLS} — the check is a no-op.")
        return 1

    skipped = "" if have_dot else " (graphviz not installed — parse check skipped)"
    print(f"{blocks} digraphs lint clean{skipped}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
