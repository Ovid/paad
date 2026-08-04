---
name: kb-brain
description: Maintain a repository-native working knowledge base for humans and coding agents. Use when initializing kb-brain, starting or closing task workspaces, recording durable context, decisions, findings, failures, questions, improvements, technical debt, handoffs, or amendments, and when coordinating lead agents and sub-agents through shared project memory.
---

**On invocation:** announce "Running paad:kb-brain v1.24.1" before anything else.

# KB-Brain

Repository-native working knowledge for humans, lead agents, and sub-agents.
Stable architecture and accepted documentation stay in `docs/`. Mutable
context, in-flight decisions, gaps, debt, lessons, and focused task workspaces
live under `kb-brain/`.

This skill does **not** change the behaviour of `pushback`, `alignment`,
`agentic-review`, or any other existing PAAD skill. Invoke it explicitly (or
via repository `AGENTS.md` instructions).

Load details on demand from:

- `references/structure.md` — directory layout, workspace levels, file roles
- `references/routing.md` — when to write, where to put it, AGENTS.md snippet
- `references/lifecycle.md` — start, close, seal, amend, validation
- `references/templates.md` — atomic record templates and ID prefixes

Bundled templates live in this skill's `templates/` directory. Deterministic
tooling is `scripts/kb_brain.py` (copied into the target repo on `init`).

**Dispatch:**

```dot
digraph kb_brain_dispatch {
    "Action known?" [shape=diamond];
    "kb-brain/ exists?" [shape=diamond];
    "Which action?" [shape=diamond];
    "Durable enough to write?" [shape=diamond];
    "Level below repo default?" [shape=diamond];
    "Human approved lower level?" [shape=diamond];
    "Promotion + closeout ready?" [shape=diamond];
    "Validation clean?" [shape=diamond];

    "Infer from conversation or show operation summary and ASK" [shape=box];
    "init scaffold (no docs ingest)" [shape=box];
    "STOP: run init first" [shape=box, style=bold];
    "start workspace" [shape=box];
    "STOP: refuse lower level without approval" [shape=box, style=bold];
    "record / route to section or workspace" [shape=box];
    "Keep in session only" [shape=box];
    "status / index / check" [shape=box];
    "close → seal → move to work/closed" [shape=box];
    "STOP: finish promotion/closeout or fix check errors" [shape=box, style=bold];
    "amend under amendments/ only" [shape=box];
    "Announce files written or updated" [shape=box];
    "Done" [shape=box];

    "Action known?" -> "Which action?" [label="yes"];
    "Action known?" -> "Infer from conversation or show operation summary and ASK" [label="no"];
    "Infer from conversation or show operation summary and ASK" -> "Action known?";

    "Which action?" -> "init scaffold (no docs ingest)" [label="init"];
    "Which action?" -> "kb-brain/ exists?" [label="other"];
    "kb-brain/ exists?" -> "STOP: run init first" [label="no"];
    "kb-brain/ exists?" -> "Level below repo default?" [label="yes + start"];
    "kb-brain/ exists?" -> "Durable enough to write?" [label="yes + record/route"];
    "kb-brain/ exists?" -> "status / index / check" [label="yes + status|index|check"];
    "kb-brain/ exists?" -> "Promotion + closeout ready?" [label="yes + close"];
    "kb-brain/ exists?" -> "amend under amendments/ only" [label="yes + amend"];

    "Level below repo default?" -> "Human approved lower level?" [label="yes"];
    "Level below repo default?" -> "start workspace" [label="no"];
    "Human approved lower level?" -> "start workspace" [label="yes"];
    "Human approved lower level?" -> "STOP: refuse lower level without approval" [label="no"];

    "Durable enough to write?" -> "record / route to section or workspace" [label="yes"];
    "Durable enough to write?" -> "Keep in session only" [label="no"];

    "Promotion + closeout ready?" -> "Validation clean?" [label="yes"];
    "Promotion + closeout ready?" -> "STOP: finish promotion/closeout or fix check errors" [label="no"];
    "Validation clean?" -> "close → seal → move to work/closed" [label="yes"];
    "Validation clean?" -> "STOP: finish promotion/closeout or fix check errors" [label="no"];

    "init scaffold (no docs ingest)" -> "Announce files written or updated";
    "start workspace" -> "Announce files written or updated";
    "record / route to section or workspace" -> "Announce files written or updated";
    "Keep in session only" -> "Done";
    "status / index / check" -> "Announce files written or updated";
    "close → seal → move to work/closed" -> "Announce files written or updated";
    "amend under amendments/ only" -> "Announce files written or updated";
    "Announce files written or updated" -> "Done";
}
```

## Global rules

