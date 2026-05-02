---
date: 2026-05-02
phase: 'Phase 2: agentic-architecture references conversion'
model: claude-opus-4-7
design_file: docs/roadmap/plans/2026-05-02-agentic-architecture-references-conversion-design.md
plan_file: docs/roadmap/plans/2026-05-02-agentic-architecture-references-conversion-plan.md
pushback:
  total: 7
  critical: 0
  important: 2
  minor: 5
alignment:
  total: 3
  critical: 0
  important: 0
  minor: 3
---

# Phase 2: agentic-architecture references conversion — Decision Log

## Pushback Findings

### [1] Enrichment-of-every-lens conflicts with "no behavior changes" scope
- **Severity:** Important
- **Category:** Contradiction
- **Summary:** The design's Section 1 and Section 4 say "out of scope: behavior changes to agentic-architecture itself," inheriting Phase 1's purely-structural refactor framing. But Question 2 of the brainstorm picked option (ii) — verbatim move + authored enrichment for every lens — which can subtly change which findings each lens emits (via severity floors, drop rules, modified anchoring). The two cannot both hold. Phase 1's empirical evidence supports a narrower enrichment heuristic (only lenses with no distinctive inline content), but Ovid's intent for Phase 2 is broader: improve each lens's quality, including questioning existing inline rules. The "out of scope" line is wrong as written.
- **Resolution:** fixed-in-design — Section 1, Section 4, and the "Authoring procedure" sub-section will be updated to make quality improvement explicit and treat existing inline rules as starting points (not contracts). Edits applied after all pushback findings are walked.

### [2] Version cadence (4 minor bumps) is heavier than Phase 1 precedent
- **Severity:** Minor
- **Category:** Ambiguity
- **Summary:** The design suggests minor bumps per logical commit (1.19.0 → 1.20.0 → 1.21.0 → 1.22.0). Phase 1 went 1.14.0 → 1.16.0 (2 minor bumps across 4 commits + flatten). Phase 2 is structurally similar (refactor + now also lens-quality improvements per Issue [1]). Whether each commit deserves a minor bump or a patch bump depends on whether lens-quality improvements count as user-visible (likely yes, per Issue [1] resolution). The design notes the cadence is negotiable but does not pick a default.
- **Resolution:** fixed-in-design — single bump at the end of Phase 2 (1.18.0 → 1.19.0 once, after commit 4). No mid-phase version landings. Commits 1–3 leave the version untouched; commit 4 includes the `make bump-version VERSION=1.19.0` step.

### [3] Design says "Bump version" but does not reference `make bump-version`
- **Severity:** Minor
- **Category:** Omission
- **Summary:** Each commit's recipe ends with "Bump version" without naming the `make bump-version VERSION=X.Y.Z` target that updates `plugin.json`, `marketplace.json`, and every SKILL.md announce line in one shot (per CLAUDE.md). Phase 1's design named the target explicitly. A future contributor reading only the Phase 2 design might bump versions by hand and miss one of the three sites, leaving the announce line drifted from `plugin.json`.
- **Resolution:** fixed-in-design — Commit 4's step list will name `make bump-version VERSION=1.19.0` explicitly, mirroring Phase 1's design discipline. Commits 1–3 do not bump (per Issue [2]).

### [4] Specialist enrichment subagent dispatch parallelism unspecified
- **Severity:** Minor
- **Category:** Ambiguity
- **Summary:** Commit 2 dispatches four think-like-this-specialist subagents (one per remaining lens). The design does not say whether to dispatch them in parallel (per `superpowers:dispatching-parallel-agents`) or sequentially. Parallel is faster but produces 4 concurrent proposals to review, which may overwhelm review bandwidth. Sequential is slower but lets each proposal inform the next. Same question applies to the verifier (commit 3) — could in principle be dispatched alongside commit 2 since they are independent.
- **Resolution:** fixed-in-design — sequential dispatch always. Each enrichment subagent runs after the previous proposal is reviewed and the ref file composed. Now that lens quality is in scope (Issue [1]), review depth dominates wall-clock time. Cost: commit 2 takes ~4× longer than commit 1. The "Authoring procedure" sub-section will be updated to make the sequential constraint explicit.

### [5] Smoke test success criterion is ambiguous when token and bail-out diverge
- **Severity:** Minor
- **Category:** Ambiguity
- **Summary:** Commit 1's smoke test requires both (a) the `[ref-loaded:integration-data]` token appearing AND (b) the not-distributed bail-out firing. The design does not specify the call when only (a) fires — token present but the lens emits findings instead of bailing. That outcome is ambiguous: the lens may have judged paad has *some* integration surface (e.g., the marketplace-as-remote-source pattern), or it may be ignoring its own bail-out instruction. Without a rule, the agent running the smoke test will not know whether to pass or escalate.
- **Resolution:** fixed-in-design — token present + bail-out fires = pass. Token absent (regardless of bail-out) = fail (dispatch wiring broken). Token present + no bail = **escalate to Ovid**: surface the lens's findings and ask whether the judgment is reasonable. Treats (a) as the load-bearing dispatch check and (b) as a lens-quality probe, not a hard gate. The Commit 1 smoke-test step will spell out the four-outcome table.

### [6] No per-commit discipline for appending to `notes/convert-skills.md`
- **Severity:** Minor
- **Category:** Omission
- **Summary:** Section 4 says cross-cutting Phase 2 findings get recorded in `notes/convert-skills.md` "as Phase 2 ships," but the commit-by-commit roadmap does not include "append to notes/convert-skills.md" as a per-commit step. A literal-minded executor following the roadmap step-by-step would skip the notes-file update because it is not an enumerated step. Phase 1 had the same gap and Ovid hand-maintained it; for Phase 2, making it explicit per-commit reduces the dependence on memory.
- **Resolution:** fixed-in-design — add "Append cross-cutting findings to `notes/convert-skills.md` (or note 'no findings this commit')" as the final step before commit on commits 1, 2, 3. Skip commit 4 (report-template extraction is sui generis; Phase 1 PR8 already covered the pattern, nothing new to record).

