---
name: pushback
description: Use when reviewing a spec, PRD, requirements doc, or design plan before implementation begins — especially when the doc feels too big, bundles unrelated features, may contradict the current codebase, or seems vague, infeasible, or thin on security and error handling. Not for cross-checking a spec against a plan — that's /paad:alignment.
---

**On invocation:** announce "Running paad:pushback v1.22.0" before anything else.

# Spec Pushback

Critically reviews a spec, PRD, requirements document, or design plan before work begins. Checks source control for conflicts with reality, then walks through issues one at a time in severity order so you can fix what matters most.

**This skill does NOT recommend a fresh session.** The conversation history may be the spec.

**Input resolution and reality check:**

```dot
digraph pushback {
  "Has $ARGUMENTS?" [shape=diamond];
  "Conversation has spec?" [shape=diamond];
  "Found in common locations?" [shape=diamond];
  "Git repo?" [shape=diamond];
  "Source control conflicts?" [shape=diamond];

  "Use that file" [shape=box];
  "Confirm with user" [shape=box];
  "Present candidates, ask user" [shape=box];
  "ASK: what spec to review?" [shape=box];
  "Present conflicts, resolve first" [shape=box];
  "Proceed to Spec Critique" [shape=box];

  "Has $ARGUMENTS?" -> "Use that file" [label="yes"];
  "Has $ARGUMENTS?" -> "Conversation has spec?" [label="no"];
  "Conversation has spec?" -> "Confirm with user" [label="yes"];
  "Conversation has spec?" -> "Found in common locations?" [label="no"];
  "Found in common locations?" -> "Present candidates, ask user" [label="yes"];
  "Found in common locations?" -> "ASK: what spec to review?" [label="no"];

  "Use that file" -> "Git repo?";
  "Confirm with user" -> "Git repo?";
  "Present candidates, ask user" -> "Git repo?";
  "ASK: what spec to review?" -> "Git repo?";

  "Git repo?" -> "Source control conflicts?" [label="yes"];
  "Git repo?" -> "Proceed to Spec Critique" [label="no"];
  "Source control conflicts?" -> "Present conflicts, resolve first" [label="yes"];
  "Source control conflicts?" -> "Proceed to Spec Critique" [label="no"];
  "Present conflicts, resolve first" -> "Proceed to Spec Critique";
}
```

**Scope shape, critique and resolution:**

```dot
digraph scope_critique_resolution {
  "Unrelated features bundled?" [shape=diamond];
  "User splits them out?" [shape=diamond];
  "Spec large?" [shape=diamond];
  "Meaningful split exists?" [shape=diamond];
  "Issues found?" [shape=diamond];
  "User says good enough / stop?" [shape=diamond];
  "More issues to present?" [shape=diamond];
  "Update spec or write report?" [shape=diamond];
  "Spec saved to a file?" [shape=diamond];

  "Identify groups, recommend splitting, ask" [shape=box];
  "Continue reviewing the remaining spec" [shape=box];
  "Note it as a scope concern, review as-is" [shape=box];
  "Suggest the split — what each piece delivers alone" [shape=box];
  "Flag the size, explain why splitting isn't practical" [shape=box];
  "Say nothing about size" [shape=box];
  "Rank findings by severity" [shape=box];
  "Present one issue: problem, options best-to-worst, recommendation" [shape=box];
  "Wait for the user's response" [shape=box];
  "ASK where to write the spec first" [shape=box];
  "Apply agreed changes; leave undiscussed requirements alone" [shape=box];
  "Write paad/pushback-reviews/<date>-<spec>-pushback.md" [shape=box];
  "List every file written or updated" [shape=box];
  "Done" [shape=box];

  "Unrelated features bundled?" -> "Identify groups, recommend splitting, ask" [label="yes"];
  "Unrelated features bundled?" -> "Spec large?" [label="no"];
  "Identify groups, recommend splitting, ask" -> "User splits them out?";
  "User splits them out?" -> "Continue reviewing the remaining spec" [label="yes"];
  "User splits them out?" -> "Note it as a scope concern, review as-is" [label="no"];
  "Continue reviewing the remaining spec" -> "Spec large?";
  "Note it as a scope concern, review as-is" -> "Spec large?";

  "Spec large?" -> "Meaningful split exists?" [label="yes (8+ requirements, many areas, long)"];
  "Spec large?" -> "Say nothing about size" [label="no"];
  "Meaningful split exists?" -> "Suggest the split — what each piece delivers alone" [label="yes"];
  "Meaningful split exists?" -> "Flag the size, explain why splitting isn't practical" [label="no — tightly interdependent"];
  "Suggest the split — what each piece delivers alone" -> "Issues found?";
  "Flag the size, explain why splitting isn't practical" -> "Issues found?";
  "Say nothing about size" -> "Issues found?";

  "Issues found?" -> "Rank findings by severity" [label="yes"];
  "Issues found?" -> "Spec saved to a file?" [label="no"];
  "Rank findings by severity" -> "Present one issue: problem, options best-to-worst, recommendation";
  "Present one issue: problem, options best-to-worst, recommendation" -> "Wait for the user's response";
  "Wait for the user's response" -> "User says good enough / stop?";
  "User says good enough / stop?" -> "Spec saved to a file?" [label="yes — remainder goes to Unresolved Issues"];
  "User says good enough / stop?" -> "More issues to present?" [label="no"];
  "More issues to present?" -> "Present one issue: problem, options best-to-worst, recommendation" [label="yes"];
  "More issues to present?" -> "Spec saved to a file?" [label="no"];

  "Spec saved to a file?" -> "Update spec or write report?" [label="yes"];
  "Spec saved to a file?" -> "ASK where to write the spec first" [label="no — came from conversation"];
  "ASK where to write the spec first" -> "Update spec or write report?";
  "Update spec or write report?" -> "Apply agreed changes; leave undiscussed requirements alone" [label="update spec"];
  "Update spec or write report?" -> "Write paad/pushback-reviews/<date>-<spec>-pushback.md" [label="write report"];
  "Apply agreed changes; leave undiscussed requirements alone" -> "List every file written or updated";
  "Write paad/pushback-reviews/<date>-<spec>-pushback.md" -> "List every file written or updated";
  "List every file written or updated" -> "Done";
}
```

