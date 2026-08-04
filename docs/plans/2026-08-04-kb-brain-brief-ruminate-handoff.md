# PAAD KB-Brain and Brief Rumination
## Implementation Handoff for a Coding Agent

**Prepared:** 4 August 2026  
**Target repository:** `Ovid/paad`  
**Delivery goal:** Produce a focused pull request adding two standalone PAAD skills without changing the behaviour of existing skills.

---

## 1. Executive summary

Implement two related but independently callable capabilities:

1. **`kb-brain`**: a repository-native, human-readable working knowledge base shared by humans, lead agents, and sub-agents. It records context, decisions, failures, working memory, technical debt, improvements, questions, and durable lessons. It also provides a focused task workspace that reduces sub-agent drift without requiring agents to load a long shared journal.
2. **`brief-ruminate`**: a brief-to-milestone-spec workflow. A human owns and writes the high-level project brief. PAAD reads the brief, repository, and KB-Brain context, then expands one milestone into a reviewable working specification. It does not approve the specification, plan implementation, or modify existing PAAD review skills.

The features must remain isolated. Do not add automatic KBB behaviour to `pushback`, `alignment`, `agentic-review`, or any other existing skill. Users and agents invoke the new skills explicitly or direct agents to use them through their repository `AGENTS.md`.

---

## 2. Source constraints and existing PAAD conventions

The PAAD repository is a Claude Code plugin marketplace whose canonical skill sources live under:

```text
plugins/paad/skills/<skill-name>/SKILL.md
```

Follow the current repository conventions documented in `CLAUDE.md`:

- skill folder names become `/paad:<skill-name>` commands;
- each skill requires YAML frontmatter with `name` and `description`;
- positional arguments should be intuitive;
- every skill except `help` needs a complete Graphviz `dot` decision-flow diagram;
- update the root README and `/paad:help` documentation;
- keep plugin and marketplace versions synchronized;
- run the repository's complete test and plugin-validation suite;
- use the repository's existing generation process for platform mirrors rather than independently editing generated copies.

The supplied KB prototype establishes this source-of-truth split:

- `docs/`: stable architecture, protocol, and accepted documentation source of truth.
- `kb-brain/`: mutable working knowledge, active context, in-flight decisions, gaps, debt, and agent memory.

Do not duplicate stable architecture documentation in `kb-brain/`. Working notes that refine or challenge stable documentation belong in `kb-brain/architecture/` and must link back to the stable source. Never invent answers for entries in `open-questions/`.

---

## 3. Global product rules

These requirements apply to both new skills.

### 3.1 Human authority

Agents may autonomously record observations, evidence, failures, questions, proposed improvements, technical debt, handoffs, and working context.

Agents must not silently convert any of the following into accepted facts:

- an inferred product requirement;
- an unapproved architectural direction;
- an answer to an unresolved question;
- a suggested improvement promoted to roadmap scope;
- a candidate specification marked as approved.

Confirmed decisions require either explicit human confirmation or unambiguous existing repository evidence. Record the owner and evidence.

### 3.2 Notice broadly, work narrowly

An agent may notice useful work outside its current scope and write an atomic improvement or technical-debt record. It must not implement that work unless the active task includes it.

### 3.3 Index-first retrieval

Agents must not read the entire KB by default. The normal read order is:

1. `kb-brain/work/ACTIVE.md`
2. the selected workspace's `TASK.md`
3. `INDEX.md`
4. `CONTEXT.md`
5. the agent's relevant assignment
6. only linked or relevant atomic records

This rule exists to avoid context rot and unnecessary token use.

### 3.4 No unsolicited bulk ingress

Bulk ingress from `docs/` or other existing documentation is a dedicated operation. Do not dump architecture documents into the KB during initialization or ordinary work.

### 3.5 Existing skills remain unchanged

Do not modify existing PAAD skills to write to or read from KBB automatically. Documentation may mention that the new skills can be used alongside existing workflows, but their behaviour and execution flows must remain unchanged.

---

# Part A — `kb-brain`

## 4. Skill purpose and activation

Create a standalone `/paad:kb-brain` skill that:

- initializes the KBB structure in a target repository;
- routes human and agent knowledge to the correct section;
- starts, updates, closes, indexes, validates, and amends task workspaces;
- supplies reusable templates for humans and agents;
- enforces the authority, lifecycle, and immutability rules in this specification;
- supports sub-agent alignment through focused shared task files.

