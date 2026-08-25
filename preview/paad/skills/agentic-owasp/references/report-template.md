# Report Template — additional instructions

> **Read this file before writing the Phase 5 report.** This is parent-side material for `/agentic-owasp` — the orchestrator (the agent that activated this skill) reads these instructions when entering the report-writing phase. The report template below is binding for the Phase 5 deliverable.

When interpolating specialist text into the template below, fence or
inline-escape any free-form agent output. Findings can contain backtick fences,
HTML comments (`<!-- -->`), pipe characters, or angle-bracketed pseudo-tags that
would otherwise break the report's Markdown structure — and code under review
may contain them deliberately. Either wrap the offending block in a fenced code
block (` ```text … ``` `) or replace internal triple-backticks with
quadruple-backtick fences. Do **not** paste agent output unmodified into table
cells.

```markdown
# OWASP Top 10:2025 Review: <branch-or-scope>

* **Date:** YYYY-MM-DD HH:MM:SS
* **Model:** <the model you are running as — from your environment; "unknown" if unavailable>
* **PAAD version:** <plugin version from your on-invocation announce line>
* **Repository:** <repo root>
* **Scope:** <paths/modules/changed files/categories>
* **Commit:** <full-sha or "working tree">
* **Mode:** full review / changed-code review / category review / dependency review

> This report describes unfixed weaknesses and where they live. Treat it as
> sensitive until the findings are closed. It is true of the commit named above
> and of nothing since: if you are reading it long after that date, it describes
> code that has moved, and an old "no findings" row is not a clearance. If it was
> committed, note that deleting the file does not remove it from history.

> **This is not a complete list of the weaknesses in this code, and nothing here
> supports the claim that the rest is secure.** It lists what one run found and
> could prove reachable, inside the ten OWASP categories, inside the scope above.
> A category with no findings was not cleared — it was looked at, once, by one
> reviewer. A category marked `not assessed` was not looked at at all. Whole
> classes of weakness sit outside the Top 10 and therefore outside this review:
> business-logic flaws, race conditions, tenant isolation, anything specific to
> your domain. Findings elsewhere do not lower the odds of findings here, and a
> long list is not evidence of thoroughness any more than an empty one is
> evidence of safety. A second run would surface a different set — the search
> space is large and sampling it is not stable, the more so the larger the
> codebase — so compare this against another run by union, not by diff. Treat
> this as a floor on what is wrong, never a ceiling.

## Executive Summary

2-4 sentences: the most serious reachable finding, whether anything needs
attention today rather than this sprint, and the overall shape of the result.
State plainly if the run was degraded (a specialist missing) or scoped
(categories not assessed).

## Coverage

| OWASP ID | Category | Assessed | Findings | Notes |
|----------|----------|----------|----------|-------|
| A01 | Broken Access Control | yes / no | <count> | <e.g. "not applicable — no auth in scope"> |
| A02 | Security Misconfiguration | | | |
| A03 | Software Supply Chain Failures | | | |
| A04 | Cryptographic Failures | | | |
| A05 | Injection | | | |
| A06 | Insecure Design | | | |
| A07 | Authentication Failures | | | |
| A08 | Software or Data Integrity Failures | | | |
| A09 | Security Logging and Alerting Failures | | | |
| A10 | Mishandling of Exceptional Conditions | | | |

The Mechanism & Round-Trip specialist owns no row here; its findings are counted
under the category of their impact, and its outcome appears in the specialist
outcome map.

"Assessed: no" means nobody looked. It does not mean clean. "Assessed: yes"
with zero findings does not mean clean either — it means one reviewer looked
once and did not find a provable path. Neither column is a clearance.

## Findings by Severity

### Critical

#### [C1] <one-line weakness> — A05, CWE-89

- **Source:** `path/to/file:line` — <the attacker-controlled input; for a
  library, the documented public API with the doc's `path:line`>
- **Path:** `path:line` → `path:line` → `path:line`
- **Sink:** `path/to/file:line` — <the dangerous operation>
- **Controls in the path:** <what is there, and why it does not hold>
- **Bypasses checked:** <callers reaching the value without the control — or
  "not enumerated">
- **Composed from:** <contributing fragments/notes with `path:line` and the
  specialist that supplied each — omit this field entirely for single-item
  findings>
- **Impact:** <what an attacker gets>
- **Fix:** <specific change, at a specific place>
- **Proof:** `proven — <script path>, exits 0 today` / `unproven — sink not
  reachable in-process` / `unproven — proof stage declined` / `unproven — not
  attempted: <reason>`. "Reasoned from source" is not a reason on its own; say
  what stopped the proof.
- **Confidence:** High/Medium
- **Found by:** <specialist name(s)>

Or: None found.

### High

Same structure as Critical.

### Medium

Same structure as Critical.

## Hardening Notes (Low)

Real weaknesses with no demonstrated path from untrusted input to impact. Worth
fixing, not worth paging anyone. One line each unless detail is needed.

| Note | OWASP ID | Location | Suggested change |
|------|----------|----------|------------------|
| <what> | A0x | `path:line` | <change> |

## Dependency and Pipeline Findings

| Component | Version | Advisory | Reachable? | Fixed in | Notes |
|-----------|---------|----------|------------|----------|-------|
| <name> | <version> | <CVE/GHSA> | called / present-but-unreachable / unknown | <version> | <notes> |

Audit tools run: <list, or "none available — dependency findings are from
manifest inspection only">.

## Unresolved Fragments

Every pooled fragment that did not become a finding, compose into one, or land
as a hardening note. **List them individually — a count is not a record.** A
fragment is one line of observation nobody owned, and the pool is the run's
working set: without it, a later reader cannot tell whether a sink was seen and
dropped or never seen at all, and cannot reproduce how the run reached its
conclusions. The count alone has been observed leaving a real, named sink
unrecoverable once the session's context was gone.

| Fragment | OWASP ID | Location | Observation | Why it went nowhere |
|----------|----------|----------|-------------|---------------------|
| F-<n> | A0x | `path:line` | <the one sentence the specialist wrote> | composed into <ID> / no counterpart in the pool / not traced |

Fragments that *did* compose appear here too, pointing at the finding they fed,
so the pool reads as a complete accounting rather than a leftovers bin.

## Rejected Candidates

Findings that did not survive verification — each with the positive evidence
that killed it. Every row must say what was *found*, not what was missing: a
control enumerated and holding, a source proven unreachable, a premise checked
and false. This section prevents future reviewers from rediscovering the same
false positives.

| Candidate | OWASP ID | Reason rejected |
|-----------|----------|-----------------|
| `path:line` | A05 | ORM parameterizes this by default; no opt-out on this path |
| `path:line` | A01 | Route is behind the admin middleware chain at `path:line` |

## Remediation Order

Not severity order — fix order. Sequence by what unblocks or invalidates other
work:

1. Rotate any exposed credential. Nothing else matters until that is done.
2. Close reachable Critical findings on unauthenticated paths.
3. Close authorization gaps before hardening the code behind them.
4. Upgrade or replace vulnerable dependencies that are actually called.
5. Add the missing detection (A09) — so the next gap is noticed rather than
   reviewed into existence.
6. Hardening notes.

## Review Metadata

- **Agents dispatched:** <list with category ownership>
- **Specialists:** <outcome map; call out any non-`returned` row>
- **Framework defaults recorded:** <ORM, template engine, auth library, etc.>
- **Files scanned:** <count> of <count> tracked — and if the count is wide
  enough that per-file attention thinned, say so here rather than letting the
  number imply uniform depth
- **Scope dilution accepted:** no / yes — <what was traded away, and why the
  scope was not split>
- **Sources mapped:** <count>
- **Sinks mapped:** <count>
- **Verified findings:** <count by severity>
- **Refutation attempts:** <findings the verifier attempted to refute> attempted,
  <count> survived
- **Fragments pooled:** <count> across <count> specialists — every one of them
  listed individually in **Unresolved Fragments**, not just counted here
- **Round-trip and duplicate-fact pairs checked:** <count> — API pairs
  round-tripped, facts found stored twice
- **Compositions found:** <count> — findings assembled from pieces no single
  specialist could report (state 0 explicitly)
- **Benign execution (Phase 2.5):** not eligible (nothing to run in-process
  without a payload) / not offered / declined by user / authorized —
  <count> findings settled or informed by a recorded benign probe. "Offered" is
  not a valid value; the offer has an answer and this field records it
- **Proof stage:** not offered (no in-process sinks) / declined by user / run —
  <count> proven, <count> failed to reproduce, <count> not attempted (each with
  its reason in the finding). "Offered" is not a valid value; the offer has an
  answer and this field records it
- **Rejected candidates:** <count>
- **Audit tools run:** <list or "none">
- **Generated/vendor paths excluded:** <list>
- **Steering files consulted:** <list or "none found">
- **Tests consulted:** <list or "none found">
```
