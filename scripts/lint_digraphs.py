#!/usr/bin/env python3
"""Lint the graphviz digraphs embedded in plugins/paad/skills/*/SKILL.md.

check-digraphs only proves a ```dot fence exists. These rules catch the
defects that fence check cannot see:

  1. node-only attributes (shape=, style=) attached to an edge statement.
     Graphviz silently accepts and ignores them, so a decision node keeps
     rendering as an ellipse and nobody notices.
  2. nodes declared with attributes but never used in any edge — a dead
     node left behind when the flow around it was rewritten.
  3. nodes used in an edge but never declared — they render unstyled, so a
     stop condition looks like an ordinary step.

If graphviz is installed, each block is also parsed with `dot`. When it
isn't, that check is skipped rather than failing the build.
"""

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

SKILLS = pathlib.Path("plugins/paad/skills")
BLOCK = re.compile(r"```dot\n(.*?)```", re.S)
DECL = re.compile(r'^\s*"([^"]+)"\s*\[', re.M)
EDGE = re.compile(r'"([^"]+)"\s*->\s*"([^"]+)"')
NODE_ATTR_ON_EDGE = re.compile(r"\[[^\]]*\b(?:shape|style)\s*=")


def lint(block):
    """Return a list of problem strings for one dot block."""
    problems = []

    if "digraph" not in block:
        problems.append("block contains no digraph")

    for line in block.splitlines():
        if "->" in line and NODE_ATTR_ON_EDGE.search(line):
            problems.append(
                f"node attribute (shape/style) on an edge statement: {line.strip()}"
            )

    declared = set(DECL.findall(block))
    edges = EDGE.findall(block)
    used = {a for a, _ in edges} | {b for _, b in edges}

    for node in sorted(declared - used):
        problems.append(f'declared but never used in an edge: "{node}"')
    for node in sorted(used - declared):
        problems.append(f'used in an edge but never declared: "{node}"')

    return problems


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

    # 2. the alignment bug: declared node with no edges
    orphan = 'digraph g {\n "a" [shape=box];\n "b" [shape=box];\n "c" [shape=box];\n "a" -> "b";\n}'
    assert any('"c"' in p and "never used" in p for p in lint(orphan)), lint(orphan)

    # 3. an edge naming a node that was never declared
    undeclared = 'digraph g {\n "a" [shape=box];\n "a" -> "b";\n}'
    assert any('"b"' in p and "never declared" in p for p in lint(undeclared)), lint(undeclared)

    # a clean block trips nothing
    good = 'digraph g {\n "a" [shape=diamond];\n "b" [shape=box];\n "a" -> "b" [label="yes"];\n}'
    assert lint(good) == [], lint(good)

    print("self-test passed.")
    return 0


def main():
    if "--self-test" in sys.argv:
        return self_test()

    have_dot = shutil.which("dot") is not None
    failures = 0
    blocks = 0

    for skill in sorted(SKILLS.glob("*/SKILL.md")):
        for index, block in enumerate(BLOCK.findall(skill.read_text())):
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

    skipped = "" if have_dot else " (graphviz not installed — parse check skipped)"
    print(f"{blocks} digraphs lint clean{skipped}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
