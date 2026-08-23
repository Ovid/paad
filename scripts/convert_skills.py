#!/usr/bin/env python3

import os
import re
import shutil
import sys
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


FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def _fm_entry(frontmatter, key):
    """Locate a top-level frontmatter key: (match, value, end-of-entry).

    Hand-rolled rather than PyYAML — this repo has no third-party Python
    dependencies and one key lookup does not justify the first. Folded and
    literal scalars (`>`, `|`) are joined into a single line: paad uses `>`
    for long descriptions, and a one-line regex captures just the marker.
    """
    m = re.search(rf"^{key}:[ \t]*(.*)$", frontmatter, flags=re.MULTILINE)
    if not m:
        return None, "", 0
    first = m.group(1).strip()
    if first not in (">", "|", ">-", "|-", ">+", "|+"):
        return m, first, m.end()
    joined, end = [], m.end()
    for line in frontmatter[m.end():].split("\n")[1:]:
        if line.strip() and not line[:1].isspace():
            break  # next top-level key
        end += len(line) + 1
        joined.append(line.strip())
    return m, " ".join(part for part in joined if part), end


def fm_value(frontmatter, key):
    return _fm_entry(frontmatter, key)[1]


def fm_set(frontmatter, key, value):
    """Replace a key's value, collapsing a folded scalar onto one line."""
    m, _, end = _fm_entry(frontmatter, key)
    if not m:
        return frontmatter
    return frontmatter[: m.start()] + f"{key}: {value}" + frontmatter[end:]


def _skill_command_re():
    """Match a Claude Code invocation of one of paad's own skills.

    Anchored on the skill names under SOURCE_DIR rather than on any bare
    slash-word: `handoff` contrasts itself with Claude Code's `/compact` on
    purpose, and that must survive. Longest name first so the alternation
    cannot stop at a shorter prefix. Both spellings are matched because the
    plugin-qualified `/paad:vibe` form still works in Claude Code and still
    means nothing anywhere else. The lookbehind keeps a rewritten output path
    (`.reviews/alignment/`) from looking like a command, and excludes `/` so a
    doubled slash is not read as one — it is the same character class the three
    Makefile checks use, and stripping only the second slash of `//vibe` left
    behind exactly what check-export-commands then rejected. The lookahead keeps
    `/alignment-reviews/` and the trailing slash of a directory out of it.
    """
    names = sorted(
        (p.name for p in Path(SOURCE_DIR).iterdir() if p.is_dir()),
        key=len,
        reverse=True,
    )
    alternation = "|".join(re.escape(name) for name in names)
    return re.compile(
        r"(?<![A-Za-z0-9._/-])/(?:paad:)?(" + alternation + r")(?![A-Za-z0-9/-])"
    )


SKILL_COMMAND = _skill_command_re()
SOURCE_SKILL_NAMES = frozenset(p.name for p in Path(SOURCE_DIR).iterdir() if p.is_dir())


SKIP_NAMES = ["makefile", "paad-help"]


def _skipped_command_re():
    """Match an invocation of a skill this exporter does not ship.

    neutralize() drops the leading slash from every paad command, which is
    right for a skill the reader has and wrong for one they do not: a
    reference to `/paad-help` exports as a bare `paad-help`, naming a skill
    that is not in that install. check-export-commands cannot catch it,
    because the slash it keys on is what the rewrite removed. So it is caught
    here, at the source, before the rewrite erases the evidence.
    """
    alternation = "|".join(
        re.escape(name) for name in sorted(SKIP_NAMES, key=len, reverse=True)
    )
    return re.compile(
        r"(?<![A-Za-z0-9._/-])/(?:paad:)?(" + alternation + r")(?![A-Za-z0-9/-])"
    )


SKIPPED_COMMAND = _skipped_command_re()


UNKNOWN_COMMAND = re.compile(
    r"(?<![A-Za-z0-9._-])/paad:([A-Za-z0-9-]+)(?![A-Za-z0-9/-])"
)


