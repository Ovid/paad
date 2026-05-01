# Agentic Code Review: ovid/force-skills-to-load

**Date:** 2026-05-01 09:54:08
**Branch:** ovid/force-skills-to-load -> main
**Commit:** 778ddd19049ff7be78b1be29fc21e5f4a3f6bb93
**Files changed:** 16 | **Lines changed:** +1122 / -49 (795 lines are design+plan docs in `docs/plans/`; ~327 lines are SKILL.md/help/Makefile/CLAUDE.md/README/manifest changes)
**Diff size category:** Large

## Executive Summary

**Better than main: yes — strongly, with caveats.** The branch bundles four logically separable improvements: (1) the original "force skills to load" work — skill description rewrites for better discoverability, (2) a substantive scope-classification + persistent backlog feature for `agentic-review`, (3) an announce-on-invocation convention plus Makefile tooling enforcing it across every skill, and (4) replacement of the Plan Alignment specialist with a richer Spec Compliance specialist. Each piece is a real improvement over `main`. No specialist found a bug that breaks the skill flow. Highest-impact issues are all documentation/contract drift produced by the rapid bundling: a CLAUDE.md typo, a missing `fix-architecture` entry in CLAUDE.md's structure tree, a stale "5 specialist agents" claim in the help skill, and an obsolete `Bug class: Plan` value in the backlog template. Confidence in the verified findings is high (multi-specialist agreement on the top four). The most notable scope question for the user is whether to keep this as one bundle or split before merge — see Out-of-Scope Additions below.

## Critical Issues

None found.

## Important Issues

### [I1] CLAUDE.md mis-labels the makefile skill as `/paad:help`
- **File:** `CLAUDE.md:29`
- **Bug:** The project-structure tree comment under the `makefile/` folder reads `← /paad:help skill` — copy-paste from the previous line. It should read `← /paad:makefile skill`.
- **Impact:** CLAUDE.md is the canonical project doc and the entry point both for human contributors and for any agent running `/init`. A wrong skill annotation here actively misleads readers about the project's surface area.
- **Suggested fix:** Change line 29's comment from `← /paad:help skill` to `← /paad:makefile skill`.
- **Confidence:** High
- **Found by:** Contract & Integration (claude-haiku-4-5), Error Handling & Edge Cases (claude-haiku-4-5)

### [I2] CLAUDE.md project-structure tree omits `fix-architecture`
- **File:** `CLAUDE.md:8-33`
- **Bug:** The tree lists 8 skill folders. The actual filesystem under `plugins/paad/skills/` has 9, with `fix-architecture/` missing from the tree. `fix-architecture` is otherwise fully documented (`README.md`, `help/SKILL.md`, its own `SKILL.md`, the Makefile auto-discovers it via `$(wildcard $(SKILLS_DIR)/*)`).
- **Impact:** New contributors reading CLAUDE.md will not see `fix-architecture` listed and may wonder if it's a first-class skill. Steering files that diverge from reality erode trust over time.
- **Suggested fix:** Insert `fix-architecture/` into the tree, alphabetically between `agentic-architecture/` and `help/` (or wherever the existing ordering convention puts it).
- **Confidence:** High
- **Found by:** Contract & Integration (claude-haiku-4-5), Error Handling & Edge Cases (claude-haiku-4-5)

