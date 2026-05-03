# Skill References Conversion Roadmap

This roadmap tracks the progressive-disclosure conversion of paad skills
to the Agent Skills `references/` pattern. Each phase corresponds to one
skill (or group) and produces its own design + plan + decision log.

Cross-phase learnings live in `notes/convert-skills.md`.

## Phase Structure

| Phase | Title                                                        | Status      |
|-------|--------------------------------------------------------------|-------------|
| 1     | Pilot — agentic-review references conversion                 | Done        |
| 2     | agentic-architecture references conversion                   | Done        |
| 3     | agentic-a11y references conversion                           | Planned     |
| 4     | Audit non-agentic skills for references-pattern candidates   | Planned     |
| 5     | Convert non-agentic candidates identified in Phase 4         | Planned     |

---

## Phase 1: Pilot — agentic-review references conversion
<!-- plan: 2026-05-01-agentic-review-references-pilot-design.md -->

Validate the references-pattern conversion on `agentic-review` via eight
extractions: six specialists, the verifier, and the Phase 4 report
template. Lock down subagent path resolution, fixture strategy, and
red-green-refactor mechanics so later phases inherit the conventions.

Done 2026-05-01: 8 extractions landed across 4 commits, SKILL.md shrank
~38%, plugin v1.14.0 → v1.16.0. See `notes/convert-skills.md` for the
locked conventions and the Phase 1 design doc's retrospective for what
deviated from the original plan.

### Dependencies
None.

### Out of scope
Other paad skills. Behavior changes to agentic-review.

---

## Phase 2: agentic-architecture references conversion
<!-- plan: 2026-05-02-agentic-architecture-references-conversion-design.md -->

Apply the validated pattern to `agentic-architecture`. Likely similar
shape to agentic-review (multi-specialist + verifier + report) but with
different lenses. Each lens gets its own ref file — content drawn from
existing inline instructions, or authored by think-like-this-specialist
subagents where no distinctive inline content exists (Phase 1 finding;
see `notes/convert-skills.md`).

### Dependencies
Phase 1 must be done — its conventions in `notes/convert-skills.md`
are what Phase 2 inherits. Merge to main is preferred but not blocking.

---

## Phase 3: agentic-a11y references conversion

Apply the validated pattern to `agentic-a11y`. Same shape as Phase 2.
Sequenced after Phase 2 only because there's no value in running them in
parallel; either could come first.

### Dependencies
Phase 1 must be done. Merge to main is preferred but not blocking.

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
