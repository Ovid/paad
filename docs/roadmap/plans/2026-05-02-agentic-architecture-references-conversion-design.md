# Phase 2 Design — agentic-architecture references conversion

**Date:** 2026-05-02
**Phase:** 2 of 5 in `docs/roadmap/roadmap.md` (Skill References Conversion Roadmap)
**Branch:** `agentic-architecture-references-conversion`
**Cross-phase notes:** `notes/convert-skills.md` (running source of truth for conventions; Phase 1 locked them, Phase 2 inherits and appends to the same file)
**Phase 1 design (template):** `docs/roadmap/plans/2026-05-01-agentic-review-references-pilot-design.md`

## Context

Phase 1 converted `agentic-review` to use the Agent Skills `references/` pattern: subagent and parent-side instructions move to per-purpose ref files, loaded on demand instead of preloaded into the parent SKILL.md. The pilot landed eight extractions, shrank SKILL.md by ~38%, and produced a body of locked conventions in `notes/convert-skills.md`. Phase 2 applies the validated pattern to `plugins/paad/skills/agentic-architecture/SKILL.md` (currently 280 lines, plugin v1.18.0).

agentic-architecture is structurally similar to agentic-review (multi-specialist + verifier + report) but routes simpler: no in-scope/out-of-scope axis, no `[OOSA]` short-circuit, no persistent backlog dedup. Five specialists, not six. Two extra static catalogs at the bottom of the file (Flaw/Risk Type Reference, Strength Category Reference) that Phase 1 did not have to think about.

## Scope

**In scope (7 extractions):**

| # | Extraction                                | New file                                          | Sub-pattern                  |
|---|-------------------------------------------|---------------------------------------------------|------------------------------|
| 1 | Integration & Data specialist             | `references/integration-data.md`                  | subagent dispatch + enrich   |
| 2 | Structure & Boundaries specialist         | `references/structure-boundaries.md`              | subagent dispatch + enrich   |
| 3 | Coupling & Dependencies specialist        | `references/coupling-dependencies.md`             | subagent dispatch + enrich   |
| 4 | Error Handling & Observability specialist | `references/error-handling-observability.md`      | subagent dispatch + enrich   |
| 5 | Security & Code Quality specialist        | `references/security-code-quality.md`             | subagent dispatch + enrich   |
| 6 | Verifier (Phase 3 dispatch)               | `references/verifier.md`                          | subagent dispatch + enrich   |
| 7 | Report template (Phase 4)                 | `references/report-template.md`                   | parent self-read (PR8 variant) |

**Out of scope:**

- Other paad skills (Phases 3–5).
- Changes to agentic-architecture's overall flow (phases, dispatch shape, output format). **In scope:** improvements to each lens's findings-quality, including modification or removal of existing "Look for" rules where the enrichment surfaces something better. The existing inline rules are starting points, not contracts; lens quality is the goal.
- The bottom-of-file static catalogs (Flaw/Risk Type Reference ~34 entries, Strength Category Reference ~14 entries). They stay inline. Revisit in a follow-up if profiling shows parent-load matters; the catalogs are loaded into specialist prompts via the dispatch table, so extracting would force a "specialists pull from ref vs. parent inlines names" decision that muddies Phase 2's pattern-transfer test.

## Inheritance from Phase 1

Every convention locked in `notes/convert-skills.md` applies verbatim. Phase 2 does not re-prove them. The load-bearing ones:

- **Subagent path resolution.** Relative paths in dispatch prompts resolve against the skill directory; no parent-side absolute-path computation. (Verified in PR1.)
- **Dispatch prompt template.** Each extracted lens's `SKILL.md` paragraph reads:
  > **\<Lens\> additional instructions:** The \<Lens\> specialist's instructions live at `references/<lens>.md`. That file covers \<one-line inventory\>. The dispatch prompt for the \<Lens\> specialist must include this instruction verbatim:
  >
  > > Read `references/<lens>.md` from this skill's directory before producing findings; treat its instructions as binding. Begin your output with the literal token `[ref-loaded:<lens>]` on its own line so the verifier can confirm the ref was read.