### [I3] help/SKILL.md says "5 specialist agents" but reality is 6 in parallel
- **File:** `plugins/paad/skills/help/SKILL.md:184-193`
- **Bug:** Help text reads "Dispatches 5 specialist agents in parallel: …" then numbers Spec Compliance as a separate step (#3). The current `agentic-review/SKILL.md:137-146` lists Spec Compliance in the same Phase 2 dispatch table as the other five, and the README correctly says "six specialists examine your branch simultaneously" (`README.md:259`). The help skill is the stale one.
- **Impact:** `paad:help` is the in-product reference. Users reading it will form a wrong mental model of how the skill runs (and when Spec Compliance fires). Inconsistency between help, README, and the SKILL.md is a contract-drift smell.
- **Suggested fix:** In `help/SKILL.md`, change the count to 6 and fold Spec Compliance into the parallel-dispatch list:
  ```
  2. Dispatches 6 specialist agents in parallel:
     - Logic & Correctness
     - Error Handling & Edge Cases
     - Contract & Integration
     - Concurrency & State
     - Security
     - Spec Compliance — pulls intent from PR description, plan/design
       docs, recent commits, or branch name; flags missing features,
       deviations, and out-of-scope additions (replaces the older Plan
       Alignment agent)
  ```
  Then renumber the subsequent steps.
- **Confidence:** High
- **Found by:** Logic & Correctness (claude-haiku-4-5), Contract & Integration (claude-haiku-4-5)

### [I4] Backlog template lists obsolete `Bug class: Plan`
- **File:** `plugins/paad/skills/agentic-review/SKILL.md:348`
- **Bug:** The backlog entry shape declares `**Bug class:** Logic | Error Handling | Contract | Concurrency | Security | Plan`. With Plan Alignment replaced by Spec Compliance (lines 144-146), no specialist now produces "Plan"-class findings. Spec Compliance's three categories are Missing / Deviation / Out-of-scope addition (lines 171-174); furthermore, Spec Compliance findings tagged out-of-scope-addition never reach the backlog at all (lines 38, 207). The "Plan" enum value is unreachable.
- **Impact:** The verifier reading this template has to choose a value from a list that includes a dead option. A future maintainer might also wire downstream tooling against the enum and inherit the dead value. Schema drift.
- **Suggested fix:** Remove `| Plan` from line 348. If backward-compat for older backlog entries is desired (none currently exist), keep `Plan` and annotate it as deprecated; otherwise just delete it.
- **Confidence:** High
- **Found by:** Logic & Correctness (claude-haiku-4-5), Contract & Integration (claude-haiku-4-5)

### [I5] Heading nesting differs between Out-of-Scope (Bugs) and Out-of-Scope Additions
- **File:** `plugins/paad/skills/agentic-review/SKILL.md:267-308`
- **Bug:** Out-of-Scope (Bugs) uses `## Out of Scope` (h2) → `### Out-of-Scope Critical` (h3 tier name) → `#### [OOSC1]` (h4 entry). Out-of-Scope Additions uses `## Out-of-Scope Additions` (h2) → `### [OOSA1]` (h3 entry) — there's no tier-name level because additions don't have severity tiers, but the entry-level heading is one shallower than the Bugs section's entries. Within a single report this produces inconsistent ToC depth and makes the two sections feel structurally different.
- **Impact:** A handoff agent (or downstream tool) parsing the report by heading depth will hit different conventions for the two sections and either has to special-case or risks miscounting. Cosmetic per-report, but it's a contract the report template defines.
- **Suggested fix:** Two acceptable options. (a) Flatten the Bugs section: drop the `### Out-of-Scope Critical` tier headers and put `### [OOSC1]` directly under `## Out of Scope`, with the tier carried as a field inside each entry — but this loses the batched-by-tier visual structure the handoff prose relies on. (b) Add a parallel tier header to Additions, e.g., `### Flagged Additions`, and bump entry headings to `#### [OOSA1]` so both sections nest h2 → h3 → h4. Option (b) preserves the existing handoff semantics.
- **Confidence:** Medium
- **Found by:** Logic & Correctness (claude-haiku-4-5)

### [I6] `.gitignore` advice in the security warning is misleading after the file has been committed
- **File:** `plugins/paad/skills/agentic-review/SKILL.md:398`
- **Bug:** The Post-Review security disclosure says: *"`paad/code-reviews/backlog.md` is committed to this repository by default. … you can `.gitignore` the file or remove specific entries."* If the backlog was committed in a prior run (which is the default lifecycle), `.gitignore` does not remove anything from history — the user must rewrite history (`git filter-repo` or similar) or accept the leak. Removing entries from the current file and committing the deletion also leaves the entries in `git log -p`.
- **Impact:** A user reading this warning at the moment they're about to disclose may believe `.gitignore` solves it. It doesn't. This is a real false-sense-of-security issue, distinct from any Spec Compliance / Plan Alignment quibble.
- **Suggested fix:** Expand the warning to mention history: *"… you can `.gitignore` the file before the next run, but if the backlog was already committed in a previous run, gitignore alone does not remove the entries from git history — you must rewrite history (e.g. `git filter-repo`) or accept the leak."*
- **Confidence:** High
- **Found by:** Security (claude-haiku-4-5)

## Suggestions

- **`SKILL.md:226` — "regardless of count" reads as if Spec Compliance might still produce additions when bailing out.** It can't (only Spec Compliance emits the tag, and bail-out means it didn't run). Reword as "the section will be empty; omit it." (Logic, Contract & Integration)
- **`SKILL.md:203` — Phase 3 step 5 dedup wording is ambiguous about whether duplicates merge or stay separate.** The report template implies merge (single `Found by:` line per entry). Clarify: *"merge duplicates into one entry; the `Found by:` field lists every specialist that flagged it."* (Logic)
- **`SKILL.md:6` vs `SKILL.md:102` — "before anything else" announce vs pre-flight stop.** The literal markdown order has the announce line ahead of the pre-flight digraph, so the announce *will* fire first. The prose is fine in practice; a one-line note saying "the announce always fires before pre-flight, even when pre-flight stops the skill" would remove any ambiguity. (Logic, Concurrency)
- **`SKILL.md:70-78` — single-argument disambiguation.** `/paad:agentic-review src/auth/` is currently ambiguous (branch name vs path). Add: *"If the single argument contains `/` or matches a path on disk, treat it as a path filter against `main`; otherwise treat it as a base branch."* (Error Handling)
- **`SKILL.md:347-362` — Symbol field protocol gap.** The backlog entry requires `Symbol` and the ID is hashed using it, but Phase 2 specialists are not asked to emit a symbol. The verifier has to derive one. Add an instruction to the verifier or to the specialist prompt: when a finding is file-scope (no enclosing function/class), use a stable sentinel like `<file-scope>`. (Error Handling)
- **`SKILL.md:207-209` — Backlog dedup match key is fragile against file renames.** When a file is renamed between runs, the existing entry's `File (at first sighting)` no longer matches and a duplicate is minted. Either accept this (rare) or add a secondary semantic match (symbol + bug class + description hash). The design doc's "Out-of-scope" list excluded "cross-branch dedup of in-scope findings" but did not exclude rename robustness. (Error Handling)
- **`SKILL.md:102` — "substantive history" is undefined.** A second invocation in the same session always has history. State explicitly that prior runs of the same skill on the same branch don't count, but other prior work does. (Error Handling)
- **`SKILL.md:38` — "ephemeral additions / forgotten after the review" overstates ephemerality.** The per-review report file is committed by default, so additions persist there. Reword to: "do not enter `backlog.md`; they live only in this review's report." (Concurrency)
- **`SKILL.md:80-104` — Empty-diff edge isn't surfaced in pre-flight.** A feature branch with zero commits ahead of base passes pre-flight, runs all specialists on an empty manifest, and produces a vacuous report. Add: *"If `git diff <base>...HEAD` is empty, stop with 'No changes to review on this branch.'"* (Error Handling, Concurrency)
- **Phase 2 prompt template (`SKILL.md:148-154`) — diff content is untrusted.** The skill should tell each specialist that diff text and PR descriptions are attacker-controllable data, not directives. One sentence in the template would do it. (Security)
- **`SKILL.md:320` — `Steering files consulted` and `Intent sources consulted` paths can disclose internal doc names.** When the per-review report is committed in private/sensitive work and later shared, these paths surface internal planning. Add a parallel warning to the security one when steering/intent paths look sensitive (rough heuristic: anything under `docs/plans/` or `secrets/`). (Security)

