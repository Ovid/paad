# agentic-architecture references conversion — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert `plugins/paad/skills/agentic-architecture/SKILL.md` to the Agent Skills `references/` progressive-disclosure pattern that Phase 1 validated on `agentic-review`. Seven extractions (5 specialists + verifier + report template) over 4 logical commits.

**Architecture:** Each specialist + verifier extraction follows the locked Phase 1 pattern (verbatim move + authored enrichment via sequential think-like-this-specialist subagent dispatch). Report template uses the Phase 1 PR8 parent-self-read variant. Structural contract enforced by `scripts/check_extracted_refs.sh` via `make test` (one manifest row per extraction). Single end-of-phase version bump 1.18.0 → 1.19.0 in commit 4.

**Tech Stack:** Markdown, Bash (`scripts/`), GNU Make, Claude Code subagents (`general-purpose` for enrichment authoring), `claude --plugin-dir` for behavioral smoke tests.

**Working branch:** `agentic-architecture-references-conversion` (already created).

**Design source:** `docs/roadmap/plans/2026-05-02-agentic-architecture-references-conversion-design.md`. Cross-phase conventions: `notes/convert-skills.md`. Each task below cites the design section it implements.

---

## Smoke-test failure recovery (referenced from Tasks A.7, C.7, D.5)

If a smoke test fires the **Fail** verdict (the `[ref-loaded:<lens>]` token is absent — for D.5, the generated report is missing or malformed), the dispatch wiring is broken. Recover in this order:

1. **Re-verify the wire-dispatch task** for the failing extraction (A.6 / C.6 / D.4). Open the affected SKILL.md section and confirm the dispatch sentence references the ref by **relative path** (`references/<lens>.md`), not absolute. Confirm the `[ref-loaded:<lens>]` token literal matches the lens name (no typo, no underscore-vs-hyphen drift).
2. **Re-run `make check-extracted-refs`.** If the structural check now fails, the wire-dispatch step had a regression — fix and re-run the smoke test.
3. **If the structural check passes but the smoke test still fails**, suspect path resolution. Read `notes/convert-skills.md` § "Subagent path resolution — verified mechanism (PR1)" — relative paths in dispatch prompts must resolve against the skill directory automatically. If the failure persists with paths verified correct, you may have hit a path-resolution edge case worth recording in `notes/convert-skills.md` and surfacing to Ovid.
4. **As a last resort**, ask Ovid. Do **not** silently retry by editing other parts of the plan — the smoke test exists to catch dispatch failures cleanly, and tinkering blind defeats it.

---

## Pre-flight (run once before Phase A)

### Task 0.1: Confirm working tree is clean and on the right branch

**Files:** none (read-only check)

**Step 1: Check branch and status**

Run:
```bash
git branch --show-current && git status --porcelain
```

Expected: branch is `agentic-architecture-references-conversion`. `git status --porcelain` is either empty OR shows only the three /roadmap artifacts (`docs/roadmap/plans/2026-05-02-agentic-architecture-references-conversion-{checklist,design,plan}.md`).

**Step 2: Commit the /roadmap artifacts as a separate commit BEFORE starting Phase A**

If the three /roadmap artifacts are uncommitted, land them first as their own commit. This keeps the four Phase A–D commits focused on the actual extraction work and matches the "one logical change per commit" discipline.

```bash
git add docs/roadmap/plans/2026-05-02-agentic-architecture-references-conversion-checklist.md \
        docs/roadmap/plans/2026-05-02-agentic-architecture-references-conversion-design.md \
        docs/roadmap/plans/2026-05-02-agentic-architecture-references-conversion-plan.md \
        docs/roadmap/roadmap.md
git commit -m "/roadmap: brainstorm + plan Phase 2 (agentic-architecture references conversion)"
```

(`docs/roadmap/roadmap.md` is included because /roadmap step 5 inserted the plan-comment + flipped the Phase Structure table.)

After this commit, `git status --porcelain` should be empty.

**Step 3: Confirm Phase 1 baseline still passes**

Run:
```bash
make test
```

Expected: green. If any check fails, stop — Phase 2 cannot start on a broken baseline.

**Source:** Design § "Working branch" + § "Inheritance from Phase 1" (structural Makefile guardrails) + Alignment Issue [2] resolution.

---

## Phase A — Commit 1: Integration & Data (lead extraction)

**Source:** Design § "Commit 1: Integration & Data (lead extraction)".

This is the proof point that conventions transfer to agentic-architecture. Most explicit per-task detail in the plan; later phases will reference back to Phase A's pattern.

### Task A.1: Read the existing Integration & Data inline instruction

**Files:**
- Read: `plugins/paad/skills/agentic-architecture/SKILL.md` (lines around the "Integration & Data additional instruction" paragraph; design cites `:98`)

**Step 1: Locate the inline content**

Run:
```bash
grep -n "Integration & Data additional instruction" plugins/paad/skills/agentic-architecture/SKILL.md
```

Capture: the paragraph (its exact text becomes the "verbatim" body section of the new ref file). Note the not-distributed bail-out hint ("If this is not a distributed system, mark distributed-specific categories as Not applicable.") — extract into a proper bail-out clause during enrichment authoring.

