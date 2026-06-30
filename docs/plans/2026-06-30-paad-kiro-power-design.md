# Design: Bundle PAAD skills into a Kiro Power

**Date:** 2026-06-30
**Status:** Design v3 — revised after a second pushback review reconciling the design with the
*already-shipping* Kiro/Antigravity path (`scripts/convert_skills.py` → `kiro_and_antigravity/`).
Coexistence, shared-generator, makefile-exclusion, and versioning findings folded in below.
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

## Existing Kiro path (this design SUPPLEMENTS it — does not replace it yet)

PAAD **already ships a Kiro distribution path**, and this power is an *additional, experimental*
channel that coexists with it — not a replacement (decided: pushback Option C):

- `scripts/convert_skills.py` generates `kiro_and_antigravity/skills/.kiro/skills/<name>/SKILL.md`
  (Kiro *skills*) plus `.agent/skills/<name>/SKILL.md` (Antigravity wrappers), committed to the repo.
- `README.md` documents manual install: users copy `.kiro/skills/*` into their own workspace's
  `.kiro/skills/`. These are *copy-source* files, inert in the paad repo until copied.

**Coexistence stance:** the power is the experimental one-click-install channel; the manual
`.kiro/skills/` copy path remains for users who want file-level control. The legacy path may be
retired later once the power is proven — until then **both are maintained**.

**No double-load risk:** the legacy artifacts sit at a *nested* path
(`kiro_and_antigravity/skills/.kiro/skills/`), not the workspace-root `.kiro/` that Kiro scans, and
a power import reads only `POWER.md` + `steering/`. Both activating at once requires a user to
deliberately install the power *and* hand-copy the legacy skills into their own workspace — their
choice, not a repo defect. (A 10-second sanity glance during the test install confirms this.)

**One shared generator core (decided: pushback Issue [2] Option A):** the power generator and
`convert_skills.py` MUST share one body-cleaning core so the two outputs never diverge in *content*,
only in *wrapper*. See "Generator behavior" — the power reuses `convert_skills.py`'s section-exclusion
set verbatim.

## Decisions (from brainstorming, revised after pushback)

1. **Goal:** Reach Kiro users — a real, maintained second distribution channel.
2. **Granularity:** One `paad` power; each skill becomes a steering file (one install, one
   identity).
3. **Sync model:** Generated from `SKILL.md` (single source of truth). Kiro artifacts are
   generated and committed, never hand-edited.
4. **Inclusion mode:** All steering files use `inclusion: manual` — surfaced as native `/`
   slash commands (and `#<name>` references), the truest equivalent of deliberate `/paad:`
   invocation, with no skill-level auto-firing of a gated multi-agent audit.