## Out-of-Scope Additions

> **Handoff instructions for any agent processing this report:** The entries below are code this branch added that the spec did not promise. They may be legitimate "while I'm here" fixes for issues exposed by this work, or scope creep that should live in a separate PR. Do **not** assume they should stay on this branch, and do **not** assume they should be reverted. Present them to the user **as a single batched ask**: "These three additions weren't promised by the spec — keep, split into a separate PR, or revert?" The user decides per item.
>
> Out-of-scope additions are flagged for this PR only — they do not persist to `paad/code-reviews/backlog.md`.

### [OOSA1] Announce-on-invocation convention added across every skill
- **File:** `plugins/paad/skills/*/SKILL.md` (announce lines), `CLAUDE.md:43, 45, 50, 55`, `Makefile` (`check-skill-versions`, `bump-version` targets)
- **Addition:** A new project-wide convention requiring every `SKILL.md` to begin with `**On invocation:** announce "Running paad:<skill-name> v<version>" before anything else.`, plus the Makefile tooling that enforces and bumps it (commits `698b67f`, then folded into `bump-version`/`check-skill-versions`).
- **Suggested intent source:** `docs/plans/2026-04-26-agentic-review-scope-design.md` and `docs/plans/2026-04-26-agentic-review-scope-implementation.md` (the only design + plan docs on this branch). Neither mentions announce lines or version-broadcast tooling.
- **Confidence:** High
- **Found by:** Spec Compliance (claude-haiku-4-5)