## When NOT to Use This Skill

- **The user wants the spec implemented, not criticized** — say what you'd push back on in a line or two, then get on with the work. Don't run a full critique nobody asked for.

## Input Resolution

Resolve the spec to review in this order:

1. **`$ARGUMENTS` contains a file path** → use that file
2. **Conversation history contains a spec/plan/design** (from brainstorming, plan writing, or the user describing what they want) → confirm with user: "I see the design we just discussed — should I review that?"
3. **Scan common locations** → look for recently modified files in `docs/plans/`, `docs/specs/`, and files named `requirements.md`, `PRD.md`, `spec.md`, or similar in the repo root. If one obvious candidate, confirm. If multiple, present the list and ask.
4. **Nothing found** → ask: "What spec should I review? Give me a file path, or describe what you want to build and I'll push back on that."

## Phase 1: Reality Check (Source Control)

**Skip this phase if the project is not a git repository.**

Before analyzing the spec itself, check whether recent codebase changes conflict with what the spec assumes:

1. Run `git log --oneline -50 --since="2 weeks ago"` (whichever limit is reached first)
2. Read commit messages and, for relevant-looking commits, check the actual diffs
3. Compare against the spec's assumptions — does the spec reference code, tables, APIs, infrastructure, or patterns that have recently been changed, removed, or replaced?
4. **If conflicts found:** present them upfront before any other analysis. For each conflict:
   - What the spec assumes
   - What actually changed (commit SHA, date, summary)
   - Why this matters
   - Ask: "How do you want to handle this?" with options
5. **If no conflicts found:** say "No conflicts with recent changes" and move on

This phase surfaces showstoppers early. A spec that assumes deleted infrastructure is wrong before the analysis even starts.

## Phase 1.5: Scope Shape

Before digging into individual requirements, check whether the spec has structural problems that should be addressed first.

### Check 1: Feature Cohesion

Do the features in this spec serve different user goals or business objectives? If the spec bundles unrelated features — things that would naturally be separate PRs — flag it.

For each group of unrelated features:
- Identify the groups and what makes them unrelated (different user goals, different business objectives, different system concerns)
- Recommend splitting into separate specs
- Ask: "Do you want to split these out before I continue, or review as-is?"

If the user splits, continue reviewing the remaining spec. If they choose to review as-is, proceed — but note it as a scope concern.

### Check 2: Spec Size

Use heuristic signals to assess whether the spec is too large to implement safely:
- Many distinct features or requirements (roughly 8+)
- Multiple unrelated system areas affected
- Very long document
- Estimated implementation would touch many modules across the codebase

**If large AND a meaningful split exists** where each piece delivers independent value: suggest the split with a brief explanation of what each piece delivers on its own.

**If large BUT the features are tightly interdependent:** flag the size and explain why splitting isn't practical — describe the interdependencies that make the features inseparable. The author knows it's big but also knows the bigness is inherent, not accidental.

**If not large:** say nothing and move on to Phase 2.

### Ordering

Run cohesion before size. If unrelated features are found and the user agrees to split, the size problem may resolve itself.

## Phase 2: Spec Critique

Analyze the spec against these categories:

| Category | What to look for |
|----------|-----------------|
| **Contradictions** | Requirements that conflict with each other, or with the current codebase state |
| **Feasibility** | Requirements that are technically difficult or impossible given the codebase as it exists today — missing infrastructure, incompatible architecture, dependencies that don't support the requirement |
| **Scope imbalance** | Requirements wildly disproportionate in effort relative to the rest — one bullet point that's a 2-week project next to others that are 2-hour tasks |
| **Omissions** | Missing requirements that are implied or necessary given context — error handling, edge cases, migration paths, rollback plans, monitoring, permissions |
| **Ambiguity** | Requirements that could be interpreted multiple ways — vague success criteria, undefined terms, unclear scope boundaries |
| **Security concerns** | Requirements that introduce or ignore security risks — auth gaps, data exposure, injection surfaces, missing rate limits, privilege escalation |