def stranded_refs(path, text, base_line=0):
    """Report references in `text` that must not reach the export.

    Two classes, and nothing downstream can see either one:

    - A skill this exporter withholds (SKIP_NAMES). neutralize() drops the
      leading slash from every paad command, so `/paad-help` exports as a bare
      `paad-help` naming a skill that is not in that install, and
      check-export-commands cannot catch it because the slash it keys on is
      what the rewrite removed.
    - A `/paad:` command naming no skill under SOURCE_DIR at all. Nothing
      rewrites it, so it ships verbatim as a live Claude Code command. Both the
      rewriter's alternation and check-export-commands' are built from that
      same directory listing, so a name the listing lacks is invisible to both
      — and promotion produces exactly that, when a skill leaves preview/ and
      `rsync --delete` takes it out of plugins/ while a sibling still names it.

    `base_line` is the line the fragment starts on, so a hit inside a section
    is reported at its real position in the file rather than within the piece.
    """
    hits = []
    for match in SKIPPED_COMMAND.finditer(text):
        line = base_line + text.count("\n", 0, match.start()) + 1
        hits.append(f"{path}:{line}: {match.group(0)} — withheld from this export")
    for match in UNKNOWN_COMMAND.finditer(text):
        if match.group(1) in SOURCE_SKILL_NAMES:
            continue
        line = base_line + text.count("\n", 0, match.start()) + 1
        hits.append(f"{path}:{line}: {match.group(0)} — names no skill in {SOURCE_DIR}")
    return hits


# Matched exactly against the heading text, never as a substring: a workflow
# step named "## Step 2: Pre-flight Checks" is not the section of the same
# name, and a substring test deleted it — leaving the export to jump from
# Step 1 to Step 3.
#
# "Arguments" and "Pre-flight Checks" are both deliberately absent. They are
# portable prose once neutralize() rewrites the example invocations, and
# deleting them stranded what the rest of the file refers to. Pre-flight is the
# sharper case: paad puts every digraph above the first heading, so the digraph
# is always kept while the section it diagrams was being dropped — the export
# shipped STOP nodes naming tests and messages that no surviving prose defined,
# and for that population the digraph *is* the pre-flight.
UNWANTED_HEADERS = ["Input Resolution", "Document classification"]


def sections(body_text):
    """Split a SKILL.md body into (header line or None, section body, offset).

    `offset` is the character position of the piece inside `body_text`, which
    is what lets a reference be reported at its true line after the section
    filter has removed everything around it.
    """
    parts = re.split(r"\n(##+ .*)", body_text)
    pieces = [(None, parts[0], 0)]
    pos = len(parts[0])
    for i in range(1, len(parts), 2):
        header_line, section_body = parts[i], parts[i + 1]
        pos += 1  # the newline the split consumed
        pieces.append((header_line, section_body, pos))
        pos += len(header_line) + len(section_body)
    return pieces


def scan_sources():
    """Collect stranded references from every fragment that survives the export.

    Runs before anything is written or deleted. Scanning the raw file instead
    aborted `make export` over text it was about to discard — unfixable without
    editing source that has no effect on the output.
    """
    stranded = []
    for skill_path in sorted(Path(SOURCE_DIR).iterdir()):
        if not skill_path.is_dir() or skill_path.name in SKIP_NAMES:
            continue
        skill_file = skill_path / "SKILL.md"
        if not skill_file.exists():
            continue
        content = skill_file.read_text(encoding="utf-8")
        fm_match = FRONTMATTER.match(content)
        body_start = fm_match.end() if fm_match else 0
        body = content[body_start:]
        base = content.count("\n", 0, body_start)
        for header_line, section_body, offset in sections(body):
            if header_line is None:
                fragment = section_body
            else:
                header_text = re.sub(r"^##+\s*", "", header_line).strip()
                if header_text in UNWANTED_HEADERS:
                    continue
                fragment = header_line + section_body
            stranded += stranded_refs(
                skill_file, fragment, base + body.count("\n", 0, offset)
            )
        src_refs = skill_path / "references"
        if src_refs.is_dir():
            for ref_file in sorted(src_refs.rglob("*.md")):
                stranded += stranded_refs(
                    ref_file, ref_file.read_text(encoding="utf-8")
                )
    return stranded


