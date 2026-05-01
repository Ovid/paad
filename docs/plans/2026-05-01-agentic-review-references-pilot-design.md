# Phase 1 Design — agentic-review references conversion (pilot)

**Date:** 2026-05-01
**Phase:** 1 of 5 in `docs/roadmap.md` (Skill References Conversion)
**Status:** Done (2026-05-01) — see retrospective below.
**Cross-phase notes:** `notes/convert-skills.md` (running source of truth for conventions).

## Phase 1 retrospective (2026-05-01)

Phase 1 is complete. All eight extractions landed on `ovid/skill-breakdown` across four logical commits (PR1 standalone; PR2–PR6 batched; PR7 standalone; PR8 standalone), plus version bumps from 1.14.0 to 1.16.0. SKILL.md shrank from 386 lines to 240 (~38%). The full red-green-refactor behavioral discipline this design proposed was applied to PR1; later PRs relied on the locked conventions plus structural-only verification (`make check-extracted-refs`) — see `notes/convert-skills.md` "agentic-review variance is stochastic" rationale for why per-PR behavioral verification was relaxed.

**Material deviation from the original plan:**

The plan assumed PRs 2–6 were "mechanical applications" of PR1's verbatim-move pattern. In practice, three of the five specialists (Logic & Correctness, Concurrency & State, Security) had **no distinctive inline instructions** in `SKILL.md` — only the common base prompt with the lens name swapped. Rather than skipping those PRs, three subagents were dispatched (one per lens) to think like that specialist and propose distinctive content. All three returned substantive recommendations that landed as **new authored content** in the corresponding ref files. The convention this established is recorded in `notes/convert-skills.md` "Finding: 'empty' specialists deserve authored content (PR2–PR6)." Phase 2+ should dispatch a similar think-like-this-specialist subagent before defaulting to "skip" on any empty lens.

**Layout adjustment after PR1:**

The original plan placed specialists at `references/specialists/<lens>.md`. The Agent Skills spec (https://agentskills.io/specification#file-references) says "Keep file references one level deep from SKILL.md," which the nested layout violated. Caught after PR1 landed; fixed by the flatten commit before PR2–PR8 began. All eight ref files now sit directly under `references/`. The plan tables and command snippets below were updated in the flatten commit.

**Open questions resolved:**

- **Subagent path resolution:** relative paths in the dispatch prompt resolve against the skill directory; no parent-side absolute-path computation needed. Recorded in `notes/convert-skills.md` "Subagent path resolution — verified mechanism (PR1)."
- **Fixture stability:** the two PR1 fixtures (`83aa677`, synthetic of `5f03453`) held up. Synthetic-fixture synthesis instructions for older commits documented in `notes/convert-skills.md`.

The original plan content below is preserved as historical record. For conventions Phase 2 should inherit, read `notes/convert-skills.md` first; this design doc second.

---

## Context

Paad's agentic skills currently inline every subagent's full instruction
set into the parent `SKILL.md`. When `/paad:agentic-review` activates,
the parent loads the full body — including ~30 lines of Spec Compliance
specialist prompt, ~90 lines of Phase 4 report template, and several
specialist-specific instruction blocks — even though most of that
content is only consumed by one dispatched subagent or one phase of the
parent's flow.

The Agent Skills specification supports moving this kind of content
into a `references/` directory so it loads on demand. Subagents can be
told to read a specific reference file before starting, keeping the
parent's context window slim and the specialists' instructions focused.
This phase validates that pattern on `agentic-review` end-to-end before
applying it to the other skills (Phases 2–5).

## Approach: pilot first

Phase 1 ships eight small PRs against `agentic-review`. PRs 2–6 are
mechanical applications of the pattern PR1 establishes; PR7 is a
higher-stakes variation (the single Verifier dispatch); PR8 is a
different sub-pattern (parent-loaded reference, not subagent-targeted).
Sequencing 1 → 2-6 → 7 → 8 lets us learn the most from the smallest
first PR, then ramp risk gradually.

After Phase 1 ships, a separate brainstorm + plan covers Phase 2
(`agentic-architecture`) using the conventions PR1 locked in.

### PR roadmap

| # | Extraction                                                        | New file                                                  |
|---|-------------------------------------------------------------------|-----------------------------------------------------------|
| 1 | Spec Compliance specialist (additional instructions block)        | `references/spec-compliance.md`               |
| 2 | Logic & Correctness specialist                                    | `references/logic-correctness.md`             |
| 3 | Error Handling & Edge Cases specialist                            | `references/error-handling.md`                |
| 4 | Contract & Integration specialist                                 | `references/contract-integration.md`          |
| 5 | Concurrency & State specialist                                    | `references/concurrency-state.md`             |
| 6 | Security specialist                                               | `references/security.md`                      |
| 7 | Verifier (Phase 3 detailed instructions)                          | `references/verifier.md`                                  |
| 8 | Phase 4 report template + backlog file shape                      | `references/report-template.md`                           |

PR1 is chosen as Spec Compliance because its content is the most
distinctive (the `category: out-of-scope-addition` tag, the
intent-source priority list, the retro-edited-spec contradiction
failure mode, missing-artifact detection). Distinctive content is
easier to detect failure on if the subagent silently no-ops on the
ref read.

## Per-PR mechanics — red, green, refactor

Each PR follows the same shape, with PR1 doing extra work to lock down
conventions for PRs 2-8 to inherit.

### Phase 0 (PR1 only): pick the fixture

Find a commit on this repo's history that exercises the Spec Compliance
specialist's distinctive behaviors (out-of-scope addition, missing
artifact, retro-edited spec contradiction, plus a sibling commit for
the bail-out case where no intent source exists). Record the SHA(s) in
`notes/convert-skills.md` under "Fixtures used." Future PRs reuse this
fixture or pick a sibling.