Recommended frontmatter description:

```yaml
---
name: kb-brain
description: Maintain a repository-native working knowledge base for humans and coding agents. Use when initializing kb-brain, starting or closing task workspaces, recording durable context, decisions, findings, failures, questions, improvements, technical debt, handoffs, or amendments, and when coordinating lead agents and sub-agents through shared project memory.
---
```

## 5. Arguments and callable operations

Use one positional action followed by intuitive positional values. Avoid a large flag surface.

```text
/paad:kb-brain init [minimal|standard|strict]
/paad:kb-brain start <task-slug> [minimal|standard|strict]
/paad:kb-brain record <section> [title]
/paad:kb-brain status [task-id]
/paad:kb-brain index [task-id]
/paad:kb-brain check [path]
/paad:kb-brain close [task-id]
/paad:kb-brain amend <closed-task-id> <record-path>
/paad:kb-brain route <description-of-knowledge>
```

Natural-language invocations must work as well, for example:

- “Use kb-brain to record the parser failure.”
- “Start a strict KBB workspace for the authentication migration.”
- “Where should this decision be stored?”
- “Close and seal the current KBB workspace.”

If no action is supplied, infer the requested operation from conversation context. When it cannot be inferred safely, display the operation summary and ask for one choice.

## 6. Project-local KBB structure

Initialization creates the following project-local structure. Do not create empty atomic records.

```text
kb-brain/
├── README.md
├── INDEX.md
├── decisions/
├── architecture/
├── domains/
├── runbooks/
├── gotchas/
├── briefs/
├── specs/
├── plans/
├── reviews/
├── learnings/
├── open-questions/
├── agents/
├── improvements/
├── tech-debt/
│   ├── LEDGER.md
│   └── closed/
├── templates/
└── work/
    ├── ACTIVE.md
    ├── active/
    └── closed/
```

`README.md` should retain the supplied section descriptions and add `briefs/`, templates, workspace behaviour, closure, and amendment rules.

### 6.1 Permanent section meanings

- `decisions/` — accepted ADR-style decisions with owner and evidence.
- `architecture/` — mutable notes that refine, question, or compare against stable architecture in `docs/`.
- `domains/` — product and business domain knowledge.
- `runbooks/` — recurring procedures that are useful but not yet stable documentation.
- `gotchas/` — sharp edges, false starts, and reliable warnings.
- `briefs/` — human-owned briefs and atomic milestone records.
- `specs/` — active working specifications, including candidate milestone expansions.
- `plans/` — implementation plans tied to approved specs.
- `reviews/` — review outputs worth preserving beyond their originating session.
- `learnings/` — post-hoc lessons and retrospectives.
- `open-questions/` — unresolved questions; agents may add evidence but not invent answers.
- `agents/` — repository-specific agent behaviour and coordination notes.
- `improvements/` — one atomic file per noticed gap or opportunity.
- `tech-debt/` — open debt records and `LEDGER.md`; resolved entries move to `tech-debt/closed/`.

## 7. Always-present task workspace

Every PAAD-managed task receives a KBB workspace, regardless of size. The repository `AGENTS.md` selects the default detail level. A task may raise its level, but lowering it below the repository default requires explicit human approval.

### 7.1 Workspace levels

**`minimal`**

Required:

- task scope and status;
- compact context;
- ownership;
- final handoff;
- durable findings selected for promotion.

**`standard` — recommended default**

Adds:

- assignments;
- findings and evidence;
- questions;
- failures and abandoned approaches;
- confirmed decisions;
- conflicts;
- handoffs;
- promotion tracking.

**`strict`**

Adds:

- explicit assumptions;
- dependency records;
- decision ownership;
- scope-change records;
- mandatory evidence references;
- detailed conflict handling;
- completion and promotion checks.

All levels use focused files and atomic record directories. Do not implement a single append-only workspace journal.

### 7.2 Active workspace structure

```text
kb-brain/work/active/<task-id>/
├── TASK.md
├── INDEX.md
├── CONTEXT.md
├── ASSIGNMENTS.md
├── PROMOTION.md
├── decisions/
├── findings/
├── questions/
├── failures/
├── conflicts/
├── handoffs/
├── assumptions/       # mandatory only in strict
├── dependencies/      # mandatory only in strict
└── scope-changes/     # mandatory only in strict
```

The task ID should be stable, human-readable, and collision-resistant. Recommended format:

```text
YYYY-MM-DD-<short-slug>
```