### [OOSA2] Plan Alignment specialist replaced by Spec Compliance specialist
- **File:** `plugins/paad/skills/agentic-review/SKILL.md:144-146, 160-191, 295-308` and the new `## Out-of-Scope Additions` report section
- **Addition:** Commit `778ddd1` swapped Plan Alignment for a richer Spec Compliance specialist that emits Missing / Deviation / Out-of-scope addition categories, introduced the `category: out-of-scope-addition` tag and verifier short-circuit, and added the entire `## Out-of-Scope Additions` report section. The design doc explicitly stated *"Specialist lenses, scopes, and dispatch behavior are unchanged"* (`docs/plans/2026-04-26-agentic-review-scope-design.md:50-52`); replacing a specialist directly contradicts that promise. The change is itself a meaningful improvement, but it is a separate feature, not part of the scope-classification design.
- **Suggested intent source:** Same as OOSA1 — neither doc mentions Spec Compliance.
- **Confidence:** High
- **Found by:** Spec Compliance (claude-haiku-4-5), Contract & Integration (claude-haiku-4-5)

### [OOSA3] Skill description rewrites (the original "force skills to load" intent)
- **File:** Frontmatter `description:` lines in every `plugins/paad/skills/*/SKILL.md` (commit `b43555a` "Rewrite skill descriptions as triggers, not workflow summaries")
- **Addition:** The branch's first commit reworded all skill descriptions into trigger phrasing so Claude Code is more likely to auto-load the right skill. This is what the branch name `ovid/force-skills-to-load` refers to — but it is unrelated to scope classification, announce lines, and Spec Compliance. It is the original branch intent and the rest accreted on top of it.
- **Suggested intent source:** Branch name. Both design docs (added later in the branch) describe scope classification only.
- **Confidence:** Medium
- **Found by:** Spec Compliance (claude-haiku-4-5)

## Review Metadata

- **Agents dispatched:** Logic & Correctness, Error Handling & Edge Cases, Contract & Integration, Concurrency & State, Security, Spec Compliance (six specialists in parallel) + one Verifier
- **Scope:** `plugins/paad/skills/agentic-review/SKILL.md`, `plugins/paad/skills/help/SKILL.md`, `CLAUDE.md`, `README.md`, `Makefile`, `plugins/paad/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, all other `plugins/paad/skills/*/SKILL.md` (announce lines), `docs/plans/2026-04-26-agentic-review-scope-design.md`, `docs/plans/2026-04-26-agentic-review-scope-implementation.md`
- **Raw findings:** 46 (across 6 specialists, before verification and dedup)
- **Verified findings:** 17 (6 Important + 11 Suggestion)
- **Filtered out:** 29 (duplicates collapsed, design's explicit "out-of-scope" exclusions dropped — atomic backlog writes, 8-char hex collision, default-by-policy security handling — and several speculative concurrency/security items without evidence in the prose)
- **Out-of-scope findings:** 0 (all confirmed findings sit on lines this branch authored fresh; nothing pre-existing surfaced)
- **Out-of-scope additions:** 3
- **Backlog:** 0 new entries added, 0 re-confirmed (no `paad/code-reviews/backlog.md` exists yet for this repo, and no out-of-scope bug findings produced; nothing to write)
- **Steering files consulted:** `CLAUDE.md`
- **Intent sources consulted:** `docs/plans/2026-04-26-agentic-review-scope-design.md`, `docs/plans/2026-04-26-agentic-review-scope-implementation.md`, recent commit messages on the branch (`git log main..HEAD`), branch name `ovid/force-skills-to-load`