- **Reference file shape.** `# <Lens> — additional instructions` heading → role-statement blockquote → body.
- **Parent-self-read variant.** Used for non-subagent content (extraction 7, the report template). Role statement names the parent agent as reader; dispatch sentence is "Before [phase action], read [the ref]" instead of "the dispatch prompt for the subagent must include…".
- **Structural guardrails.** `scripts/extracted-refs.tsv` (manifest), `scripts/check_extracted_refs.sh` (asserts ref exists, sentinel moved out of SKILL.md, sentinel present in ref, ref path referenced in SKILL.md), wired into `make test` via the `check-extracted-refs` target. Phase 2 adds 7 new rows; no script or Makefile changes needed.
- **Behavioral verification uses `--plugin-dir`.** Always: `claude --plugin-dir ./plugins/paad`. Without this flag, the marketplace-cached older version of paad gets loaded and any test against it is meaningless.
- **`[ref-loaded:<lens>]` echo tokens.** Each subagent emits the token on line 1 so the verifier can confirm the ref was read. Used by the smoke test as the signal that dispatch wired correctly.
- **`BAIL: <lens-name> <reason>` token shape.** Each specialist ref with a bail-out clause emits this on line 2 of bail output and stops.

## Per-extraction mechanics

Every specialist + verifier extraction (extractions 1–6) gets **verbatim move + authored enrichment**. The reference file shape:

```markdown
# <Lens> — additional instructions

> <one-paragraph role statement: name the role, the dispatching skill+phase
> ("agentic-architecture, Phase 2 specialist dispatch"), the parent-vs-this-file
> boundary, and the imperative to read before producing findings.>

## Verbatim from SKILL.md
<the existing "Look for: X, Y, Z" paragraph, moved as-is>

## Authored enrichment

### Anchoring
<lens-specific anchor rule — what the specialist must locate in the
codebase before producing findings>

### Bail-out
<lens-specific condition that warrants emitting `BAIL: <lens-name> <reason>`
and stopping. E.g., for Integration & Data: not a distributed system / no
service boundaries / no async surface.>

### Finding subtypes (where applicable)
<short closed-set taxonomy>

### Drop rules
<patterns the specialist should NOT report — common false positives
specific to this lens>

### Severity floor (where applicable)
<minimum impact level for this lens to use Low/Medium/High consistently>
```

Subsection headings vary per lens — `Anchoring` and `Bail-out` apply to most; `Finding subtypes` only where a useful taxonomy exists; `Severity floor` only where the lens has obvious consistency issues. The enrichment subagent decides which apply.

### Authoring procedure (per lens)

**Two-stage dispatch discipline.**

1. **Sequential at the lens level.** Lens N's enrichment fully completes (both subagents back, judging done, ref composed, dispatch wired, manifest row green) before lens N+1 starts. This applies to commit 2's four lenses *and* to the verifier in commit 3. Cost: commit 2 takes ~4× as long as a parallel batch — intentional, because review depth dominates wall-clock time now that lens quality is in scope.

2. **Tournament within each lens — two competing subagents in parallel.** For each lens, dispatch **two** `general-purpose` subagents in a single message (parallel tool calls), with **identical prompts and identical resources**. Each subagent is told it is competing against another subagent dispatched in parallel; the most accurate and complete enrichment proposal wins five points. The orchestrator and Ovid judge both proposals side-by-side and the winning content (or a merged best-of-both) becomes the ref's authored-enrichment section.

Each `general-purpose` subagent receives:

- the lens's verbatim paragraph from `SKILL.md` — its **starting point, not a contract**. The subagent is invited to propose modifications, removals, or replacements where existing rules are weak, wrong, or incomplete.
- its assigned flaw types and strength categories from the dispatch table,
- the Phase 1 examples in `plugins/paad/skills/agentic-review/references/security.md` and `plugins/paad/skills/agentic-review/references/concurrency-state.md` as templates,
- instruction to propose content that improves the lens's quality — both consistency (taxonomies, anchoring, bail-outs, drop rules, severity floors) *and* findings-quality (better detection of real architectural problems). No padding, no restating what's already in the verbatim block.
- **tournament framing** (append verbatim to the end of each subagent's prompt): *"You are competing against another subagent dispatched in parallel with this same prompt and the same resources. The orchestrator and Ovid will judge both proposals against each other; the subagent that produces the most accurate and complete enrichment proposal wins five points. Push for depth, specificity, and lens-improving structure — a thin or generic proposal will lose."*

**Judging.** After both proposals return, the orchestrator surfaces them side-by-side to Ovid with: (a) what each proposes per ref-shape sub-section (anchoring, bail-out, finding subtypes, drop rules, severity floor), (b) where they agree, (c) where they diverge, (d) which existing inline rules each modifies. Ovid picks the winner — or instructs the orchestrator to compose a merged ref drawing the strongest sub-sections from each. Both outcomes are normal; "merged" is acceptable when each proposal contributed a strong subsection the other lacked.

If both proposals are thin (no distinctive structure to add, no improvements to existing rules), record that and land the verbatim-only version. If only one proposal is thin and the other is strong, the strong one wins by default.

### Verifier specifics (extraction 6)

Same shape as the specialists. Verbatim move = the existing prose at `SKILL.md:108-120`. Authored enrichment expected (per the brainstorm decision):

- max-confidence rule for cross-specialist agreement (mirror Phase 1 verifier's resolution),
- evidence-quality drop rule (no symbol reference → drop),
- impact-tiebreaker (max vs. average vs. lowest),
- "small file" rejection-trap drop rule (file size alone is not a god-object signal),
- explicit "what counts as verified" checklist (file:line readable, symbol exists at that line, excerpt matches actual code).

agentic-architecture's verifier ref will be smaller than Phase 1's `references/verifier.md` because there is no in-scope/out-of-scope routing, no backlog dedup, no field-encoding rules, no sole-writer rule.

### Report template specifics (extraction 7)

Parent-self-read variant. Role statement names the parent agent (the orchestrator activating `paad:agentic-architecture`) as reader, not a dispatched subagent. Body = the verbatim Phase 4 report template currently at `SKILL.md:128-199` plus the empty-section / coverage-checklist sub-templates. SKILL.md Phase 4 keeps parent-side state (output path computation, `mkdir -p paad/architecture-reviews/`) and the dispatch sentence becomes:

> Before writing the report, read `references/report-template.md` — its instructions are binding for the report's structure, the Coverage Checklist tables, and empty-section behavior.

No `[ref-loaded:…]` token (no subagent to echo it). The smoke test for this extraction is "a generated report has the expected structure" instead.

## Commit-by-commit roadmap

All four commits land on `agentic-architecture-references-conversion`. Each commit ends with `make test` clean.

### Commit 1: Integration & Data (lead extraction)

The proof point that conventions transfer to agentic-architecture.

1. Author the ref. Dispatch the think-like-this-Integration-&-Data-specialist subagent. Compose `references/integration-data.md` per the shape above. Expected enrichment: not-distributed bail-out (extract the inline hint already in `SKILL.md:98`), idempotency anchoring, transactional-boundary check, distributed-monolith detection criteria.
2. Wire the dispatch. Replace the existing "Integration & Data additional instruction" paragraph in `SKILL.md` with the Phase 1 dispatch shape (prose inventory + binding blockquote with `[ref-loaded:integration-data]` echo token).
3. Add manifest row to `scripts/extracted-refs.tsv` with a distinctive sentinel from the ref's body.
4. **Smoke test** (the locked light-behavioral check): `claude --plugin-dir ./plugins/paad`, run `/paad:agentic-architecture` against this paad repo, then assess against this four-outcome table:

    | Token `[ref-loaded:integration-data]` | Not-distributed bail-out | Verdict                                                  |
    |---|---|---|
    | present | fires        | **Pass** — dispatch wired, lens correctly bailed         |
    | present | doesn't fire | **Escalate to Ovid** — surface findings, ask if reasonable (lens may have judged paad has integration surface, e.g. marketplace-as-remote-source) |
    | absent  | (any)        | **Fail** — ref wasn't read; structural extraction broken |

5. **Append cross-cutting findings to `notes/convert-skills.md`** — agentic-architecture-specific dispatch-shape tweaks, path-resolution surprises, smoke-test outcome. If nothing surfaced, append a one-line note saying so; silence is also evidence.
6. `make test` clean, commit. (No version bump — bumps are deferred to commit 4 per the Version cadence section below.)

### Commit 2: Four remaining specialists (batched)

Mechanical application of the per-extraction shape to Structure & Boundaries, Coupling & Dependencies, Error Handling & Observability, Security & Code Quality. Order within the commit doesn't matter — all four are independent extractions; the dispatch in `SKILL.md` is a flat list of paragraphs.

For each lens **sequentially** (per the Authoring procedure): dispatch the per-lens enrichment subagent → review proposal with Ovid (surface modifications to existing rules explicitly) → compose ref → wire dispatch → add manifest row. No per-lens smoke test (locked verification scope is lead-only). After all four lenses land, **append per-lens enrichment outcomes to `notes/convert-skills.md`** (what the subagent proposed, what landed, what was rejected; whether existing rules were modified). Commit. (No version bump — deferred to commit 4.)

### Commit 3: Verifier

`references/verifier.md` per the verifier specifics above. Wire dispatch in SKILL.md Phase 3 with the binding blockquote + `[ref-loaded:verifier]` token. Smoke test: confirm token appears in verifier output during a `paad:agentic-architecture` run. Add manifest row. **Append the verifier enrichment outcome to `notes/convert-skills.md`** (same shape as commit 2 — what was proposed, what landed, whether existing prose was modified). Commit. (No version bump — deferred to commit 4.)

### Commit 4: Report template

`references/report-template.md` per the report-template specifics above (parent self-read variant). SKILL.md Phase 4 keeps parent-side state (output path, mkdir) and instructs the parent to read the ref before writing. No `[ref-loaded:…]` token. Smoke test: confirm a generated report has the expected structure (Strengths section, Flaws section, Coverage Checklist tables for all 34 flaws + 14 strengths, Hotspots, Next Questions, Analysis Metadata). Add manifest row.

**Update CLAUDE.md §Project structure** (the directory tree near the top of the file) to show `references/` subdirectories under both `agentic-review/` (cleanup of a Phase 1 omission) and `agentic-architecture/` (the Phase 2 addition). Each affected skill folder gains a sibling `references/` entry below its `SKILL.md` line, annotated as on-demand content per the Agent Skills spec. This is a small documentation edit included in commit 4 by Ovid's explicit decision (CLAUDE.md review, step 7) — folded in here so it lands as a planned phase deliverable, not an afterthought.

Run `make bump-version VERSION=1.19.0` — single end-of-phase bump (per the Version cadence section); it updates `plugin.json`, `marketplace.json`, and every SKILL.md announce line atomically. `make test` clean, commit.

### Version cadence

Current is `v1.18.0`. Final: **single bump to `v1.19.0` after commit 4.** Commits 1–3 leave the version untouched. Commit 4's recipe explicitly invokes `make bump-version VERSION=1.19.0` so the bump touches `plugin.json`, `marketplace.json`, and every SKILL.md announce line atomically. The mid-phase versionless commits make `agentic-architecture` reachable as 1.18.0-with-commits-1-through-N during the work; users who pin between commits get a coherent intermediate state without an ephemeral version label.

## Cross-cutting items

### What gets recorded in `notes/convert-skills.md` as Phase 2 ships

Phase 1 used `notes/convert-skills.md` as the running source of truth for conventions. Phase 2 appends to the same file as findings emerge:

- Whether the dispatch shape transfers cleanly to a different parent. If anything had to be tweaked for agentic-architecture (e.g., the per-specialist dispatch paragraph format adapted because parent input is a codebase not a diff), record the delta.
- Per-lens enrichment outcomes — for each of the 5 specialists + verifier, did the think-like-this-specialist subagent return useful authored content, or did the lens land verbatim-only? Phase 1's "empty specialists deserve authored content" finding had a clear cross-skill implication; Phase 2's "non-empty specialists where enrichment was attempted anyway" outcome will inform Phases 3–5.
- The smoke-test-as-verification approach: did paad-as-fixture surface any signal beyond "the dispatch wired correctly"? If yes, document for Phase 3+; if no, that's also a finding (it confirms the smoke test's signal is narrow, not broad).
- Any drift from Phase 1's locked conventions caught while extracting (e.g., if subagent path-resolution behaves differently for a whole-repo specialist than a diff-specialist, that's load-bearing for Phase 3).

