#!/usr/bin/env python3
"""KB-Brain: deterministic scaffold, index, check, seal, and amend tooling.

Stdlib only. Designed to be copied into a target repository's scripts/
directory during `init`. Safe to re-run; fails clearly without destructive
partial changes where practical.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

VERSION = "1.0.0"

TOP_SECTIONS = [
    "decisions",
    "architecture",
    "domains",
    "runbooks",
    "gotchas",
    "briefs",
    "specs",
    "plans",
    "reviews",
    "learnings",
    "open-questions",
    "agents",
    "improvements",
    "tech-debt",
    "templates",
    "work",
]

WORKSPACE_LEVELS = ("minimal", "standard", "strict")
DEFAULT_LEVEL = "standard"

# Atomic record prefixes and their default directories (relative to a workspace
# or permanent section root, depending on type).
PREFIXES = {
    "decision": "D",
    "finding": "F",
    "question": "Q",
    "failure": "X",
    "conflict": "C",
    "handoff": "H",
    "improvement": "I",
    "tech-debt": "TD",
    "assumption": "A",
    "dependency": "DEP",
    "scope-change": "SC",
    "amendment": "AM",
    "milestone": "M",
}

SECTION_TO_TYPE = {
    "decisions": "decision",
    "findings": "finding",
    "questions": "question",
    "failures": "failure",
    "conflicts": "conflict",
    "handoffs": "handoff",
    "improvements": "improvement",
    "tech-debt": "tech-debt",
    "assumptions": "assumption",
    "dependencies": "dependency",
    "scope-changes": "scope-change",
    "amendments": "amendment",
    "open-questions": "question",
}

VALID_STATUSES = {
    "open",
    "closed",
    "resolved",
    "deferred",
    "blocked",
    "unresolved",
    "accepted",
    "rejected",
    "superseded",
    "active",
    "done",
    "promoted",
    "abandoned",
    "review-needed",
    "approved-spec",
    "brief",
    "incubating",
    "ready-for-expansion",
    "expanding",
    "planned",
    "in-progress",
    "completed",
}

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}"),
    re.compile(r"(?i)secret\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?i)password\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
]

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)
ID_RE = re.compile(r"^[A-Z]+-\d+$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

MAKEFILE_BLOCK_BEGIN = "# >>> kb-brain targets (managed by kb_brain.py; do not edit by hand)"
MAKEFILE_BLOCK_END = "# <<< kb-brain targets"

MAKEFILE_BLOCK = f"""{MAKEFILE_BLOCK_BEGIN}
.PHONY: kb-index kb-new kb-check kb-start kb-close kb-amend

kb-index:
\tpython3 scripts/kb_brain.py index

kb-new:
\tpython3 scripts/kb_brain.py new "$(SECTION)" "$(TITLE)"

kb-check:
\tpython3 scripts/kb_brain.py check

kb-start:
\tpython3 scripts/kb_brain.py start "$(SLUG)" "$(LEVEL)"

kb-close:
\tpython3 scripts/kb_brain.py close "$(TASK)"

kb-amend:
\tpython3 scripts/kb_brain.py amend "$(TASK)" "$(RECORD)" "$(TITLE)"
{MAKEFILE_BLOCK_END}
"""

README_BODY = """# KB-Brain

Repository-native working knowledge shared by humans, lead agents, and
sub-agents. Stable architecture and accepted documentation live under `docs/`.
This tree holds mutable context: decisions in flight, gaps, debt, lessons, and
focused task workspaces.

## Index-first retrieval

Do not read the entire KB by default. Normal order:

1. `work/ACTIVE.md`
2. the selected workspace's `TASK.md`
3. `INDEX.md` (workspace, then repository)
4. `CONTEXT.md`
5. the agent's assignment
6. only linked or relevant atomic records

## Permanent sections

| Section | Meaning |
|---------|---------|
| `decisions/` | Accepted ADR-style decisions with owner and evidence |
| `architecture/` | Mutable notes that refine or challenge stable `docs/` architecture — always link back |
| `domains/` | Product and business domain knowledge |
| `runbooks/` | Recurring procedures not yet promoted to stable docs |
| `gotchas/` | Sharp edges, false starts, reliable warnings |
| `briefs/` | Human-owned briefs and atomic milestone records |
| `specs/` | Active working specifications, including candidate milestone expansions |
| `plans/` | Implementation plans tied to approved specs |
| `reviews/` | Review outputs worth preserving beyond their session |
| `learnings/` | Post-hoc lessons and retrospectives |
| `open-questions/` | Unresolved questions — agents may add evidence, never invent answers |
| `agents/` | Repository-specific agent behaviour and coordination notes |
| `improvements/` | One atomic file per noticed gap or opportunity |
| `tech-debt/` | Open debt plus `LEDGER.md`; resolved entries move to `tech-debt/closed/` |
| `templates/` | Project-local copies of record templates |
| `work/` | Active and closed task workspaces |

## Workspace levels

Configured in `AGENTS.md` (default `standard`). A task may raise its level;
lowering below the repository default requires explicit human approval.

- **minimal** — scope, status, ownership, handoff, durable findings
- **standard** — findings, questions, decisions, failures, conflicts, handoffs
- **strict** — standard plus assumptions, dependencies, ownership, scope-change tracking

## Closure and amendments

Closed workspaces under `work/closed/` are immutable. Corrections go in
`amendments/` and are marked in regenerated indexes. See `SEAL.json`.

## Tooling

```bash
make kb-index
make kb-new SECTION=improvements TITLE="Example gap"
make kb-check
make kb-start SLUG=auth-migration LEVEL=strict
make kb-close TASK=2026-08-04-auth-migration
make kb-amend TASK=2026-08-04-auth-migration RECORD=findings/F-001-parser.md TITLE="Clarify parser note"
```

Or call `python3 scripts/kb_brain.py --help`.

Bulk ingress from `docs/` is a dedicated operation — never dump architecture
documents into this tree during ordinary work.
"""


# ---------------------------------------------------------------------------
# Frontmatter (stdlib YAML subset)
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse a minimal YAML frontmatter block into a dict and body."""
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    meta: dict[str, Any] = {}
    lines = match.group(1).splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, _, raw = line.partition(":")
        key = key.strip()
        value = raw.strip()
        if value in ("", "|", ">"):
            # Multi-line scalar or empty — collect indented follow-ons as list/string
            items: list[str] = []
            i += 1
            while i < len(lines) and (lines[i].startswith("  ") or lines[i].startswith("\t") or lines[i].startswith("- ")):
                item = lines[i].strip()
                if item.startswith("- "):
                    items.append(item[2:].strip().strip("'\""))
                else:
                    items.append(item.strip("'\""))
                i += 1
            meta[key] = items if items else ""
            continue
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            meta[key] = [p.strip().strip("'\"") for p in inner.split(",") if p.strip()] if inner else []
        elif value.lower() in ("true", "false"):
            meta[key] = value.lower() == "true"
        elif re.fullmatch(r"-?\d+", value):
            meta[key] = int(value)
        else:
            meta[key] = value.strip("'\"").strip('"')
        i += 1
    body = text[match.end() :]
    return meta, body