If a second task would use the same ID, append `-2`, `-3`, and so on.

### 7.3 File responsibilities

**`TASK.md`** is the authoritative task card. It contains:

- objective;
- scope;
- non-goals;
- completion criteria;
- workspace level;
- lead owner;
- lifecycle status;
- current focus;
- blockers;
- controlling brief, spec, issue, or plan links.

**`INDEX.md`** is generated. It lists all atomic records grouped by type, status, owner, and relationship. It must include amendment markers for closed workspaces.

**`CONTEXT.md`** is compact shared working memory needed by most participants. Keep it brief. Move detailed material to atomic records and link it.

**`ASSIGNMENTS.md`** is lead-controlled and records each human or agent assignment, boundary, dependencies, and status.

**`PROMOTION.md`** tracks durable information that must move into permanent KBB sections or stable `docs/` before closure.

## 8. Agent permissions and sub-agent alignment

Use the agreed hybrid model.

### 8.1 Sub-agents may append

Sub-agents may autonomously create atomic records for:

- findings and evidence;
- questions;
- failures and abandoned approaches;
- conflicts;
- handoffs;
- suggested improvements;
- technical debt.

### 8.2 Lead-only changes

Only the lead agent or human task owner may change:

- task scope or non-goals;
- task lifecycle status;
- assignments and ownership;
- confirmed decisions;
- blocker disposition;
- conflict resolution status;
- workspace closure and sealing.

This is primarily a governed workflow, not a security sandbox. The skill instructions and validation should make unauthorized changes visible. Where practical, require `role: lead` metadata for privileged record changes and detect invalid ownership transitions during `kb-check`.

### 8.3 Conflict protocol

Conflicting findings are recorded, never overwritten.

When a conflict pertains to current work, address it during the current session. The lead records one of three outcomes:

- `resolved` — evidence or a human decision establishes the controlling conclusion;
- `deferred` — the conflict is real but safely outside the current bounded task; record why and where it will be handled;
- `blocked` — work cannot safely continue; add the blocker to `TASK.md` so it appears in `ACTIVE.md`.

Unrelated conflicts remain recorded and do not block the current assignment.

## 9. Repository-level active work summary

Generate:

```text
kb-brain/work/ACTIVE.md
```

This file is an inexpensive repository-wide overview. It contains only:

- active task ID and link;
- status;
- workspace level;
- lead/owner;
- objective;
- current focus;
- blockers.

Do not list conflicts in `ACTIVE.md`. Conflicts are reviewed inside the relevant workspace when they affect the current work.

`ACTIVE.md` must be generated from task workspace metadata. Do not permit manually authored narrative that can drift.

## 10. Atomic records and templates

Provide templates that can be used by both humans and agents. Store distributable templates with the skill and copy project-local versions into `kb-brain/templates/` during initialization.

### 10.1 Common frontmatter

Use YAML frontmatter for atomic records:

```yaml
---
id: F-001
type: finding
status: open
author: agent-parser-review
owner: task-lead
created: 2026-08-04
updated: 2026-08-04
related:
  - questions/Q-002-import-order.md
  - src/parser/imports.ts
---
```

Required common fields:

- `id`
- `type`
- `status`
- `author`
- `created`
- `updated`

Add `owner`, `related`, `evidence`, `supersedes`, `amends`, or `decision-owner` where applicable.

IDs are scoped to a workspace or permanent section and use prefixes:

- Decision: `D-`
- Finding: `F-`
- Question: `Q-`
- Failure: `X-`
- Conflict: `C-`
- Handoff: `H-`
- Improvement: `I-`
- Technical debt: `TD-`
- Assumption: `A-`
- Dependency: `DEP-`
- Scope change: `SC-`
- Amendment: `AM-`
- Milestone: `M-`

Allocate the next numeric ID by inspecting the relevant directory. Avoid a shared mutable counter file that causes concurrent-write contention.

### 10.2 Required templates

Provide at least:

- task card;
- context;
- assignments;
- finding;
- decision;
- question;
- failure;
- conflict;
- handoff;
- improvement;
- technical debt;
- assumption;
- dependency;
- scope change;
- promotion;
- closeout;
- amendment;
- human project brief;
- milestone;
- candidate milestone specification.

### 10.3 Improvement template

