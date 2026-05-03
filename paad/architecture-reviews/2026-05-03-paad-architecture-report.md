# Architecture Report — paad

**Date:** 2026-05-03
**Commit:** 2dbb4297f9704fbe87d3697200b39ea5f02250c2 (working tree dirty: `plugins/paad/skills/agentic-architecture/SKILL.md` + `scripts/extracted-refs.tsv` modified; `plugins/paad/skills/agentic-architecture/references/report-template.md` and `paad/architecture-reviews/` untracked)
**Branch:** `agentic-architecture-references-conversion`
**Languages:** Markdown (skill specs and references), Python 3 (1 file, stdlib-only), Bash (2 scripts), Make, JSON manifests
**Key directories:** `.claude-plugin/`, `plugins/paad/.claude-plugin/`, `plugins/paad/skills/<name>/{SKILL.md,references/}`, `.claude/skills/roadmap/`, `scripts/`, `Makefile`
**Scope:** Full repo, ~34 in-scope source files. Excluded: `kiro_and_antigravity/` (vendored copies), `paad/code-reviews/` and `paad/architecture-reviews/` (skill outputs), `notes/`, `scratch/`, `docs/roadmap/`, `images/`, `.git/`.

## Repo Overview

`paad` is a Claude Code plugin marketplace distributing a single plugin (also named `paad`) containing nine end-user skills: `agentic-a11y`, `agentic-architecture`, `agentic-review`, `alignment`, `fix-architecture`, `help`, `makefile`, `pushback`, `vibe`. Two of those skills (`agentic-architecture`, `agentic-review`) are split into a SKILL.md orchestrator plus per-specialist `references/<lens>.md` instruction files; the other seven inline everything. A separate project-local skill at `.claude/skills/roadmap/SKILL.md` ships with a deliberately different lifecycle (no plugin namespace, no version literal, no announce line, no help/README cross-reference).

The repo's mechanical surface — what the Makefile actually runs — is a small Bash + Python toolchain that validates manifests, enforces version-literal sync across plugin.json + marketplace.json + every SKILL.md announce line, asserts that each skill has a digraph and is mentioned in `paad:help` and the README, validates frontmatter `name:` matches folder name, and enforces an extraction-refs invariant (sentinel moved out of SKILL.md, present in the ref file, co-located with the word "binding") via `scripts/check_extracted_refs.sh` and its self-test `scripts/test_check_extracted_refs.sh`. There is no service runtime, no auth surface, no networked integration, and no committed secrets.

The branch under review (`agentic-architecture-references-conversion`) is in the middle of an in-flight refactor that extracted per-specialist content from `agentic-architecture/SKILL.md` into seven `references/*.md` files; the equivalent extraction has not been propagated to `agentic-a11y`, the closest structural analog. CLAUDE.md does not yet document the references/ extraction pattern as a convention. Several of the findings below are direct consequences of this paused intermediate state and should be revisited after the branch lands.

## Strengths

### [S-1] Distributed-vs-project-local skill split is documented and enforced
- **Category:** S1 (clear modular boundaries)
- **Impact:** Medium
- **Explanation:** Two distinct skill lifecycles (distributed plugin vs. project-local) are explicitly stated in CLAUDE.md and mechanically enforced by every Make check (none walk `.claude/skills/`). Convention and tooling reinforce each other.
- **Evidence:** `CLAUDE.md:54-65` (`<file-scope>`), excerpt: "The repo also hosts **project-local** skills at .claude/skills/<name>/SKILL.md … These are **not** part of the paad plugin and follow a different lifecycle"; `Makefile:1` (`SKILLS_DIR`), excerpt: "SKILLS_DIR := plugins/paad/skills"
- **Found by:** Structure & Boundaries

