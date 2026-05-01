# Verifier — additional instructions

> **Read this file before classifying findings or producing backlog directives.** You are the Verifier dispatched by `/paad:agentic-review` Phase 3. You receive all findings from the parallel specialists in Phase 2, plus a pre-filtered slice of `paad/code-reviews/backlog.md`. Your job is to verify each finding, classify the survivors, and emit backlog directives for out-of-scope bugs. The standing inputs (diff, file contents, manifest) and the basic finding-report format come from the parent `SKILL.md`; this file covers the verification pipeline, output shape, and discipline.

## Pipeline

1. For each finding, read the actual current code at the referenced `file:line`.
2. Confirm the bug exists and isn't already handled elsewhere.
3. Drop false positives and findings below 60% confidence.
4. Assign severity: **Critical** / **Important** / **Suggestion**.
5. Merge duplicates into one entry; the `Found by:` field lists every specialist that flagged it.
6. **Classify** each surviving finding as `in-scope`, `out-of-scope`, or `out-of-scope-addition`:
   - Findings carrying the tag `category: out-of-scope-addition` (emitted by the Spec Compliance specialist) skip the blame check and route directly to the report's Out-of-Scope Additions section. Rationale: the addition was made by this branch, so blame would say "in-scope" — but spec-wise the addition is out-of-scope, which is the relevant axis here.
   - All other findings: apply blame default → reasoning promotion → cosmetic-touch demotion in that order, using the touched-lines map (from Phase 1) and the diff. Result is `in-scope` or `out-of-scope`.
7. **Backlog dedup** for out-of-scope **bug** findings only (not for out-of-scope additions — those are ephemeral per-PR decisions, not persistent issues). For each out-of-scope bug:
   - **Match** in the pre-filtered backlog slice → emit `{id, last_seen, branch, sha}` update directive.
   - **No match** → mint a new entry with a fresh 8-char hex ID hashed from `file + symbol + bug-class + first-seen-iso-date`.
   - **Symbol field.** Specialists are not asked to emit a symbol. The verifier derives it: enclosing function, class, or method name at the finding's anchor line. When the finding has no enclosing symbol (module-level code, top-of-file imports, top-level constants), use the literal sentinel `<file-scope>`. The sentinel is stable, so the ID hash is stable across runs.
   - **Known limitation: file renames.** The path-based pre-filter compares against `File (at first sighting)`, so a rename between runs can mint a duplicate entry under the new path while the old entry remains. This is accepted as a rare event; downstream agents (or the user) can collapse the duplicates when triaging the backlog.

## Output

Three lists:

- **In-scope findings** with severity (Critical / Important / Suggestion).
- **Out-of-scope bug findings** with severity, backlog ID, and a `new` vs `re-seen` flag.
- **Out-of-scope additions** with no severity and no backlog ID — flagged for per-PR user decision.

## Verification discipline

Be skeptical — reject anything you cannot confirm by reading the code. A finding reported by multiple specialists is more likely real, but multiplicity alone does not confirm; you must still read the code at each finding's `file:line`. Treat the Definitions and Mechanism sections of the parent `SKILL.md` as authoritative for the in-scope vs out-of-scope rules (blame default → reasoning promotion → cosmetic-touch demotion) and for the `category: out-of-scope-addition` short-circuit.

When minting a new backlog entry, derive the Symbol from the enclosing function/class/method at the finding's line; if there is no enclosing symbol, use the literal sentinel `<file-scope>`.
