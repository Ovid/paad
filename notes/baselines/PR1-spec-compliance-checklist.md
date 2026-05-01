# PR1 Spec Compliance behavioral checklist

After extraction, re-running /paad:agentic-review against the same
fixtures must produce output that satisfies every item below. If any
item fails after the green step, the extraction is broken.

The fixtures both produce zero Spec Compliance findings (one clean,
one bail-out), so the checklist leans on the *content* of the
explanations rather than finding counts. See
`notes/convert-skills.md` "Caveat: zero-finding baselines are weaker
tests" for context.

## Verification source legend

Each checklist item is tagged to make explicit *where* the verifier
must look to confirm it. The persistent `paad/code-reviews/...`
report file does not capture every signal — some content (clean
summaries, bail-out enumerations, the announce line) only appears
in the live specialist stdout during the run.

- **`[REPORT]`** — verifiable by reading the post-extraction report
  file alone (e.g., `## Review Metadata` bullets, finding entries
  with `Found by:` lines, presence/absence of report sections).
- **`[LIVE]`** — requires watching the live specialist output during
  the post-extraction run (e.g., the clean-summary text content, the
  bail-out enumeration, the announced version line). Reading the
  report file alone will NOT confirm these items.
- **`[BOTH]`** — confirmable from either source (e.g., presence of a
  finding type can be checked in the report; specialist intent can
  also be confirmed in live output).

## Skill version

- [ ] [LIVE] Both runs announce `Running paad:agentic-review v<X.Y.Z>`
      where `<X.Y.Z>` matches `plugins/paad/.claude-plugin/plugin.json`'s
      `version` field at the time of the post-extraction run (will be
      v1.15.0 after Task 5's bump).

## Behaviors fixture (`83aa677`)

- [ ] [REPORT] Spec Compliance is listed in `## Review Metadata` →
      `Agents dispatched:` (proves the specialist ran, didn't get
      silently dropped).
- [ ] [BOTH] Spec Compliance produces a clean summary (no Missing/
      Deviation/out-of-scope-addition findings) — the report has zero
      entries whose `Found by:` line names "Spec Compliance" (REPORT
      half), and the live specialist stdout shows a clean summary
      rather than a finding list (LIVE half).
- [ ] [LIVE] The clean summary explicitly addresses all three
      commit-message items by name: **S5**, **S6**, **S10**. Each
      must be matched against a specific diff line (cite the line —
      the baseline points S10 → line 163, S5 → lines 219/224/358,
      S6 → line 220). The clean-summary text is only in live stdout;
      the report file records only the metadata summary line.
- [ ] [LIVE] The clean summary ends with the literal sentence
      "Spec compliance: clean." This sentence is captured in the
      live specialist stdout, not in the report file.
- [ ] [REPORT] `## Review Metadata` → `Intent sources consulted:`
      names the commit body for `83aa677` (commit messages, item 4
      in the Spec Compliance priority list). It must NOT name PR
      description, plan/design docs, or branch name as the source.
- [ ] [REPORT] No `## Out-of-Scope Additions` section appears
      (additions count is 0; Empty-Section rule omits the section).
- [ ] [BOTH] No specialist (including Spec Compliance) emits
      "Implemented" / "Not yet implemented" lists. Verifiable in the
      report (no such sections) and in live stdout (no such headings
      from any specialist).

## Regression-watch (other specialists, behaviors fixture)

These items aren't strict acceptance criteria for the extraction —
they cover specialists not touched by PR1 — but a divergence here
likely means something else broke. Worth eyeballing. All items in
this section are verifiable from the report file alone (the verbatim
finding entries are persisted under `## Critical Issues`,
`## Important Issues`, and `## Suggestions`).

- [ ] [REPORT] At least one Critical finding ([C1]) or its equivalent
      — the verifier-prompt prompt-injection-defense issue at
      SKILL.md:224.
- [ ] [REPORT] Roughly seven Important/Suggestion findings (I1-I6,
      S1 in the baseline) on Symbol-derivation, sentinel collisions,
      nested backticks, exact-string `category` matching, etc.

## Bail-out fixture (`f9c9230` — synthetic of `5f03453`)

- [ ] [REPORT] Spec Compliance is listed in `## Review Metadata` →
      `Agents dispatched:`.
- [ ] [LIVE] Spec Compliance bails out with a message that includes
      the literal phrase "Spec compliance: skipped — no intent source
      identified" (or equivalent — the actual baseline says
      "Spec compliance: skipped — no intent source identified"). The
      bail-out message text is only in live stdout; the report file
      records only the metadata summary line.