### [7] (user-added) Enrichment subagents must be dispatched as a competitive tournament
- **Severity:** Important
- **Category:** Omission
- **Summary:** Surfaced by Ovid post-step-11 (after the /roadmap run technically completed), applying the §Per-Phase Checklist File "Provenance of findings appended after the Na tick" pattern by analogy to a post-decision-log finding. The design's Authoring procedure dispatches a single enrichment subagent per lens, then reviews. This omits a known prompt-engineering technique that measurably improves output quality: dispatch TWO subagents in parallel with identical prompts, tell each it is competing against the other for "five points" awarded by the orchestrator+Ovid, then judge both proposals side-by-side and pick the winner (or compose a merged best-of-both). Phase 1 did not use this pattern; Phase 2 should, given lens-quality improvements are now in scope (Issue [1]). The two-stage discipline (sequential at lens level + tournament within each lens) preserves Issue [4]'s review-depth constraint while doubling the proposal surface.
- **Resolution:** fixed-in-design + fixed-in-plan — design's §"Authoring procedure (per lens)" rewritten to describe the two-stage discipline (sequential at lens level, tournament within each lens) with the verbatim "tournament context" framing for the subagent prompt. Plan's enrichment-dispatch tasks (A.2, B.1–B.4 via inherited pattern, C.2 directly) updated to dispatch two subagents in parallel via two `Agent` calls in a single message, with judging step folded in. Cost: doubles the per-lens subagent surface (12 dispatches across the phase instead of 6); accepted because review depth + lens quality dominate wall-clock time per Issues [1] and [4].

## Alignment Findings

### [1] Plan does not define recovery path on smoke-test FAIL
- **Severity:** Minor
- **Category:** tdd-format
- **Summary:** Tasks A.7, C.7, and D.5 each define the smoke-test verdict (Pass / Escalate / Fail) but only Task A.7's verdict table says what FAIL means ("ref wasn't read; structural extraction broken"). None of the three tasks say what the executor should DO after a FAIL — go back to which prior task, re-run which check. Phase 1's design had a "stop and rethink" hint when the broken-extraction red didn't behave as expected; Phase 2's plan inherits the same need but does not satisfy it.
- **Resolution:** fixed-in-plan — add a single "Smoke-test failure recovery" section at the top of the plan that all three smoke-test tasks (A.7, C.7, D.5) reference. Centralizes the recovery path; eliminates near-identical sub-steps in three places.

### [2] Pre-flight Task 0.1 does not address unstaged /roadmap artifacts
- **Severity:** Minor
- **Category:** out-of-scope
- **Summary:** When a future agent picks up this plan, the working tree contains three uncommitted /roadmap artifacts (checklist, design, plan). Task 0.1 says `git status --porcelain` may show them but does not tell the executor what to do. Two failure modes: artifacts stay uncommitted forever (executor only stages planned paths in Task A.10), or they ride along with commit 1 (executor uses `git add -A`), blurring the boundary between /roadmap setup and the agentic-architecture extraction.
- **Resolution:** fixed-in-plan — add a step to Task 0.1: "Commit the /roadmap artifacts as a separate commit BEFORE starting Phase A." Suggested message covers checklist + design + plan together. Keeps Phase A's commits clean and matches "one logical change per commit" discipline.

### [3] Task D.2 does not define "real omission" or where to "file separately"
- **Severity:** Minor
- **Category:** design-gap
- **Summary:** Task D.2 says "If the move surfaces a real omission in the template, file separately and revisit; do not enrich here." Two ambiguities: (a) what counts as a "real omission" — subjective preference vs. structural defect, and (b) where "file separately" means — GitHub issue, new line in roadmap, bug tracker, notes file. This matters because the report-template extraction is the one place in Phase 2 where lens-quality improvements are explicitly out of scope; without a sharp bar, an executor might either silently enrich (breaking the verbatim contract) or over-flag stylistic preferences as omissions.
- **Resolution:** fixed-in-plan — tighten Task D.2 wording. Define "real omission" as "structural defect that makes the template unusable as-written (e.g., section heading with no closing, malformed Coverage Checklist row count)" — not subjective preferences. Define "file separately" as "open an issue at github.com/Ovid/paad/issues with title 'agentic-architecture report template: <defect>' and reference Phase 2 commit 4 in the body." Falls back to "ask Ovid" if uncertain.

## Summary

- Pushback raised 7 issues (one Important post-decision-log addition by Ovid, prefixed `(user-added)` per the §Per-Phase Checklist File provenance pattern by analogy). All 7 resolved with design and/or plan changes. Two Important findings: Issue [1] reframed the phase from "structural refactor only" to "structural refactor + lens-quality improvement"; Issue [7] introduced the two-stage tournament discipline (sequential at lens level, two competing subagents in parallel within each lens) for enrichment dispatch. Five Minor findings closed ambiguities and omissions in version cadence, sequential dispatch wording, smoke-test verdict semantics, and per-commit notes-file discipline.
- Alignment raised 3 issues; all 3 resulted in plan changes (`fixed-in-plan`). All Minor — recovery paths and clarifications layered onto an otherwise well-aligned plan (every design requirement has plan task coverage; every plan task traces to a design section; no orphaned tasks).