```markdown
# <Improvement title>

## Observed during
<Task, branch, issue, spec, or command>

## Observation
<What was noticed>

## Evidence
<Files, behaviour, tests, logs, or history>

## Why it matters
<Likely consequence if unchanged>

## Possible direction
<Unapproved proposal>

## Relationship to current work
<Why it is not being implemented now>
```

### 10.4 Conflict template

```markdown
# <Conflict title>

## Position A
<First conclusion or assumption>

## Position B
<Conflicting conclusion or assumption>

## Evidence
<Links to findings, code, tests, and documentation>

## Impact
<Why this matters>

## Required resolution
<Specific evidence or decision needed>

## Resolution
<Lead-controlled: unresolved, resolved, deferred, or blocked>
```

## 11. Autonomous write routing

The skill must decide whether a note is durable enough to write. Use this test:

> Will this information materially help a future developer understand, decide, avoid a failure, or continue unfinished work?

If no, keep it in session context and do not create a file.

If yes, route it by intent:

- accepted choice and rationale → `decisions/`;
- mutable architectural reasoning → `architecture/`;
- product/domain fact → `domains/`;
- recurring procedure → `runbooks/`;
- sharp edge or false start → `gotchas/`;
- unresolved decision → `open-questions/`;
- out-of-scope opportunity → `improvements/`;
- remediation liability → `tech-debt/` and `LEDGER.md`;
- task-specific evidence or working state → current workspace;
- stable accepted documentation → propose or perform promotion to `docs/`, then link from KBB.

Avoid duplicate records. Search indexes and relevant titles before creating a new entry. Append evidence to an active compatible record when appropriate; create a new record when the conclusion, scope, owner, or lifecycle differs.

## 12. Tooling

The project-local KB README promises:

```bash
make kb-index
make kb-new SECTION=… TITLE=…
make kb-check
```

Implement deterministic, dependency-light tooling using the repository's established scripting language. If no convention controls this choice, use Python 3 standard library.

Recommended project-local script surface:

```text
scripts/kb_brain.py init [level]
scripts/kb_brain.py start <task-slug> [level]
scripts/kb_brain.py new <section> <title> [--task <id>]
scripts/kb_brain.py index [path]
scripts/kb_brain.py check [path]
scripts/kb_brain.py close <task-id>
scripts/kb_brain.py amend <closed-task-id> <record-path> <title>
```

Initialization should add Makefile targets only through a clearly marked, idempotent block. If no Makefile exists, create `kb-brain/Makefile.inc` and document how to include it rather than replacing project build tooling.

At minimum expose:

```make
kb-index:
	python3 scripts/kb_brain.py index

kb-new:
	python3 scripts/kb_brain.py new "$(SECTION)" "$(TITLE)"

kb-check:
	python3 scripts/kb_brain.py check
```

Additional targets may include `kb-start`, `kb-close`, and `kb-amend`.

All operations must be idempotent where reasonable and fail clearly without destructive partial changes.

## 13. Closing, sealing, and amendments

### 13.1 Final cleanup

Immediately before closing, the lead may:

- remove empty placeholders and accidental duplicate files;
- repair metadata and broken links;
- update statuses, ownership, and final context;
- remove accidentally captured secrets or sensitive transient output;
- complete `PROMOTION.md` and `CLOSEOUT.md`;
- regenerate indexes;
- run validation.

Do not erase substantive failures, disagreements, abandoned approaches, or evidence to make the history appear cleaner.

### 13.2 Closure flow

```text
active work
→ final cleanup
→ durable knowledge promotion
→ closeout generation
→ index regeneration
→ validation
→ seal creation
→ move to work/closed/
→ immutable
```

A closed workspace retains the same atomic structure and additionally contains:

```text
CLOSEOUT.md
SEAL.json
amendments/
```

### 13.3 Immutability enforcement

Generate `SEAL.json` containing SHA-256 hashes of every historical workspace file at closure, excluding:

- `SEAL.json` itself;
- generated `INDEX.md`;
- files under `amendments/`.

`kb-check` must report any mutation, removal, or rename of sealed files. It may regenerate `INDEX.md` and accept new valid amendment files without invalidating the seal.

### 13.4 Amendments

After closure, never edit, rename, or delete original records. Create an atomic amendment under:

```text
kb-brain/work/closed/<task-id>/amendments/
```

An amendment must identify what it corrects, clarifies, or supersedes, explain why, link new evidence, and state impact. Regenerated indexes must visibly mark amended records.

---

# Part B — `brief-ruminate`

## 14. Skill purpose and activation

