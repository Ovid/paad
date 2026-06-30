# Design: Bundle PAAD skills into a Kiro Power

**Date:** 2026-06-30
**Status:** Design v2 — revised after adversarial pushback review (findings folded in below)
**Goal:** Distribute PAAD's skills to Kiro IDE users as an installable Kiro "power," maintained alongside the existing Claude Code plugin from a single source of truth.

## Background

PAAD is a Claude Code plugin marketplace (`github.com/Ovid/paad`) distributing 9 skills:
`agentic-a11y`, `agentic-architecture`, `agentic-review`, `alignment`, `fix-architecture`,
`help`, `makefile`, `pushback`, `vibe`. Each skill is a pure prompt/instruction skill — a
`SKILL.md` with `name` + `description` frontmatter, markdown instructions, and a graphviz
digraph. No executable tools or MCP servers.

A Kiro **power** bundles tools, workflows, and best practices that the Kiro IDE activates
on-demand. Verified structure (from https://kiro.dev/docs/powers/create/ and
https://kiro.dev/docs/steering/):

- **POWER.md** (required) — frontmatter (`name`, `displayName`, `description`, `keywords`,
  `author`) + onboarding/steering body. Power-level `keywords` drive when the power activates.
- **mcp.json** (optional) — MCP server config. **Not needed** for PAAD (no tools/servers).
- **steering/** (optional) — workflow-specific markdown guidance files.

Powers install via the Kiro IDE, kiro.dev, or GitHub repo URLs ("Add Custom Power → Import
from GitHub" / "Local Directory" with an absolute path to the power directory).

**Verified install constraint (load-bearing):** for GitHub-URL installs, *"The power must have
a valid `POWER.md` file in the repository root"* (https://kiro.dev/docs/powers/installation/).
There is **no subdirectory/path support** for GitHub imports. Kiro consumes the committed
files directly (it does not build from source) and updates by refreshing from the remote repo.
This single fact drives the distribution decision below.

**Verified discovery mechanism:** manual steering files are discovered two native ways
(https://kiro.dev/docs/steering/): typing `#steering-file-name` in chat, and — importantly —
*"Manual steering files also appear as slash commands — type `/` in chat to see and select
them."* The native `/` slash-command list is the discovery primitive; we do **not** need to
invent a POWER.md dispatcher to surface `#names`.

## Decisions (from brainstorming, revised after pushback)

1. **Goal:** Reach Kiro users — a real, maintained second distribution channel.
2. **Granularity:** One `paad` power; each skill becomes a steering file (one install, one
   identity).
3. **Sync model:** Generated from `SKILL.md` (single source of truth). Kiro artifacts are
   generated and committed, never hand-edited.
4. **Inclusion mode:** All steering files use `inclusion: manual` — surfaced as native `/`
   slash commands (and `#<name>` references), the truest equivalent of deliberate `/paad:`
   invocation, with no skill-level auto-firing of a gated multi-agent audit.
5. **Distribution = single repo, `POWER.md` at the `paad` repo root (REVISED twice).**
   - v1 was `powers/paad/` subdirectory — *rejected*: GitHub-URL installs require `POWER.md`
     at the **repository root** (verified), and a subdirectory cannot be installed.
   - v2 was a dedicated `Ovid/paad-kiro` repo — *also workable, but rejected for ceremony*: it
     adds a second repo and a cross-repo publish step.
   - **v3 (chosen): generate `POWER.md` + `steering/` directly into the existing `paad` repo
     root.** Kiro's only hard requirement is a valid `POWER.md` at the repo root, which `paad`
     already has. Kiro users install `github.com/Ovid/paad`; Kiro reads `POWER.md` + `steering/`
     and ignores everything else in the repo.
   - **Why:** lowest ceremony (no second repo, no submodule, no cross-repo push), and the
     strongest drift/provenance story because source and generated artifact share one git
     history — `git diff --exit-code` and commit history alone prove the power matches the
     `SKILL.md` files that produced it.
   - **Trade-off accepted:** the marketplace repo root carries Kiro files alongside
     `.claude-plugin/`, and Kiro consumers pull the whole repo (harmless — Kiro reads only
     POWER.md + steering).
   - **One caveat to confirm before build:** that Kiro tolerates unrelated extra files at the
     repo root (very likely — the docs state only the POWER.md-at-root requirement, not an
     exclusivity rule — but verify empirically with a test install).

## Verified: Kiro steering inclusion modes

Frontmatter **must be the very first content** in the file — no blank lines or content before it.

| Mode | Syntax | Activation |
|---|---|---|
| always | `inclusion: always` | Every interaction |
| fileMatch | `inclusion: fileMatch` + `fileMatchPattern: "..."` | When editing matching files |
| **manual** | `inclusion: manual` | Only when user types `#steering-file-name` |
| auto | `inclusion: auto` + `name:` + `description:` | When the request matches `description` |

PAAD uses **manual** for all steering files (decision 4). `auto` was considered (it is the
native analog of Claude Code's description-based skill activation) but rejected because PAAD's
gated workflows should not auto-fire from conversation alone. Manual files are invoked
deliberately via the native `/` slash-command list or `#<name>` — no dispatcher needed.

**Residual noise caveat (from pushback):** the *power itself* still activates on its
power-level `keywords` (POWER.md frontmatter). So a broad aggregate keyword set re-introduces
"noisy activation" at the power level — the very thing manual mode avoids at the skill level.
This is a real tension, not fully eliminated; mitigation is a *curated, narrow* aggregate
keyword set (see open questions), not a naive union of every skill's keywords. Even when the
power activates, no gated workflow runs until the user explicitly invokes its slash command.

## Repo layout (single repo)

Everything lives in `github.com/Ovid/paad`. `POWER.md` + `steering/` sit at the root
(required for GitHub-URL install) and are generated; only `SKILL.md` is hand-edited.

```
paad/                                ← Kiro installs this repo; reads root POWER.md + steering/
├── POWER.md                         ← GENERATED, root (required for GitHub-URL install)
├── steering/                        ← GENERATED
│   ├── agentic-a11y.md
│   ├── agentic-architecture.md
│   ├── agentic-review.md
│   ├── alignment.md
│   ├── fix-architecture.md
│   ├── makefile.md
│   ├── pushback.md
│   └── vibe.md                      ← 8 files: all skills EXCEPT help (see edge cases)
├── plugins/paad/skills/*/SKILL.md   ← canonical source (unchanged, hand-edited)
├── scripts/
│   └── build-kiro-power.<ext>       ← generator: reads SKILL.md → writes POWER.md + steering/
├── .claude-plugin/                  ← Claude Code marketplace (Kiro ignores)
├── CLAUDE.md, README.md, docs/      ← (Kiro ignores)
```

Workflow: edit a `SKILL.md` → run the generator (`make kiro`) → commit `POWER.md` + `steering/`
in the same repo. No second repo, no push to elsewhere, no submodule. Kiro users who already
installed the power get updates via Kiro's "refresh from remote."

## Claude Code coexistence check (no conflict)

Verified against https://code.claude.com/docs/en/plugins. The key structural fact that makes
Option D safe: **the Claude Code plugin is not at the repo root — it lives at `plugins/paad/`.**
So the repo root is purely a *marketplace* root, whose only artifact Claude Code reads is
`.claude-plugin/marketplace.json`.

- **Reserved names are scoped to the *plugin* root, not the repo root.** Claude Code recognizes
  `skills/`, `commands/`, `agents/`, `hooks/`, `monitors/`, `bin/`, `.mcp.json`, `.lsp.json`,
  `settings.json`, and `.claude-plugin/` **at the plugin root** (`plugins/paad/`). None of these
  is `POWER.md` or `steering/`, and none is read from the marketplace repo root anyway.
- **`POWER.md` + `steering/` at the repo root collide with nothing.** They sit alongside
  `.claude-plugin/`, `plugins/`, `README.md`, `docs/` — all ignored by the other tool. Claude
  scans `plugins/paad/` for plugin components; Kiro reads root `POWER.md` + `steering/`. Fully
  orthogonal directories.
- **The `paad` name reused by both** (Kiro power `name: paad`, Claude plugin `name: paad`) is
  fine — different tools, different namespaces; it's intentional shared branding.
- **Two residual empirical checks** (folded into "must-resolve" below):
  1. Run `claude plugin validate .` *after* adding root `POWER.md` + `steering/` to confirm
     marketplace validation tolerates the extra root entries (expected to pass — marketplaces
     routinely carry README/LICENSE/docs at root).
  2. ~~`keywords`-in-frontmatter tolerance~~ — **RESOLVED 2026-06-30**: testing showed
     `claude plugin validate` doesn't inspect `SKILL.md` frontmatter at all (it passes even on
     bogus keys), so the question is moot — we use a sidecar and leave `SKILL.md` untouched.
     See "Keywords source: sidecar file" above.

## The mapping (per skill)

| SKILL.md | → | Kiro power |
|---|---|---|
| `skills/<name>/SKILL.md` body | → | `steering/<name>.md` body |
| frontmatter `name`, `description` | → | aggregated into POWER.md "when to load" mapping |
| keywords (from **sidecar**, see below) | → | aggregated into POWER.md `keywords` |
| ```` ```dot ```` digraphs | → | copied verbatim (agent guidance — valid markdown) |
| `$ARGUMENTS` usage | → | rewritten to "the user may provide a path/scope" prose |

### Keywords source: sidecar file (DECIDED — was: SKILL.md frontmatter)

Keywords live in a generator-side sidecar `scripts/kiro-keywords.yaml`, keyed by skill name —
**not** in `SKILL.md` frontmatter.

```yaml
# scripts/kiro-keywords.yaml
agentic-architecture: [architecture, coupling, structure, design review, tech debt]
pushback:             [pushback, spec review, requirements, scope, feasibility]
# ...one line per skill
```

**Why the sidecar, not frontmatter (resolved 2026-06-30 by test — pushback SERIOUS-5):**
- `claude plugin validate` was run with `keywords` added, and again with a deliberately *bogus*
  frontmatter key. **Both passed** — proving `validate` only checks `plugin.json` and does
  **not** inspect `SKILL.md` frontmatter at all. So validation can never confirm that an unknown
  frontmatter key is runtime-safe; there is no clean green signal to rely on.
- Keywords are a *Kiro* concern, not a PAAD-skill concern — keeping them in the generator keeps
  `SKILL.md` byte-for-byte untouched (zero risk to the Claude plugin) and is cleaner separation.
- Single-source-of-truth is preserved: the sidecar is the canonical source for the *Kiro-only*
  keyword metadata, versioned next to the generator that consumes it.
- The generator **warns** if a skill in `skills/` has no entry in the sidecar (catches drift
  when a new skill is added).

## Generated POWER.md shape

```yaml
---
name: paad
displayName: PAAD — Architecture, Review & Quality Skills
description: Multi-agent architecture analysis, code review, accessibility, and quality workflows.
keywords: [architecture, review, accessibility, a11y, pushback, vibe, alignment, makefile, ...]
author: Ovid
---
```

Body: **onboarding** (what PAAD is) plus a generated **"When to load steering files"
mapping** — the agent-facing routing pattern the Kiro docs describe (workflow → file). This is
derived from each skill's `name` + `description` (the `paad:help` content, generated, so it
cannot drift). Discovery for the *user* is the native `/` slash-command list, not a hand-rolled
index — the POWER.md mapping exists so Kiro's agent loads the right steering file per request,
not as a user-facing `#name` directory (correcting the v1 "dispatcher" framing).