1. **Human authority.** Agents may record observations, evidence, failures,
   questions, improvements, debt, handoffs, and working context. They must
   **not** silently promote inferred requirements, unapproved architecture,
   invented answers to open questions, improvements-as-roadmap, or candidate
   specs to accepted facts. Confirmed decisions need explicit human
   confirmation or unambiguous repository evidence — record owner and evidence.
2. **Notice broadly, work narrowly.** Out-of-scope gaps become atomic
   improvement or tech-debt records. Do not implement them unless the active
   task includes them.
3. **Index-first retrieval.** Read `kb-brain/work/ACTIVE.md`, then the
   workspace `TASK.md`, indexes, `CONTEXT.md`, assignment, then only linked
   records. Never load the whole KB by default.
4. **No unsolicited bulk ingress.** Do not dump `docs/` into `kb-brain/` on
   init or during ordinary work.
5. **Existing skills unchanged.** Do not wire automatic KBB reads/writes into
   other PAAD skills.

## Tooling

After `init`, the target repo has `scripts/kb_brain.py` and Make targets
(`kb-index`, `kb-new`, `kb-check`, plus `kb-start` / `kb-close` / `kb-amend`).
Prefer:

```bash
python3 scripts/kb_brain.py init standard
python3 scripts/kb_brain.py start <slug> [level]
python3 scripts/kb_brain.py new <section> "<title>" [--task <id>]
python3 scripts/kb_brain.py index
python3 scripts/kb_brain.py check
python3 scripts/kb_brain.py close <task-id>
python3 scripts/kb_brain.py amend <closed-task-id> <record-path> "<title>"
```

Until `init` has run in the target repo, invoke the bundled copy:

`python3 <path-to-this-skill>/scripts/kb_brain.py --root <repo> …`

If the target has no Makefile, `init` writes `kb-brain/Makefile.inc` instead
of replacing project build tooling.

## Operations

### init

Scaffold `kb-brain/` (see `references/structure.md`). Copy templates. Install
script + Make block. Default level is `standard` unless overridden. **Do not**
ingest existing documentation.

### start

Create `kb-brain/work/active/YYYY-MM-DD-<slug>/` with level-appropriate files.
Collision-safe IDs (`-2`, `-3`, …). Raise above repo default freely; lowering
requires explicit human approval. Regenerate `ACTIVE.md` and indexes.

### record / route

Apply the durability test in `references/routing.md`. Search indexes before
creating duplicates. Allocate the next ID by inspecting the target directory
(no shared counter file). Sub-agents may append findings, questions, failures,
conflicts, handoffs, improvements, and tech-debt. Only the lead or human task
owner may change scope, lifecycle, assignments, confirmed decisions, blockers,
conflict resolution, or close/seal.

### status / index / check

`status` summarizes active work from `ACTIVE.md` / `TASK.md`. `index`
regenerates indexes. `check` validates structure, frontmatter, IDs, seals, and
amendments — report **all** safe-to-collect errors in one run.

### close

Final cleanup → promote durable knowledge → `CLOSEOUT.md` → index → validate →
`SEAL.json` (SHA-256 of historical files, excluding seal, generated `INDEX.md`,
and `amendments/`) → move to `work/closed/`. Do not erase substantive failures
or disagreements to “clean up” history.

### amend

After closure, never edit sealed originals. Create
`work/closed/<task-id>/amendments/AM-…md` that names what it corrects.
Regenerated indexes must mark amended records.

## Conflict protocol

Record conflicting findings; never overwrite. When a conflict affects current
work, the lead sets `resolved`, `deferred`, or `blocked` (and adds blockers to
`TASK.md` so they appear in `ACTIVE.md`). Unrelated conflicts stay recorded
and do not block the current assignment. `ACTIVE.md` lists ownership and
blockers — **not** conflicts.

## Announce What You Wrote

Before any summary, list every path this run created or updated:

```
Files written or updated:
  new      kb-brain/work/active/2026-08-04-auth-migration/TASK.md
  updated  kb-brain/work/ACTIVE.md
```

Source and test files outside `kb-brain/` need only a count and a pointer to
the diff when there are many. Skills that write nothing are exempt; this skill
almost always writes.

## Common Mistakes

| Mistake | What to do instead |
|---------|-------------------|
| Dumping `docs/` into KBB on init | Init scaffolds empty sections only |
| Reading the whole KB every turn | Index-first retrieval order |
| Inventing answers in `open-questions/` | Add evidence; leave unanswered |
| Editing a sealed closed workspace | Write an amendment |
| Lowering workspace level silently | Get explicit human approval |
| Auto-wiring KBB into other PAAD skills | Leave those skills unchanged |
| Implementing every improvement you notice | Record it; stay in task scope |
