#!/usr/bin/env python3

import os
import re
import shutil
from pathlib import Path

# Paths relative to repository root
SOURCE_DIR = "plugins/paad/skills"
TARGET_DIR = "kiro_and_antigravity/skills"


def neutralize(text):
    """Strip paad-plugin specifics from a chunk of skill prose.

    Applied to SKILL.md section bodies and to every file under a skill's
    references/ directory, so a reference file never tells the agent to
    write to a path its own SKILL.md has already rewritten.
    """
    # Neutralize "paad/" output paths to ".reviews/" or ".reports/".
    text = text.replace("paad/architecture-reviews/", ".reviews/architecture/")
    text = text.replace("paad/code-reviews/", ".reviews/code/")
    text = text.replace("paad/pushback-reviews/", ".reviews/pushback/")
    text = text.replace("paad/alignment-reviews/", ".reviews/alignment/")
    # The catch-all must not eat the "paad" in a github.com/Ovid/paad URL —
    # skills link to the repo's issue tracker, which stays valid everywhere.
    text = re.sub(r"(?<!Ovid/)paad/", ".reviews/", text)

    # Drop the subagent_type FRAGMENT, not the line. Kiro and Antigravity have
    # no agents/ directory, so the type would dangle — but the dispatch
    # instruction lives on the same line, and deleting it would silently kill
    # the fan-out. None of the /paad: rules below match this (they need a "/").
    text = re.sub(r" with `subagent_type: paad:[a-z0-9-]+`", "", text)

    # Remove entire lines containing /paad: (usually follow-up suggestions
    # or command examples — there are no /paad: commands outside Claude Code)
    text = re.sub(r"^.*\/paad:[a-z0-9-]+.*$", "", text, flags=re.MULTILINE)

    # Additional cleanup for any remaining /paad: mentions just in case
    text = re.sub(r"\(?/paad:[a-z0-9-]+\)?", "", text)

    return text


def convert_skills():
    # Detect root if possible, but assume relative to cwd
    kiro_skills_root = Path(TARGET_DIR) / ".kiro" / "skills"
    agent_skills_root = Path(TARGET_DIR) / ".agent" / "skills"
    
    kiro_skills_root.mkdir(parents=True, exist_ok=True)
    agent_skills_root.mkdir(parents=True, exist_ok=True)
    
    skip_names = ["makefile", "help"]
    unwanted_headers = ["Arguments", "Input Resolution", "Pre-flight Checks", "Document classification"]

    for skill_path in Path(SOURCE_DIR).iterdir():
        if not skill_path.is_dir() or skill_path.name in skip_names:
            continue
            
        skill_file = skill_path / "SKILL.md"
        if not skill_file.exists():
            continue
            
        print(f"Converting {skill_path.name}...")
        
        with open(skill_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract frontmatter for wrapper
        name_match = re.search(r"name:\s*(.*)", content)
        desc_match = re.search(r"description:\s*(.*)", content)
        skill_name = name_match.group(1).strip() if name_match else skill_path.name
        description = desc_match.group(1).strip() if desc_match else ""

        # Split into sections by headers (##)
        # We use a non-capturing group for the split but keep the header as part of the next chunk
        # Actually splitting by \n## works better if we prepend \n to content
        parts = re.split(r'\n(##+ .*)', content)
        
        # parts[0] is everything before the first ## — the intro, the
        # announce line, and (by paad convention) every digraph. Those
        # digraphs name output paths, so parts[0] gets neutralized on the
        # same terms as the section bodies or the two disagree.
        cleaned_content = neutralize(parts[0])

        # Process header/body pairs
        for i in range(1, len(parts), 2):
            header_line = parts[i]
            body = parts[i+1]

            header_text = re.sub(r'^##+\s*', '', header_line).strip()

            # Skip unwanted sections
            if any(uh in header_text for uh in unwanted_headers):
                continue

            body = neutralize(body)

            # Clean up trailing whitespace and excessive newlines
            body = body.rstrip() + "\n"

            cleaned_content += "\n" + header_line + body

        # Final cleanup for consecutive empty lines
        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content).strip() + "\n"
        
        # Write Kiro Skill
        kiro_skill_dir = kiro_skills_root / skill_path.name
        kiro_skill_dir.mkdir(exist_ok=True)
        with open(kiro_skill_dir / "SKILL.md", "w", encoding="utf-8") as f:
            f.write(cleaned_content)

        # Copy references/, if the skill has one. A SKILL.md that dispatches
        # to references/ is only a router — without these files the exported
        # skill points at nothing. Rewritten (not copied verbatim) so their
        # output paths match the SKILL.md that loads them.
        src_refs = skill_path / "references"
        dst_refs = kiro_skill_dir / "references"
        # Drop the previous export first, so a reference deleted upstream
        # does not linger here and get loaded by a stale dispatch line.
        if dst_refs.exists():
            shutil.rmtree(dst_refs)
        if src_refs.is_dir():
            dst_refs.mkdir()
            for ref_file in sorted(src_refs.rglob("*")):
                target = dst_refs / ref_file.relative_to(src_refs)
                if ref_file.is_dir():
                    target.mkdir(exist_ok=True)
                elif ref_file.suffix == ".md":
                    text = neutralize(ref_file.read_text(encoding="utf-8"))
                    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
                    target.write_text(text, encoding="utf-8")
                else:
                    shutil.copy2(ref_file, target)
            print(f"  + {len(list(dst_refs.rglob('*.md')))} reference file(s)")


        # Write Antigravity wrapper
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
        with open(agent_skill_dir / "SKILL.md", "w", encoding="utf-8") as f:
            f.write(wrapper)

    print("Conversion complete.")

if __name__ == "__main__":
    convert_skills()