Create a separate `/paad:brief-ruminate` skill. It depends on a KBB structure being present but does not modify `kb-brain` skill logic or any existing PAAD skill.

Purpose:

- preserve the human-written project brief as controlling intent;
- track its milestones atomically;
- use repository and KBB evidence to expand one milestone at a time;
- produce a candidate specification for human review;
- record consequential questions, assumptions, dependencies, and conflicts;
- stop before approval, planning, or implementation.

Recommended frontmatter:

```yaml
---
name: brief-ruminate
description: Expand a human-owned project brief or selected milestone into a repository-grounded candidate specification using KB-Brain context. Use when creating or reviewing project milestones, identifying dependencies and unresolved decisions, or preparing a milestone specification for human approval before pushback, planning, alignment, or implementation.
---
```

## 15. Arguments

```text
/paad:brief-ruminate <brief-path>
/paad:brief-ruminate <brief-path> <milestone-id>
/paad:brief-ruminate next <brief-path>
/paad:brief-ruminate status <brief-path>
```

Without a milestone ID, inspect the brief and milestone index, then recommend the next milestone that is both valuable and sufficiently unblocked. Do not select a milestone solely because it appears first.

## 16. Brief and milestone storage

Use atomic storage:

```text
kb-brain/briefs/<brief-slug>/
├── BRIEF.md
├── INDEX.md
└── milestones/
    ├── M-001-<slug>.md
    ├── M-002-<slug>.md
    └── ...

kb-brain/specs/<brief-slug>/
└── M-001-<slug>-spec.md
```

The human owns `BRIEF.md`. Agents may suggest amendments but must not silently rewrite the brief's intent, outcomes, constraints, or non-goals.

## 17. Brief template

A brief should remain product-level and implementation-light:

```markdown
# <Project or feature brief>

## Intended outcome
<What should become possible>

## Users and stakeholders
<Who benefits or is affected>

## Why it matters
<Value, problem, or risk addressed>

## Constraints
<Hard boundaries>

## Non-goals
<Explicit exclusions>

## Success at project level
<Observable outcomes>

## Known milestone ideas
<Initial human-authored decomposition; may be incomplete>

## Open questions
<Questions the human has intentionally left unresolved>
```

## 18. Milestone lifecycle

Use these explicit states:

```text
brief
→ incubating
→ ready-for-expansion
→ expanding
→ review-needed
→ approved-spec
→ planned
→ in-progress
→ completed
→ superseded
```

The skill may move a milestone as far as `review-needed`. Only a human may mark it `approved-spec`.

Existing PAAD skills can then be invoked separately:

```text
approved specification
→ pushback
→ implementation planning
→ alignment
→ implementation
→ agentic-review
```

Do not auto-run or modify those skills.

## 19. Rumination workflow

For one selected milestone:

1. Read `BRIEF.md`, its milestone record, and the brief index.
2. Read `kb-brain/work/ACTIVE.md` to identify ownership or blockers relevant to the milestone.
3. Read the relevant repository files, stable documentation, KBB indexes, decisions, questions, failures, and gotchas.
4. Check whether previous decisions constrain the milestone.
5. Identify dependencies, conflicts, assumptions, compatibility concerns, data implications, operational concerns, and non-goals.
6. Determine whether the milestone is independently valuable and reasonably scoped.
7. If it is oversized, propose an atomic milestone split without changing the human brief automatically.
8. Ask only consequential questions that materially change scope or behaviour.
9. Write a candidate milestone spec with status `review-needed`.
10. Link all supporting and unresolved KBB records.
11. Update the milestone index and stop for human review.

Do not “ruminate” indefinitely or repeatedly rewrite a candidate spec without new evidence or human direction.

## 20. Candidate milestone specification template

```markdown
# <Milestone title>

## Status
review-needed

## Brief linkage
<Brief path and milestone ID>

## Outcome
<Concrete result delivered by this milestone>

## Scope
<Included behaviour>

## Non-goals
<Excluded behaviour>

## User and system behaviour
<Observable behaviours and flows>

## Constraints and controlling decisions
<Hard limits and links to accepted decisions>

## Components and boundaries
<Likely areas involved, without pretending the implementation is already planned>

## Data and interface implications
<Schemas, APIs, compatibility, migration, or persistence concerns>

## Failure and recovery behaviour
<Expected handling of errors and partial completion>

## Security, privacy, accessibility, and operational concerns
<Only relevant concerns; state not applicable where justified>

## Dependencies
<Internal and external dependencies>

## Acceptance criteria
<Testable product-level criteria>

## Testing expectations
<Required evidence categories, not a full implementation plan>

## Open questions
<Unresolved consequential questions>

## Assumptions
<Explicit assumptions requiring validation>

## Evidence consulted
<Repository and KBB links>

## Human approval
Unapproved candidate specification.
```

