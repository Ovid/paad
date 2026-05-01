# Skill References Conversion Roadmap

This roadmap tracks the progressive-disclosure conversion of paad skills
to the Agent Skills `references/` pattern. Each phase corresponds to one
skill (or group) and produces its own design + plan + decision log.

Cross-phase learnings live in `notes/convert-skills.md`.

## Phase Structure

| Phase | Title                                                        | Status      |
|-------|--------------------------------------------------------------|-------------|
| 1     | Pilot — agentic-review references conversion                 | Done        |
| 2     | agentic-architecture references conversion                   | Planned     |
| 3     | agentic-a11y references conversion                           | Planned     |
| 4     | Audit non-agentic skills for references-pattern candidates   | Planned     |
| 5     | Convert non-agentic candidates identified in Phase 4         | Planned     |

---

## Phase 1: Pilot — agentic-review references conversion
<!-- plan: 2026-05-01-agentic-review-references-pilot-design.md -->

Validate the references-pattern conversion on `agentic-review` via eight
small PRs (one per extraction): six specialists, the verifier, and the
Phase 4 report template. Lock down subagent path resolution, fixture
strategy, and red-green-refactor mechanics so later phases inherit the
conventions.

### Dependencies
None.

### Out of scope
Other paad skills. Behavior changes to agentic-review.

---

## Phase 2: agentic-architecture references conversion

Apply the validated pattern to `agentic-architecture`. Likely similar
shape to agentic-review (multi-specialist + verifier + report) but with
different lenses; each lens needs its own ref file with content drawn
from the existing inline instructions.

### Dependencies
Phase 1 must be merged so the conventions are stable.

---

## Phase 3: agentic-a11y references conversion

Apply the validated pattern to `agentic-a11y`. Same shape as Phase 2.
Sequenced after Phase 2 only because there's no value in running them in
parallel; either could come first.

### Dependencies
Phase 1 must be merged.

---

## Phase 4: Audit non-agentic skills for references-pattern candidates

For each of `alignment`, `fix-architecture`, `pushback`, `vibe`,
`makefile`, and `help`: identify any conditional content ("if X, do Y")
where Y is large enough to warrant moving to a ref file loaded only when
X holds. Produce a per-skill recommendation (convert / skip / partial)
with sentinel phrases identified for each candidate extraction.

### Dependencies
Phase 1. (Phases 2 and 3 are not strict dependencies but their learnings
will inform the audit.)

---

## Phase 5: Convert non-agentic candidates identified in Phase 4

Apply the validated pattern to whichever skills Phase 4 flagged as
worth converting. Granularity (one phase per skill vs. one PR per
extraction across multiple skills) is a Phase 4 deliverable.

### Dependencies
Phase 4.
