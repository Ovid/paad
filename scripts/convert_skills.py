#!/usr/bin/env python3

import os
import re
import shutil
from pathlib import Path

# Paths relative to repository root
SOURCE_DIR = "plugins/paad/skills"
TARGET_DIR = "kiro_and_antigravity/skills"
SOURCE_AGENT = "plugins/paad/agents/paad-analyst.md"
PI_AGENT_DIR = "pi/agents"

# Claude Code tool names -> Pi's. Pi has no Glob; `find` plus `ls` cover what
# the analyst used it for. Every name here is read-only, which is the whole
# point of the file — an unmapped name is a hard error rather than a silent
# drop, because dropping one quietly hands the Pi analyst a different toolset
# than the Claude Code one it is supposed to mirror.
# WebSearch/WebFetch map to nothing on purpose: Pi's built-ins are read, bash,
# edit, write, grep, find, and ls — there is no web tool to map onto. An empty
# list is the one case where dropping a tool is deliberate rather than silent,
# so it is spelled out here instead of being left unmapped. The consequence is
# real and documented in README's Pi section: paad:rethink on Pi cannot reach a
# primary source, so it verifies against the repo alone and must say so.
PI_TOOLS = {
    "Read": ["read"],
    "Grep": ["grep"],
    "Glob": ["find", "ls"],
    "Bash": ["bash"],
    "WebSearch": [],
    "WebFetch": [],
}


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


def convert_pi_agent():
    """Emit the Pi copy of the read-only analyst agent.

    Pi has no `agents` key in its package manifest, so this file cannot ship
    as part of the package — the user drops it into ~/.pi/agent/agents/ by
    hand. Generating it anyway keeps it from drifting out of sync with
    plugins/paad/agents/paad-analyst.md, which is the file that actually
    defines the role; `make check-export-current` fails if it does.

    The body is copied verbatim, NOT neutralized: Pi loads the skills straight
    out of plugins/paad/skills, so the paad/ output paths and /paad: names the
    Kiro export rewrites are still correct here. Only the tool list changes.
    """
    source = Path(SOURCE_AGENT)
    text = source.read_text(encoding="utf-8")

    match = re.search(r"^tools:\s*(.+)$", text, flags=re.MULTILINE)
    if not match:
        raise SystemExit(f"{SOURCE_AGENT}: no `tools:` line — cannot build the Pi agent")

    claude_tools = [t.strip() for t in match.group(1).split(",") if t.strip()]
    unknown = [t for t in claude_tools if t not in PI_TOOLS]
    if unknown:
        raise SystemExit(
            f"{SOURCE_AGENT}: no Pi equivalent for {', '.join(unknown)} — "
            f"add it to PI_TOOLS in {__file__} (read-only tools only)"
        )

    pi_tools = []
    for tool in claude_tools:
        for mapped in PI_TOOLS[tool]:
            if mapped not in pi_tools:
                pi_tools.append(mapped)

    text = text[: match.start()] + "tools: " + ", ".join(pi_tools) + text[match.end() :]

    target_dir = Path(PI_AGENT_DIR)
    shutil.rmtree(target_dir, ignore_errors=True)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.name
    target.write_text(text, encoding="utf-8")
    print(f"Wrote {target} (tools: {', '.join(pi_tools)})")


def convert_skills():
    # Detect root if possible, but assume relative to cwd
    kiro_skills_root = Path(TARGET_DIR) / ".kiro" / "skills"
    agent_skills_root = Path(TARGET_DIR) / ".agent" / "skills"

    # Wipe first: a renamed, deleted, or newly skipped skill would otherwise
    # leave its old copy behind forever, since nothing else prunes the export.
    for root in (kiro_skills_root, agent_skills_root):
        shutil.rmtree(root, ignore_errors=True)
        root.mkdir(parents=True, exist_ok=True)
    
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

        # Copy templates/ and scripts/ verbatim (md templates still neutralized
        # so any paad/ output paths match the exported skill). These are part
        # of the skill package for Kiro/Cursor/Antigravity users who copy the
        # export tree; Claude Code and Pi load them from plugins/paad/skills.
        for bundle in ("templates", "scripts"):
            src_bundle = skill_path / bundle
            dst_bundle = kiro_skill_dir / bundle
            if dst_bundle.exists():
                shutil.rmtree(dst_bundle)
            if not src_bundle.is_dir():
                continue
            dst_bundle.mkdir()
            count = 0
            for src_file in sorted(src_bundle.rglob("*")):
                if "__pycache__" in src_file.parts or src_file.suffix in (".pyc", ".pyo"):
                    continue
                target = dst_bundle / src_file.relative_to(src_bundle)
                if src_file.is_dir():
                    target.mkdir(exist_ok=True)
                elif src_file.suffix == ".md":
                    text = neutralize(src_file.read_text(encoding="utf-8"))
                    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
                    target.write_text(text, encoding="utf-8")
                    count += 1
                else:
                    ensure_parent = target.parent
                    ensure_parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, target)
                    count += 1
            print(f"  + {count} {bundle} file(s)")


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
    convert_pi_agent()