## Generated steering file shape

```yaml
---
inclusion: manual
---
```
…followed by the SKILL.md body (with `$ARGUMENTS` and cross-skill-reference transforms).
The `inclusion: manual` block MUST be the literal first content — no blank line before it.

## Generator behavior

`scripts/build-kiro-power.*` reads `plugins/paad/skills/*/SKILL.md` and writes `POWER.md` +
`steering/` at the repo root:

1. **Per skill →** `steering/<name>.md`: prepend `inclusion: manual` frontmatter, then the
   body with transforms:
   - `$ARGUMENTS` → "the user may provide a path/scope after invoking this guide"
     (**known parity loss — pushback MODERATE-8:** Kiro manual invocation has no `$ARGUMENTS`
     substitution, so scoped skills like `agentic-architecture src/` degrade from a structured
     contract to a prose hope. Must be tested: does the agent reliably pick up a path the user
     types after the slash command? Document as a known limitation in the power's README.)
   - cross-skill refs ("run `/paad:agentic-architecture`") → "use the `/agentic-architecture`
     slash command" (or `#agentic-architecture`)
   - digraphs copied verbatim
2. **Aggregate →** `POWER.md`: frontmatter (`name`, `displayName`, `description`, aggregated
   `keywords` from `scripts/kiro-keywords.yaml`, `author`) + onboarding + the generated
   "when to load steering files" mapping.
3. **Provenance stamp:** embed the source commit into the generated output (e.g. a
   `<!-- Generated from paad@<short-sha> by build-kiro-power -->` line in `POWER.md`). In the
   single-repo model the shared git history already records provenance, but the stamp makes a
   freshly-installed power self-describing and pins exactly which `SKILL.md` revision produced
   it. (Note: the generator must read the SHA from git at run time, then write deterministic
   output — keep the stamp out of the idempotency `git diff` comparison, or the diff check
   will flip on every commit.)

### Edge cases

- A skill with no entry in `scripts/kiro-keywords.yaml` → generator **warns** (so a new skill
  is not shipped with no way to surface in the power's keyword set).
- `help` skill → becomes the POWER.md index itself; **no separate steering file** (redundant
  in Kiro — the power's onboarding *is* the help).
- Cross-skill references rewritten from `/paad:<name>` to `#<name>`.

## Testing / validation

- **Idempotency:** running the generator twice produces no diff.
- **CI/Make drift check:** regenerate and `git diff --exit-code -- POWER.md steering/` — fails
  if anyone hand-edited the generated files or forgot to regenerate after a `SKILL.md` change.
  Same repo, so this is a trivial one-line check that mechanically enforces single-source-of-truth.
- **Claude side:** `claude plugin validate .` and `claude plugin validate ./plugins/paad`
  remain the source of truth for the plugin.
- **Kiro side:** lightweight YAML-frontmatter lint enforcing the "frontmatter is first line"
  rule for steering files and POWER.md.

## Out of scope (YAGNI)

- No `mcp.json` (PAAD skills have no tools/servers).
- No `auto`/`fileMatch` inclusion modes (manual only).
- No per-skill inclusion-mode field (all manual; revisit only if a skill genuinely warrants
  seamless activation).

## Must-resolve before build (from pushback)

- ~~Verify `keywords` frontmatter tolerance~~ **DONE (2026-06-30)** — tested; `claude plugin
  validate` ignores `SKILL.md` frontmatter entirely, so we use a `scripts/kiro-keywords.yaml`
  sidecar and leave `SKILL.md` untouched. (SERIOUS-5 closed)
- **Measure steering/POWER.md size against Kiro's actual limit before building.** Data already
  exists: `agentic-a11y` ≈ 392 lines, `agentic-architecture` ≈ 278; total skill body ≈ 2,237
  lines. If Kiro caps steering-file length, the "one big steering file per skill" mapping
  breaks for the large skills and they need splitting. Test empirically; do not defer. (omission)
- **Curate the power-level keyword set** (narrow, not a union) to limit noisy power activation
  while staying discoverable. Resolve before build, not after. (MODERATE-7)
- **Pick the generator runtime** (`build-kiro-power.<ext>`) — affects CI wiring and the
  idempotency/drift-check tests. Bash vs Node vs a Make target. (omission)
- **Confirm Kiro tolerates extra root files** (Decision #5 caveat) — a test install of
  `github.com/Ovid/paad` should succeed despite `.claude-plugin/`, `plugins/`, `docs/` at root.

## Open questions (lower stakes)

- Does Kiro render/respect graphviz `dot` blocks in steering, or are they inert text? (Inert
  is acceptable — they're agent guidance, not user-facing — but worth confirming.)
- **Versioning/update story for the Kiro side.** CLAUDE.md mandates semver bumps in
  `plugin.json` + `marketplace.json`; the power's `POWER.md` should carry a matching version,
  and updates reach Kiro users via "refresh from remote" on each commit to `paad`.
- **Security/trust note** for the power README: installing from a GitHub URL injects steering
  that dispatches multi-agent workflows — same trust boundary as the Claude plugin.

## Sources

- https://kiro.dev/docs/powers/create/
- https://kiro.dev/docs/powers/
- https://kiro.dev/docs/powers/installation/
- https://kiro.dev/docs/steering/
- https://code.claude.com/docs/en/plugins (Claude Code coexistence check)
- https://github.com/kirodotdev/powers/blob/main/power-builder/POWER.md