### Presentation order

1. Rank all findings by severity (most impactful first)
2. Present **one issue at a time**
3. For each issue:
   - State the problem clearly
   - Present specific options from best to worst, with your recommendation and a short explanation for each
   - Wait for the user's response before presenting the next issue
4. The user can say "good enough" or "stop" at any point to end the review

### Analysis guidance

- **Read the codebase.** Don't just review the spec in isolation — check whether what it describes is feasible given actual code, actual schemas, actual infrastructure.
- **Be concrete.** "This is ambiguous" is unhelpful. "This says 'fast response times' — do you mean <200ms p99? <1s? This determines whether you need caching." is useful.
- **Don't nitpick wording.** Focus on issues that would cause real problems during implementation or after launch.
- **Respect scope.** The spec author chose what to include and exclude. Flag genuine omissions, not "nice to haves." If something is intentionally out of scope, don't push back on it unless it creates a real gap.
- **Consider the audience.** A rough spec from a brainstorming session deserves different treatment than a formal PRD about to be handed to a team.

## Phase 3: Resolution

After all issues are addressed (or user says "good enough" / "stop"):

Ask: **"Would you like me to update the spec directly, or write a separate pushback report?"**

### If updating the spec

- Apply agreed-upon changes to the original file
- Add/modify requirements based on the user's responses
- Don't touch requirements that weren't discussed
- If the spec came from conversation history and hasn't been saved to a file, ask: "The spec isn't saved to a file yet. Where should I write it?" — suggest a reasonable path

### If writing a report

Write to `paad/pushback-reviews/<YYYY-MM-DD>-<spec-name>-pushback.md`.

Create the `paad/pushback-reviews/` directory if it doesn't exist.

**Report template:**

```markdown
# Pushback Review: <spec name or filename>

**Date:** YYYY-MM-DD
**Spec:** <file path or "conversation history">
**Commit:** <current HEAD sha, or "N/A">

## Source Control Conflicts

<conflicts found, or "None — no conflicts with recent changes.">

## Issues Reviewed

### [1] <title>
- **Category:** <contradictions / feasibility / scope imbalance / omissions / ambiguity / security>
- **Severity:** <critical / serious / moderate / minor>
- **Issue:** <what's wrong>
- **Resolution:** <what the user decided>

(Repeat for each issue discussed.)

## Unresolved Issues

Issues not yet discussed (user stopped early). Listed for future reference.

### [N] <title>
- **Category:** ...
- **Severity:** ...
- **Issue:** ...
- **Suggested options:** ...

(Omit section if all issues were addressed.)

## Summary

- **Issues found:** N
- **Issues resolved:** M
- **Unresolved:** N - M
- **Spec status:** <ready for implementation / needs further work>
```

### If the spec came from conversation history

Ask: "The spec isn't saved to a file yet. Want me to write it to a file first?" Suggest a reasonable path based on the project structure (e.g., `docs/plans/`, `docs/specs/`). Then proceed with the chosen output option (update or report).

### List every file you wrote or updated

End the session with the file list, always — this skill edits the developer's own spec, and an edit nobody notices is worse than no edit. One line per path, each marked new or updated, covering the spec if it was updated and the report if one was written:

```
Files written or updated:
  updated  docs/specs/checkout-prd.md
  new      paad/pushback-reviews/2026-08-01-checkout-pushback.md
```

Say it even when only one file changed, and even when the user watched you change it.

## Common Mistakes

These patterns produce pushback that reads well and changes nothing. Avoid them:

| Mistake | What to do instead |
|---------|-------------------|
| Critiquing the spec without checking the codebase | Phase 1 is first for a reason. "This contradicts what already shipped" outranks every stylistic concern. |
| Listing every issue at once | One at a time, most impactful first. A wall of twenty findings gets skimmed and dismissed. |
| Raising a problem without options | Every issue needs concrete options, best to worst, with a recommendation. "This is ambiguous" is an observation, not pushback. |
| Suggesting a split because the spec is long | Length isn't the test — independent value is. Split only when each piece ships something useful on its own. |
| Mistaking sequenced work for bundled features | Phases of one coherent feature belong together. Cohesion is about whether they'd be separate PRs, not whether they're separate steps. |
| Softening findings to seem agreeable | The skill's whole value is saying what a reviewer would say before the code exists. Hedged criticism is worse than none. |
| Manufacturing issues to fill all six categories | Not every spec has security concerns or contradictions. Say a category is clean and move on. |
| Continuing past "good enough" | That's the stop signal. Keep going and the user stops reading. |
| Rewriting the spec instead of critiquing it | Present issues and let the user decide. Silent rewrites replace their judgment with yours. |
