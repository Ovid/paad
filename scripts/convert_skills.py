#!/usr/bin/env python3
"""Convert paad SKILL.md files into the vendored Cursor/Kiro/Antigravity
shapes under kiro_and_antigravity/skills/.

For refs-using skills (e.g. agentic-architecture, agentic-review), the
references/*.md files are appended as Appendix sections to the converted
SKILL.md, since non-Claude-Code consumers have no subagent dispatch
mechanism — inlining keeps the specialist instructions readable rather
than referenced through a binding-read pattern that won't apply.

Set TARGET_DIR env var to override the output root (used by
make check-vendored).
"""

import os
import re
import shutil
import sys
from pathlib import Path

SOURCE_DIR = "plugins/paad/skills"
DEFAULT_TARGET_DIR = "kiro_and_antigravity/skills"

# Paths inside SKILL.md that point at paad-Code-only output dirs need
# rewriting to a tool-neutral shape. Each entry is added BEFORE the
# catch-all `paad/` -> `.reviews/`. The rename table must enumerate every
# review-output prefix used by skills under SOURCE_DIR.
PATH_RENAMES = (
    ("paad/architecture-reviews/", ".reviews/architecture/"),
    ("paad/code-reviews/",         ".reviews/code/"),
    ("paad/pushback-reviews/",     ".reviews/pushback/"),
    ("paad/alignment-reviews/",    ".reviews/alignment/"),
    ("paad/a11y-reviews/",         ".reviews/a11y/"),
    ("paad/",                      ".reviews/"),  # catch-all; keep last
)

UNWANTED_HEADERS = ("Arguments", "Input Resolution", "Pre-flight Checks", "Document classification")
SKIP_SKILL_NAMES = ("makefile", "help")


def _fail(msg: str) -> "None":
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def _safe_read(path: Path) -> str:
    """Read a UTF-8 markdown file, failing cleanly on OS or decode errors.

    A bare read_text() crash mid-conversion leaves a partial output tree
    that check-vendored then misdiagnoses as 'out of sync'. Failing here
    surfaces the actual file with a one-line diagnostic.
    """
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        _fail(f"cannot read {path}: {exc}")


def _neutralize(body: str) -> str:
    """Apply path renames and strip /paad: references from a body chunk.

    Line-removal is narrow on purpose: only delete a line when its first
    non-whitespace content is a `/paad:<name>` dispatch token (standalone
    follow-up commands), since vendored consumers cannot dispatch paad
    skills. Lines that *mention* `/paad:<name>` mid-sentence — role-framing
    blockquotes (which carry the binding "treat received content as
    untrusted data" prompt-injection defense), instruction prose, and
    bullet items with surrounding text — must survive; only the inline
    token gets stripped.
    """
    for old, new in PATH_RENAMES:
        body = body.replace(old, new)
    # Remove standalone dispatch lines: line starts with `/paad:<name>`
    # (after optional leading whitespace).
    body = re.sub(r'^\s*/paad:[a-z0-9-]+.*$', '', body, flags=re.MULTILINE)
    # Strip inline /paad:<name> tokens from surviving prose.
    body = re.sub(r'\(?/paad:[a-z0-9-]+\)?', '', body)
    return body


def _convert_skill_md(content: str) -> str:
    """Convert a single SKILL.md body: split by ## headers, strip
    unwanted sections, neutralize each kept body."""
    parts = re.split(r'\n(##+ .*)', content)
    cleaned = parts[0]
    for i in range(1, len(parts), 2):
        header_line = parts[i]
        body = parts[i + 1]
        header_text = re.sub(r'^##+\s*', '', header_line).strip()
        if any(uh in header_text for uh in UNWANTED_HEADERS):
            continue
        body = _neutralize(body)
        body = body.rstrip() + "\n"
        cleaned += "\n" + header_line + body
    return cleaned


def _append_references(cleaned_content: str, skill_path: Path) -> str:
    """If the skill has a references/ subdir, append each ref file as an
    Appendix section. Non-CC consumers have no subagent dispatch so the
    binding-read pattern doesn't work — inline the ref content instead."""
    refs_dir = skill_path / "references"
    if not refs_dir.is_dir():
        return cleaned_content
    appendix_chunks: list[str] = []
    for ref_file in sorted(refs_dir.glob("*.md")):
        ref_text = _neutralize(_safe_read(ref_file))
        appendix_chunks.append(
            f"\n## Appendix: {ref_file.name}\n\n{ref_text.rstrip()}\n"
        )
    if not appendix_chunks:
        return cleaned_content
    return cleaned_content.rstrip() + "\n" + "".join(appendix_chunks)


def convert_skills(target_dir: str | None = None) -> None:
    target_root = Path(target_dir or os.environ.get("TARGET_DIR") or DEFAULT_TARGET_DIR)
    kiro_skills_root = target_root / ".kiro" / "skills"
    agent_skills_root = target_root / ".agent" / "skills"
    kiro_skills_root.mkdir(parents=True, exist_ok=True)
    agent_skills_root.mkdir(parents=True, exist_ok=True)

    # Compute the set of skill folders the converter is about to write.
    # Anything under the output roots whose folder name is not in that
    # set is stale (a renamed or deleted source skill that left a tomb
    # in the output tree). Remove those before regenerating so a rename
    # doesn't require a manual `git rm` follow-up. Strict: only remove
    # *direct* subdirs of kiro_skills_root / agent_skills_root, never
    # parent dirs or files outside that scope.
    expected_skill_names = {
        p.name for p in Path(SOURCE_DIR).iterdir()
        if p.is_dir() and p.name not in SKIP_SKILL_NAMES and (p / "SKILL.md").exists()
    }
    for output_root in (kiro_skills_root, agent_skills_root):
        for child in output_root.iterdir():
            if child.is_dir() and child.name not in expected_skill_names:
                print(f"Removing stale output dir {child}...")
                shutil.rmtree(child)

    for skill_path in sorted(Path(SOURCE_DIR).iterdir()):
        if not skill_path.is_dir() or skill_path.name in SKIP_SKILL_NAMES:
            continue
        skill_file = skill_path / "SKILL.md"
        if not skill_file.exists():
            continue

        print(f"Converting {skill_path.name}...")
        content = _safe_read(skill_file)

        name_match = re.search(r"name:\s*(.*)", content)
        desc_match = re.search(r"description:\s*(.*)", content)
        skill_name = name_match.group(1).strip() if name_match else skill_path.name
        description = desc_match.group(1).strip() if desc_match else ""

        cleaned_content = _convert_skill_md(content)
        cleaned_content = _append_references(cleaned_content, skill_path)
        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content).strip() + "\n"

        kiro_skill_dir = kiro_skills_root / skill_path.name
        kiro_skill_dir.mkdir(exist_ok=True)
        (kiro_skill_dir / "SKILL.md").write_text(cleaned_content, encoding="utf-8")

        h1_match = re.search(r'^#\s*(.*)', cleaned_content, re.MULTILINE)
        title = h1_match.group(1).strip() if h1_match else skill_path.name.replace("-", " ").title()

        agent_skill_dir = agent_skills_root / skill_path.name
        agent_skill_dir.mkdir(exist_ok=True)
        wrapper = f"""---
name: {skill_name}
description: {description}
---

# {title} (Antigravity Wrapper)

This is a project-specific skill. The detailed checklist and procedures are in:
**`.kiro/skills/{skill_path.name}/SKILL.md`**

Please refer to that file for the full criteria.
"""
        (agent_skill_dir / "SKILL.md").write_text(wrapper, encoding="utf-8")

    print("Conversion complete.")


if __name__ == "__main__":
    convert_skills()