## 21. Brief-rumination stop conditions

Stop and leave the milestone unapproved when:

- the brief is contradictory or lacks a usable intended outcome;
- a controlling decision is missing;
- unresolved dependencies make a meaningful specification impossible;
- the milestone overlaps another active owner's work and the boundary is unresolved;
- the candidate would require inventing product behaviour;
- the milestone is too large and the human has not accepted a proposed split.

Record the blocker or open question in KBB rather than guessing.

---

# Part C — Repository implementation

## 22. Expected repository changes

The implementing agent must inspect the current repository and adjust paths to existing generation conventions. The expected canonical additions are:

```text
plugins/paad/skills/kb-brain/
├── SKILL.md
├── references/
│   ├── structure.md
│   ├── routing.md
│   ├── lifecycle.md
│   └── templates.md
├── templates/
│   └── <project-local template files>
└── scripts/
    └── <deterministic scaffold/index/check/seal tool>

plugins/paad/skills/brief-ruminate/
├── SKILL.md
├── references/
│   ├── brief-format.md
│   ├── milestone-lifecycle.md
│   └── candidate-spec.md
└── templates/
    ├── BRIEF.md
    ├── MILESTONE.md
    └── MILESTONE-SPEC.md
```

Keep `SKILL.md` focused. Put detailed templates and long reference material in bundled resources so they are loaded only when needed.

Also update:

- `README.md` available-skills documentation;
- `plugins/paad/skills/help/SKILL.md` overview and detailed sections;
- `CHANGELOG.md`;
- plugin and marketplace manifests with a synchronized semver bump;
- repository-generated or mirrored platform skill directories using the existing generator;
- tests and validation scripts required by current repository conventions.

Do not change prose or flows inside existing skills unless a shared generated index absolutely requires a mechanical listing update.

## 23. AGENTS.md integration text

Provide this as an installation snippet and include it in the `kb-brain` reference material:

```markdown
## KB-Brain

Use the `kb-brain` skill for section routing, templates, workspace lifecycle, and write rules.

Every PAAD-managed task uses a focused shared workspace under:

`kb-brain/work/active/<task-id>/`

Repository workspace level: `standard`

Supported levels:

- `minimal` — scope, status, ownership, handoff, and durable findings
- `standard` — findings, questions, decisions, failures, conflicts, and handoffs
- `strict` — standard plus evidence, assumptions, dependencies, ownership, and scope-change tracking

A task may raise its level. Lowering below the repository level requires explicit human approval.

Sub-agents may append findings, evidence, questions, failures, conflicts, and handoffs.

Only the lead agent or human task owner may change task scope, lifecycle status, assignments, blockers, confirmed decisions, or conflict resolution state.

Conflicting findings must be recorded rather than overwritten. Address conflicts during the session when they affect current work.

Agents may autonomously:

- add one file per gap under `kb-brain/improvements/`;
- track smoothing or remediation work under `kb-brain/tech-debt/`;
- update `kb-brain/tech-debt/LEDGER.md`;
- move resolved debt into `kb-brain/tech-debt/closed/`;
- promote durable task knowledge into the appropriate permanent KBB section.

Use the provided templates for human- and agent-authored records.

Bulk content ingress from existing documentation is a dedicated operation. Do not copy architecture documentation into KBB unprompted.

Closed workspaces are immutable. Add corrections or later findings as explicit amendments.
```

## 24. Required validation behaviour

`kb-check` should validate at least:

- expected top-level section names;
- required workspace files for the selected level;
- valid YAML frontmatter;
- required fields and valid status values;
- unique IDs within their scope;
- valid relative links where deterministically checkable;
- task ownership and lead-only metadata consistency;
- blockers represented consistently between `TASK.md` and generated `ACTIVE.md`;
- closed workspace seal hashes;
- amendment references point to an existing sealed record;
- no original closed file has been changed, removed, or renamed;
- no obvious secret patterns are present in files being sealed;
- `INDEX.md` and `ACTIVE.md` are up to date or can be regenerated cleanly.