### [S-2] Makefile target list maps 1:1 to one invariant each
- **Category:** S1 (clear modular boundaries)
- **Impact:** Medium
- **Explanation:** Each Make target enforces a single named invariant with a single failure mode and a single output. The `test` aggregator composes them without conditional logic — adding a new check means adding a new target, never extending a centralized dispatcher.
- **Evidence:** `Makefile:10` (`test`), excerpt: "test: validate check-versions check-skill-versions check-digraphs check-help check-readme check-frontmatter test-check-extracted-refs check-extracted-refs"; sub-targets at `Makefile:13-18, 20-27, 29-41, 67-78, 80-91, 93-104, 106-131, 133-134, 136-137`
- **Found by:** Structure & Boundaries

### [S-3] `extracted-refs.tsv` + `check_extracted_refs.sh` is well-scoped
- **Category:** S3 (loose coupling)
- **Impact:** Medium
- **Explanation:** A 3-column TSV declares `(skill, ref-path, sentinel)` triples; a focused script validates four things in order without ever needing to know what each ref says. A self-test against synthetic fixtures locks the contract.
- **Evidence:** `scripts/check_extracted_refs.sh:60-62` (`<file-scope>`), excerpt: `awk -v path="$ref_path" 'index($0, path) && /binding/ { found=1; exit } …'`; `scripts/extracted-refs.tsv:1` (header), 15 data rows; consumers `Makefile:133-134, 136-137`
- **Found by:** Coupling & Dependencies