def dump_frontmatter(meta: dict[str, Any], body: str = "") -> str:
    lines = ["---"]
    for key, value in meta.items():
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    if body and not body.startswith("\n"):
        return "\n".join(lines) + body.lstrip("\n")
    return "\n".join(lines) + (body or "")


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def repo_root_from_cwd(start: Path | None = None) -> Path:
    """Walk up looking for kb-brain/ or .git; fall back to cwd."""
    cur = (start or Path.cwd()).resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / "kb-brain").is_dir() or (candidate / ".git").exists():
            return candidate
    return cur


def kb_root(root: Path) -> Path:
    return root / "kb-brain"


def skill_dir() -> Path:
    """Directory that owns templates/ — skill package or project kb-brain/."""
    here = Path(__file__).resolve().parent
    # Skill package: .../kb-brain/scripts/kb_brain.py
    if (here.parent / "templates").is_dir() or (here.parent / "SKILL.md").exists():
        return here.parent
    # After init the script lives at <root>/scripts/kb_brain.py
    root = here.parent
    if (root / "kb-brain" / "templates").is_dir():
        return root / "kb-brain"
    return here.parent


def today() -> str:
    return date.today().isoformat()


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "item"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_if_absent(path: Path, content: str) -> bool:
    """Write content only if the file does not exist. Returns True if written."""
    if path.exists():
        return False
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")
    return True


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def relative_to_kb(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(kb_root(root).resolve()))
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATE_FILES = {
    "TASK.md": """---
id: {task_id}
type: task
status: active
level: {level}
lead: {lead}
author: {author}
created: {created}
updated: {created}
related: []
---

# {title}

## Objective
{objective}

## Scope
-

## Non-goals
-

## Completion criteria
-

## Current focus
-

## Blockers
-

## Controlling links
- brief:
- spec:
- issue:
- plan:
""",
    "CONTEXT.md": """---
id: {task_id}-context
type: context
status: active
author: {author}
created: {created}
updated: {created}
---

# Shared context

Keep this brief. Move detail into atomic records and link them.

## What matters right now
-

## Pointers
-
""",
    "ASSIGNMENTS.md": """---
id: {task_id}-assignments
type: assignments
status: active
author: {author}
owner: {lead}
role: lead
created: {created}
updated: {created}
---

# Assignments

Lead-controlled. Record each human or agent assignment, boundary, dependencies, and status.

| Agent / human | Boundary | Depends on | Status |
|---------------|----------|------------|--------|
| | | | |
""",
    "PROMOTION.md": """---
id: {task_id}-promotion
type: promotion
status: open
author: {author}
created: {created}
updated: {created}
---

# Promotion tracking

Durable information that must move into permanent KBB sections or stable `docs/` before closure.

| Record | Destination | Status |
|--------|-------------|--------|
| | | |
""",
    "finding.md": """---
id: {id}
type: finding
status: open
author: {author}
owner: {owner}
created: {created}
updated: {created}
related: []
evidence: []
---

# {title}

## Observation
-

## Evidence
-

## Impact
-
""",
    "decision.md": """---
id: {id}
type: decision
status: accepted
author: {author}
owner: {owner}
decision-owner: {owner}
role: lead
created: {created}
updated: {created}
related: []
evidence: []
---

# {title}

## Context
-

## Decision
-

## Rationale
-

## Evidence
-

## Consequences
-
""",
    "question.md": """---
id: {id}
type: question
status: open
author: {author}
owner: {owner}
created: {created}
updated: {created}
related: []
evidence: []
---

# {title}

## Question
-

## Why it matters
-

## Evidence so far
-

## Answer
Unanswered. Do not invent an answer.
""",
    "failure.md": """---
id: {id}
type: failure
status: open
author: {author}
owner: {owner}
created: {created}
updated: {created}
related: []
evidence: []
---

# {title}

## What was tried
-

## Why it failed
-

## Evidence
-

## Lesson
-
""",
    "conflict.md": """---
id: {id}
type: conflict
status: unresolved
author: {author}
owner: {owner}
created: {created}
updated: {created}
related: []
evidence: []
---

# {title}

## Position A
-

## Position B
-

## Evidence
-

## Impact
-

## Required resolution
-

## Resolution
unresolved
""",
    "handoff.md": """---
id: {id}
type: handoff
status: open
author: {author}
owner: {owner}
created: {created}
updated: {created}
related: []
---

# {title}

## From
-

## To
-

## State of play
-

## Next actions
-

## Blockers
-
""",
    "improvement.md": """---
id: {id}
type: improvement
status: open
author: {author}
owner: {owner}
created: {created}
updated: {created}
related: []
evidence: []
---

# {title}

## Observed during
-

## Observation
-

## Evidence
-

## Why it matters
-

## Possible direction
-

## Relationship to current work
-
""",
    "tech-debt.md": """---
id: {id}
type: tech-debt
status: open
author: {author}
owner: {owner}
created: {created}
updated: {created}
related: []
evidence: []
---

# {title}

## Liability
-

## Evidence
-

## Suggested remediation
-

## Urgency
-
""",
    "assumption.md": """---
id: {id}
type: assumption
status: open
author: {author}
owner: {owner}
created: {created}
updated: {created}
related: []
evidence: []
---

# {title}

## Assumption
-

## If wrong
-

## Validation needed
-
""",
    "dependency.md": """---
id: {id}
type: dependency
status: open
author: {author}
owner: {owner}
created: {created}
updated: {created}
related: []
---

# {title}

## Depends on
-

## Needed by
-

## Status
-
""",
    "scope-change.md": """---
id: {id}
type: scope-change
status: open
author: {author}
owner: {owner}
role: lead
created: {created}
updated: {created}
related: []
---

# {title}

## Change
-

## Why
-

## Approved by
-
""",
    "closeout.md": """---
id: {task_id}-closeout
type: closeout
status: done
author: {author}
owner: {lead}
role: lead
created: {created}
updated: {created}
---

# Closeout — {task_id}

## Outcome
-

## What was promoted
-

## What was not promoted (and why)
-

## Remaining risks
-

## Follow-ups
-
""",
    "amendment.md": """---
id: {id}
type: amendment
status: open
author: {author}
owner: {owner}
created: {created}
updated: {created}
amends: {amends}
related: []
evidence: []
---

# {title}

## What this corrects
-

## Why
-

## New evidence
-

## Impact
-
""",
    "BRIEF.md": """---
id: brief-{slug}
type: brief
status: active
author: {author}
owner: {owner}
created: {created}
updated: {created}
---

# {title}

## Intended outcome
-

## Users and stakeholders
-

## Why it matters
-

## Constraints
-

## Non-goals
-

## Success at project level
-

## Known milestone ideas
-

## Open questions
-
""",
    "MILESTONE.md": """---
id: {id}
type: milestone
status: brief
author: {author}
owner: {owner}
created: {created}
updated: {created}
related: []
---

# {title}

## Outcome
-

## Notes
-
""",
    "MILESTONE-SPEC.md": """---
id: {id}-spec
type: milestone-spec
status: review-needed
author: {author}
owner: {owner}
created: {created}
updated: {created}
related: []
---

# {title}

## Status
review-needed

## Brief linkage
-

## Outcome
-

## Scope
-

## Non-goals
-

## User and system behaviour
-

## Constraints and controlling decisions
-

## Components and boundaries
-

## Data and interface implications
-

## Failure and recovery behaviour
-

## Security, privacy, accessibility, and operational concerns
-

## Dependencies
-

## Acceptance criteria
-

## Testing expectations
-

## Open questions
-

## Assumptions
-

## Evidence consulted
-

## Human approval
Unapproved candidate specification.
""",
}