5. **Distribution = single repo, `POWER.md` at the existing `paad` repo root (RECOMMENDED —
   revised twice).**
   - v1 was `powers/paad/` subdirectory — *rejected*: GitHub-URL installs require `POWER.md`
     at the **repository root** (verified), and a subdirectory cannot be installed.
   - v2 was a dedicated `Ovid/paad-kiro` repo — *workable, and the safe fallback (see below), but
     not the default*: it adds a second repo, a submodule/checkout, and a cross-repo publish push.
   - **v3 (CHOSEN): generate `POWER.md` + `steering/` directly into the existing `paad` repo
     root.** Kiro's only documented requirement is a valid `POWER.md` at the repo root; `paad`
     already is a repo root. Kiro users install `github.com/Ovid/paad`; Kiro reads `POWER.md` +
     `steering/`.
   - **Why single repo wins:** one place to edit and commit, **shared git history** (so provenance
     and the drift check are trivial — no cross-repo stamp needed to span histories), no submodule,
     no publish push. The daily simplicity dividend is real and recurring.
   - **The one risk, and why it's acceptable:** no *observed* published power shares its root with
     unrelated files (the official catalog organizes powers as subdirs). But that is absence of
     observation, not a documented prohibition — the docs state only the POWER.md-at-root
     *requirement*, no exclusivity rule, and a GitHub-URL import that rejected repos for carrying a
     README would reject nearly every real repo. The risk is low **and cheaply verified**: one test
     install before relying on it (see "Must-resolve").
   - **Fallback if that test fails:** the dedicated `Ovid/paad-kiro` repo (v2) — a clean
     POWER.md-at-root repo matching the catalog convention exactly. The same generator output ships
     there instead, with a `paad@<sha>` provenance stamp to bridge the now-separate histories. Adopt
     only if the busy-root test actually fails.

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
│   ├── pushback.md
│   └── vibe.md                      ← 7 files: all skills EXCEPT help AND makefile (edge cases)
├── plugins/paad/skills/*/SKILL.md   ← canonical source (unchanged, hand-edited)
├── kiro_and_antigravity/            ← legacy Kiro/Antigravity copy-source (coexists; see above)
├── scripts/
│   ├── convert_skills.py            ← EXISTING: SKILL.md → .kiro/skills + .agent/skills (legacy)
│   └── build-kiro-power.py          ← power generator; shares body-cleaning core with the above
├── .claude-plugin/                  ← Claude Code marketplace (Kiro ignores)
├── CLAUDE.md, README.md, docs/      ← (Kiro ignores)
```

Workflow: edit a `SKILL.md` → run the generator (`make kiro`) → commit `POWER.md` + `steering/`
in the same repo. No second repo, no push elsewhere, no submodule. Kiro users who already
installed the power get updates via Kiro's "refresh from remote."

**Fallback (dedicated repo, v2):** if the pre-build test install shows Kiro rejects a busy root,
publish the same generated `POWER.md` + `steering/` to a dedicated `github.com/Ovid/paad-kiro` repo
(clean root) instead, with a `paad@<sha>` provenance stamp to bridge the separate histories. Only if
the test fails.

## Claude Code coexistence check (no conflict)

Verified against https://code.claude.com/docs/en/plugins. The key structural fact that makes
the single-repo plan safe: **the Claude Code plugin is not at the repo root — it lives at `plugins/paad/`.**
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
keywords: [architecture, review, accessibility, a11y, pushback, vibe, alignment, ...]
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
   body run through the **shared body-cleaning core** (the same logic `convert_skills.py` uses),
   with transforms:
   - **Strip non-portable orchestration sections** — reuse `convert_skills.py`'s exclusion set
     verbatim: `["Arguments", "Input Resolution", "Pre-flight Checks", "Document classification"]`.
     These are Claude-Code-specific scaffolding (e.g. the "search your system prompt for your model
     ID" probe, `$ARGUMENTS` resolution logic) that misfires in Kiro. **This closes pushback
     Issue [2]:** the power's transforms must not be thinner than the tool already shipping working
     Kiro output. A test asserts no `## Pre-flight`/`## Input Resolution` survives in `steering/`.
   - `$ARGUMENTS` → an explicit instruction to the user to **name the scope in their chat message**
     (e.g. "After invoking this guide, state the path or scope you want reviewed, such as `src/`").
     (**CONFIRMED parity loss — pushback MODERATE-8, RESOLVED 2026-06-30:** Kiro's docs are explicit
     that invoking a manual steering file just *"adds the file's contents to your current conversation
     context"* — there is **no** argument/parameter/`$ARGUMENTS` mechanism on slash commands at all.
     So this is not a "test whether it works" item; it is a known, permanent limitation. The prose
     transform must therefore *prompt* the user for scope rather than imply automatic capture, and the
     power README documents it. Source: https://kiro.dev/docs/chat/slash-commands/ ,
     https://kiro.dev/docs/steering/)
   - cross-skill refs ("run `/paad:agentic-architecture`") → "use the `/agentic-architecture`
     slash command" (or `#agentic-architecture`)
   - digraphs copied verbatim
2. **Aggregate →** `POWER.md`: frontmatter (`name`, `displayName`, `description`, aggregated
   `keywords` from `scripts/kiro-keywords.yaml`, `author`) + onboarding + the generated
   "when to load steering files" mapping.
3. **Provenance stamp:** embed the source commit into the generated output (e.g. a
   `<!-- Generated from paad@<short-sha> by build-kiro-power -->` line in `POWER.md`). In the
   single-repo model the shared git history already records provenance, so this is a nice-to-have
   that makes a freshly-installed power self-describing; it becomes *load-bearing* only in the
   dedicated-repo fallback (where histories are separate). (Note: the generator reads the SHA from
   git at run time, then writes otherwise-deterministic output — keep the stamp out of the
   idempotency `git diff` comparison, or the drift check will flip on every commit.)

### Edge cases

- A skill with no entry in `scripts/kiro-keywords.yaml` → generator **warns** (so a new skill
  is not shipped with no way to surface in the power's keyword set).
- `help` skill → becomes the POWER.md index itself; **no separate steering file** (redundant
  in Kiro — the power's onboarding *is* the help).
- `makefile` skill → **excluded** (no steering file), matching the legacy `convert_skills.py`
  `skip_names = ["makefile", "help"]`. Decided: pushback Issue [4] Option B — keep the two outputs'
  skill sets identical; makefile was intentionally omitted from the shipping Kiro path and the power
  follows suit. Net: **7 steering files** (all skills except `help` and `makefile`).
- Cross-skill references rewritten from `/paad:<name>` to `#<name>`.

## Testing / validation

- **Idempotency:** running the generator twice produces no diff.
- **CI/Make drift check:** regenerate and `git diff --exit-code -- POWER.md steering/` — fails
  if anyone hand-edited the generated files or forgot to regenerate after a `SKILL.md` change.
  Same repo, so this is a trivial one-line check that mechanically enforces single-source-of-truth
  (exclude the provenance stamp from the comparison — see Generator behavior #3). (In the
  dedicated-repo fallback this runs against the `paad-kiro` checkout instead.)
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
- ~~**Measure steering/POWER.md size against Kiro's actual limit**~~ **RESOLVED (2026-06-30,
  docs + search).** No per-file size cap is documented. Kiro manages size via the *context window*:
  it auto-summarizes at ~80% of the model limit, with ~50–60K tokens (~200–240K chars) of working
  context (kirodotdev/Kiro #4162 is an open feature request for context-size monitoring → no hard
  enforcement today). PAAD's largest skill (`agentic-a11y` ≈ 392 lines) is far under that, and
  because every steering file is `inclusion: manual`, only the single invoked file enters context —
  never the ~2,237-line aggregate. The "one steering file per skill" mapping holds; no splitting
  needed. Source: https://kiro.dev/docs/steering/ , https://github.com/kirodotdev/Kiro/issues/4162
- **Curate the power-level keyword set** (narrow, not a union) to limit noisy power activation
  while staying discoverable. Resolve before build, not after. (MODERATE-7)
- ~~**Pick the generator runtime**~~ **RESOLVED (pushback Issue [2])** — Python, reusing
  `scripts/convert_skills.py`'s body-cleaning core (`build-kiro-power.py`). No new runtime; the two
  generators share one transform core so legacy and power outputs can never diverge in content.
- **Root-file tolerance — one quick pre-build test gate for the single-repo plan (low risk).**
  - *Requirement confirmed:* https://kiro.dev/docs/powers/installation/ — "The power must have a valid
    `POWER.md` file in the repository root"; no subdirectory/path support. (The `kirodotdev/powers`
    monorepo's powers-in-subdirs does NOT contradict this — it has no root POWER.md and is the
    first-party *catalog*, consumed via Kiro's built-in browser, not "Import from GitHub URL.")
  - *Why low risk:* docs state only the POWER.md-at-root *requirement*, **no exclusivity rule**; a
    GitHub-URL import that rejected repos for carrying a README/LICENSE would reject nearly every real
    repo, and the catalog repo's own root carries `README`, `CONTRIBUTING`, `.github/`, `.kiro/`. The
    "every published power has a minimal root" observation (verified via
    `gh api repos/kirodotdev/powers/contents/...` 2026-06-30: `stripe`, `power-builder`) reflects how
    the *catalog* organizes subdirs, not an enforced minimalism — absence of observation, not
    prohibition.
  - *The gate:* before relying on single-repo, do one test install of `github.com/Ovid/paad` and
    confirm Kiro reads `POWER.md` + `steering/` despite `.claude-plugin/`, `plugins/`, `docs/`,
    `kiro_and_antigravity/`, `scripts/`, `CLAUDE.md` at root. **If it fails → dedicated `Ovid/paad-kiro`
    repo fallback (Decision #5).** Source: https://github.com/kirodotdev/powers.

## Implementation plan

Ordered so the cheap kill-switch checks (Phase 0) run before any code is written, and each later
phase has a concrete done-condition. Phases 1–3 are the build; 4–5 wire up safety and docs.

### Phase 0 — Resolve the gates (no code yet)

These are the "Must-resolve before build" items; none requires writing the generator first.

1. **Busy-root test install (the one real risk).** Hand-author a *minimal throwaway* `POWER.md` +
   `steering/one-file.md` at the `paad` repo root **on a scratch branch**, push, and install
   `github.com/Ovid/paad` into Kiro via "Add Custom Power → Import from GitHub."
   - **Pass** → Kiro reads `POWER.md` + `steering/` despite `.claude-plugin/`, `plugins/`, `docs/`,
     etc. at root → proceed single-repo.
   - **Fail** → switch to the dedicated `Ovid/paad-kiro` repo fallback (Decision #5) before Phase 1.
   - Delete the scratch branch either way.
2. **Curate the power-level keyword set** (narrow, not a union of all skills' keywords) — draft
   `scripts/kiro-keywords.yaml` now; it is an input to Phase 1, not an output.
3. **Re-run `claude plugin validate .` and `claude plugin validate ./plugins/paad`** to capture the
   green baseline *before* adding any root files, so a later failure is attributable.

**Gate:** do not start Phase 1 until #1 has a verdict and #2 exists.

### Phase 1 — Generator (`scripts/build-kiro-power.py`)

1. **Refactor the shared body-cleaning core out of `convert_skills.py`** into an importable function
   (section-exclusion set `["Arguments", "Input Resolution", "Pre-flight Checks", "Document
   classification"]`, `/paad:`-line handling, path neutralization). Both generators import it — this
   is pushback Issue [2] Option A; the two outputs must never diverge in body content.
   - **Legacy regression guard (alignment Issue [1]):** *before* refactoring, snapshot the current
     `kiro_and_antigravity/` tree; *after* refactoring, regenerate via `convert_skills.py` and
     `git diff --exit-code` against the snapshot. **Done-condition: zero diff** — the shared-core
     extraction must not alter a single byte of the shipping legacy/Antigravity output.
2. **`build-kiro-power.py` reads `plugins/paad/skills/*/SKILL.md`** and, per skill (skipping `help`
   and `makefile`), writes `steering/<name>.md`: `inclusion: manual` frontmatter as the literal first
   line, then the cleaned body with the power-specific transforms (`$ARGUMENTS` → prose prompt;
   cross-skill refs → `#<name>`; digraphs verbatim).
