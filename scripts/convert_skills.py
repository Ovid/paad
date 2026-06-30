#!/usr/bin/env python3

import re
import sys
from pathlib import Path

# Make the shared body-cleaning core importable regardless of cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_body import clean_body  # noqa: E402

# Paths relative to repository root
SOURCE_DIR = "plugins/paad/skills"
TARGET_DIR = "kiro_and_antigravity/skills"

def convert_skills():
    # Detect root if possible, but assume relative to cwd
    kiro_skills_root = Path(TARGET_DIR) / ".kiro" / "skills"
    agent_skills_root = Path(TARGET_DIR) / ".agent" / "skills"
    
    kiro_skills_root.mkdir(parents=True, exist_ok=True)
    agent_skills_root.mkdir(parents=True, exist_ok=True)
    
    skip_names = ["makefile", "help"]

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

        # Clean the body using the shared core (section split + exclusion +
        # path neutralization + legacy /paad: stripping + whitespace collapse).
        cleaned_content = clean_body(content)

        # Write Kiro Skill
        kiro_skill_dir = kiro_skills_root / skill_path.name
        kiro_skill_dir.mkdir(exist_ok=True)
        with open(kiro_skill_dir / "SKILL.md", "w", encoding="utf-8") as f:
            f.write(cleaned_content)
            
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