def bundled_templates_dir() -> Path:
    return skill_dir() / "templates"


def materialize_bundled_templates() -> None:
    """Ensure skill-package templates/ exists with the canonical set."""
    dest = bundled_templates_dir()
    ensure_dir(dest)
    for name, content in TEMPLATE_FILES.items():
        path = dest / name
        if not path.exists():
            # Store unsubstituted exemplars for humans/agents to copy.
            exemplar = content
            for key, sample in {
                "{task_id}": "YYYY-MM-DD-slug",
                "{level}": "standard",
                "{lead}": "task-lead",
                "{author}": "author",
                "{owner}": "owner",
                "{created}": "YYYY-MM-DD",
                "{title}": "Title",
                "{objective}": "Objective",
                "{id}": "F-001",
                "{slug}": "slug",
                "{amends}": "path/to/record.md",
            }.items():
                exemplar = exemplar.replace(key, sample)
            write_text(path, exemplar)


def copy_templates_to_project(root: Path) -> None:
    materialize_bundled_templates()
    dest = kb_root(root) / "templates"
    ensure_dir(dest)
    for src in bundled_templates_dir().iterdir():
        if src.is_file():
            target = dest / src.name
            if not target.exists():
                shutil.copy2(src, target)


def render_template(name: str, **kwargs: str) -> str:
    materialize_bundled_templates()
    # Prefer in-memory TEMPLATE_FILES for substitution fidelity.
    if name in TEMPLATE_FILES:
        text = TEMPLATE_FILES[name]
    else:
        text = read_text(bundled_templates_dir() / name)
    for key, value in kwargs.items():
        text = text.replace("{" + key + "}", value)
    # Leave any unused placeholders as-is only if they look intentional;
    # replace common leftovers with empty/defaults.
    return text


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

def cmd_init(root: Path, level: str) -> int:
    if level not in WORKSPACE_LEVELS:
        print(f"FAIL: level must be one of {', '.join(WORKSPACE_LEVELS)}", file=sys.stderr)
        return 2

    kb = kb_root(root)
    ensure_dir(kb)

    # Top-level sections — empty dirs with .gitkeep only (no atomic records).
    for section in TOP_SECTIONS:
        ensure_dir(kb / section)

    ensure_dir(kb / "tech-debt" / "closed")
    write_if_absent(
        kb / "tech-debt" / "LEDGER.md",
        "# Technical debt ledger\n\n| ID | Title | Status | Path |\n|----|-------|--------|------|\n",
    )

    ensure_dir(kb / "work" / "active")
    ensure_dir(kb / "work" / "closed")

    write_if_absent(kb / "README.md", README_BODY)
    write_if_absent(
        kb / "INDEX.md",
        "# KB-Brain index\n\n_Generated. Run `make kb-index` or `python3 scripts/kb_brain.py index`._\n",
    )
    write_if_absent(
        kb / "work" / "ACTIVE.md",
        "# Active work\n\n_No active KB-Brain workspaces._\n",
    )

    # Default level marker (read by start when AGENTS.md has no override).
    write_if_absent(
        kb / ".default-level",
        level + "\n",
    )

    copy_templates_to_project(root)
    install_script(root)
    install_makefile_targets(root)
    regenerate_repo_index(root)
    regenerate_active(root)

    print(f"Initialized kb-brain/ at {kb} (default level: {level})")
    print("Did not ingest docs/ or other existing documentation.")
    return 0


def install_script(root: Path) -> None:
    src = Path(__file__).resolve()
    dest_dir = root / "scripts"
    ensure_dir(dest_dir)
    dest = dest_dir / "kb_brain.py"
    if dest.resolve() == src.resolve():
        return
    shutil.copy2(src, dest)
    dest.chmod(dest.stat().st_mode | 0o111)


def install_makefile_targets(root: Path) -> None:
    makefile = root / "Makefile"
    if not makefile.exists():
        inc = kb_root(root) / "Makefile.inc"
        write_text(
            inc,
            f"# Include from your Makefile with: include kb-brain/Makefile.inc\n{MAKEFILE_BLOCK}\n",
        )
        print(f"No Makefile found — wrote {inc.relative_to(root)} (include it from your build file)")
        return

    text = read_text(makefile)
    if MAKEFILE_BLOCK_BEGIN in text:
        # Replace existing managed block idempotently.
        pattern = re.compile(
            re.escape(MAKEFILE_BLOCK_BEGIN) + r".*?" + re.escape(MAKEFILE_BLOCK_END),
            re.DOTALL,
        )
        text = pattern.sub(MAKEFILE_BLOCK.strip(), text)
        write_text(makefile, text if text.endswith("\n") else text + "\n")
        return

    separator = "" if text.endswith("\n") else "\n"
    write_text(makefile, text + separator + "\n" + MAKEFILE_BLOCK + "\n")


def read_default_level(root: Path) -> str:
    """Resolve repository default workspace level."""
    agents = root / "AGENTS.md"
    if agents.exists():
        text = read_text(agents)
        m = re.search(
            r"Repository workspace level:\s*`?(minimal|standard|strict)`?",
            text,
            re.IGNORECASE,
        )
        if m:
            return m.group(1).lower()
    marker = kb_root(root) / ".default-level"
    if marker.exists():
        value = read_text(marker).strip().lower()
        if value in WORKSPACE_LEVELS:
            return value
    return DEFAULT_LEVEL


# ---------------------------------------------------------------------------
# Workspace start
# ---------------------------------------------------------------------------

def allocate_task_id(root: Path, slug: str) -> str:
    slug = slugify(slug)
    base = f"{today()}-{slug}"
    active = kb_root(root) / "work" / "active"
    closed = kb_root(root) / "work" / "closed"
    existing = set()
    for parent in (active, closed):
        if parent.is_dir():
            existing.update(p.name for p in parent.iterdir() if p.is_dir())
    if base not in existing:
        return base
    n = 2
    while f"{base}-{n}" in existing:
        n += 1
    return f"{base}-{n}"


def required_workspace_dirs(level: str) -> list[str]:
    base = ["decisions", "findings", "questions", "failures", "conflicts", "handoffs"]
    if level == "minimal":
        return ["findings", "handoffs"]
    if level == "strict":
        return base + ["assumptions", "dependencies", "scope-changes"]
    return base


def required_workspace_files(level: str) -> list[str]:
    files = ["TASK.md", "INDEX.md", "CONTEXT.md", "PROMOTION.md"]
    if level in ("standard", "strict"):
        files.append("ASSIGNMENTS.md")
    return files