### [S-4] Stable dependency direction marketplace → plugin → skill → references
- **Category:** S4 (dependency direction is stable)
- **Impact:** Medium
- **Explanation:** All version-truth flows downward — `plugin.json` is the single source for the version literal; `marketplace.json`'s `plugins[0].version` and every SKILL.md's announce string are verified consumers. No file in the dependent layers writes back to the source. Bounded by F-1 (one of marketplace.json's two version fields escapes the discipline).
- **Evidence:** `Makefile:30-31` (`check-skill-versions`), excerpt: `plugin_ver=$$(python3 -c "import json; print(json.load(open('plugins/paad/.claude-plugin/plugin.json'))['version'])")`; `Makefile:21-27` (`check-versions`)
- **Found by:** Coupling & Dependencies

### [S-5] `references/` extraction earns its keep where it exists
- **Category:** S14 (simple, pragmatic abstractions)
- **Impact:** Medium
- **Explanation:** Specialist instructions (76–191 lines each) factored into separate ref files; the orchestrator dispatches via a fixed-shape `Read … binding … [ref-loaded:<lens>]` line; the manifest enumerates only the 15 actual extractions, no aspirational rows. Resisted over-application to `vibe`, `makefile`, `pushback`, `alignment`, `fix-architecture` where it would be pure overhead.
- **Evidence:** `plugins/paad/skills/agentic-architecture/references/` (7 files), `plugins/paad/skills/agentic-review/references/` (8 files); `scripts/extracted-refs.tsv:1-3` (`<file-scope>`), excerpt: "# skill\tref-path-relative-to-skill\tsentinel-phrase"
- **Found by:** Structure & Boundaries

### [S-6] `check_extracted_refs.sh` consistent failure vocabulary
- **Category:** S7 (robust error handling)
- **Impact:** Medium
- **Explanation:** Every error site uses `FAIL:` (or `FAIL [row N, name]:` for per-row failures) plus `set -euo pipefail`. Per-row errors increment a counter and continue scanning so the user sees every failure in one run; manifest-level errors exit immediately. Both translate to exit 1 at the boundary.
- **Evidence:** `scripts/check_extracted_refs.sh:6` (`<file-scope>`), excerpt: "set -euo pipefail"; `scripts/check_extracted_refs.sh:36`, excerpt: `echo "FAIL [row $row, $skill]: SKILL.md not found at $skill_md"`; failure sites at lines 12, 41, 46, 50, 61, 67
- **Found by:** Error Handling & Observability

### [S-7] `make bump-version` + paired post-hoc invariant checks
- **Category:** S9 (configuration discipline)
- **Impact:** Medium
- **Explanation:** Three of six discipline signals present: single rewrite entry point, validated input (X.Y.Z grammar), idempotent no-op short-circuit, plus paired post-hoc invariant readers. The bumper rejects malformed VERSION values before mutating anything. Bounded by F-1, F-5, F-6 (convention-enforced rather than CI-enforced; coverage gap on metadata.version; no atomicity between bumper and check).
- **Evidence:** `Makefile:48-51` (`bump-version`), excerpt: `case "$(VERSION)" in [0-9]*.[0-9]*.[0-9]*) ;; *) echo "FAIL: VERSION must be in X.Y.Z form (got $(VERSION))"; exit 1 ;; esac`; `Makefile:52-56` (idempotency check); `Makefile:20-27, 29-41` (paired readers)
- **Found by:** Error Handling & Observability

### [S-8] `test_check_extracted_refs.sh` is a model fixture-driven seam
- **Category:** S11 (testability & coverage)
- **Impact:** Medium
- **Explanation:** Properly isolated tests — each case in its own tmpdir, scrubbed by trap, contract-asserted by exit code. The harness exercises 8 well-named fault modes including encoding-portability (CRLF) and missing-trailing-newline edge cases that real-world TSVs hit. Self-tested via Makefile target.
- **Evidence:** `scripts/test_check_extracted_refs.sh:1-164` (`run_subtest` harness), 8 named cases (well-formed; missing-trailing-newline; empty; comments-only; CRLF; dispatch-without-binding-context; dispatch-with-binding-context; sentinel-still-in-SKILL.md; sentinel-missing-from-ref-file)
- **Found by:** Security & Code Quality

### [S-9] Version-invariant chain has automated enforcement
- **Category:** S11 (testability & coverage), partial
- **Impact:** Low (positive)
- **Explanation:** While the mutator (`bump-version`) has no fixture test (F-5), the invariant the bumper must preserve has direct in-tree enforcement that runs as part of `make test`. Detection-without-prevention limits silent drift to "between commit and next `make test`" rather than "indefinitely."
- **Evidence:** `Makefile:35` (`check-skill-versions`), excerpt: `if ! grep -qF "Running paad:$$name v$$plugin_ver\"" "$$file" 2>/dev/null; then`; aggregator at `Makefile:10`
- **Found by:** Security & Code Quality

## Flaws/Risks

### [F-1] Version literal duplicated across 11 surfaces, with stale 12th surface unchecked
- **Category:** 22 (configuration sprawl)
- **Impact:** Medium
- **Explanation:** The same logical setting (plugin version) is duplicated across 11 active surfaces and one stale-12th surface. `make bump-version` rewrites only the indented `plugins[0].version` (Makefile:59 anchored to six-space indent), never the unindented `metadata.version` at marketplace.json:9 — currently 1.0.0 (last touched at v1.0.0 release). `check-versions` reads only `plugins[0]['version']` and `plugin.json['version']`, so it cannot detect the metadata drift.
- **Evidence:** `.claude-plugin/marketplace.json:9` (stale `metadata.version`), excerpt: `"version": "1.0.0"`; `.claude-plugin/marketplace.json:16` (current), excerpt: `"version": "1.18.0",`; `plugins/paad/.claude-plugin/plugin.json:4`; nine SKILL.md announce lines at `plugins/paad/skills/*/SKILL.md:6`
- **Found by:** Error Handling & Observability; corroborated by Security & Code Quality

### [F-2] Confidence threshold `60` hard-coded across 9 sites
- **Category:** 28 (magic numbers/strings everywhere)
- **Impact:** Medium
- **Explanation:** `60` is the operational floor that gates whether specialist findings are emitted at all. It appears as a literal in dispatch prompts, in verifier instructions, and in score-band mapping. A change to the threshold requires hand-editing every site with no central definition, and silent desynchronization between specialist floor and verifier floor would invalidate findings without warning.
- **Evidence:** `plugins/paad/skills/agentic-architecture/SKILL.md:92` (`<file-scope>`), excerpt: "Only report findings with confidence >= 60"; `plugins/paad/skills/agentic-architecture/references/verifier.md:56`, excerpt: "Drop findings below 60% confidence"; also `plugins/paad/skills/agentic-a11y/SKILL.md:140, :254`, `plugins/paad/skills/agentic-review/SKILL.md:165`, `plugins/paad/skills/agentic-review/references/{concurrency-state.md:23, error-handling.md:24, contract-integration.md:24, verifier.md:25}`
- **Found by:** Error Handling & Observability

### [F-3] `[ref-loaded:<lens>]` sentinel format hand-written across 13+ sites
- **Category:** 28 (magic numbers/strings everywhere)
- **Impact:** Medium
- **Explanation:** Token shape is the routing primitive between subagent and verifier — a missing or mistyped token causes the verifier to silently drop **all** findings from that specialist. `check_extracted_refs.sh` enforces sentinel-presence/absence per row, but it does not enforce sentinel **format**. Adding a lens or renaming a lens requires hand-editing 4+ sites per lens with no central definition.
- **Evidence:** `plugins/paad/skills/agentic-architecture/SKILL.md:96` (`<file-scope>`), excerpt: "literal token `[ref-loaded:structure-boundaries]` on its own line"; parallel sites at SKILL.md:100, 104, 108, 112, 124; ref echoes at `plugins/paad/skills/agentic-architecture/references/{structure-boundaries.md:75, coupling-dependencies.md:53, integration-data.md:37, error-handling-observability.md:71, security-code-quality.md:65, verifier.md:38, :52}`; 7 parallel sites under agentic-review/
- **Found by:** Error Handling & Observability

### [F-4] `paad/<topic>-reviews/` output path inconsistent across SKILL.md and `convert_skills.py`
- **Category:** 22 (configuration sprawl)
- **Impact:** Medium
- **Explanation:** Five `paad/<topic>-reviews/` output paths exist across skills; the converter's explicit rename table covers four (architecture, code, pushback, alignment) but omits `a11y`. The catch-all on line 65 fires for `paad/` → `.reviews/`, so converted output becomes `.reviews/a11y-reviews/` (asymmetric with the other four `.reviews/<topic>/`). The converter is itself dead per F-7, so visible impact is currently zero — but the architectural pattern (config in two places that disagree) is real.
- **Evidence:** `scripts/convert_skills.py:60-65` (`convert_skills`), excerpt:
  ```python
  body = body.replace("paad/architecture-reviews/", ".reviews/architecture/")
  body = body.replace("paad/code-reviews/",         ".reviews/code/")
  body = body.replace("paad/pushback-reviews/",     ".reviews/pushback/")
  body = body.replace("paad/alignment-reviews/",    ".reviews/alignment/")
  body = body.replace("paad/",                       ".reviews/")
  ```
  `plugins/paad/skills/agentic-a11y/SKILL.md:267, :269`, excerpt: "paad/a11y-reviews/a11y-<YYYY-MM-DD-HH-MM-SS>.md"
- **Found by:** Error Handling & Observability

### [F-5] `make bump-version` has zero tests despite mutating 11+ files via brittle sed
- **Category:** 32 (missing or inadequate test coverage for critical paths)
- **Impact:** Medium
- **Explanation:** The Makefile's marketplace.json sed (line 59) requires exact six-space indentation and field-on-its-own-line — silently no-ops on any reformat (and never matches the unindented `metadata.version` at marketplace.json:9, which is why F-1's stale 1.0.0 exists). The plugin.json sed (line 58) is unanchored and would double-rewrite if a second `"version"` field were ever added (currently safe by accident). The compensating control verifies only the SKILL.md announce lines, not the JSON manifests it just mutated.
- **Evidence:** `Makefile:58-59` (`bump-version`), excerpt:
  ```make
  sed -i.bak 's|"version": "[^"]*"|"version": "$(VERSION)"|' plugins/paad/.claude-plugin/plugin.json …
  sed -i.bak 's|^      "version": "[^"]*"|      "version": "$(VERSION)"|' .claude-plugin/marketplace.json …
  ```
  zero matches for `grep -rn "bump-version" scripts/` and `find . -name "test_bump*"`