Validation should report all safe-to-collect errors in one run rather than stopping at the first issue.

## 25. Testing requirements

Follow the repository's existing test style. Add automated coverage for at least:

### Initialization

- creates the required KBB structure;
- preserves existing files;
- is idempotent;
- creates project-local templates;
- defaults to the repository-selected workspace level;
- does not ingest `docs/`.

### Workspace lifecycle

- creates a workspace for every task;
- creates only level-appropriate required directories/files;
- uses collision-safe task IDs;
- generates `INDEX.md` and `ACTIVE.md`;
- lists ownership and blockers but not conflicts in `ACTIVE.md`;
- updates task status without losing atomic records.

### Routing and records

- allocates unique atomic IDs;
- routes improvements and debt correctly;
- supports human and agent authors;
- detects invalid frontmatter and duplicate IDs;
- prevents unresolved questions from being marked answered without owner/evidence metadata.

### Closure and immutability

- permits final cleanup before closure;
- requires closeout and promotion checks;
- creates `SEAL.json` correctly;
- detects mutation, removal, and rename of sealed files;
- permits valid amendments;
- marks amended records in regenerated indexes;
- retains all atomic historical files.

### Brief rumination

- preserves the human brief unchanged;
- reads milestone and KBB context selectively;
- creates an atomic candidate spec with `review-needed` status;
- cannot mark a spec approved;
- records blockers rather than inventing missing requirements;
- updates milestone and brief indexes;
- does not invoke or alter other PAAD skills.

### Skill package validation

- frontmatter names match directories;
- Graphviz diagrams cover all decision branches and stop conditions;
- README and help documentation list both skills and arguments;
- manifests use the same new version;
- generated platform copies match canonical sources;
- complete repository test suite passes.

## 26. Suggested implementation sequence

1. Inspect current main branch, repository generation scripts, tests, manifests, and current version.
2. Add failing tests for skill discovery, docs coverage, and KBB deterministic tooling.
3. Implement shared KBB templates and project-local scaffold/index/check functions.
4. Implement workspace start, record creation, global active index, and validation.
5. Implement close, seal, immutable validation, and amendments.
6. Write the `kb-brain` skill workflow and complete Graphviz diagram.
7. Add brief and milestone templates plus candidate-spec generation support.
8. Write the `brief-ruminate` skill workflow and complete Graphviz diagram.
9. Add README, help, AGENTS snippet, and changelog documentation.
10. Regenerate all supported platform mirrors using repository tooling.
11. Bump patch version in all required manifests.
12. Run formatting, generated-file checks, repository tests, plugin validation, and local skill smoke tests.
13. Review the diff to confirm existing skills have no behavioural changes.
14. Commit in coherent units and open a pull request.

## 27. Pull request requirements

Suggested title:

```text
feat: add KB-Brain memory and brief rumination skills
```

The PR description should explain:

- why persistent repository-native memory is needed;
- the `docs/` versus `kb-brain/` authority boundary;
- autonomous atomic writes and lead/sub-agent permissions;
- workspace levels and index-first retrieval;
- closure sealing and amendment rules;
- brief-to-milestone-spec expansion and its human approval boundary;
- explicit confirmation that existing PAAD skills are not behaviourally modified;
- tests and validation commands run.

Keep the PR focused. Do not include unrelated refactors.

## 28. Definition of done

The change is complete when:

- both new skills are discoverable and documented;
- `/paad:kb-brain init` can scaffold a usable KBB without ingesting existing docs;
- every managed task can receive a focused atomic workspace;
- humans and agents share templates;
- sub-agents can append evidence without being able to redefine task authority silently;
- `ACTIVE.md` exposes ownership and blockers economically;
- conflicts affecting current work are surfaced in-session;
- closed workspaces are verifiably immutable and amendable;
- `/paad:brief-ruminate` can turn one human-owned milestone into an unapproved candidate spec grounded in repository and KBB evidence;
- existing PAAD skill behaviour is unchanged;
- all repository tests, generation checks, documentation checks, and plugin validations pass.

---

## 29. Source basis

- User-supplied `KB_README.md`, including the mutable KBB section model and promised Make targets.
- PAAD repository README: `https://github.com/Ovid/paad`
- PAAD contribution conventions: `https://github.com/Ovid/paad/blob/main/CLAUDE.md`

Where repository implementation details differ from this handoff, preserve the product rules and adapt the mechanics to the current canonical generation and testing conventions.