def neutralize_paths(text):
    """Rewrite paad's output paths and drop Claude-Code-only fragments.

    Safe on any text, including a single-line YAML value: it holds no rule
    about paad's slash commands, so each caller applies its own — neutralize()
    drops the slash, neutralize_description() names the skill outright.
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

    return text


def neutralize(text):
    """Strip paad-plugin specifics from a chunk of skill prose.

    Applied to SKILL.md section bodies and to every file under a skill's
    references/ directory, so a reference file never tells the agent to
    write to a path its own SKILL.md has already rewritten.

    NOT for frontmatter — that goes through neutralize_description(), which
    spells the name out rather than leaving a bare word in the one string
    these platforms match a request against.
    """
    text = neutralize_paths(text)

    # Drop the leading slash: `/agentic-dedup src/x/` -> `agentic-dedup src/x/`.
    # The skill is called the same thing everywhere, only the way you invoke it
    # differs, and keeping the name plus any arguments is what makes the
    # sentence still readable when it carries an example invocation.
    text = SKILL_COMMAND.sub(r"\1", text)

    return text


def neutralize_description(text):
    """Neutralize a frontmatter description.

    Same command rule as neutralize(), different replacement, because a
    description is one unbroken run of sentences and is the one string these
    platforms match a request against. Dropping the slash the way a body does
    would leave a bare word mid-sentence ("that's alignment"), so the sibling
    is named outright instead: "that's the alignment skill". The skill is
    called the same thing everywhere; only the way you invoke it differs.
    """
    text = neutralize_paths(text)
    return SKILL_COMMAND.sub(r"the \1 skill", text)


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

    # Everything that can refuse runs before the first destructive act. Both of
    # these used to sit after it: `make export` would empty both export roots and
    # only then abort, and the downstream message is "run 'make export' first" —
    # when `make export` is what emptied it. A failed run also left
    # kiro_and_antigravity/ fully regenerated and pi/ untouched: two trees built
    # from different source states.
    skip_names = SKIP_NAMES
    missing = [n for n in skip_names if not (Path(SOURCE_DIR) / n).is_dir()]
    if missing:
        print(
            f"FAIL: SKIP_NAMES lists {', '.join(missing)}, which is not a directory under "
            f"{SOURCE_DIR}. A typo here silently exports a skill meant to be withheld.",
            file=sys.stderr,
        )
        sys.exit(1)

    stranded = scan_sources()
    if stranded:
        print(
            "FAIL: exported skill(s) name a skill this export does not ship. The leading slash "
            "is dropped on export, so these would read as an instruction to run something the "
            "reader does not have:",
            file=sys.stderr,
        )
        for hit in stranded:
            print(f"  {hit}", file=sys.stderr)
        sys.exit(1)

    # Wipe: a renamed, deleted, or newly skipped skill would otherwise leave its
    # old copy behind forever, since nothing else prunes the export.
    for root in (kiro_skills_root, agent_skills_root):
        shutil.rmtree(root, ignore_errors=True)
        root.mkdir(parents=True, exist_ok=True)

    unwanted_headers = UNWANTED_HEADERS

    for skill_path in Path(SOURCE_DIR).iterdir():
        if not skill_path.is_dir() or skill_path.name in skip_names:
            continue
            
        skill_file = skill_path / "SKILL.md"
        if not skill_file.exists():
            continue
            
        print(f"Converting {skill_path.name}...")
        
        with open(skill_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Frontmatter is parsed and rewritten on its own terms and never
        # reaches neutralize() — see neutralize_description().
        fm_match = FRONTMATTER.match(content)
        frontmatter = fm_match.group(1) if fm_match else ""
        body = content[fm_match.end():] if fm_match else content

        skill_name = fm_value(frontmatter, "name") or skill_path.name
        description = neutralize_description(fm_value(frontmatter, "description"))

        # The same split scan_sources() used, so what is checked and what is
        # written can never disagree about which sections survive.
        pieces = sections(body)

        # pieces[0] is everything before the first ## — the intro, the
        # announce line, and (by paad convention) every digraph. Those
        # digraphs name output paths, so it gets neutralized on the
        # same terms as the section bodies or the two disagree. The
        # frontmatter is no longer in here; it is spliced back on below.
        cleaned_content = neutralize(pieces[0][1])

        for header_line, section_body, _ in pieces[1:]:
            header_text = re.sub(r'^##+\s*', '', header_line).strip()

            # Skip unwanted sections
            if header_text in unwanted_headers:
                continue

            section_body = neutralize(section_body)

            # Clean up trailing whitespace and excessive newlines
            section_body = section_body.rstrip() + "\n"

            cleaned_content += "\n" + neutralize(header_line) + section_body

        # Final cleanup for consecutive empty lines
        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content).strip() + "\n"

        # Splice the frontmatter back on with only its description rewritten.
        # Every other key — test-roadmap's compatibility: — keeps its place.
        if fm_match:
            cleaned_content = (
                "---\n"
                + fm_set(frontmatter, "description", description)
                + "\n---\n\n"
                + cleaned_content
            )
        
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
                    text = ref_file.read_text(encoding="utf-8")
                    text = neutralize(text)
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
    convert_pi_agent()