3. **Aggregate `POWER.md`**: frontmatter (`name`, `displayName`, `description`, curated `keywords`
   from the sidecar, `author`, version mirrored from `plugin.json`) + **onboarding generated from the
   `help` skill's content** (so it can't drift — alignment Issue [3]) + the generated "when to load
   steering files" mapping (derived from each skill's `name`/`description`).
4. **Provenance stamp** (`<!-- Generated from paad@<sha> ... -->`), read from git at run time and
   **excluded from the idempotency diff**.
5. **Warn** on any skill in `skills/` missing a `kiro-keywords.yaml` entry.

**Done when:** running it produces `POWER.md` + 7 `steering/*.md`; a second run yields no diff
(idempotency, stamp excluded); the legacy regression guard (#1) shows zero diff; **and**
`claude plugin validate .` + `claude plugin validate ./plugins/paad` still pass with the new root
files present (alignment Issue [2] — the Claude-side complement to Phase 0.3's baseline).

### Phase 2 — Make target + drift check

1. `make kiro` runs the generator.
2. Drift check: `make kiro && git diff --exit-code -- POWER.md steering/` (stamp excluded). Wire it
   into whatever CI exists, or document it as a pre-commit step if none.

**Done when:** a deliberate hand-edit to a generated file makes the drift check fail.

### Phase 3 — Frontmatter lint

Lightweight check that every `steering/*.md` and `POWER.md` has YAML frontmatter as the **literal
first content** (no leading blank line) — the one Kiro hard rule. Done when it flags a file with a
blank line before its frontmatter.

### Phase 4 — Docs

1. **`README.md`**: add a Kiro *power* install section (install `github.com/Ovid/paad`) alongside the
   existing manual `.kiro/skills/` copy section — frame the power as the experimental one-click
   channel, the copy path as the existing one (Issue [1] Option C coexistence).
2. **Power README / onboarding**: document the `$ARGUMENTS` limitation (user states scope in chat)
   and the security/trust note (installing injects steering that dispatches multi-agent workflows).
3. **`CLAUDE.md`**: add "regenerate the Kiro power after editing a `SKILL.md`" to the skill-change
   checklist so the power can't silently drift.

### Phase 5 — Ship

Bump `plugin.json` (+ sync `marketplace.json`), regenerate, commit `POWER.md` + `steering/` +
generator + sidecar + docs together, and do a final real install from the pushed repo to confirm
end-to-end.

### TDD task breakdown (code phases)

Phase 0 (empirical gates) and Phases 4–5 (docs/ship) are not code and stay as written above. The
code-producing units of Phases 1–3 are recast here in red/green/refactor form (alignment skill,
mandatory step). All tests are generator unit tests run against the real `plugins/paad/skills/` tree
or small fixtures.

#### Task: Shared body-cleaning core (Phase 1.1)

**Requirement:** Issue [2] Option A (one transform core) + Issue [1] (legacy output unchanged).

- **RED** — Write a test that snapshots `convert_skills.py`'s current output for one representative
  skill (e.g. `pushback`, which has the excluded `Input Resolution`/`Pre-flight Checks` sections),
  then asserts the *extracted* `clean_body()` function reproduces that exact output. Expected failure:
  the function doesn't exist yet (ImportError). *If it passes unexpectedly:* the core was already
  extracted — verify it's actually shared, not duplicated.
- **GREEN** — Extract `clean_body()` from the inline logic in `convert_skills.py` and have
  `convert_skills.py` call it. Minimal: no new behavior, just a lifted function.
- **REFACTOR** — Add the full-tree golden guard (snapshot `kiro_and_antigravity/` → regenerate →
  `git diff --exit-code`). Look to consolidate the section-exclusion list into one named constant
  both generators import (no copy-paste of the four header names).

#### Task: Steering file generation (Phase 1.2)

**Requirement:** Decisions 2 & 4 (one steering file per skill, `inclusion: manual`); edge cases
(skip `help` + `makefile`); the mapping (`$ARGUMENTS`→prose, cross-refs→`#name`, digraphs verbatim).

- **RED** — Write tests asserting: (a) exactly 7 `steering/*.md` are produced (not 8, not 9);
  (b) `help.md` and `makefile.md` are absent; (c) each file's **first line** is `---` then
  `inclusion: manual` (no leading blank); (d) a fixture containing `$ARGUMENTS` and `/paad:vibe`
  yields the prose-scope prompt and `#vibe` respectively; (e) a ```dot block survives verbatim.
  Expected failure: generator doesn't exist.
- **GREEN** — Implement per-skill emission with the three transforms. Simplest mapping that passes.
- **REFACTOR** — Extract the frontmatter-prepend and transform steps into named helpers; ensure the
  power transforms layer *on top of* the shared `clean_body()` rather than re-implementing any of it.

#### Task: POWER.md aggregation (Phase 1.3–1.5)

**Requirement:** "Generated POWER.md shape"; help-sourced onboarding (Issue [3]); keyword sidecar +
missing-entry warning; version mirrors `plugin.json`.

- **RED** — Tests asserting: (a) frontmatter has `name/displayName/description/keywords/author` and a
  `version` equal to `plugin.json`'s; (b) onboarding text is derived from the `help` skill content
  (assert a known phrase from `help/SKILL.md` appears, proving it's sourced, not hand-written);
  (c) `keywords` equals the curated sidecar values, not a union of every skill's; (d) a skill with no
  sidecar entry emits a warning. Expected failure: aggregator absent.
- **GREEN** — Build `POWER.md` from the sidecar + `help` content + `plugin.json` version.
- **REFACTOR** — Move the version read and git-SHA stamp behind small helpers; confirm the stamp is
  injected *after* the content used for the idempotency comparison so the drift check stays stable.

#### Task: Idempotency + drift check (Phase 2)

**Requirement:** Testing/validation — "running the generator twice produces no diff"; `make kiro` +
`git diff --exit-code` enforce single-source-of-truth.

- **RED** — Test that runs the generator twice and asserts the second run produces no change to
  `POWER.md` + `steering/` (with the provenance stamp normalized/excluded). Expected failure:
  non-deterministic output (e.g. dict ordering, or the raw SHA stamp flipping the diff).
- **GREEN** — Make output deterministic (sorted iteration, stable formatting); exclude the stamp from
  the compared content.
- **REFACTOR** — Wire the `make kiro && git diff --exit-code` target; share the "compare ignoring
  stamp" logic between the idempotency test and the drift check so they can't disagree.

#### Task: Frontmatter-first lint (Phase 3)

**Requirement:** Kiro hard rule — frontmatter must be the literal first content.

- **RED** — Test the linter against two fixtures: one valid (`---` on line 1) and one with a leading
  blank line; assert pass and fail respectively. Expected failure: linter absent.
- **GREEN** — Implement the check over `steering/*.md` + `POWER.md`.
- **REFACTOR** — Reuse the same frontmatter-parse helper the generator uses for writing, so "what we
  write" and "what we lint" share one definition of valid frontmatter.

## Open questions (lower stakes)

- Does Kiro render/respect graphviz `dot` blocks in steering, or are they inert text? (Inert
  is acceptable — they're agent guidance, not user-facing — but worth confirming.)
- **Versioning/update story for the Kiro side (RESOLVED — pushback Issue [5] Option A).**
  `POWER.md` mirrors the **`plugin.json`** version (the precedence source per CLAUDE.md), written
  automatically by the generator so it cannot drift and is never a third hand-maintained source.
  This disambiguates "matching version" — note `marketplace.json` (currently 1.0.0) and
  `plugin.json` (currently 1.11.0) are already out of sync, so the power explicitly follows
  `plugin.json`, not `marketplace.json`. Updates reach Kiro users via "refresh from remote."
- **Security/trust note** for the power README: installing from a GitHub URL injects steering
  that dispatches multi-agent workflows — same trust boundary as the Claude plugin.

## Sources

- https://kiro.dev/docs/powers/create/
- https://kiro.dev/docs/powers/
- https://kiro.dev/docs/powers/installation/
- https://kiro.dev/docs/steering/
- https://code.claude.com/docs/en/plugins (Claude Code coexistence check)
- https://github.com/kirodotdev/powers/blob/main/power-builder/POWER.md
