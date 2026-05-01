# PR1 Spec Compliance behavioral checklist

After extraction, re-running /paad:agentic-review against the same
fixtures must produce output that satisfies every item below. If any
item fails after the green step, the extraction is broken.

The fixtures both produce zero Spec Compliance findings (one clean,
one bail-out), so the checklist leans on the *content* of the
explanations rather than finding counts. See
`notes/convert-skills.md` "Caveat: zero-finding baselines are weaker
tests" for context.

## Skill version

- [ ] Both runs announce `Running paad:agentic-review v<X.Y.Z>` where
      `<X.Y.Z>` matches `plugins/paad/.claude-plugin/plugin.json`'s
      `version` field at the time of the post-extraction run (will be
      v1.15.0 after Task 5's bump).

## Behaviors fixture (`83aa677`)

- [ ] Spec Compliance is listed in `## Review Metadata` →
      `Agents dispatched:` (proves the specialist ran, didn't get
      silently dropped).
- [ ] Spec Compliance produces a clean summary (no Missing/Deviation/
      out-of-scope-addition findings) — the report has zero entries
      whose `Found by:` line names "Spec Compliance".
- [ ] The clean summary explicitly addresses all three commit-message
      items by name: **S5**, **S6**, **S10**. Each must be matched
      against a specific diff line (cite the line — the baseline
      points S10 → line 163, S5 → lines 219/224/358, S6 → line 220).
- [ ] The clean summary ends with the literal sentence
      "Spec compliance: clean."
- [ ] `## Review Metadata` → `Intent sources consulted:` names the
      commit body for `83aa677` (commit messages, item 4 in the
      Spec Compliance priority list). It must NOT name PR description,
      plan/design docs, or branch name as the source.
- [ ] No `## Out-of-Scope Additions` section appears (additions count
      is 0; Empty-Section rule omits the section).
- [ ] No specialist (including Spec Compliance) emits "Implemented" /
      "Not yet implemented" lists.

## Regression-watch (other specialists, behaviors fixture)

These items aren't strict acceptance criteria for the extraction —
they cover specialists not touched by PR1 — but a divergence here
likely means something else broke. Worth eyeballing:

- [ ] At least one Critical finding ([C1]) or its equivalent — the
      verifier-prompt prompt-injection-defense issue at SKILL.md:224.
- [ ] Roughly seven Important/Suggestion findings (I1-I6, S1 in the
      baseline) on Symbol-derivation, sentinel collisions, nested
      backticks, exact-string `category` matching, etc.

## Bail-out fixture (`f9c9230` — synthetic of `5f03453`)

- [ ] Spec Compliance is listed in `## Review Metadata` →
      `Agents dispatched:`.
- [ ] Spec Compliance bails out with a message that includes the
      literal phrase "Spec compliance: skipped — no intent source
      identified" (or equivalent — the actual baseline says
      "Spec compliance: skipped — no intent source identified").
- [ ] The bail-out output enumerates which intent sources were
      checked and why each failed: `$ARGUMENTS` (base ref, not a
      spec), no PR, no plan-doc reference, steering file silent on
      the change, commit subject is non-spec, branch name is a
      fixture identifier.
- [ ] `## Review Metadata` → `Intent sources consulted:` reads
      "none — Spec Compliance skipped" (or close).
- [ ] No findings whose `Found by:` line names "Spec Compliance".
- [ ] No `## Out-of-Scope Additions` section.

## Optional: post-extraction divergence note

After the post-extraction run, fill in a short note here recording
any acceptable divergences from the baseline (e.g. minor wording
shifts that don't affect any checklist item). If the extraction
landed cleanly, leave this section empty.