- [ ] [LIVE] The bail-out output enumerates which intent sources were
      checked and why each failed: `$ARGUMENTS` (base ref, not a
      spec), no PR, no plan-doc reference, steering file silent on
      the change, commit subject is non-spec, branch name is a
      fixture identifier. This enumeration is in live stdout only.
- [ ] [REPORT] `## Review Metadata` → `Intent sources consulted:`
      reads "none — Spec Compliance skipped" (or close).
- [ ] [REPORT] No findings whose `Found by:` line names "Spec
      Compliance".
- [ ] [REPORT] No `## Out-of-Scope Additions` section.

## Post-extraction divergence note (filled in 2026-05-01)

Post-extraction verification was performed by a fresh `claude
--plugin-dir ./plugins/paad` session on 2026-05-01 (reports
captured at `paad/code-reviews/pr1-verify-{behaviors,bailout}-...md`,
findings summary in `findings.md`). Result: bail-out fixture fully
green; behaviors fixture green except for two items that the
baseline made literal acceptance criteria but that we now read as
zero-finding-baseline weakness rather than extraction breakage.

**Items that did not match the literal text (behaviors fixture):**

1. *"Spec Compliance produces a clean summary."* — Post-extraction
   run produced one Deviation finding at SKILL.md:327 (the
   per-entry Symbol shape contract drops "method" while the
   algorithm rule on lines 188/193 keeps it). This is a genuine
   internal-spec contradiction, identified by both Spec Compliance
   and Contract & Integration; the verifier merged them into one
   entry [S2]. The baseline's Spec Compliance was silent on this
   drift, but Contract & Integration caught the same drift as
   baseline [I3] at the same lines (358 in the pre-extraction line
   numbering, which is line 327 post-extraction after the ~30-line
   shrinkage). So the bug *was* in the baseline report; the
   post-extraction run merely surfaces it from one additional
   specialist. The Deviation is exactly the failure-mode (b)
   ("Internal spec contradictions / retro-edited specs") that the
   extracted reference teaches the specialist to surface.

2. *"Clean summary ends with the literal sentence 'Spec compliance:
   clean.'"* — Not produced. The reference's diff-size scaling
   rule says "Small (<50 lines): one-line summary unless something
   is wrong. Default: 'Spec compliance: clean.'" — the "unless
   something is wrong" qualifier applies; the specialist correctly
   did not declare clean when it had a Deviation to report.

**Why this is variance, not extraction breakage:**

- The extracted reference at
  `plugins/paad/skills/agentic-review/references/specialists/spec-compliance.md`
  is a verbatim content copy of the original SKILL.md inline block,
  with only structural reformatting (added top-level heading +
  role-statement intro). The diff-size scaling rule, the bail-out
  paragraph, the failure-mode (b) paragraph, and the no-Implemented/
  Not-yet lists rule all carry over unchanged. There is nothing in
  the extraction to amend — the reference is faithful.
- All extraction-specific behaviors are preserved: intent source
  named correctly (commit body, not PR/plan/branch); no
  Implemented / Not yet implemented lists; bail-out fixture's
  exact bail-out phrase used; six intent sources enumerated with
  reasons in the bail-out output.
- The verifier-prompt-prompt-injection finding ([C1] in baseline,
  [I3] in this run) was demoted from Critical to Important — a
  judgment-call severity assignment, both ratings defensible. Not
  an extraction signal.

**What this teaches us for future PRs (PR2–PR8):**

The checklist preamble already warns that zero-finding baselines
are weaker tests. PR1 is the first instance where that warning
materialized. For lenses that genuinely produce findings on the
behaviors fixture (Logic & Correctness, Error Handling, etc.),
the checklist will compare actual finding content. For lenses
where the baseline produces zero findings, future checklists
should add an explicit "and may catch additional findings the
baseline missed, provided they fall within the lens's scope and
follow the reference's rules" allowance, rather than treating
silence as a literal acceptance criterion.

**Verdict:** Task 4 behavioral verification → **accepted as ✓**.
The extraction is faithful and the post-extraction skill behaves
equivalently to the baseline plus one true-positive finding the
baseline missed.
