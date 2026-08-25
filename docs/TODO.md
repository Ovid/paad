- Skills really don't allow subroutines. Should I start using **templates**?
    - Version announce
    - Explain things SIMPLY so that everyone can understand.
    - paad-analyst is another example of something that must be copied.
    - backlog item count
    - prompt injection guard
- Steal notes from
  https://github.com/obra/dotfiles/commits/main/.claude/CLAUDE.md
- don't rewrite to red/green/refactor if already done.
- When agents return, always produce a very terse summary
    - Verifier will replay the summary, with duplicates removed
    - Verifier will replay the summary, when false positives are rejected
- paad:analyst: add something along the lines of "trust nothing, even your own
  memory; verify everything"
- Do we want to tell pushback to first look to see if there is a simpler, more
  correct solution to a spec before pushing back? That could be disastrous if
  it's written poorly. "Only do this step if you're absolutely sure it's
  correct, and if you have a better idea, propose it."
- RELATED: We have a persistent issue whereby the skills assume that the steering files
  are correct, and that code patterns are good (unless challenged). We should
  consider if we can modify skills to be more skeptical of the steering files
  and code patterns, and to challenge them if there is a CLEAR reason for
  doing so.
- Do negative assertions distract?
- Add /implement skill to go with roadmap. That skill should be live "vibe
  mode on steroids", running brainstorming, pushback, writing plans, and
  alignment. /roadmap can call it, kind of like a subroutine. Open question is
  how the checklist applies, or if it should be?

# REJECTED

- Add .paadrc file for configuration. (decided against it, maybe later)
- memory system?

# DONE

- Reports:
    - Reports need to have proper bullet points at the top.
    - ALL REPORTS should list model name and PAAD version. This is important for
      debugging and for understanding the context of the report.
- Persistent, intermittent bug where we announce the version and then stop. We
  should change it to announcing the version and explicitly telling it to
  continue.