def cmd_start(root: Path, slug: str, level: str | None, lead: str, author: str) -> int:
    if not kb_root(root).is_dir():
        print("FAIL: kb-brain/ not found — run init first", file=sys.stderr)
        return 2

    repo_level = read_default_level(root)
    chosen = (level or repo_level).lower()
    if chosen not in WORKSPACE_LEVELS:
        print(f"FAIL: level must be one of {', '.join(WORKSPACE_LEVELS)}", file=sys.stderr)
        return 2

    level_rank = {name: i for i, name in enumerate(WORKSPACE_LEVELS)}
    if level_rank[chosen] < level_rank[repo_level]:
        print(
            f"FAIL: lowering workspace level below repository default "
            f"({repo_level} → {chosen}) requires explicit human approval. "
            f"Pass the repo default or higher, or obtain approval and re-run "
            f"with --force-lower after documenting the approval.",
            file=sys.stderr,
        )
        return 2

    task_id = allocate_task_id(root, slug)
    ws = kb_root(root) / "work" / "active" / task_id
    if ws.exists():
        print(f"FAIL: workspace already exists: {ws}", file=sys.stderr)
        return 2

    ensure_dir(ws)
    created = today()
    title = slug.replace("-", " ").strip().title() or task_id

    write_text(
        ws / "TASK.md",
        render_template(
            "TASK.md",
            task_id=task_id,
            level=chosen,
            lead=lead,
            author=author,
            created=created,
            title=title,
            objective=title,
        ),
    )
    write_text(
        ws / "CONTEXT.md",
        render_template(
            "CONTEXT.md",
            task_id=task_id,
            author=author,
            created=created,
        ),
    )
    write_text(
        ws / "PROMOTION.md",
        render_template(
            "PROMOTION.md",
            task_id=task_id,
            author=author,
            created=created,
        ),
    )
    if chosen in ("standard", "strict"):
        write_text(
            ws / "ASSIGNMENTS.md",
            render_template(
                "ASSIGNMENTS.md",
                task_id=task_id,
                author=author,
                lead=lead,
                created=created,
            ),
        )

    for dirname in required_workspace_dirs(chosen):
        ensure_dir(ws / dirname)
        gitkeep = ws / dirname / ".gitkeep"
        write_if_absent(gitkeep, "")

    regenerate_workspace_index(ws)
    regenerate_active(root)
    regenerate_repo_index(root)

    print(f"Started workspace {task_id} (level={chosen}) at {ws.relative_to(root)}")
    return 0


# ---------------------------------------------------------------------------
# Record creation
# ---------------------------------------------------------------------------

def next_id(directory: Path, prefix: str) -> str:
    highest = 0
    if directory.is_dir():
        for path in directory.iterdir():
            if not path.is_file() or path.name.startswith("."):
                continue
            meta, _ = parse_frontmatter(read_text(path))
            rid = str(meta.get("id", ""))
            m = re.match(rf"^{re.escape(prefix)}-(\d+)$", rid)
            if m:
                highest = max(highest, int(m.group(1)))
            else:
                m2 = re.match(rf"^{re.escape(prefix)}-(\d+)", path.stem)
                if m2:
                    highest = max(highest, int(m2.group(1)))
    return f"{prefix}-{highest + 1:03d}"


def resolve_section_dir(root: Path, section: str, task_id: str | None) -> tuple[Path, str]:
    """Return (directory, record_type) for a section name."""
    section = section.strip().strip("/")
    if section in SECTION_TO_TYPE:
        rtype = SECTION_TO_TYPE[section]
    elif section in PREFIXES:
        rtype = section
        # Map type back to plural dir when needed
        plural = {
            "decision": "decisions",
            "finding": "findings",
            "question": "questions",
            "failure": "failures",
            "conflict": "conflicts",
            "handoff": "handoffs",
            "improvement": "improvements",
            "tech-debt": "tech-debt",
            "assumption": "assumptions",
            "dependency": "dependencies",
            "scope-change": "scope-changes",
            "amendment": "amendments",
        }.get(section, section)
        section = plural
    else:
        raise ValueError(f"unknown section '{section}'")

    if section in ("improvements", "tech-debt", "open-questions", "decisions", "gotchas", "learnings"):
        # Permanent sections (and decisions may also be workspace-local)
        if task_id and section == "decisions":
            ws = find_workspace(root, task_id)
            if ws is None:
                raise ValueError(f"task not found: {task_id}")
            return ws / "decisions", rtype
        if section == "open-questions":
            return kb_root(root) / "open-questions", rtype
        return kb_root(root) / section, rtype

    # Workspace-local sections
    if not task_id:
        active = list_active_workspaces(root)
        if len(active) == 1:
            task_id = active[0].name
        elif not active:
            raise ValueError("no active workspace — pass --task or start one")
        else:
            raise ValueError("multiple active workspaces — pass --task <id>")

    ws = find_workspace(root, task_id)
    if ws is None:
        raise ValueError(f"task not found: {task_id}")
    return ws / section, rtype


def find_workspace(root: Path, task_id: str) -> Path | None:
    for parent in ("active", "closed"):
        candidate = kb_root(root) / "work" / parent / task_id
        if candidate.is_dir():
            return candidate
    return None


def list_active_workspaces(root: Path) -> list[Path]:
    active = kb_root(root) / "work" / "active"
    if not active.is_dir():
        return []
    return sorted(p for p in active.iterdir() if p.is_dir())


def template_name_for_type(rtype: str) -> str:
    return {
        "decision": "decision.md",
        "finding": "finding.md",
        "question": "question.md",
        "failure": "failure.md",
        "conflict": "conflict.md",
        "handoff": "handoff.md",
        "improvement": "improvement.md",
        "tech-debt": "tech-debt.md",
        "assumption": "assumption.md",
        "dependency": "dependency.md",
        "scope-change": "scope-change.md",
        "amendment": "amendment.md",
        "milestone": "MILESTONE.md",
    }[rtype]


def cmd_new(
    root: Path,
    section: str,
    title: str,
    task_id: str | None,
    author: str,
    owner: str,
) -> int:
    if not kb_root(root).is_dir():
        print("FAIL: kb-brain/ not found — run init first", file=sys.stderr)
        return 2
    try:
        directory, rtype = resolve_section_dir(root, section, task_id)
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    ensure_dir(directory)
    # Remove .gitkeep once real content arrives
    gitkeep = directory / ".gitkeep"
    if gitkeep.exists():
        gitkeep.unlink()

    prefix = PREFIXES[rtype]
    rid = next_id(directory, prefix)
    slug = slugify(title)[:60]
    filename = f"{rid}-{slug}.md"
    path = directory / filename
    if path.exists():
        print(f"FAIL: refusing to overwrite {path}", file=sys.stderr)
        return 2

    created = today()
    content = render_template(
        template_name_for_type(rtype),
        id=rid,
        title=title,
        author=author,
        owner=owner,
        created=created,
        amends="",
        slug=slug,
    )
    write_text(path, content)

    if rtype == "tech-debt":
        update_debt_ledger(root)

    # Refresh indexes
    ws = directory
    while ws.name not in ("active", "closed") and ws != kb_root(root) and ws.parent != ws:
        if (ws / "TASK.md").exists():
            regenerate_workspace_index(ws)
            break
        ws = ws.parent
    regenerate_repo_index(root)
    regenerate_active(root)

    print(f"Created {path.relative_to(root)}")
    return 0