### Red

Two sub-steps.

1. **Capture baseline.** Check out the fixture commit, run
   `/paad:agentic-review` with the *current* inline-instructions skill,
   save the relevant section of the report to
   `notes/baselines/PR<N>-<extraction>.md`. Then write a short
   *behavioral checklist* alongside it — 4-6 bullet items naming what
   findings should appear and why (e.g., "produces 1 Missing finding
   pointing at `STRINGS.error.somekey`", "tags 1 finding as
   `category: out-of-scope-addition`"). This is what we expect to
   preserve.
2. **Stage the broken extraction.** Move the content into the new
   `references/...` file but **do not** update the dispatch prompt —
   leave it pointing at thin air. Re-run against the fixture. The
   relevant section should now miss the distinctive behaviors. If it
   doesn't, the inline content wasn't doing work and the test isn't
   discriminating — stop and rethink.

### Green

Update the dispatch prompt in `SKILL.md` to instruct the subagent to
read the reference file first. Re-run against the fixture. Output should
hit every item on the behavioral checklist. The structural Makefile
check (added in PR1, see below) should also pass.

### Refactor

Tighten the dispatch prompt — remove scaffolding the ref now duplicates.
Try a small variant fixture (e.g., the bail-out case for Spec
Compliance). Re-run after each tightening to confirm still green.

### Commit hygiene

Bump the version with `make bump-version VERSION=X.Y.Z`, ensure
`make test` is clean (existing checks plus the new structural
guardrail), smoke-test once more before opening the PR.

## Structural guardrails

> **Retrospective deviation (2026-05-01):** The design below promises
> per-PR behavioral subagent tests as "the test of record." In
> practice, only PR1 captured baselines (`notes/baselines/PR1-*.md`);
> PR2–PR8 relied on the structural Makefile guardrail plus the locked
> conventions documented in `notes/convert-skills.md`. See the Phase 1
> retrospective at the top of this document for the rationale (skill
> output is stochastic; zero-finding fixtures are weak regression
> tests). The `notes/baselines/PR{1..8}-*.md` line in the deliverables
> summary should be read as PR1-only. The text below is preserved as
> historical record of the original design.

The behavioral subagent test is the test of record. The Makefile
addition is a CI guardrail — cheap, repeatable, catches accidental
regressions (someone re-inlines content during a future edit, deletes
a ref file, breaks a dispatch path).

### Manifest file

`scripts/extracted-refs.tsv`. Three tab-separated columns, one row per
landed extraction. Comments via `#`.

```
# skill	ref-path-relative-to-skill	sentinel-phrase
agentic-review	references/spec-compliance.md	Internal spec contradictions (retro-edited specs)
```

Each PR adds exactly one row.

### New script

`scripts/check_extracted_refs.sh`. For each row in the manifest:

1. Assert `plugins/paad/skills/$SKILL/$REF_PATH` exists.
2. Assert the sentinel phrase is *absent* from
   `plugins/paad/skills/$SKILL/SKILL.md` (content was moved out).
3. Assert the sentinel phrase is *present* in the ref file (sanity —
   it actually moved, didn't get accidentally deleted).
4. Assert `$REF_PATH` appears at least once in `SKILL.md` (dispatch
   references the new path).

Exit 1 on any failure with a clear message naming the row and the
failed assertion.

### Makefile addition

New target `check-extracted-refs` runs the script. Add it to the `test`
target's dependency list after the existing checks so existing failures
surface first:

```
test: validate check-versions check-skill-versions check-digraphs check-help check-readme check-frontmatter check-extracted-refs ## Run all checks
```

### Sentinel choice

Pick a distinctive, semantically meaningful phrase from the extracted
content — not boilerplate. For Spec Compliance, "Internal spec
contradictions (retro-edited specs)" works: it's distinctive, future
authors are unlikely to reintroduce verbatim, and it carries enough
meaning that even a textual match implies the content is back.

### How this composes with red-green-refactor

Adding the manifest row is part of the structural red — `make test`
fails until the move happens. Once the move is done and the dispatch is
wired, structural and behavioral both go green together. The structural
check stays as a permanent guardrail after merge.

## PR1 concrete checklist

In order, gated:

1. **Branch.** Stay on the current working branch (`ovid/skill-breakdown`).
   Phase 1 lands as a series of commits on this branch — no per-PR
   feature branches. The "PR" framing in the rest of this design refers
   to a logical extraction unit (one commit or small commit cluster),
   not a separate GitHub PR.
2. **Pick fixture.** Find a commit on this repo's history that
   exercises Spec Compliance behaviors (out-of-scope addition,
   missing artifact, retro-edited contradiction, plus a sibling for
   bail-out). Record SHA(s) in `notes/convert-skills.md` under
   "Fixtures used."
3. **Capture baseline.** Check out fixture, run
   `/paad:agentic-review`, save Spec Compliance section to
   `notes/baselines/PR1-spec-compliance.md` plus a behavioral
   checklist (4-6 bullets: what findings should appear and why).
4. **Add manifest infrastructure.** Create
   `scripts/extracted-refs.tsv` (header + Spec Compliance row),
   `scripts/check_extracted_refs.sh`, wire into Makefile `test`
   target. Run `make test` — should fail on the new check (red).
5. **Stage broken extraction.** Move content to
   `references/spec-compliance.md`, leave dispatch
   unwired. Re-run against fixture. Spec Compliance section should
   miss checklist items (behavioral red). Document what regressed.
6. **Wire dispatch.** Update `SKILL.md` Phase 2 dispatch to instruct
   subagent to read the ref. Re-run fixture. Output hits checklist
   (green). `make test` passes (structural green).
7. **Refactor.** Tighten dispatch prompt; remove duplicated
   scaffolding; re-run fixture; confirm still green.
8. **Lock subagent path-resolution answer** in
   `notes/convert-skills.md` — which of the three options actually
   worked (relative path inherited / absolute path resolved by
   parent / something else).
9. **Bump version, commit, open PR** with baseline + checklist +
   fixture SHA in PR description.

## PRs 2-8 inherit the conventions

PRs 2-6 are mechanical:
- Pick a sibling fixture or reuse PR1's if it exercises the relevant
  specialist's behaviors.
- Capture baseline + behavioral checklist for that specialist.
- Add manifest row, do the broken-extraction red, then green, then
  refactor.

PR7 (Verifier) follows the same pattern but the dispatch is the single
post-specialist verifier, not one of the parallel specialists. Higher
stakes because the verifier's output drives the in-scope/out-of-scope
classification and backlog dedup; baseline checklist must cover at
least: blame default, reasoning promotion, cosmetic-touch demotion,
backlog ID minting.

PR8 (report template) is a different sub-pattern. The report template
is parent-side material, not a subagent prompt. The "extraction" moves
the template into `references/report-template.md`, and the parent's
Phase 4 instructions tell the parent agent (not a subagent) to read
the ref when entering report-write phase. Behavioral test: the report
file produced has the same structure as before. Same fixture flow
applies; no new dispatch site, just a parent self-read.

## Open questions for PR1 to resolve

- **Subagent path resolution.** The Agent Skills spec says relative
  paths resolve to the skill directory root for the activating agent.
  It's silent on subagents. Three candidates: (1) subagent inherits
  the parent's "skill dir as command root" — relative paths in
  dispatch prompts Just Work; (2) subagent lands in user-repo CWD
  with no skill awareness, parent must resolve to absolute path
  before embedding; (3) some middle ground (env var, prompt-time
  substitution). PR1 must lock this down and record the verified
  answer in `notes/convert-skills.md`. The other PRs depend on this
  convention.

- **Fixture stability.** Pointing at a known commit on this repo's
  history is the choice for now (over a hand-crafted synthetic
  fixture). If history rewrites or branch deletes break the
  reference, promote to a tagged commit or move to a synthetic
  fixture under `paad/test-fixtures/`. Track in
  `notes/convert-skills.md`.

## Out of scope for Phase 1

- Other paad skills (Phases 2–5).
- Any rewrite of agentic-review's behavior. If the pilot uncovers a
  real bug in agentic-review, file separately.
- Rolling out the manifest pattern to skills outside agentic-review.
  The manifest will accumulate cross-skill rows naturally as Phase 2+
  ship.

## Post-pilot

After the eight PRs land:
1. Update `docs/roadmap.md` Phase Structure: Phase 1 → Done.
2. Run `/roadmap` to brainstorm Phase 2 (agentic-architecture).
3. Phase 2's design doc reuses the conventions locked in by Phase 1
   (manifest format, dispatch prompt shape, baseline-checklist style).

## Deliverables summary

- `plugins/paad/skills/agentic-review/references/{spec-compliance,logic-correctness,error-handling,contract-integration,concurrency-state,security}.md`
- `plugins/paad/skills/agentic-review/references/{verifier,report-template}.md`
- `plugins/paad/skills/agentic-review/SKILL.md` — slimmer body, dispatches reference paths.
- `scripts/extracted-refs.tsv` (8 rows after Phase 1 completes).
- `scripts/check_extracted_refs.sh`.
- `Makefile` — `check-extracted-refs` target wired into `test`.
- `notes/convert-skills.md` — fixtures used, path-resolution answer, conventions established.
- `notes/baselines/PR{1..8}-*.md` — behavioral checklists per extraction.