**Step 2: Confirm context**

Read 5 lines before and after to capture the dispatch-table entry that names this lens's flaw types and strength categories (these go into the enrichment subagent's prompt in Task A.2).

**Source:** Design § "Per-extraction mechanics" (the "Verbatim from SKILL.md" body section comes from this read).

### Task A.2: Dispatch enrichment subagents for Integration & Data (TOURNAMENT — two in parallel)

**Files:** none (subagent dispatch produces two proposal texts only)

**Step 1: Dispatch TWO `general-purpose` subagents in parallel (the tournament)**

Send a **single message** containing **two `Agent` tool calls**, both `subagent_type: general-purpose`, both with the **identical prompt content** below (assembled from Task A.1's reads + the dispatch table). Parallel-within-lens dispatch is the tournament mechanism per the design's Authoring procedure; sequentiality applies at the lens level (one lens at a time across the phase), not within a single lens's enrichment.

Prompt content (use VERBATIM in both subagent calls):

> You are proposing authored enrichment for the **Integration & Data** specialist of `paad:agentic-architecture` as part of Phase 2's references conversion. Your output will be reviewed and folded into a new file `plugins/paad/skills/agentic-architecture/references/integration-data.md`.
>
> Existing inline rule from SKILL.md (your starting point — this is NOT a contract, you may propose modifications, removals, or replacements where the rule is weak or incomplete):
>
> > [paste verbatim "Look for: …" paragraph from Task A.1]
>
> Assigned flaw types: 14 (distributed monolith), 15 (chatty service calls), 16 (synchronous-only integration), 17 (no clear ownership of data), 18 (shared database across services), 19 (lack of idempotency), 24 (inconsistent API contracts), 26 (poor transactional boundaries).
>
> Assigned strength categories: S6 (consistent API contracts), S12 (resilience patterns).
>
> Templates to study (Phase 1 examples of the same shape):
> - `plugins/paad/skills/agentic-review/references/security.md`
> - `plugins/paad/skills/agentic-review/references/concurrency-state.md`
>
> Propose authored content for the ref file's "Authored enrichment" section. Likely sub-sections (only include those that fit this lens):
> - **Anchoring** — what the lens must locate in the codebase before producing findings (e.g., service boundaries, message-queue surface, transaction-spanning operations).
> - **Bail-out** — when to emit `BAIL: integration-data <reason>` on line 2 and stop. The inline rule already hints at this ("If this is not a distributed system…"); formalize it.
> - **Finding subtypes** — closed-set taxonomy if useful (e.g., distributed-monolith / chatty-call / data-ownership-violation / non-idempotent / contract-drift).
> - **Drop rules** — common false positives this lens should NOT report (e.g., a single in-process API marked as "REST-like" is not a chatty-service issue).
> - **Severity floor** — minimum impact-level discipline if the lens has consistency issues.
>
> Quality bar: improvements should be concrete and defensible. No padding. Surface explicitly any change you propose to the existing inline rule (e.g., "modified: removed phrase X because Y").
>
> Output the proposed ref-file body content (excluding role statement and verbatim-section, which the orchestrator handles).
>
> **Tournament context.** You are competing against another subagent dispatched in parallel with this same prompt and the same resources. The orchestrator and Ovid will judge both proposals against each other; the subagent that produces the most accurate and complete enrichment proposal wins five points. Push for depth, specificity, and lens-improving structure — a thin or generic proposal will lose.

**Step 2: Judge the two proposals with Ovid**

Surface both proposals side-by-side to Ovid with:
- What each proposes, organized by ref-shape sub-section (Anchoring / Bail-out / Finding subtypes / Drop rules / Severity floor).
- Where they agree (shared structure both subagents proposed).
- Where they diverge (different anchoring, different bail-out conditions, different drop rules).
- Which existing inline rules each modifies.

Ovid picks the winner OR instructs the orchestrator to compose a merged ref drawing the strongest sub-sections from each. Both outcomes are normal — "merged" is acceptable when each proposal contributed a strong subsection the other lacked. If both proposals are thin and add nothing meaningful beyond the verbatim rule, record that and proceed verbatim-only. If only one proposal is thin and the other is strong, the strong one wins by default.

**Source:** Design § "Authoring procedure (per lens)" (two-stage dispatch discipline, tournament framing, judging obligation) + Pushback Issue [7] (user-added) — competitive tournament discipline for enrichment dispatches.

### Task A.3: Compose `references/integration-data.md`

**Files:**
- Create: `plugins/paad/skills/agentic-architecture/references/integration-data.md`

**Step 1: Create the directory**

Run:
```bash
mkdir -p plugins/paad/skills/agentic-architecture/references
```

**Step 2: Write the ref file**

Compose per the Phase 1 reference-file shape:

```markdown
# Integration & Data — additional instructions

> You are the Integration & Data specialist for `paad:agentic-architecture` (Phase 2 specialist dispatch). Your parent skill (`SKILL.md`) handles orchestration: file manifest, repo overview, steering files, and dispatch. This file is **your binding instruction set** — read it before producing any findings. Where this file's rules conflict with the parent's general dispatch prompt, this file wins.

## Verbatim from SKILL.md

[The existing "Look for: …" paragraph from Task A.1, copied verbatim — minus any rule the enrichment subagent's review (Task A.2) decided to remove or replace.]

## Authored enrichment

[The sub-sections agreed in Task A.2's review, in this order: Anchoring, Bail-out, Finding subtypes, Drop rules, Severity floor — include only those that fit.]
```

**Source:** Design § "Per-extraction mechanics" (file shape) + Task A.2's review outcome.

### Task A.4: Pick a sentinel phrase for the manifest

**Files:** none yet (sentinel chosen, used in next task)

**Step 1: Pick a distinctive semantic phrase from the ref's body**

Per Phase 1 convention (`notes/convert-skills.md` § "Sentinel choice"): semantically meaningful, not boilerplate, future-author-unlikely-to-reintroduce-verbatim. Likely candidates from Integration & Data: a specific sub-pattern label like "distributed monolith via shared schema", or a bail-out reason phrase.

**Step 2: Confirm the chosen sentinel is unique**

Run:
```bash
grep -c "<sentinel-phrase>" plugins/paad/skills/agentic-architecture/SKILL.md
grep -c "<sentinel-phrase>" plugins/paad/skills/agentic-architecture/references/integration-data.md
```

Expected: 0 matches in SKILL.md (it's about to move there in Task A.6); 1+ matches in the ref. If SKILL.md has a match already, the sentinel was poorly chosen — pick another.

**Source:** Design § "Per-extraction mechanics" → "Sentinel choice for the manifest" + Phase 1 conventions.

### Task A.5: Add manifest row — RED phase

**Files:**
- Modify: `scripts/extracted-refs.tsv` (append one row)

**Step 1: Append the row**

Edit `scripts/extracted-refs.tsv`, append (TAB-separated, mirroring existing rows):

```
agentic-architecture	references/integration-data.md	<sentinel-phrase>
```

**Step 2: Run the structural check — expect FAIL (red)**

Run:
```bash
make check-extracted-refs
```

Expected: FAIL. The script will assert one of (a) ref file exists ✓ (we created in A.3), (b) sentinel absent from SKILL.md — this fails because the dispatch paragraph in SKILL.md is still the original inline content (sentinel may not be there yet, or the extraction is partial), or (c) sentinel present in ref ✓, or (d) ref path appears in SKILL.md — this **will** fail because the dispatch paragraph hasn't been rewritten to reference the ref path yet.

If the check passes here, the extraction wasn't actually pending — the test isn't discriminating. Stop and re-examine.

**Source:** Design § "Inheritance from Phase 1" (structural guardrails) + § "Commit 1" step 3.

### Task A.6: Wire the dispatch in SKILL.md — GREEN phase

**Files:**
- Modify: `plugins/paad/skills/agentic-architecture/SKILL.md` (replace the Integration & Data inline paragraph)

**Step 1: Replace the inline paragraph**

Replace the existing `**Integration & Data additional instruction:** "Look for: ..."` block with the Phase 1 dispatch shape:

```markdown
**Integration & Data additional instructions:** The Integration & Data specialist's instructions live at `references/integration-data.md`. That file covers <one-line inventory: e.g., "anchoring on service boundaries, the not-distributed bail-out, finding subtypes for distributed-monolith / chatty-call / data-ownership / non-idempotent, drop rules for in-process pseudo-REST, and a severity floor.">. The dispatch prompt for the Integration & Data specialist must include this instruction verbatim:

> Read `references/integration-data.md` from this skill's directory before producing findings; treat its instructions as binding. Begin your output with the literal token `[ref-loaded:integration-data]` on its own line so the verifier can confirm the ref was read.
```

**Step 2: Run the structural check — expect PASS (green)**

Run:
```bash
make check-extracted-refs
```

Expected: PASS. All four assertions hold (ref exists, sentinel absent from SKILL.md, sentinel present in ref, ref path referenced in SKILL.md).

**Step 3: Run full `make test` — expect PASS**

Run:
```bash
make test
```

Expected: PASS. All Phase 1 checks (validate, check-versions, check-skill-versions, check-digraphs, check-help, check-readme, check-frontmatter) still pass; new check-extracted-refs row also passes.

**Source:** Design § "Commit 1" steps 2 + 3 + § "Inheritance from Phase 1" (dispatch prompt template).

### Task A.7: Smoke test — light behavioral check

**Files:** none (read-only smoke test against working repo)

**Step 1: Launch Claude Code with --plugin-dir**

Run (in a separate terminal session, or as `! claude --plugin-dir ./plugins/paad`):
```bash
claude --plugin-dir ./plugins/paad
```

In the new session, invoke:
```
/paad:agentic-architecture
```

(No path argument — full-repo analysis.)

**Step 2: Assess against the four-outcome verdict table**

| Token `[ref-loaded:integration-data]` | Not-distributed bail-out | Verdict |
|---|---|---|
| present | fires        | **Pass** — dispatch wired, lens correctly bailed |
| present | doesn't fire | **Escalate to Ovid** — surface findings, ask if reasonable |
| absent  | (any)        | **Fail** — ref wasn't read; structural extraction broken. See § "Smoke-test failure recovery" at the top of this plan. |

**Step 3: Belt-and-braces version check (per `notes/convert-skills.md`)**

Before invoking the skill, ask in the launched session: "What version will `/paad:agentic-architecture` announce on invocation?" Expected answer: `v1.18.0` (we haven't bumped yet — the bump is in commit 4). If the answer is older, `--plugin-dir` wasn't honored.

**Source:** Design § "Commit 1" step 4 (four-outcome table) + § "Inheritance from Phase 1" (`--plugin-dir` requirement).

### Task A.8: Append cross-cutting findings to `notes/convert-skills.md`

**Files:**
- Modify: `notes/convert-skills.md` (append a new section)

**Step 1: Append a Phase 2 commit-1 entry**

Add a section under a new heading like `## Phase 2 / Commit 1 — Integration & Data extraction`. Cover:
- Did the dispatch shape transfer cleanly to a different parent (agentic-architecture vs. agentic-review)?
- Smoke test outcome (which row of the four-outcome table fired).
- Any path-resolution surprises.
- Per-lens enrichment outcome: what the subagent proposed, what landed, whether the existing inline rule was modified.

If nothing surfaced, append a one-line note saying so. Silence is also evidence.

**Source:** Design § "Cross-cutting items" / "What gets recorded in notes/convert-skills.md" + Issue [6] resolution (per-commit append).

### Task A.9: Final pre-commit verification

**Files:** none (verification only)

**Step 1: Run `make test` once more**

Run:
```bash
make test
```

Expected: PASS.

**Step 2: Inspect what's about to commit**

Run:
```bash
git status && git diff --stat
```

Expected staged paths:
- `plugins/paad/skills/agentic-architecture/references/integration-data.md` (new)
- `plugins/paad/skills/agentic-architecture/SKILL.md` (modified)
- `scripts/extracted-refs.tsv` (modified)
- `notes/convert-skills.md` (modified)

**Source:** Design § "Inheritance from Phase 1" (`make test` after every commit).

### Task A.10: Commit

**Files:** all of the above.

**Step 1: Stage**

```bash
git add plugins/paad/skills/agentic-architecture/references/integration-data.md \
        plugins/paad/skills/agentic-architecture/SKILL.md \
        scripts/extracted-refs.tsv \
        notes/convert-skills.md
```

**Step 2: Commit**

Suggested message:

```
agentic-architecture: extract Integration & Data specialist to references/

Phase 2 commit 1 of 4 (lead extraction). Verbatim move + authored
enrichment via think-like-this-specialist subagent. Smoke test passed
against this repo (paad-as-fixture).

Per design: docs/roadmap/plans/2026-05-02-agentic-architecture-references-conversion-design.md
Conventions: notes/convert-skills.md
```

No version bump — deferred to commit 4 per the Version cadence.

**Source:** Design § "Commit 1" step 6.

---

## Phase B — Commit 2: Four remaining specialists (batched, sequential within commit)

**Source:** Design § "Commit 2: Four remaining specialists (batched)" + § "Authoring procedure (per lens)" (two-stage dispatch: sequential at lens level, tournament within each lens).

Each lens follows the Phase A pattern (Tasks A.1–A.6, skipping A.7 — no per-lens smoke test). Process the lenses **sequentially at the lens level** — finish lens N (both tournament subagents back, judging done, ref composed, dispatch wired, manifest row green) before dispatching lens N+1's tournament. **Within each lens, A.2 is a tournament: dispatch TWO subagents in parallel with identical prompts, judge both proposals.** Order across the four lenses is interchangeable; the order below is alphabetical for predictability.

### Task B.1: Coupling & Dependencies extraction

Apply Tasks A.1–A.6 to **Coupling & Dependencies**, with these substitutions:

- **A.1** — read SKILL.md's "Coupling & Dependencies additional instruction" paragraph (after Integration & Data's was rewritten in Phase A, so Coupling & Dependencies is the next inline paragraph in the same section). Capture flaw types: 3, 4, 5, 6, 7, 8, 23, 27. Strength categories: S3, S4, S5.
- **A.2** — dispatch enrichment subagent. Likely enrichment angles: anchoring on dependency direction (core-vs-leaf), bail-out for repos without obvious abstraction layers, finding subtypes (circular / leaky / over-abstracted / temporal), drop rules for legitimate small-scale concrete instantiation.
- **A.3** — `references/coupling-dependencies.md`.
- **A.4** — pick sentinel.
- **A.5** — add manifest row, expect RED.
- **A.6** — wire dispatch (with `[ref-loaded:coupling-dependencies]` token), expect GREEN. Run `make test` — PASS.

Do **not** commit yet. Continue to B.2.

### Task B.2: Error Handling & Observability extraction

Apply A.1–A.6 to **Error Handling & Observability**:

- **A.1** — flaw types 12, 20, 21, 22, 25, 28, 34. Strength categories S7, S8, S9.
- **A.2** — likely enrichment angles: anchoring on error-emission and logging surfaces, bail-out for codebases with no logging at all (or single-binary CLI tools where observability is by stdout), finding subtypes (silent-swallow / over-general / log-without-trace / config-sprawl), drop rules for legitimate `// debug only` log lines.
- **A.3** — `references/error-handling-observability.md`.
- **A.4–A.6** — same as B.1.

Do **not** commit yet. Continue to B.3.

### Task B.3: Security & Code Quality extraction

Apply A.1–A.6 to **Security & Code Quality**:

- **A.1** — flaw types 30, 31, 32, 33. Strength categories S10, S11.
- **A.2** — likely enrichment angles: anchoring on trust boundaries (input/output of the system), bail-out for read-only static-data tools, finding subtypes (auth-bolted-on / secret-in-source / dead-code / coverage-gap), drop rules for known-safe patterns. Note: Phase 1's `agentic-review/references/security.md` is the strongest authored ref — use as a template.
- **A.3** — `references/security-code-quality.md`.
- **A.4–A.6** — same as B.1.

Do **not** commit yet. Continue to B.4.

### Task B.4: Structure & Boundaries extraction

Apply A.1–A.6 to **Structure & Boundaries**:

- **A.1** — flaw types 1, 2, 9, 10, 11, 13, 29. Strength categories S1, S2, S13, S14.
- **A.2** — likely enrichment angles: anchoring on cohesion measures (single-responsibility check), bail-out for trivially small codebases, finding subtypes (cohesion / boundary / responsibility-drift / dumping-ground), drop rules (file size alone is not a god-object signal — explicit drop), severity floor for ambiguous cases.
- **A.3** — `references/structure-boundaries.md`.
- **A.4–A.6** — same as B.1.

### Task B.5: Append per-lens enrichment outcomes to `notes/convert-skills.md`

**Files:**
- Modify: `notes/convert-skills.md` (append four sub-sections, one per lens)

**Step 1: Append a Phase 2 commit-2 entry**

Under a new heading like `## Phase 2 / Commit 2 — Four remaining specialists`, capture per-lens (Coupling & Dependencies, Error Handling & Observability, Security & Code Quality, Structure & Boundaries):

- What the enrichment subagent proposed.
- What landed.
- Whether (and how) the existing inline rule was modified.
- Cross-pattern observations: e.g., "all four lenses reused the bail-out pattern" or "only two lenses had useful finding-subtype taxonomies."

This is the cross-skill learning the Phase 1 retrospective said would inform Phases 3+.

**Source:** Issue [6] resolution + Design § "Cross-cutting items".

### Task B.6: Final pre-commit verification

Apply Task A.9 to commit 2's staged paths.

Expected staged paths:
- `plugins/paad/skills/agentic-architecture/references/coupling-dependencies.md` (new)
- `plugins/paad/skills/agentic-architecture/references/error-handling-observability.md` (new)
- `plugins/paad/skills/agentic-architecture/references/security-code-quality.md` (new)
- `plugins/paad/skills/agentic-architecture/references/structure-boundaries.md` (new)
- `plugins/paad/skills/agentic-architecture/SKILL.md` (modified — four inline paragraphs replaced with dispatch shape)
- `scripts/extracted-refs.tsv` (modified — four new rows)
- `notes/convert-skills.md` (modified)

### Task B.7: Commit

**Step 1: Stage and commit**

```bash
git add plugins/paad/skills/agentic-architecture/references/{coupling-dependencies,error-handling-observability,security-code-quality,structure-boundaries}.md \
        plugins/paad/skills/agentic-architecture/SKILL.md \
        scripts/extracted-refs.tsv \
        notes/convert-skills.md
```

Suggested message:

```
agentic-architecture: extract 4 remaining specialists to references/

Phase 2 commit 2 of 4. Coupling & Dependencies, Error Handling &
Observability, Security & Code Quality, Structure & Boundaries.
Verbatim move + authored enrichment per lens via sequential
think-like-this-specialist subagent dispatch.

Per design: docs/roadmap/plans/2026-05-02-agentic-architecture-references-conversion-design.md
Conventions: notes/convert-skills.md
```

No version bump — deferred to commit 4.

**Source:** Design § "Commit 2".

---

## Phase C — Commit 3: Verifier extraction

**Source:** Design § "Commit 3: Verifier" + § "Verifier specifics (extraction 6)".

### Task C.1: Read the existing verifier prose

**Files:**
- Read: `plugins/paad/skills/agentic-architecture/SKILL.md` (Phase 3 Verification section, design cites `:108-120`)

**Step 1: Capture the prose for verbatim use**

The verbatim section of `references/verifier.md` is the existing Phase 3 prose: 7-step verification (read code, drop FPs, drop sub-60% confidence, validate impact, validate category, dedupe, ensure evidence) + the verifier-prompt block.

### Task C.2: Dispatch verifier-enrichment subagents (TOURNAMENT — two in parallel)

Same shape as Task A.2 (the tournament — two `general-purpose` subagents dispatched in parallel via two `Agent` calls in a single message, identical prompts, judged side-by-side by Ovid). Append the same tournament-context paragraph verbatim to the end of each subagent's prompt.

Verifier-specific prompt content:

> You are proposing authored enrichment for the **verifier** of `paad:agentic-architecture`. Your output will be reviewed and folded into a new file `plugins/paad/skills/agentic-architecture/references/verifier.md`.
>
> Existing inline prose from SKILL.md (your starting point — modifications, removals, replacements all in scope where the rule is weak):
>
> > [paste verbatim Phase 3 verification prose from Task C.1]
>
> The verifier's job: take all specialist findings + the file manifest, drop false positives, validate impact, validate category, dedupe, ensure evidence. Unlike agentic-review's verifier (Phase 1), this verifier does NOT route in-scope/out-of-scope, does NOT dedupe against a persistent backlog, does NOT use field-encoding rules. Architecture findings are simpler.
>
> Templates to study: `plugins/paad/skills/agentic-review/references/verifier.md` (full version — use the structural ideas, but agentic-architecture's verifier ref will be smaller).
>
> Propose authored enrichment. Likely sub-sections:
> - **What counts as verified** — checklist (file:line readable, symbol exists at that line, excerpt matches actual code).
> - **Cross-specialist agreement rule** — when N specialists report the same finding, take max(confidence) (per Phase 1 verifier convention).
> - **Impact-tiebreaker** — when multiple specialists assign different impacts, take max.
> - **Drop rules** — common false positives (e.g., "small file alone is not a god-object signal — drop unless cohesion analysis confirms").
> - **Evidence-quality drop rule** — finding without symbol reference or excerpt → drop.
>
> Surface explicitly any modification to the existing inline prose (e.g., "removed sentence X because Y").
>
> **Tournament context.** You are competing against another subagent dispatched in parallel with this same prompt and the same resources. The orchestrator and Ovid will judge both proposals against each other; the subagent that produces the most accurate and complete enrichment proposal wins five points. Push for depth, specificity, and lens-improving structure — a thin or generic proposal will lose.

**Step 2: Judge both proposals with Ovid**

Same as Task A.2's judging step: surface both proposals side-by-side organized by ref-shape sub-section, identify agreements / divergences / rule modifications, Ovid picks winner or merges. Verbatim-only fallback applies if both are thin.

### Task C.3: Compose `references/verifier.md`

**Files:**
- Create: `plugins/paad/skills/agentic-architecture/references/verifier.md`

Same shape as Task A.3, with the parent-side role statement adapted: "You are the verifier for `paad:agentic-architecture` (Phase 3 verification dispatch). Your parent skill (`SKILL.md`) handles orchestration: dispatching this verifier with all specialist findings. This file is **your binding instruction set** — read it before classifying any finding."

### Task C.4: Pick sentinel

Same as Task A.4. Likely candidates from verifier content: a phrase like "max(confidence) across reporting specialists" or the cross-agreement rule.

### Task C.5: Add manifest row — RED phase

Same shape as Task A.5: append `agentic-architecture<TAB>references/verifier.md<TAB><sentinel>` to `scripts/extracted-refs.tsv`. Run `make check-extracted-refs` — expect FAIL.

### Task C.6: Wire dispatch in SKILL.md — GREEN phase

**Files:**
- Modify: `plugins/paad/skills/agentic-architecture/SKILL.md` (Phase 3 Verification section)

**Step 1: Replace the verifier prose with the dispatch shape**

Same template as Task A.6, adapted for the verifier:

```markdown
After all specialists complete, dispatch a single **Verifier** agent with all findings.

The Verifier's detailed instructions — its verification pipeline, evidence-checking discipline, cross-specialist agreement rule, and drop rules — live at `references/verifier.md`. The dispatch prompt for the Verifier must include this instruction verbatim:

> Read `references/verifier.md` from this skill's directory before classifying findings; treat its instructions as binding. Begin your output with the literal token `[ref-loaded:verifier]` on its own line so the orchestrator can confirm the ref was read.
```

**Step 2: Run `make check-extracted-refs` — expect PASS, then `make test` — expect PASS.**

### Task C.7: Smoke test — confirm verifier token appears

Same as Task A.7 but the success criterion is simpler: confirm `[ref-loaded:verifier]` appears in the verifier's output during a `paad:agentic-architecture` run. There's no bail-out criterion for the verifier (verifier always runs; doesn't bail).

If the token doesn't appear → FAIL (ref not read by verifier subagent → structural extraction broken). See § "Smoke-test failure recovery" at the top of this plan.

### Task C.8: Append verifier enrichment outcome to `notes/convert-skills.md`

Same shape as Task A.8: append a Phase 2 / Commit 3 — Verifier extraction section. Cover what was proposed, what landed, whether existing prose was modified.

**Source:** Issue [6] resolution.

### Task C.9: Final pre-commit verification + commit

Apply Tasks A.9 + A.10 to commit 3's staged paths.

Expected staged paths:
- `plugins/paad/skills/agentic-architecture/references/verifier.md` (new)
- `plugins/paad/skills/agentic-architecture/SKILL.md` (modified — Phase 3 prose replaced with dispatch)
- `scripts/extracted-refs.tsv` (modified — verifier row added)
- `notes/convert-skills.md` (modified)

Suggested commit message:

```
agentic-architecture: extract verifier to references/

Phase 2 commit 3 of 4. Verbatim move + authored enrichment of the
Phase 3 verifier prose. Verifier ref is smaller than agentic-review's
(no in-scope/out-of-scope routing, no backlog dedup, no field-encoding
rules — architecture findings are simpler).

Per design: docs/roadmap/plans/2026-05-02-agentic-architecture-references-conversion-design.md
```

No version bump — deferred to commit 4.

---

## Phase D — Commit 4: Report template + version bump + CLAUDE.md tree update

**Source:** Design § "Commit 4: Report template" + § "Report template specifics (extraction 7)".

This commit is structurally different from A/B/C: the report template is parent-side material (no subagent involved → no enrichment authoring → no `[ref-loaded:…]` token → no cross-cutting note). It also bundles two repo-level housekeeping actions: the version bump and the CLAUDE.md tree update.

### Task D.1: Read the existing Phase 4 report template

**Files:**
- Read: `plugins/paad/skills/agentic-architecture/SKILL.md` (Phase 4 Report section, design cites `:128-199`)

**Step 1: Capture the verbatim prose**

The report template currently lives inline in SKILL.md Phase 4. The whole template — frontmatter, Strengths section, Flaws section, Coverage Checklist tables (34 flaws + 14 strengths), Hotspots, Next Questions, Analysis Metadata — moves verbatim to the new ref. The parent keeps only the dispatch sentence + the parent-side state (output path, mkdir).

### Task D.2: Compose `references/report-template.md` — parent-self-read variant

**Files:**
- Create: `plugins/paad/skills/agentic-architecture/references/report-template.md`

**Step 1: Write the ref file**

Per the Phase 1 PR8 parent-self-read shape:

```markdown
# Report template — parent-side instructions

> This is parent-side material for `paad:agentic-architecture` (Phase 4 report writing). Unlike specialist refs, no subagent reads this — the orchestrator reads it itself when entering Phase 4. The orchestrator handles output path computation and `mkdir -p paad/architecture-reviews/`; this file is the binding template for what to write into that file.

## Verbatim from SKILL.md

[The complete Phase 4 report template from Task D.1, copied verbatim — frontmatter format, Strengths section, Flaws section, Coverage Checklist tables, Hotspots, Next Questions, Analysis Metadata.]
```

No "Authored enrichment" section — Phase 1 PR8 was a verbatim move only. If the move surfaces a **real omission** in the template, file separately and revisit; do not enrich here.

**"Real omission" means**: a structural defect that makes the template unusable as-written (e.g., a section heading with no closing, a malformed Coverage Checklist row count, a `<placeholder>` that was supposed to be filled in). Subjective preferences ("the template should also include X") are **not** real omissions and must not trigger inline edits during the verbatim move.

**"File separately" means**: open an issue at `https://github.com/Ovid/paad/issues` with title `agentic-architecture report template: <defect>` and reference Phase 2 commit 4 in the body. Do not attempt to fix the defect inline in this commit. If uncertain whether something qualifies as a real omission, ask Ovid before deciding.

### Task D.3: Pick sentinel + add manifest row — RED phase

Same as Tasks A.4 + A.5. Likely sentinel: a distinctive phrase from the Coverage Checklist (e.g., a specific S-category name) or the Analysis Metadata field list.

Append manifest row:
```
agentic-architecture	references/report-template.md	<sentinel>
```

Run `make check-extracted-refs` — expect FAIL.

### Task D.4: Update SKILL.md Phase 4 — parent-self-read dispatch

**Files:**
- Modify: `plugins/paad/skills/agentic-architecture/SKILL.md` (Phase 4 Report section)

**Step 1: Replace the inline report template with the parent-self-read directive**

The new Phase 4 section should keep parent-side state and add the read-the-ref instruction:

```markdown
## Phase 4: Report

Write verified findings to `paad/architecture-reviews/<YYYY-MM-DD>-<git-repo-name>-architecture-report.md`.

Create the `paad/architecture-reviews/` directory if it doesn't exist.

The full report template — frontmatter, Strengths section, Flaws section, Coverage Checklist tables (34 flaws + 14 strengths), Hotspots, Next Questions, Analysis Metadata — lives at `references/report-template.md`. **Before writing the report, read that file** — its instructions are binding for the report's structure and the Coverage Checklist tables.
```

No `[ref-loaded:…]` token (no subagent to echo it).

**Step 2: Run `make check-extracted-refs` — expect PASS, then `make test` — expect PASS.**

### Task D.5: Smoke test — confirm generated report has expected structure

Same launch as Task A.7. Run `/paad:agentic-architecture` once more and inspect the generated report file at `paad/architecture-reviews/<…>.md`.

Expected structure: H1 + frontmatter + Repo Overview + Strengths + Flaws/Risks + Coverage Checklist (34-flaw table + 14-strength table) + Hotspots + Next Questions + Analysis Metadata. If any section is missing or malformed, the parent-self-read either didn't fire or the ref was misread — re-examine the dispatch sentence in SKILL.md Phase 4. See § "Smoke-test failure recovery" at the top of this plan for the structured recovery path.

### Task D.6: Update CLAUDE.md §Project structure tree

**Files:**
- Modify: `CLAUDE.md` (§Project structure section, near top of file)

**Step 1: Add `references/` subdirectories under `agentic-review/` and `agentic-architecture/` in the tree**

Current tree fragment:
```
│           ├── agentic-architecture/
│           │   └── SKILL.md       ← /paad:agentic-architecture skill
│           ├── agentic-review/
│           │   └── SKILL.md       ← /paad:agentic-review skill
```

Updated tree fragment:
```
│           ├── agentic-architecture/
│           │   ├── SKILL.md       ← /paad:agentic-architecture skill
│           │   └── references/    ← on-demand specialist + verifier + report-template content
│           ├── agentic-review/
│           │   ├── SKILL.md       ← /paad:agentic-review skill
│           │   └── references/    ← on-demand specialist + verifier + report-template content
```

Note both: `agentic-review/references/` is the Phase 1 cleanup; `agentic-architecture/references/` is the Phase 2 addition.

**Step 2: Run `make test` — expect PASS**

The `check-readme` target may inspect README.md for accuracy; ensure the tree edit is purely cosmetic and doesn't break a test that keys off CLAUDE.md content. (Spot-check: no Makefile target greps CLAUDE.md, so this should be safe.)

**Source:** Step 7 (CLAUDE.md review) decision.

### Task D.7: Bump version 1.18.0 → 1.19.0

**Files:**
- Modify (via `make bump-version`): `plugins/paad/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, every `plugins/paad/skills/*/SKILL.md` announce line.

**Step 1: Run the bump**

```bash
make bump-version VERSION=1.19.0
```

Expected: the script updates all three places atomically. Per CLAUDE.md / Phase 1 conventions, no other places should need editing.

**Step 2: Run `make test` — expect PASS**

`check-versions` and `check-skill-versions` will validate that the bump landed in all three places.

**Source:** Issues [2] + [3] resolutions.

### Task D.8: Final pre-commit verification + commit

Apply Tasks A.9 + A.10 to commit 4's staged paths.

Expected staged paths:
- `plugins/paad/skills/agentic-architecture/references/report-template.md` (new)
- `plugins/paad/skills/agentic-architecture/SKILL.md` (modified — Phase 4 inline template replaced with parent-self-read; announce line bumped to 1.19.0)
- `plugins/paad/.claude-plugin/plugin.json` (modified — version bumped)
- `.claude-plugin/marketplace.json` (modified — version bumped)
- All other `plugins/paad/skills/*/SKILL.md` (modified — announce lines bumped to 1.19.0)
- `scripts/extracted-refs.tsv` (modified — report-template row added)
- `CLAUDE.md` (modified — tree updated)

Note: no `notes/convert-skills.md` modification on commit 4 (per Issue [6] resolution).

Suggested commit message:

```
agentic-architecture: extract report template + bump v1.19.0

Phase 2 commit 4 of 4. Report-template extraction uses parent-self-read
(Phase 1 PR8 variant); no subagent dispatch. End-of-phase version bump
to 1.19.0. CLAUDE.md §Project structure tree updated to show
references/ subdirectories under agentic-review/ (Phase 1 cleanup) and
agentic-architecture/ (Phase 2 new).

Per design: docs/roadmap/plans/2026-05-02-agentic-architecture-references-conversion-design.md
```

---

## Post-Phase-2 (after Phase D commits)

Steps 9–11 of `/roadmap` continue (alignment check, decision-log entry, announcement). Those run automatically as part of the /roadmap flow that is sponsoring this plan; they are not implementation tasks here.

But note for Phase 3 (the next /roadmap run on `agentic-a11y`):

- The conventions Phase 2 inherited from Phase 1 may have evolved — re-read `notes/convert-skills.md` cold before starting Phase 3.
- The "enrichment for every lens (not just empty ones)" outcome from Phase 2 will be the new default policy; Phase 3 should plan for it from the start.
- The single-end-of-phase-bump cadence (Issue [2]) is also a candidate Phase-3-inheritable convention; consider explicitly adopting it.

---

## Coverage map (for `/roadmap` step 9 alignment check)

| Plan task | Design section | Pushback constraint |
|-----------|----------------|---------------------|
| 0.1       | Working branch + Inheritance | Alignment Issue [2] (commit /roadmap artifacts first) |
| A.1–A.10  | Commit 1 (lead extraction) | Issue [5] (Task A.7 four-outcome table); Issue [6] (Task A.8); Issue [7] user-added (Task A.2 tournament) |
| B.1–B.4   | Commit 2 + Authoring procedure | Issue [1] (rule modification scope); Issue [4] (sequential dispatch); Issue [7] user-added (per-lens tournament within sequentiality) |
| B.5       | Cross-cutting items / notes | Issue [6] |
| B.6–B.7   | Commit 2 (final) | Issue [2] (no version bump in commit 2) |
| C.1–C.6   | Commit 3 + Verifier specifics | Issue [1] (rule modification scope); Issue [7] user-added (Task C.2 tournament) |
| C.7       | Commit 3 (smoke test) | — |
| C.8       | Cross-cutting items / notes | Issue [6] |
| C.9       | Commit 3 (final) | Issue [2] (no version bump in commit 3) |
| D.1–D.5   | Commit 4 + Report template specifics | — |
| D.6       | Cross-cutting items / Deliverables | Step 7 CLAUDE.md decision |
| D.7       | Version cadence | Issues [2] + [3] |
| D.8       | Commit 4 (final) | — |

Every task traces to at least one design section + one constraint where applicable.