def update_debt_ledger(root: Path) -> None:
    debt_dir = kb_root(root) / "tech-debt"
    rows = ["# Technical debt ledger", "", "| ID | Title | Status | Path |", "|----|-------|--------|------|"]
    for path in sorted(debt_dir.glob("TD-*.md")):
        meta, body = parse_frontmatter(read_text(path))
        title = _heading(body) or path.stem
        rows.append(
            f"| {meta.get('id', path.stem)} | {title} | {meta.get('status', '')} | {path.relative_to(kb_root(root))} |"
        )
    closed = debt_dir / "closed"
    if closed.is_dir():
        for path in sorted(closed.glob("TD-*.md")):
            meta, body = parse_frontmatter(read_text(path))
            title = _heading(body) or path.stem
            rows.append(
                f"| {meta.get('id', path.stem)} | {title} | closed | {path.relative_to(kb_root(root))} |"
            )
    write_text(debt_dir / "LEDGER.md", "\n".join(rows) + "\n")


def _heading(body: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


# ---------------------------------------------------------------------------
# Index generation
# ---------------------------------------------------------------------------

def iter_markdown_records(directory: Path) -> Iterable[Path]:
    if not directory.is_dir():
        return
    for path in sorted(directory.rglob("*.md")):
        if path.name in ("INDEX.md", "README.md", "LEDGER.md", "ACTIVE.md", "CLOSEOUT.md"):
            continue
        if path.name.startswith("."):
            continue
        # Skip pure template copies at kb-brain/templates
        if "templates" in path.parts:
            continue
        yield path


def regenerate_workspace_index(ws: Path) -> None:
    amendments: dict[str, list[str]] = {}
    amend_dir = ws / "amendments"
    if amend_dir.is_dir():
        for path in amend_dir.glob("*.md"):
            meta, _ = parse_frontmatter(read_text(path))
            target = str(meta.get("amends", "")).strip()
            if target:
                amendments.setdefault(target, []).append(path.name)

    lines = [
        f"# Index — {ws.name}",
        "",
        "_Generated by kb_brain.py. Do not edit by hand._",
        "",
    ]
    groups: dict[str, list[str]] = {}
    for path in iter_markdown_records(ws):
        if path.parent.name == "amendments":
            continue
        meta, body = parse_frontmatter(read_text(path))
        rtype = str(meta.get("type", path.parent.name))
        status = str(meta.get("status", ""))
        owner = str(meta.get("owner", meta.get("author", "")))
        rid = str(meta.get("id", path.stem))
        title = _heading(body) or path.stem
        rel = path.relative_to(ws).as_posix()
        marker = ""
        for key, names in amendments.items():
            if key == rel or key.endswith(path.name) or key == rid:
                marker = f" **[amended: {', '.join(names)}]**"
                break
        groups.setdefault(rtype, []).append(
            f"- `{rid}` {title} — status={status or '—'}; owner={owner or '—'}; [{rel}]({rel}){marker}"
        )

    if not groups:
        lines.append("_No atomic records yet._")
    else:
        for rtype in sorted(groups):
            lines.append(f"## {rtype}")
            lines.extend(groups[rtype])
            lines.append("")

    if amendments:
        lines.append("## amendments")
        for path in sorted(amend_dir.glob("*.md")):
            meta, body = parse_frontmatter(read_text(path))
            lines.append(
                f"- `{meta.get('id', path.stem)}` {_heading(body) or path.stem} — amends `{meta.get('amends', '')}`"
            )
        lines.append("")

    write_text(ws / "INDEX.md", "\n".join(lines).rstrip() + "\n")


def regenerate_repo_index(root: Path) -> None:
    kb = kb_root(root)
    lines = [
        "# KB-Brain index",
        "",
        "_Generated by kb_brain.py. Do not edit by hand._",
        "",
        "## Active workspaces",
        "",
    ]
    active = list_active_workspaces(root)
    if not active:
        lines.append("_None._")
    else:
        for ws in active:
            lines.append(f"- [{ws.name}](work/active/{ws.name}/TASK.md)")
    lines.append("")
    lines.append("## Permanent sections")
    lines.append("")
    for section in TOP_SECTIONS:
        if section in ("templates", "work"):
            continue
        directory = kb / section
        records = [p for p in iter_markdown_records(directory) if p.parent == directory or section in p.parts]
        # Only top-level section files for the summary (briefs/specs have nested trees)
        count = len(list(directory.rglob("*.md"))) if directory.is_dir() else 0
        if section == "tech-debt":
            count = len(list(directory.glob("TD-*.md"))) + len(list((directory / "closed").glob("TD-*.md"))) if directory.is_dir() else 0
        lines.append(f"- `{section}/` — {count} markdown file(s)")
    lines.append("")
    write_text(kb / "INDEX.md", "\n".join(lines))


def parse_task_card(ws: Path) -> dict[str, Any]:
    path = ws / "TASK.md"
    if not path.exists():
        return {}
    meta, body = parse_frontmatter(read_text(path))
    fields = {
        "id": meta.get("id", ws.name),
        "status": meta.get("status", "active"),
        "level": meta.get("level", DEFAULT_LEVEL),
        "lead": meta.get("lead", meta.get("owner", "")),
        "objective": "",
        "focus": "",
        "blockers": "",
    }
    section = None
    buckets: dict[str, list[str]] = {}
    for line in body.splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
            buckets[section] = []
            continue
        if section is not None:
            buckets[section].append(line)
    def section_text(name: str) -> str:
        lines = [ln for ln in buckets.get(name, []) if ln.strip() and ln.strip() != "-"]
        return " ".join(ln.strip("- ").strip() for ln in lines).strip()

    fields["objective"] = section_text("objective") or _heading(body)
    fields["focus"] = section_text("current focus")
    fields["blockers"] = section_text("blockers")
    return fields


def regenerate_active(root: Path) -> None:
    lines = [
        "# Active work",
        "",
        "_Generated from workspace TASK.md metadata. Do not edit by hand._",
        "",
    ]
    active = list_active_workspaces(root)
    if not active:
        lines.append("_No active KB-Brain workspaces._")
    else:
        for ws in active:
            info = parse_task_card(ws)
            lines.append(f"## [{info['id']}](active/{ws.name}/TASK.md)")
            lines.append("")
            lines.append(f"- **Status:** {info['status']}")
            lines.append(f"- **Level:** {info['level']}")
            lines.append(f"- **Lead:** {info['lead'] or '—'}")
            lines.append(f"- **Objective:** {info['objective'] or '—'}")
            lines.append(f"- **Current focus:** {info['focus'] or '—'}")
            lines.append(f"- **Blockers:** {info['blockers'] or '—'}")
            lines.append("")
    write_text(kb_root(root) / "work" / "ACTIVE.md", "\n".join(lines).rstrip() + "\n")


def cmd_index(root: Path, path: str | None) -> int:
    if not kb_root(root).is_dir():
        print("FAIL: kb-brain/ not found — run init first", file=sys.stderr)
        return 2
    if path:
        target = Path(path)
        if not target.is_absolute():
            target = root / target
        if (target / "TASK.md").exists():
            regenerate_workspace_index(target)
            print(f"Indexed workspace {target}")
        else:
            print(f"FAIL: not a workspace path: {path}", file=sys.stderr)
            return 2
    else:
        for ws in list_active_workspaces(root):
            regenerate_workspace_index(ws)
        closed = kb_root(root) / "work" / "closed"
        if closed.is_dir():
            for ws in closed.iterdir():
                if ws.is_dir():
                    regenerate_workspace_index(ws)
        regenerate_active(root)
        regenerate_repo_index(root)
        update_debt_ledger(root)
        print("Regenerated KB-Brain indexes")
    return 0


# ---------------------------------------------------------------------------
# Check / validation
# ---------------------------------------------------------------------------

class CheckReport:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors


def scan_secrets(path: Path, report: CheckReport) -> None:
    try:
        text = read_text(path)
    except UnicodeDecodeError:
        return
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            report.error(f"possible secret pattern in {path}: {pattern.pattern[:40]}...")


def check_frontmatter_record(path: Path, report: CheckReport, require_owner_for_answered: bool = True) -> dict[str, Any]:
    text = read_text(path)
    meta, body = parse_frontmatter(text)
    if not meta:
        report.error(f"{path}: missing YAML frontmatter")
        return {}
    for field in ("id", "type", "status", "author", "created", "updated"):
        if field not in meta or meta[field] in ("", None):
            report.error(f"{path}: missing required frontmatter field '{field}'")
    status = str(meta.get("status", "")).lower()
    if status and status not in VALID_STATUSES:
        report.warn(f"{path}: unusual status '{status}'")
    rid = str(meta.get("id", ""))
    if rid and not ID_RE.match(rid) and not rid.startswith("brief-") and "-context" not in rid and "-assignments" not in rid and "-promotion" not in rid and "-closeout" not in rid and not rid.endswith("-spec"):
        # Allow task ids like 2026-08-04-slug
        if not re.match(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+$", rid):
            report.warn(f"{path}: id '{rid}' does not match expected patterns")

    # Unresolved questions must not look answered without owner/evidence
    if str(meta.get("type")) == "question" and status in ("answered", "resolved", "closed"):
        if require_owner_for_answered:
            if not meta.get("owner") and not meta.get("decision-owner"):
                report.error(f"{path}: answered question lacks owner/decision-owner")
            evidence = meta.get("evidence") or []
            answer_section = "## Answer" in body
            if not evidence and answer_section:
                # Check answer isn't the placeholder
                after = body.split("## Answer", 1)[-1]
                if "Unanswered" in after.split("##", 1)[0]:
                    report.error(f"{path}: question marked {status} but answer is still Unanswered")
                elif not evidence:
                    report.warn(f"{path}: answered question has no evidence links")

    # Lead-only types should carry role: lead when status is confirmatory
    if str(meta.get("type")) in ("decision", "scope-change") and status in ("accepted", "resolved", "done"):
        if meta.get("role") != "lead" and not meta.get("decision-owner"):
            report.error(f"{path}: confirmed {meta.get('type')} lacks role: lead or decision-owner")

    # Relative links
    for match in re.finditer(r"\[([^\]]*)\]\(([^)]+)\)", body):
        href = match.group(2)
        if href.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = (path.parent / href).resolve()
        if not target.exists():
            report.warn(f"{path}: broken relative link ({href})")

    scan_secrets(path, report)
    return meta


def check_workspace(ws: Path, report: CheckReport, sealed: bool = False) -> None:
    task = ws / "TASK.md"
    if not task.exists():
        report.error(f"{ws}: missing TASK.md")
        return
    meta, _ = parse_frontmatter(read_text(task))
    level = str(meta.get("level", DEFAULT_LEVEL))
    if level not in WORKSPACE_LEVELS:
        report.error(f"{task}: invalid level '{level}'")
        level = DEFAULT_LEVEL

    for name in required_workspace_files(level):
        if not (ws / name).exists():
            report.error(f"{ws}: missing required file {name} for level={level}")

    for dirname in required_workspace_dirs(level):
        if not (ws / dirname).is_dir():
            report.error(f"{ws}: missing required directory {dirname}/ for level={level}")

    ids_seen: dict[str, Path] = {}
    for path in iter_markdown_records(ws):
        rec_meta = check_frontmatter_record(path, report)
        rid = str(rec_meta.get("id", ""))
        if rid:
            if rid in ids_seen:
                report.error(f"duplicate id '{rid}' in {ids_seen[rid]} and {path}")
            else:
                ids_seen[rid] = path

    if sealed:
        seal = ws / "SEAL.json"
        if not seal.exists():
            report.error(f"{ws}: closed workspace missing SEAL.json")
        else:
            verify_seal(ws, report)
        if not (ws / "CLOSEOUT.md").exists():
            report.error(f"{ws}: closed workspace missing CLOSEOUT.md")
        # Amendments must point at existing sealed records
        amend_dir = ws / "amendments"
        if amend_dir.is_dir():
            for path in amend_dir.glob("*.md"):
                ameta, _ = parse_frontmatter(read_text(path))
                target = str(ameta.get("amends", "")).strip()
                if not target:
                    report.error(f"{path}: amendment missing 'amends'")
                    continue
                candidate = ws / target
                if not candidate.exists():
                    # try by basename
                    matches = list(ws.rglob(Path(target).name))
                    if not matches:
                        report.error(f"{path}: amends target not found: {target}")


def verify_seal(ws: Path, report: CheckReport) -> None:
    seal_path = ws / "SEAL.json"
    try:
        seal = json.loads(read_text(seal_path))
    except json.JSONDecodeError as exc:
        report.error(f"{seal_path}: invalid JSON ({exc})")
        return
    expected = seal.get("files", {})
    if not isinstance(expected, dict):
        report.error(f"{seal_path}: 'files' must be an object")
        return

    current: dict[str, str] = {}
    for path in ws.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ws).as_posix()
        if rel == "SEAL.json":
            continue
        if rel == "INDEX.md":
            continue
        if rel.startswith("amendments/"):
            continue
        current[rel] = sha256_file(path)

    for rel, digest in expected.items():
        if rel not in current:
            report.error(f"{ws}: sealed file missing or renamed: {rel}")
        elif current[rel] != digest:
            report.error(f"{ws}: sealed file mutated: {rel}")
    for rel in current:
        if rel not in expected:
            report.error(f"{ws}: unsealed new file in closed workspace (use amendments/): {rel}")


def cmd_check(root: Path, path: str | None) -> int:
    if not kb_root(root).is_dir():
        print("FAIL: kb-brain/ not found — run init first", file=sys.stderr)
        return 2

    report = CheckReport()
    kb = kb_root(root)

    for section in TOP_SECTIONS:
        if not (kb / section).exists():
            report.error(f"missing top-level section: {section}/")

    # Permanent section records
    for section in ("decisions", "improvements", "open-questions", "gotchas", "learnings"):
        directory = kb / section
        if not directory.is_dir():
            continue
        ids: dict[str, Path] = {}
        for path in directory.glob("*.md"):
            if path.name in ("INDEX.md", "README.md"):
                continue
            meta = check_frontmatter_record(path, report)
            rid = str(meta.get("id", ""))
            if rid:
                if rid in ids:
                    report.error(f"duplicate id '{rid}' in {ids[rid]} and {path}")
                ids[rid] = path

    debt = kb / "tech-debt"
    if debt.is_dir():
        if not (debt / "LEDGER.md").exists():
            report.error("tech-debt/LEDGER.md missing")
        for path in list(debt.glob("TD-*.md")) + list((debt / "closed").glob("TD-*.md")):
            check_frontmatter_record(path, report)

    # Workspaces
    for ws in list_active_workspaces(root):
        check_workspace(ws, report, sealed=False)
    closed_root = kb / "work" / "closed"
    if closed_root.is_dir():
        for ws in closed_root.iterdir():
            if ws.is_dir():
                check_workspace(ws, report, sealed=True)

    # ACTIVE.md consistency: blockers from TASK.md should appear
    active_md = kb / "work" / "ACTIVE.md"
    if active_md.exists():
        active_text = read_text(active_md)
        for ws in list_active_workspaces(root):
            info = parse_task_card(ws)
            if info.get("blockers") and info["blockers"] not in active_text and info["blockers"] != "—":
                report.warn(f"ACTIVE.md missing blockers text for {ws.name}; regenerate with index")
            if "conflict" in active_text.lower() and "## conflict" in active_text.lower():
                report.error("ACTIVE.md must not list conflicts")

    if path:
        target = Path(path)
        if not target.is_absolute():
            target = (root / target).resolve()
        # path-scoped checks already covered; keep CLI compatible
        _ = target

    for warn in report.warnings:
        print(f"WARN: {warn}")
    for err in report.errors:
        print(f"ERROR: {err}")

    if report.ok:
        print("kb-check: OK")
        return 0
    print(f"kb-check: {len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    return 1


# ---------------------------------------------------------------------------
# Close / seal / amend
# ---------------------------------------------------------------------------

def build_seal(ws: Path) -> dict[str, Any]:
    files: dict[str, str] = {}
    for path in sorted(ws.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ws).as_posix()
        if rel == "SEAL.json" or rel == "INDEX.md" or rel.startswith("amendments/"):
            continue
        files[rel] = sha256_file(path)
    return {
        "version": 1,
        "sealed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_id": ws.name,
        "files": files,
    }


def cmd_close(root: Path, task_id: str, author: str, lead: str) -> int:
    ws = kb_root(root) / "work" / "active" / task_id
    if not ws.is_dir():
        print(f"FAIL: active workspace not found: {task_id}", file=sys.stderr)
        return 2

    # Require promotion tracking present
    if not (ws / "PROMOTION.md").exists():
        print("FAIL: PROMOTION.md missing — complete promotion tracking before close", file=sys.stderr)
        return 2

    created = today()
    if not (ws / "CLOSEOUT.md").exists():
        write_text(
            ws / "CLOSEOUT.md",
            render_template(
                "closeout.md",
                task_id=task_id,
                author=author,
                lead=lead,
                created=created,
            ),
        )

    ensure_dir(ws / "amendments")

    # Mark task closed in TASK.md
    task_path = ws / "TASK.md"
    meta, body = parse_frontmatter(read_text(task_path))
    meta["status"] = "closed"
    meta["updated"] = created
    write_text(task_path, dump_frontmatter(meta, body))

    regenerate_workspace_index(ws)

    # Validate before sealing
    report = CheckReport()
    check_workspace(ws, report, sealed=False)
    # Soft: don't require seal yet
    if report.errors:
        for err in report.errors:
            # Ignore seal-related (not sealed yet)
            if "SEAL.json" in err or "CLOSEOUT.md" in err:
                continue
            print(f"ERROR: {err}")
        # Still allow close if only missing seal — but surface other errors
        real = [e for e in report.errors if "SEAL.json" not in e]
        if real:
            print("FAIL: fix validation errors before closing", file=sys.stderr)
            return 1

    seal = build_seal(ws)
    write_text(ws / "SEAL.json", json.dumps(seal, indent=2, sort_keys=True) + "\n")

    dest_parent = kb_root(root) / "work" / "closed"
    ensure_dir(dest_parent)
    dest = dest_parent / task_id
    if dest.exists():
        print(f"FAIL: closed path already exists: {dest}", file=sys.stderr)
        return 2
    shutil.move(str(ws), str(dest))

    regenerate_active(root)
    regenerate_repo_index(root)
    regenerate_workspace_index(dest)

    # Final seal verification
    report2 = CheckReport()
    check_workspace(dest, report2, sealed=True)
    if report2.errors:
        for err in report2.errors:
            print(f"ERROR: {err}")
        print("FAIL: closed workspace failed seal validation", file=sys.stderr)
        return 1

    print(f"Closed and sealed workspace {task_id} → work/closed/{task_id}")
    return 0


def cmd_amend(root: Path, task_id: str, record_path: str, title: str, author: str, owner: str) -> int:
    ws = kb_root(root) / "work" / "closed" / task_id
    if not ws.is_dir():
        print(f"FAIL: closed workspace not found: {task_id}", file=sys.stderr)
        return 2

    target = Path(record_path)
    if not target.is_absolute():
        candidate = ws / record_path
        if candidate.exists():
            target = candidate
        else:
            matches = list(ws.rglob(Path(record_path).name))
            if len(matches) == 1:
                target = matches[0]
            else:
                print(f"FAIL: cannot resolve record path: {record_path}", file=sys.stderr)
                return 2

    try:
        rel = target.resolve().relative_to(ws.resolve()).as_posix()
    except ValueError:
        print("FAIL: record is not inside the closed workspace", file=sys.stderr)
        return 2

    if rel == "SEAL.json" or rel.startswith("amendments/"):
        print("FAIL: cannot amend SEAL.json or another amendment via this path", file=sys.stderr)
        return 2

    ensure_dir(ws / "amendments")
    rid = next_id(ws / "amendments", "AM")
    slug = slugify(title)[:60]
    path = ws / "amendments" / f"{rid}-{slug}.md"
    content = render_template(
        "amendment.md",
        id=rid,
        title=title,
        author=author,
        owner=owner,
        created=today(),
        amends=rel,
    )
    write_text(path, content)
    regenerate_workspace_index(ws)
    print(f"Created amendment {path.relative_to(root)} (amends {rel})")
    return 0


# ---------------------------------------------------------------------------
# Brief helpers (used by brief-ruminate skill; do not approve specs)
# ---------------------------------------------------------------------------

def cmd_brief_init(root: Path, slug: str, title: str, author: str, owner: str) -> int:
    if not kb_root(root).is_dir():
        print("FAIL: kb-brain/ not found — run init first", file=sys.stderr)
        return 2
    slug = slugify(slug)
    brief_dir = kb_root(root) / "briefs" / slug
    if brief_dir.exists() and (brief_dir / "BRIEF.md").exists():
        print(f"Brief already exists at {brief_dir.relative_to(root)}")
        return 0
    ensure_dir(brief_dir / "milestones")
    write_text(
        brief_dir / "BRIEF.md",
        render_template(
            "BRIEF.md",
            slug=slug,
            title=title or slug.replace("-", " ").title(),
            author=author,
            owner=owner,
            created=today(),
        ),
    )
    write_text(
        brief_dir / "INDEX.md",
        f"# Brief index — {slug}\n\n_No milestones yet._\n",
    )
    regenerate_repo_index(root)
    print(f"Created brief at {brief_dir.relative_to(root)}")
    return 0


def regenerate_brief_index(brief_dir: Path) -> None:
    lines = [f"# Brief index — {brief_dir.name}", "", "| ID | Title | Status | Spec |", "|----|-------|--------|------|"]
    milestones = brief_dir / "milestones"
    specs_root = kb_root(brief_dir.parents[1]) / "specs" / brief_dir.name if brief_dir.parents[1].name == "kb-brain" else brief_dir.parents[2] / "specs" / brief_dir.name
    # brief_dir = kb-brain/briefs/<slug>
    kb = brief_dir.parent.parent
    specs_root = kb / "specs" / brief_dir.name
    if milestones.is_dir():
        for path in sorted(milestones.glob("M-*.md")):
            meta, body = parse_frontmatter(read_text(path))
            rid = str(meta.get("id", path.stem))
            status = str(meta.get("status", ""))
            title = _heading(body) or path.stem
            spec = ""
            if specs_root.is_dir():
                matches = list(specs_root.glob(f"{rid}-*-spec.md")) + list(specs_root.glob(f"{rid}-spec.md"))
                if matches:
                    spec = matches[0].relative_to(kb).as_posix()
            lines.append(f"| {rid} | {title} | {status} | {spec or '—'} |")
    if len(lines) == 4:
        lines = [f"# Brief index — {brief_dir.name}", "", "_No milestones yet._"]
    write_text(brief_dir / "INDEX.md", "\n".join(lines) + "\n")


def cmd_brief_milestone(root: Path, brief_slug: str, title: str, author: str, owner: str) -> int:
    brief_dir = kb_root(root) / "briefs" / slugify(brief_slug)
    if not (brief_dir / "BRIEF.md").exists():
        print(f"FAIL: brief not found: {brief_slug}", file=sys.stderr)
        return 2
    ensure_dir(brief_dir / "milestones")
    rid = next_id(brief_dir / "milestones", "M")
    slug = slugify(title)[:60]
    path = brief_dir / "milestones" / f"{rid}-{slug}.md"
    write_text(
        path,
        render_template(
            "MILESTONE.md",
            id=rid,
            title=title,
            author=author,
            owner=owner,
            created=today(),
        ),
    )
    regenerate_brief_index(brief_dir)
    print(f"Created milestone {path.relative_to(root)}")
    return 0


def cmd_brief_spec(root: Path, brief_slug: str, milestone_id: str, author: str, owner: str) -> int:
    """Create a candidate milestone spec with status review-needed. Never approved."""
    brief_slug = slugify(brief_slug)
    brief_dir = kb_root(root) / "briefs" / brief_slug
    if not (brief_dir / "BRIEF.md").exists():
        print(f"FAIL: brief not found: {brief_slug}", file=sys.stderr)
        return 2

    matches = list((brief_dir / "milestones").glob(f"{milestone_id}-*.md"))
    matches += list((brief_dir / "milestones").glob(f"{milestone_id}.md"))
    if not matches:
        print(f"FAIL: milestone not found: {milestone_id}", file=sys.stderr)
        return 2
    milestone_path = matches[0]
    meta, body = parse_frontmatter(read_text(milestone_path))
    title = _heading(body) or milestone_id

    # Refuse if somehow asked to write approved
    specs_dir = kb_root(root) / "specs" / brief_slug
    ensure_dir(specs_dir)
    slug = slugify(title)[:60]
    spec_path = specs_dir / f"{milestone_id}-{slug}-spec.md"
    if spec_path.exists():
        existing_meta, _ = parse_frontmatter(read_text(spec_path))
        if str(existing_meta.get("status")) == "approved-spec":
            print("FAIL: refusing to overwrite an approved specification", file=sys.stderr)
            return 2
        print(f"Candidate spec already exists at {spec_path.relative_to(root)}")
        return 0

    content = render_template(
        "MILESTONE-SPEC.md",
        id=milestone_id,
        title=title,
        author=author,
        owner=owner,
        created=today(),
    )
    # Hard-enforce review-needed in the written file
    if "approved-spec" in content and "Human approval" not in content:
        print("FAIL: template unexpectedly contains approved-spec", file=sys.stderr)
        return 2
    write_text(spec_path, content)

    # Advance milestone status only as far as review-needed
    meta["status"] = "review-needed"
    meta["updated"] = today()
    write_text(milestone_path, dump_frontmatter(meta, body))
    regenerate_brief_index(brief_dir)
    regenerate_repo_index(root)
    print(f"Created candidate spec {spec_path.relative_to(root)} (status=review-needed)")
    print("Human approval required before planning or implementation.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="KB-Brain tooling")
    parser.add_argument("--root", type=Path, default=None, help="Repository root (default: auto-detect)")
    parser.add_argument("--author", default="agent", help="Author metadata")
    parser.add_argument("--owner", default="task-lead", help="Owner metadata")
    parser.add_argument("--lead", default="task-lead", help="Lead metadata for workspaces")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize kb-brain/ structure")
    p_init.add_argument("level", nargs="?", default=DEFAULT_LEVEL, choices=WORKSPACE_LEVELS)

    p_start = sub.add_parser("start", help="Start a task workspace")
    p_start.add_argument("slug")
    p_start.add_argument("level", nargs="?", default=None, choices=WORKSPACE_LEVELS)

    p_new = sub.add_parser("new", help="Create an atomic record")
    p_new.add_argument("section")
    p_new.add_argument("title")
    p_new.add_argument("--task", default=None)

    p_index = sub.add_parser("index", help="Regenerate indexes")
    p_index.add_argument("path", nargs="?", default=None)

    p_check = sub.add_parser("check", help="Validate KB-Brain structure and seals")
    p_check.add_argument("path", nargs="?", default=None)

    p_close = sub.add_parser("close", help="Close, seal, and archive a workspace")
    p_close.add_argument("task_id")

    p_amend = sub.add_parser("amend", help="Amend a sealed closed workspace")
    p_amend.add_argument("task_id")
    p_amend.add_argument("record_path")
    p_amend.add_argument("title")

    p_bi = sub.add_parser("brief-init", help="Scaffold a human-owned brief")
    p_bi.add_argument("slug")
    p_bi.add_argument("title", nargs="?", default="")

    p_bm = sub.add_parser("brief-milestone", help="Add a milestone under a brief")
    p_bm.add_argument("brief_slug")
    p_bm.add_argument("title")

    p_bs = sub.add_parser("brief-spec", help="Create a review-needed candidate milestone spec")
    p_bs.add_argument("brief_slug")
    p_bs.add_argument("milestone_id")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = (args.root or repo_root_from_cwd()).resolve()

    if args.command == "init":
        return cmd_init(root, args.level)
    if args.command == "start":
        return cmd_start(root, args.slug, args.level, args.lead, args.author)
    if args.command == "new":
        return cmd_new(root, args.section, args.title, args.task, args.author, args.owner)
    if args.command == "index":
        return cmd_index(root, args.path)
    if args.command == "check":
        return cmd_check(root, args.path)
    if args.command == "close":
        return cmd_close(root, args.task_id, args.author, args.lead)
    if args.command == "amend":
        return cmd_amend(root, args.task_id, args.record_path, args.title, args.author, args.owner)
    if args.command == "brief-init":
        return cmd_brief_init(root, args.slug, args.title, args.author, args.owner)
    if args.command == "brief-milestone":
        return cmd_brief_milestone(root, args.brief_slug, args.title, args.author, args.owner)
    if args.command == "brief-spec":
        return cmd_brief_spec(root, args.brief_slug, args.milestone_id, args.author, args.owner)
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