- **Found by:** Security & Code Quality; corroborated by Coupling & Dependencies (F-6) and Error Handling & Observability (F-1)

### [F-6] `bump-version` rewrites version literals without atomic post-condition check
- **Category:** 27 (temporal coupling)
- **Impact:** Medium
- **Explanation:** Step ordering matters and the relationship between "rewrite" and "verify the rewrite landed" is left to a different command and to operator discipline (CLAUDE.md step 10 is "Run `make test`"). If sed matches zero lines in any SKILL.md (smart-quote contamination, hand-edit divergence, missing announce line), the rewrite is a silent no-op and the loop proceeds. Detection is deferred to whoever runs `make test` next.
- **Evidence:** `Makefile:60-64` (`bump-version`), excerpt:
  ```make
  for dir in $(SKILL_DIRS); do \
      name=$$(basename "$$dir"); \
      file="$$dir/SKILL.md"; \
      sed -i.bak "s|Running paad:$$name v$$old_ver\"|Running paad:$$name v$(VERSION)\"|g" "$$file" && rm -f "$$file.bak"; \
  done
  ```
- **Found by:** Coupling & Dependencies; corroborated by Security & Code Quality (F-5)

### [F-7] `convert_skills.py` is unreferenced and would emit broken output for refs-using skills; vendored output stale 6+ weeks; README still documents it as the install path
- **Category:** 31 (dead code / unused dependencies)
- **Impact:** Medium
- **Explanation:** Three compounding problems on the same surface: the script has zero invokers (not in `make test`, not in CLAUDE.md's "Adding a new skill" workflow); even if invoked it cannot produce correct output for `agentic-architecture` or `agentic-review` because it ignores the `references/` subdir those two skills now depend on; and README's documented install path for Cursor/Kiro/Antigravity users points at the stale vendored output (last touched Mar 17 2026, 7 weeks before review date) which preceded the references/ refactor.
- **Evidence:** `scripts/convert_skills.py:26-28` (`convert_skills`), excerpt: `skill_file = skill_path / "SKILL.md"` then `if not skill_file.exists(): continue` (reads only SKILL.md, never references/); `README.md:111`, excerpt: `cp -r kiro_and_antigravity/skills/.kiro/skills/* .cursor/skills/`; `kiro_and_antigravity/skills/.kiro/skills/agentic-architecture/SKILL.md` last touched Mar 17 vs source last touched May 3
- **Found by:** Security & Code Quality

### [F-8] `.claude/skills/roadmap/SKILL.md` co-locates six independent responsibilities in one 990-line file
- **Category:** 11 (low cohesion); secondary 2 (god object)
- **Impact:** Medium
- **Explanation:** Six independent responsibilities live in one file with three separate statements of the same filename-slug rule. The change-axis cohesion vector is broken: per-step orchestration prose, per-Phase Checklist file format, resume detection state machine, working-branch suggestion module, decision-log schema, and filename slug rules each take their own commits. CLAUDE.md correctly notes that project-local skills don't extract to `references/`, so the path of least resistance pushes everything inline — but the breadth here is past where one file can stay coherent.
- **Evidence:** `.claude/skills/roadmap/SKILL.md:1-990` (`<file-scope>`), six responsibility blocks at lines 12-148 (Checklist file format), 150-303 (resume detection), 305-836 (per-step orchestration), 376-586 (working-branch suggestion), 838-987 (decision-log schema); slug rules at lines 17-43, 465-493, 964-985; ~33 commits in last 6 months touching distinct sections (e.g., `447a974`, `9f3b9e4`, `545f778`, `9b0493f`, `361ca55`, `bdbfc6b`, `ca18a3c`, `74c269a`)
- **Found by:** Structure & Boundaries

### [F-9] `plugins/paad/skills/` has two architectural shapes for the same kind of skill, with the new shape undocumented in CLAUDE.md
- **Category:** 13 (inconsistent boundaries)
- **Impact:** Low (downgraded one tier from Medium per refactor-history calibration — refactor in flight)
- **Explanation:** Two skills (`agentic-architecture`, `agentic-review`) extract per-specialist instructions into `references/<lens>.md`; the other seven do not. `agentic-a11y` is the closest structural analog of `agentic-architecture` (multi-specialist parallel dispatch, verifier, report writer) but stays monolithic at 394 lines. CLAUDE.md does not document the references/ pattern, so a future maintainer has no rule for which shape applies. The finding does not say "go back to monolithic" — it says "finish the extraction or document why some skills don't get it."
- **Evidence:** extracted: `plugins/paad/skills/agentic-architecture/{SKILL.md, references/×7}`, `plugins/paad/skills/agentic-review/`; monolithic analog: `plugins/paad/skills/agentic-a11y/SKILL.md` (394 lines); `CLAUDE.md:30-44` (Adding a new skill) does not mention `references/`; recent refactor commits `bafbb27`, `23db697`, `2dbb429`
- **Found by:** Structure & Boundaries; corroborated by Coupling & Dependencies (F-10)

### [F-10] Orchestrator SKILL.md duplicates each ref's content (subtype lists, bail reasons) verbatim
- **Category:** 3 (tight coupling); secondary 7 (over-abstraction)
- **Impact:** Low (downgraded one tier from Medium per refactor-history calibration — same refactor wave as F-9)
- **Explanation:** Each per-specialist paragraph in SKILL.md (≈ 150-250 words) re-states the ref's subtype enumeration and bail-out catalog. When subtypes change in a ref, both the ref and the orchestrator paragraph must change in lockstep, but only the ref is the binding source. This is the inverse of the boundary the references/ extraction is meant to establish — expected to either thin or stabilize as the convention solidifies.
- **Evidence:** `plugins/paad/skills/agentic-architecture/SKILL.md:94, 98, 102, 106, 110, 122` (`<file-scope>`), excerpt (line 94, abridged): "Subtypes include global-state / god-class / shotgun-surgery / feature-envy / anemic-domain / mixed-cohesion / boundary-drift / utility-grab-bag" — verbatim duplicate of `plugins/paad/skills/agentic-architecture/references/structure-boundaries.md` subtype enumeration
- **Found by:** Coupling & Dependencies

### [F-11] `report-template.md` is untracked but SKILL.md declares a binding dependency on it
- **Category:** 4 (high/unstable dependencies)
- **Impact:** Low
- **Explanation:** The orchestrator declares a binding read-dependency on a ref that is currently in the working tree but not in the index. Severity is genuinely low because the branch is in-flight and the file will presumably be added before merge — but a reviewer should flag it so the author doesn't merge with the dependency missing.
- **Evidence:** `plugins/paad/skills/agentic-architecture/SKILL.md:132` (`<file-scope>`), excerpt: "The full report template … lives at `references/report-template.md`. **Before writing the report, read that file** — its instructions are binding"; `git status` shows `?? plugins/paad/skills/agentic-architecture/references/report-template.md`
- **Found by:** Coupling & Dependencies

## Coverage Checklist

### Flaw/Risk Types 1–34
| # | Type | Status | Finding |
|---|------|--------|---------|
| 1 | Global mutable state | Not observed | — |
| 2 | God object | Observed (secondary) | #F-8 |
| 3 | Tight coupling | Observed | #F-10 |
| 4 | High/unstable dependencies | Observed | #F-11 |
| 5 | Circular dependencies | Not observed | — |
| 6 | Leaky abstractions | Not observed | — (Coupling specialist's leaky-abstraction claim was subsumed by F-7 dead-module; the script that "leaks" is itself dead code) |
| 7 | Over-abstraction | Observed (secondary) | #F-10 |
| 8 | Premature optimization | Not observed | — |
| 9 | Shotgun surgery | Not observed | — |
| 10 | Feature envy / anemic domain model | Not applicable | — (no domain model — Markdown specs + thin tooling) |
| 11 | Low cohesion | Observed | #F-8 |
| 12 | Hidden side effects | Not observed | — |
| 13 | Inconsistent boundaries | Observed | #F-9 |
| 14 | Distributed monolith | Not applicable | — (single-unit Markdown plugin marketplace; integration-data BAIL: not-distributed) |
| 15 | Chatty service calls | Not applicable | — (BAIL: not-distributed) |
| 16 | Synchronous-only integration | Not applicable | — (BAIL: not-distributed) |
| 17 | No clear ownership of data | Not applicable | — (BAIL: not-distributed) |
| 18 | Shared database across services | Not applicable | — (BAIL: not-distributed) |
| 19 | Lack of idempotency | Not applicable | — (BAIL: not-distributed) |
| 20 | Weak error handling strategy | Not observed | — (Error specialist's wrong-error-type claim against `convert_skills.py` was dropped: the `continue` past missing SKILL.md is intended scoping, not partial-success masquerade) |
| 21 | No observability plan | Not applicable | — (CLI/Makefile context — `print` and `echo` are the API; bail-eligible per `stdout-cli-tool` rule) |
| 22 | Configuration sprawl | Observed | #F-1, #F-4 |
| 23 | Dependency injection misuse | Not applicable | — (no runtime DI; one composition root: the Makefile) |
| 24 | Inconsistent API contracts | Not applicable | — (BAIL: not-distributed) |
| 25 | Business logic in the UI | Not applicable | — (no UI surface) |
| 26 | Poor transactional boundaries | Not applicable | — (BAIL: not-distributed) |
| 27 | Temporal coupling | Observed | #F-6 |
| 28 | Magic numbers/strings everywhere | Observed | #F-2, #F-3 |
| 29 | "Utility" dumping ground | Not observed | — |
| 30 | Security as an afterthought | Not applicable | — (no auth surface; no service runtime) |
| 31 | Dead code / unused dependencies | Observed | #F-7 |
| 32 | Missing or inadequate test coverage for critical paths | Observed | #F-5 |
| 33 | Hard-coded credentials or secrets in source | Not observed | — (full-repo grep returned zero hits) |
| 34 | Inconsistent error/logging conventions across services | Not observed | — (Error specialist's format-drift claim Python-vs-Bash was dropped per drop rule 16: language-idiom divergence is not architectural) |

### Strength Categories S1–S14
| # | Category | Status | Finding |
|---|----------|--------|---------|
| S1 | Clear modular boundaries | Observed | #S-1, #S-2 |
| S2 | High cohesion | Not observed | — (the inverse of F-8) |
| S3 | Loose coupling | Observed | #S-3 |
| S4 | Dependency direction is stable | Observed | #S-4 |
| S5 | Dependency management hygiene | Not observed | — (Coupling specialist self-flagged "partial" with three sub-claims that were themselves N/A — net signal too weak; the meaningful sub-signal merges into S-3) |
| S6 | Consistent API contracts | Not applicable | — (no networked contracts; integration-data BAIL: not-distributed) |
| S7 | Robust error handling | Observed | #S-6 |
| S8 | Observability present | Not applicable | — (CLI/Makefile context; no telemetry surface) |
| S9 | Configuration discipline | Observed | #S-7 |
| S10 | Security built-in | Not applicable | — (no service runtime; no auth surface; no secrets to manage). Security specialist's partial-credit claim was below floor for full-strength credit. |
| S11 | Testability & coverage | Observed | #S-8, #S-9 |
| S12 | Resilience patterns | Not applicable | — (no cross-process calls; integration-data BAIL: not-distributed) |
| S13 | Domain modeling strength | Not applicable | — (no domain model — Markdown specs + thin tooling) |
| S14 | Simple, pragmatic abstractions | Observed | #S-5 |

## Hotspots

1. **`plugins/paad/skills/agentic-architecture/`** — the in-flight refactor wave that drove F-9, F-10, F-11. The subdirectory carries the most unfinished structural decisions in the repo: orchestrator paragraphs that still summarize what the refs already say (F-10), an untracked `report-template.md` that the orchestrator binds against (F-11), and a convention (extract per-specialist content) that has not been propagated to its `agentic-a11y` analog or documented in CLAUDE.md (F-9). Reviewers landing this branch should look here first.

2. **`Makefile:43-65` + `scripts/convert_skills.py`** — the version-bump and skill-conversion mutator surfaces (F-5, F-6, F-7) plus the one-shot output-path renaming table (F-4). Both are scripted critical paths that mutate the distributed surface, both are silently brittle (untested sed in bump-version; dead-and-broken converter), and the second is what the README still tells non-Claude-Code users to invoke. Three of the eleven flaws cluster here.

3. **`.claude/skills/roadmap/SKILL.md`** — the most-churned file in the repo by a wide margin (F-8). 990 lines with six independent responsibilities and ~33 commits in the last 6 months across distinct sections. Project-local lifecycle removes the references/ extraction option, but the file's growth pattern shows structural pressure that has been actively *added* rather than relieved.

## Next Questions

1. Is `agentic-a11y` intended to follow the references/ extraction pattern that `agentic-architecture` and `agentic-review` adopted, or is it deliberately exempted? Either answer would resolve F-9, but it needs to be stated somewhere durable (CLAUDE.md, an ADR, or a comment in extracted-refs.tsv).
2. Should the orchestrator's per-specialist paragraphs in `agentic-architecture/SKILL.md` shrink to one-line dispatches (`Read … binding … [ref-loaded:<lens>]`) once the references are stable, or do the inline summaries serve a purpose the refs don't? F-10 cannot be classified as "in-progress noise" or "intended structure" without that decision.
3. Is the `metadata.version: "1.0.0"` field in `marketplace.json:9` semantically meaningful (e.g., the marketplace catalog's own schema version, separate from any plugin's version), or is it stale-by-neglect? F-1's severity depends on the answer.
4. Does `convert_skills.py` still have a maintained downstream user, or has the Cursor/Kiro/Antigravity install path been deprecated in practice while the README still documents it? F-7's impact (low if unused, medium if real users follow the README) hinges on this.
5. What is the intended escalation path when `make bump-version` is run by a contributor without follow-up `make test` — pre-commit hook, CI, or trust? F-5 and F-6 both reduce to convention-vs-mechanism, and a single answer would resolve both.

## Analysis Metadata

- **Agents dispatched:** 5 specialists in parallel (Structure & Boundaries; Coupling & Dependencies; Integration & Data; Error Handling & Observability; Security & Code Quality), then 1 Verifier
- **Scope:** 34 in-scope source files (9 distributed SKILL.md + 15 references/*.md + 1 project-local SKILL.md + 2 plugin manifests + Makefile + 4 scripts files + README.md + CLAUDE.md). Excluded: `kiro_and_antigravity/`, `paad/code-reviews/`, `paad/architecture-reviews/`, `notes/`, `scratch/`, `docs/roadmap/`, `images/`, `.git/`
- **Raw findings:** 27 (before verification: 19 flaws + 8 strengths from 4 reporting specialists; Integration & Data BAIL contributed 0)
- **Verified findings:** 20 (11 flaws + 9 strengths)
- **Filtered out:** 7 (3 false-positive drops; 1 floor-below-threshold drop; 2 subsumed/recategorized into other findings; 1 recommendation-not-diagnosis drop)
- **By impact:** 0 high, 14 medium, 6 low
- **Bail-outs:** 1 (Integration & Data: `not-distributed` — single-unit Markdown plugin marketplace; flaws 14/15/16/17/18/19/24/26 and strengths S6/S12 marked Not Applicable)
- **Steering files consulted:** `CLAUDE.md` (project conventions, lifecycle rules, digraph requirements, project-local skill caveat); no AGENTS.md, ADR directory, or architecture docs found