### Deliverables summary

- `plugins/paad/skills/agentic-architecture/references/{integration-data,structure-boundaries,coupling-dependencies,error-handling-observability,security-code-quality,verifier,report-template}.md` — 7 files.
- `plugins/paad/skills/agentic-architecture/SKILL.md` — slimmer body; specialist dispatches replaced with the prose-inventory + binding-blockquote shape; Phase 4 dispatches the parent-self-read.
- `scripts/extracted-refs.tsv` — 7 new rows (skill column = `agentic-architecture`).
- `notes/convert-skills.md` — Phase 2 cross-cutting findings appended.
- `CLAUDE.md` — §Project structure tree updated to show `references/` subdirectories under both `agentic-review/` (Phase 1 cleanup) and `agentic-architecture/` (Phase 2 new). Lands in commit 4.
- 4 logical commits on `agentic-architecture-references-conversion`. Single end-of-phase version bump (1.18.0 → 1.19.0) lands in commit 4.

### Post-Phase-2

1. Mark Phase 2 Done in `docs/roadmap/roadmap.md` Phase Structure table.
2. `/roadmap` to brainstorm Phase 3 (`agentic-a11y`). Phase 3 reuses the same conventions; if Phase 2 surfaced any drift from Phase 1, Phase 3 inherits the updated `notes/convert-skills.md`.

## Open risks / things worth flagging

- **The smoke test's signal is narrow.** It proves "dispatch wired correctly," not "extraction preserves quality." If a future agentic-architecture run produces noticeably worse findings after Phase 2, suspect the enrichment content (not the structural extraction) and treat as a real bug.
- **Six enrichment subagent dispatches across the phase, sequential.** 1 in commit 1 (Integration & Data), 4 in commit 2 (the remaining specialists), 1 in commit 3 (verifier). Sequential dispatch (per the Authoring procedure) means commit 2's wall-clock cost is roughly 4× a parallel batch — intentional to preserve review depth. Budget time per enrichment proposal; do not rubber-stamp.
- **paad-as-fixture is intentionally a weak signal.** Small repo, no distributed system, low complexity. It catches "dispatch failed" cleanly but not "ref content is wrong." Acceptable given the locked verification scope; flag if this proves insufficient.
- **Phase 1 PR1's path-resolution proof.** Phase 1's PR1 verified relative paths in dispatch prompts resolve against the skill directory. Phase 2's lead extraction does not re-prove this — the smoke test only confirms the echo token appears (which means the ref was read, which means the path resolved). If the smoke test fails on the token check, suspect path resolution first; the failure mode looks identical to a malformed dispatch prompt.
