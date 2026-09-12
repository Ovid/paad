# Security Findings → `paad/security/` Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Every security finding from every paad skill lands only under `paad/security/`, a self-ignoring directory, so ordinary reports stay safe to commit.

**Architecture:** One "Security findings" paragraph and one Post-Review block are copied verbatim into the six skills that can produce a security finding; a new `scripts/check_security.py` (wired as `make check-security`) enforces the copies and an allowlist of skills that may name `paad/security/`. Each skill then reroutes its own qualifying findings to a file under `paad/security/`, leaves a count-and-pointer line in its ordinary report, and gains one digraph gate for the split. `backlog` learns to consume the security backlog. Migration is warn-only.

**Tech Stack:** Markdown skills, Python 3 check script (pattern: `scripts/check_internal_flag.py`), GNU make, git 2.53.

**Design doc:** `docs/plans/2026-09-12-security-findings-design.md` — read it first; this plan does not repeat its rationale.

**Rules that bind every task:**
- Edit only `preview/paad/`. Never `plugins/paad/`, `kiro_and_antigravity/`, `pi/`.
- Every skill-content task ends with `make export && make test` green before commit. `make export` regenerates from `plugins/` only, so it is a no-op for content here — run it anyway; it is the project convention.
- Digraph node labels must not contain double quotes. `scripts/lint_digraphs.py` rejects declared-but-unused nodes, undeclared nodes, and `shape=` on an edge.
- Commit messages end with the attribution lines from the session's system reminder.
- Branch: `ovid/security` (already checked out).

---

## The two verbatim texts

Both tasks 2 and 3 use these. They are the single source of truth; the script carries them as constants and the six skills carry copies.

**PARAGRAPH** (one line, placed directly under the Configuration paragraph in each of the six `SKILL.md` files):

```
**Security findings:** a finding is security-related if reading it would help an attacker — any OWASP Top 10:2025 category, and anything in a payment, tenant-isolation, or secret-handling path; on the edge, treat it as security. Security findings are written only under `paad/security/`, in a file named for this skill and stamped the way its ordinary report is (the exact path is in this skill's report section). Before the first write of a run, make sure `paad/security/.gitignore` exists and contains the single line `*` — create it if absent, never rewrite it if present. Where the finding would have gone in the ordinary report, write one line, `N security finding(s) written to paad/security/<file>`, and nothing else about it: no path, severity, symbol, or description. Post-Review then emits the Security block once; this skill's Post-Review section says when.
```

**BLOCK** (five lines inside a fenced code block, placed in each skill's Post-Review / file-list section; indentation is free, the check strips it):

```
Security: N finding(s) in paad/security/<file> (new|updated).
paad/security/.gitignore keeps the directory out of git. Deleting that file or `git add -f` bypasses it.
Also list paad/security/ in your root .gitignore, or in .git/info/exclude to keep the rule local and unmentioned.
If anything under paad/security/ was ever committed, ignoring it now does not remove it from history.
paad/security/ is scratch, not state: it exists only on this machine, `git clean -x` deletes it, and nothing brings it back.
```

The exporter's `paad/` → `.reviews/` rewrite (`scripts/convert_skills.py:251`) turns these into `.reviews/security/` for Kiro, Antigravity and Pi. No generator change.

---

### Task 1: Migrate this repo's own findings, then the root `.gitignore`

Order matters: move first, ignore second. The other order leaves live findings visible to `git add -A` in between.

**Files:**
- Move: `paad/owasp-reviews/*` → `paad/security/`
- Create: `paad/security/.gitignore`
- Modify: `.gitignore` (line 8 — the single `paad/owasp-reviews/` line; the file is 9 lines and has no other `owasp-reviews`, `code-reviews`, or `pushback-reviews` entry)

**Step 1: Confirm the directory is untracked**

Run: `git ls-files paad/owasp-reviews | wc -l`
Expected: `0`

**Step 2: Move the contents and create the local ignore file**

```bash
mkdir -p paad/security
printf '*\n' > paad/security/.gitignore
mv paad/owasp-reviews/* paad/security/
rmdir paad/owasp-reviews
ls -a paad/security
```
Expected: `.gitignore`, `INDEX.md`, the four report files and two `-proofs` directories.

**Step 3: Verify git sees nothing**

Run: `git status --short paad/`
Expected: no output.

**Step 4: Swap the root `.gitignore` line**

Replace the line `paad/owasp-reviews/` with `paad/security/`. That is the only edit. Leave `paad/owasp-llm-reviews/` and every other line alone, and add nothing: `paad/code-reviews/` and `paad/pushback-reviews/` are committed output (CLAUDE.md, and 12 tracked files between them), and a bare `code-reviews` or `pushback-reviews` pattern would silently drop every future report from `git add -A` while leaving the tracked ones in place. Result — the whole file:

```
/scratch/
.DS_Store
__pycache__/
/spec-kit/
handoff.md

# These contain potential zero-days for projects. They must *not* be committed
paad/security/
paad/owasp-llm-reviews/
```

**Step 5: Verify**

Run: `git check-ignore -v paad/security/INDEX.md`
Expected: two matching rules are possible; git prints the first — either `paad/security/.gitignore:1:*` or `.gitignore:8:paad/security/`. Either is a pass. Then `git status --short` shows only `.gitignore` modified (plus the pre-existing `docs/TODO.md` / `TODO.md` changes, which are not this branch's business — do not stage them).

**Step 6: Commit**

```bash
git add .gitignore
git commit -m "Ignore paad/security/ instead of paad/owasp-reviews/

Local OWASP reports moved by hand under paad/security/, which now
carries its own .gitignore. Move before ignore, so nothing was
visible to git add -A in between."
```

---

### Task 2: `scripts/check_security.py` and `make check-security`

**Files:**
- Create: `scripts/check_security.py`
- Modify: `Makefile:10` (`.PHONY`), `Makefile:16-22` (`self-tests`), `Makefile:31` (`tree-checks`), and a new target after `check-config` (ends at `Makefile:422`)

**Step 1: Write the script with its self-test**

```python
#!/usr/bin/env python3
"""Check the shared 'Security findings' paragraph and the paad/security/ allowlist.

Six skills can produce a finding that would help an attacker. Each carries one
paragraph and one Post-Review block, copied verbatim because skills have no
include mechanism; this script is what keeps the copies identical. It also
fails any skill outside the allowlist that names paad/security/, so a new
skill cannot start writing there without joining the list.

A tree in which no skill carries the paragraph is skipped: a shipped tree that
predates the feature can only acquire it through promotion. Partial adoption
fails.
"""

import pathlib
import sys
import tempfile

PARAGRAPH = (
    "**Security findings:** a finding is security-related if reading it would help an attacker "
    "— any OWASP Top 10:2025 category, and anything in a payment, tenant-isolation, or "
    "secret-handling path; on the edge, treat it as security. Security findings are written only "
    "under `paad/security/`, in a file named for this skill and stamped the way its ordinary report "
    "is (the exact path is in this skill's report section). Before the first write of a run, make "
    "sure `paad/security/.gitignore` exists and contains the single line `*` — create it if absent, "
    "never rewrite it if present. Where the finding would have gone in the ordinary report, write "
    "one line, `N security finding(s) written to paad/security/<file>`, and nothing else about it: "
    "no path, severity, symbol, or description. Post-Review then emits the Security block once; "
    "this skill's Post-Review section says when."
)

BLOCK = """Security: N finding(s) in paad/security/<file> (new|updated).
paad/security/.gitignore keeps the directory out of git. Deleting that file or `git add -f` bypasses it.
Also list paad/security/ in your root .gitignore, or in .git/info/exclude to keep the rule local and unmentioned.
If anything under paad/security/ was ever committed, ignoring it now does not remove it from history.
paad/security/ is scratch, not state: it exists only on this machine, `git clean -x` deletes it, and nothing brings it back."""

PRODUCERS = {
    "agentic-owasp", "agentic-review", "test-roadmap",
    "agentic-architecture", "pushback", "agentic-dedup",
}
ALLOWED = PRODUCERS | {"paad-help", "backlog"}
MARKER = "**Security findings:**"
PATH = "paad/security/"


def _normalize(text):
    return "\n".join(line.strip() for line in text.splitlines())


def check(skills_dir):
    """Return None to skip the tree, else a list of problem strings."""
    skills_dir = pathlib.Path(skills_dir)
    skill_md = {
        d.name: (d / "SKILL.md").read_text(encoding="utf-8")
        for d in sorted(skills_dir.iterdir())
        if (d / "SKILL.md").is_file()
    }
    if not any(MARKER in text for text in skill_md.values()):
        return None

    problems = []
    for name in sorted(PRODUCERS):
        text = _normalize(skill_md.get(name, ""))
        if PARAGRAPH not in text:
            problems.append(f"{name}: the Security findings paragraph is missing or not verbatim")
        if _normalize(BLOCK) not in text:
            problems.append(f"{name}: the Post-Review Security block is missing or not verbatim")
    for d in sorted(skills_dir.iterdir()):
        if d.name in ALLOWED or not d.is_dir():
            continue
        for md in sorted(d.rglob("*.md")):
            if PATH in md.read_text(encoding="utf-8"):
                problems.append(f"{md.relative_to(skills_dir)}: names {PATH} but {d.name} is not in the allowlist")
    return problems


def _write_skill(root, name, body):
    (root / name).mkdir()
    (root / name / "SKILL.md").write_text(body, encoding="utf-8")


def self_test():
    good = f"---\nname: x\n---\n\n{PARAGRAPH}\n\n## Post-Review\n\n   ```\n" + \
        "\n".join("   " + l for l in BLOCK.splitlines()) + "\n   ```\n"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        _write_skill(root, "vibe", "---\nname: vibe\n---\nnothing here\n")
        assert check(root) is None, "tree without the marker must be skipped"

        for name in PRODUCERS:
            _write_skill(root, name, good)
        assert check(root) == [], check(root)

        (root / "pushback" / "SKILL.md").write_text(good.replace("(new|updated)", "(new)"), encoding="utf-8")
        assert any(p.startswith("pushback: the Post-Review") for p in check(root)), check(root)
        (root / "pushback" / "SKILL.md").write_text(good, encoding="utf-8")

        (root / "test-roadmap" / "SKILL.md").write_text(good.replace("secret-handling", "secret handling"), encoding="utf-8")
        assert any(p.startswith("test-roadmap: the Security findings paragraph") for p in check(root)), check(root)
        (root / "test-roadmap" / "SKILL.md").write_text(good, encoding="utf-8")

        _write_skill(root, "handoff", "---\nname: handoff\n---\nwrites paad/security/handoff.md\n")
        assert check(root) == ["handoff/SKILL.md: names paad/security/ but handoff is not in the allowlist"], check(root)
    print("check_security.py: self-tests passed")


def main(argv):
    if argv[1:] == ["--self-test"]:
        self_test()
        return 0
    if len(argv) != 2:
        print("usage: check_security.py <skills-dir> | --self-test", file=sys.stderr)
        return 2
    tree = pathlib.Path(argv[1]).parent
    problems = check(argv[1])
    if problems is None:
        print(f"{tree}: SKIP check-security — no skill carries the Security findings paragraph yet (predates paad/security/).")
        return 0
    for p in problems:
        print(f"FAIL: {p}")
    if problems:
        print("      The paragraph and block are the constants in scripts/check_security.py — copy them verbatim.")
        return 1
    print(f"{tree}: security findings route to paad/security/ in every producing skill, and nowhere else.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

**Step 2: Run the self-test**

Run: `python3 scripts/check_security.py --self-test`
Expected: `check_security.py: self-tests passed`

**Step 3: Run it against both trees**

Run: `python3 scripts/check_security.py preview/paad/skills; python3 scripts/check_security.py plugins/paad/skills`
Expected: both print the `SKIP check-security` line and exit 0 (no skill carries the marker yet).

**Step 4: Wire the Makefile**

- `Makefile:10` — add `check-security` to `.PHONY`, after `check-config`.
- `Makefile:16-22` — add `@python3 scripts/check_security.py --self-test` as the last line of `self-tests`.
- `Makefile:31` — add `check-security` to `tree-checks` after `check-config`.
- After the `check-config` target (its last line is `echo "$(TREE): all skills read paad/config/."`), add:

```make
check-security: check-skill-names ## Check the six security-producing skills carry the shared paragraph verbatim, and no other skill names paad/security/
# The paragraph, the block, the producer list and the allowlist all live in the
# script; the Makefile only picks the tree. Same skip rule as check-config.
	@python3 scripts/check_security.py $(SKILLS_DIR)
```

**Step 5: Run the full suite**

Run: `make export && make test`
Expected: `All checks passed.` with two `SKIP check-security` lines in the output.

**Step 6: Commit**

```bash
git add scripts/check_security.py Makefile
git commit -m "Add make check-security for the shared Security findings paragraph

Verbatim copy in six skills, paad/security/ allowed in eight. Skips a
tree with no copy at all, so plugins/ passes until promotion."
```

---

### Task 3: Copy the paragraph and block into all six skills

Do this before any routing edit, so `check-security` is green from here on instead of failing on partial adoption for six tasks.

**Files (all under `preview/paad/skills/`):**
- Modify: `agentic-owasp/SKILL.md` (paragraph after line 10; block in Post-Review, after item 1's file list, ~line 1431)
- Modify: `agentic-review/SKILL.md` (paragraph after line 10; block after Post-Review item 1's file list, ~line 338)
- Modify: `test-roadmap/SKILL.md` (paragraph after line 18; block at the end of the file under a new `## Post-Review` heading)
- Modify: `agentic-architecture/SKILL.md` (paragraph after line 10; block after Post-Analysis item 1's file list, ~line 284)
- Modify: `pushback/SKILL.md` (paragraph after line 10; block after the file list in "List every file you wrote or updated", ~line 349)
- Modify: `agentic-dedup/SKILL.md` (paragraph after line 10; block after Post-Review item 1's file list, ~line 780)

**Step 1: Insert the paragraph**

In each of the six files, directly after the `**Configuration (experimental):**` line and its trailing blank line, insert PARAGRAPH from "The two verbatim texts" plus a blank line. Copy it from `scripts/check_security.py` — do not retype it.

**Step 2: Insert the block**

At the position listed per file above, insert this (adjust indentation to the surrounding list; the check strips it):

```markdown
   When the run wrote a security file, add the Security block once, filling in
   N, the file, and new or updated:

   ```
   Security: N finding(s) in paad/security/<file> (new|updated).
   paad/security/.gitignore keeps the directory out of git. Deleting that file or `git add -f` bypasses it.
   Also list paad/security/ in your root .gitignore, or in .git/info/exclude to keep the rule local and unmentioned.
   If anything under paad/security/ was ever committed, ignoring it now does not remove it from history.
   paad/security/ is scratch, not state: it exists only on this machine, `git clean -x` deletes it, and nothing brings it back.
   ```
```

For `test-roadmap/SKILL.md`, which has no Post-Review section (its mode files own the ending), append at the end of the file:

```markdown
## Post-Review

Both mode files end the run with their own file list (`references/execute-test-roadmap.md § Ending the run`, `references/build-test-roadmap.md § Stage 5`). When the run wrote `paad/security/test-roadmap-findings.md`, that list is followed by the Security block, once:

```
<BLOCK>
```
```

The intro sentence is deliberately generic ("when the run wrote a security file"); later tasks replace it with each skill's rule (owasp: always; the rest: N > 0).

**Step 3: Verify**

Run: `make check-security TREE=preview/paad`
Expected: `preview/paad: security findings route to paad/security/ in every producing skill, and nowhere else.`

Run: `make export && make test`
Expected: `All checks passed.` (`plugins/paad` still prints SKIP.)

**Step 4: Commit**

```bash
git add preview/paad/skills
git commit -m "Copy the Security findings paragraph and block into the six producing skills

Routing edits follow per skill; this lands the verbatim text first so
check-security is green throughout."
```

---

### Task 4: `agentic-owasp` — every path moves to `paad/security/`

**Files:**
- Modify: `preview/paad/skills/agentic-owasp/SKILL.md` at lines 95-159 (session digraph), 407, 1195-1198, 1209, 1232-1236, 1271, 1281-1284, 1417-1462 (Post-Review)

**Step 1: Paths**

Replace every `paad/owasp-reviews/` with `paad/security/` **except** the one at line 407, which becomes the cross-run rule below. Then fix the report filename at line 1235 to carry the `owasp-` prefix:

```
`paad/security/owasp-<branch-or-scope>-<YYYY-MM-DD-HH-MM-SS>-<short-sha>.md`.
```

Update the Post-Review example (lines 1427-1428) to match:

```
     new      paad/security/owasp-ovid-api-2026-08-19-10-42-13-a1b2c3d.md
     updated  paad/security/INDEX.md
```

After "Create the directory if it does not exist." (line 1236) add: "Then apply the Security findings paragraph's `.gitignore` rule before writing anything."

**Step 2: Cross-run reading (line 407)**

Replace `and any prior report cross-referenced from `paad/owasp-reviews/`.` with:

```
and any prior report cross-referenced from `paad/security/` — or from
`paad/owasp-reviews/`, where releases before this one wrote them; read that
directory too if it still exists, and if it does, add the migration line in
Post-Review.
```

**Step 3: Proof scripts (lines 1195-1198)**

Change "written under the report directory and named for the finding" to "written under `paad/security/<report-stem>-proofs/` — the report's filename without `.md`, plus `-proofs` — and named for the finding", and "no writes outside the report directory and a temp directory" to "no writes outside that `-proofs/` directory and a temp directory". The layout stays per-report, which is what runs produce today (two `<stem>-proofs/` directories sit in this repo's local `paad/owasp-reviews/`); a single shared `proofs/` would let a second run overwrite the first run's script for the same finding name and orphan the older report's proof reference.

**Step 4: Post-Review**

- Item 3: delete the first bullet ("It is a map of live weaknesses…"). The remaining two bullets stay. Change "State three limits" to "State two limits".
- Item 4: replace the whole item with:

```
4. **The Security block, every run, even at zero findings** — that is the
   version most likely to be quoted back later. Then one line of your own: a
   committed report ages into a false clearance, true of one commit and more
   authoritative-looking the staler it gets. If `paad/owasp-reviews/` still
   exists, add: *"Older reports are in `paad/owasp-reviews/`; move them under
   `paad/security/` — a committed copy stays in history."*
```

Move the block inserted in Task 3 so it sits inside this item 4, and delete the generic intro sentence from Task 3.

- Item 5: change "name them in the file list and in the commit warning" to "name them in the file list; they live under `paad/security/<report-stem>-proofs/` and are covered by the Security block".

**Step 5: Digraph**

In the session digraph (lines 98-159):
- Add node: `"Ensure paad/security/.gitignore holds * (create if absent, never rewrite)" [shape=box];`
- Rename node `"Post-Review: warn the report is a vulnerability roadmap"` to `"Post-Review: Security block, always; migration line if paad/owasp-reviews/ exists"` everywhere it appears (declaration and four edges).
- Rename node `"Post-Review: findings NOT complete, clean != secure, say why committing is risky"` to `"Post-Review: findings NOT complete, clean != secure, a committed report ages into a false clearance"` (declaration and two edges).
- Rewire the three edges that enter Phase 5 / the no-findings report so they pass through the new node first:
  - `"Write self-proving scripts, exit 0 = open" -> "Ensure paad/security/.gitignore holds * (create if absent, never rewrite)" [label="failed proofs go to rejected table"];`
  - `"Mark findings unproven, keep severity" -> "Ensure paad/security/.gitignore holds * (create if absent, never rewrite)";`
  - `"User says proceed unverified?" -> "Ensure paad/security/.gitignore holds * (create if absent, never rewrite)" [label="yes"];`
  - `"Surface found?" -> "Ensure paad/security/.gitignore holds * (create if absent, never rewrite)" [label="no"];`
  - Then: `"Ensure paad/security/.gitignore holds * (create if absent, never rewrite)" -> "Phase 5: Report (verified findings)";` and `-> "Phase 5: Report (Specialist Findings — Unverified banner)";` and `-> "Report: no reachable findings in scope";`

  That makes the gitignore node fan out to three nodes without a label saying which; that is acceptable — the lint checks structure, and the prose says the rule runs "before the first write". If you prefer precision, keep the original three edges and instead put the new node between "Phase 1: Reconnaissance" and "Live credential seen?" — one edge in, one out. Pick one; do not do both.

**Step 6: Verify**

Run: `grep -n "owasp-reviews" preview/paad/skills/agentic-owasp/SKILL.md`
Expected: only the cross-run sentence (Step 2) and the Post-Review migration line (Step 4).

Run: `make check-digraphs TREE=preview/paad && make check-security TREE=preview/paad && make export && make test`
Expected: all pass.

**Step 7: Commit**

```bash
git add preview/paad/skills/agentic-owasp
git commit -m "agentic-owasp: write reports, index and proofs under paad/security/

Old paad/owasp-reviews/ is still read for cross-run context and gets a
warn-only migration line in Post-Review."
```

---

### Task 5: `agentic-review` — verifier retags, orchestrator routes by bug class

**Files:**
- Modify: `preview/paad/skills/agentic-review/SKILL.md` at lines 20-48 (classification digraph), 149-151, 200, 287, 301-303, 325-354 (Post-Review)
- Modify: `preview/paad/skills/agentic-review/references/verifier.md` at lines 25 (step 5), 34 (bug-class bullet), 48-54 (Output)
- Modify: `preview/paad/skills/agentic-review/references/report-template.md` at lines 15, 107, 115-119

**Step 1: verifier.md — retag**

Append to step 5 (the merge step, line 25):

```
Then **retag for security**: apply the Security findings definition from the parent `SKILL.md` — a finding is security-related if reading it would help an attacker, whichever lens found it. An off-by-one in a refund calculation found by Logic & Correctness qualifies. Set that finding's `Bug class:` to `Security` and note the original lens in the entry as `(retagged from <lens>)`. Every surviving finding, in-scope or out, carries an explicit `Bug class:` line; the orchestrator routes by that line and makes no second judgment.
```

In step 7's **Bug-class field** bullet (line 34), add after the mapping sentence: "A finding retagged to `Security` in step 5 hashes as `Security` regardless of the canonical order."

In step 7's **Match** bullet (line 31): change to "**Match** in the pre-filtered backlog slice → emit `{id, last_seen, branch, sha, source}` update directive, copying `source` from the matched entry so the orchestrator writes it back to the file it came from. One exception: a match whose `source` is `paad/code-reviews/backlog.md` and whose `Bug class:` is `Security` is a legacy entry from before security routing. Emit a `migrate` directive instead — the full entry, same `id`, `last_seen` updated — so the orchestrator copies it into `paad/security/backlog.md` and never edits the committed file. The ID survives the move, so the finding hashes the same before and after the user deletes the committed copy."

In **Output** (lines 48-54): add after the three lists: "Every finding carries its `Bug class:` line. Retagged findings say `Bug class: Security (retagged from <lens>)`."

**Step 2: report-template.md — the security report and backlog**

- Line 15: after "If writing `paad/code-reviews/backlog.md` fails" add "or `paad/security/backlog.md`".
- Line 107: replace the `Backlog:` metadata line with two:

```
- **Backlog:** X new entries added, Y re-confirmed (see `paad/code-reviews/backlog.md`)
- **Security:** N finding(s) written to `paad/security/<file>`; security backlog: X new, Y re-confirmed on this machine
```

- After the "Sole writer" paragraph (line 119), add:

```
**Two backlogs, one shape.** `paad/security/backlog.md` holds every entry whose `Bug class:` is `Security`; `paad/code-reviews/backlog.md` holds the rest. Same header, same per-entry shape, same ID format, same removal rule. The orchestrator creates the security file only on the first Security directive of a run — a header-only security backlog is a file that says "look here" for nothing — and applies the `.gitignore` rule from the parent `SKILL.md`'s Security findings paragraph before the first write. An update directive is written back to the file its `source` names. The security backlog is never committed and never shared across clones: a teammate's run mints its own IDs, `git log` on it shows nothing, and "re-confirmed" there means re-confirmed on this machine.

**The security report** at `paad/security/code-review-<branch>-<YYYY-MM-DD-HH-MM-SS>-<short-sha>.md` uses this same template, holding only the `Bug class: Security` findings — in-scope tiers, Out of Scope, and their backlog IDs. In the main report, each tier or Out of Scope section that lost a finding to it carries one line: `N security finding(s) written to paad/security/<file>`. Write the security report only when N > 0.
```

**Step 3: SKILL.md — prose**

- Line 149: change "against a **file-filtered slice** of `paad/code-reviews/backlog.md`" to "against a **file-filtered slice** merged from `paad/code-reviews/backlog.md` and `paad/security/backlog.md`". After "Before invoking the verifier, the orchestrator pre-filters the backlog" add: "— both files, tagging every slice entry with `source: <file>` so the update directive lands back where the entry lives".
- Line 151: change "`git log` on the file is the audit trail." to "`git log` on `paad/code-reviews/backlog.md` is the audit trail for the committed backlog; the security backlog has no history and no audit trail beyond this machine."
- Line 200: change "the project-wide backlog at `paad/code-reviews/backlog.md`" to "the project-wide backlogs at `paad/code-reviews/backlog.md` and `paad/security/backlog.md`".
- Line 287: change "A pre-filtered slice of `paad/code-reviews/backlog.md`" to "A pre-filtered slice merged from `paad/code-reviews/backlog.md` and `paad/security/backlog.md`, each entry tagged with its `source:`". Add a sentence: "Entries with `Bug class: Security` in the committed backlog are older than this routing; they stay in the slice for dedup, and a match against one comes back as a `migrate` directive (`references/verifier.md` step 7): the orchestrator copies the entry into `paad/security/backlog.md` under its original ID, updates `last_seen` there, and never edits the committed file — see Post-Review."
- Phase 4 (lines 301-303): after the first paragraph add:

```
**Route by bug class, nothing else.** The Verifier already decided what is security-related. Every finding whose `Bug class:` is `Security`, in scope or out, goes to `paad/security/code-review-<branch>-<YYYY-MM-DD-HH-MM-SS>-<short-sha>.md`, and its backlog entry to `paad/security/backlog.md`. The main report gets the count-and-pointer line in each section that lost a finding. Apply the Security findings paragraph's `.gitignore` rule before the first write under `paad/security/`.
```

**Step 4: SKILL.md — Post-Review**

- Item 1's example gains the security lines, and the sentence gains a clause:

```
   Files written or updated:
     new      paad/code-reviews/my-branch-2026-08-01-10-42-13-a1b2c3d.md
     updated  paad/code-reviews/backlog.md
     new      paad/security/code-review-my-branch-2026-08-01-10-42-13-a1b2c3d.md
     updated  paad/security/backlog.md
```

  ("…never omit `backlog.md`, and never omit the `paad/security/` files, just because the report is the interesting file.")
- Item 2: `Backlog: X new entries added, Y re-confirmed, Z total active (committed); security backlog: X new, Y re-confirmed on this machine, Z total.`
- Item 3's out-of-scope bug sentence: after "(X new entries, Y re-confirmed)" add ", security entries in `paad/security/backlog.md`".
- Item 4: replace entirely with:

```
4. **Security block** (only when this run wrote anything under `paad/security/`): emit the block below once. Then, if this run copied any legacy entries across via `migrate` directives, say how many and: *"N legacy security entries copied to `paad/security/backlog.md` under their original IDs; delete them from `paad/code-reviews/backlog.md` — a committed copy stays in history."* If the committed file holds `Bug class: Security` entries this run did not match, say how many remain and that they move by hand the same way.
```

  Move the Task 3 block under this item and delete the Task 3 intro sentence.

**Step 5: Digraph**

In the classification digraph (lines 20-48), add:

```
  "Bug class: Security (verifier retag)?" [shape=diamond];
  "Write to paad/security/ report and backlog; count-and-pointer line in the main report" [shape=box, style=bold];
  "Write to paad/code-reviews/ report and backlog" [shape=box];
```

and edges:

```
  "In-scope" -> "Bug class: Security (verifier retag)?";
  "Update last_seen on existing entry" -> "Bug class: Security (verifier retag)?";
  "Mint new backlog entry" -> "Bug class: Security (verifier retag)?";
  "Bug class: Security (verifier retag)?" -> "Write to paad/security/ report and backlog; count-and-pointer line in the main report" [label="yes"];
  "Bug class: Security (verifier retag)?" -> "Write to paad/code-reviews/ report and backlog" [label="no"];
```

**Step 6: Verify**

Run: `make check-digraphs TREE=preview/paad && make check-references TREE=preview/paad && make check-security TREE=preview/paad && make export && make test`
Expected: all pass.

**Step 7: Commit**

```bash
git add preview/paad/skills/agentic-review
git commit -m "agentic-review: verifier retags security findings, orchestrator routes them to paad/security/

Two backlogs, one shape; the committed one keeps its git-log audit
trail, the security one is local scratch."
```

---

### Task 6: `backlog` — consume both backlogs

**Files:**
- Modify: `preview/paad/skills/backlog/SKILL.md` at lines 3, 16, 25-72 (digraph), 86-87, 108, 122-132, 170-178

**Step 1: Prose**

- Line 3 (description) and line 16: "at `paad/code-reviews/backlog.md`" → "at `paad/code-reviews/backlog.md` and `paad/security/backlog.md`". (Description is frontmatter; `paad/` there is fine for this skill — the export frontmatter check only rejects it in the *exported* description, and the exporter rewrites the path. If `make check-export-dryrun` objects, leave line 3 alone and change only line 16.)
- Line 86: "If `paad/code-reviews/backlog.md` is missing" → "If both `paad/code-reviews/backlog.md` and `paad/security/backlog.md` are missing, or together contain zero `## <id>` entries".
- Line 87: add "Show which file each entry came from; every edit goes back to the file the entry came from."
- Line 108: after "recoverable from `git log -- paad/code-reviews/backlog.md`" add ", and a security entry is not recoverable at all — `paad/security/` is ignored scratch — which is one more reason the skeptical default matters there".
- Lines 122-132: change "Delete every … from `backlog.md`" to "from the file each came from". After the commit-command example add: "The command names only `paad/code-reviews/backlog.md`. Edits to `paad/security/backlog.md` are reported in the file list and never committed — it is ignored by design."

**Step 2: Post-run (lines 170-178)**

```
Files written or updated:
  updated  paad/code-reviews/backlog.md
  updated  paad/security/backlog.md        (only when a security entry changed)
  <in Fix mode, the source files changed — count + pointer to the diff>
```

Add: "Never `git add -f` anything under `paad/security/`."

**Step 3: Digraph**

Rename `"Backlog missing or empty?"` to `"Both backlogs missing, or zero entries between them?"` (declaration and two edges). Add:

```
  "Write each edit back to the file its entry came from; security backlog never in the commit command" [shape=box];
```

and route both `"Any doubt: KEEP the entry (never delete on ambiguity)"` and `"Delete RESOLVED/GONE entries + merge-losers"` and `"Delete the entry"` through it before `"Print the git commit command for the user; NEVER run git commit"` — replace their three existing edges to the print node with edges to the new node, and add one edge from the new node to the print node.

**Step 4: Verify and commit**

Run: `make check-digraphs TREE=preview/paad && make check-security TREE=preview/paad && make export && make test`
Expected: all pass.

```bash
git add preview/paad/skills/backlog
git commit -m "backlog: read and write both backlogs, commit command covers only the committed one"
```

---

### Task 7: `test-roadmap` — security findings go to their own log

**Files:**
- Modify: `preview/paad/skills/test-roadmap/SKILL.md` at lines 36-72 (digraph), and the `## Post-Review` section added in Task 3
- Modify: `preview/paad/skills/test-roadmap/references/build-test-roadmap.md` at lines 142-145, 165-167, 267-300
- Modify: `preview/paad/skills/test-roadmap/references/execute-test-roadmap.md` at lines 70-84, 105-111, 327-354

**Step 1: build-test-roadmap.md**

- After the findings-log bullet (lines 142-145) add a bullet:

```
- **`paad/security/test-roadmap-findings.md`** — the security findings log:
  entries that pass the inclusion gate *and* the security test in the router's
  Security findings paragraph (reading it would help an attacker). Same entry
  format. Created only when there is an entry to write, after the paragraph's
  `.gitignore` rule. Never committed.
```

- Line 165-167 (the `git add` list): append one sentence: "Never `git add -f` anything under `paad/security/` — the security log stays out of every commit."
- In *The findings log* (line 267 onward), after the inclusion gate's third condition add:

```
**Then the security test.** An entry that clears the gate goes to one of two
files: if reading it would help an attacker — the router's Security findings
paragraph gives the definition — it goes to
`paad/security/test-roadmap-findings.md`; otherwise to
`paad/test-roadmap/test-roadmap-findings.md`. The ordinary log carries one
line in place of each routed entry: `N security finding(s) written to
paad/security/test-roadmap-findings.md`. On the edge, route to security.
```

**Step 2: execute-test-roadmap.md**

- Lines 70-84: add a line to the example and a sentence:

```
  updated  paad/test-roadmap/test-roadmap-findings.md (F4 added)
  updated  paad/security/test-roadmap-findings.md     (S2 added — never committed)
```

  "Name the security log the same way, only when this run added to it, and follow the file list with the Security block from the router's `## Post-Review`."
- Line 109: "point at `paad/test-roadmap/test-roadmap-findings.md` if it has entries" → "point at `paad/test-roadmap/test-roadmap-findings.md` and `paad/security/test-roadmap-findings.md` if either has entries".
- Lines 327-354 (*Logging suspected bugs*): after "record it in `paad/test-roadmap/test-roadmap-findings.md`" add "— or in `paad/security/test-roadmap-findings.md` when it passes the security test (`build-test-roadmap.md § The findings log`)". In the commit paragraph (line 344-347) change "**Commit it in the same commit as the phase's tests**" to "**Commit the ordinary log in the same commit as the phase's tests**; the security log is never committed and never `git add -f`'d — the commit invariant in step 6 covers only what git can see."
- Line 341 (the roadmap pointer) and the `Pinned by:` rule: the routed entry's reproduction must not travel in the commit either. Add, after "add a one-line pointer on the phase block in the roadmap where the finding maps to it": "For an entry routed to `paad/security/`, the pointer is the count line only — `1 security finding, see paad/security/test-roadmap-findings.md` — never the entry's ID, title, or symbol, because the roadmap is committed. And the test that pins it is the reproduction by design, so name it for the input and the observed outcome in neutral terms — what was passed, what came back or was raised — never for the class of weakness or the word that names it; the developer decodes it from the log entry, an attacker reading the suite does not." Mirror the same two sentences in `build-test-roadmap.md` at line 106-108, where the pointer rule is first stated, and in the `Pinned by:` paragraph after the entry format.

**Step 3: SKILL.md digraph**

Add to the route digraph:

```
  "Suspected bug clears the inclusion gate?" [shape=diamond];
  "Would reading it help an attacker?" [shape=diamond];
  "Log to paad/security/test-roadmap-findings.md; count line in the ordinary log; never git add -f" [shape=box, style=bold];
  "Log to paad/test-roadmap/test-roadmap-findings.md" [shape=box];
  "Drop it, never a vague note" [shape=box];
```

and edges from both `Load references/...` nodes:

```
  "Load references/execute-test-roadmap.md (next phase, break-it-check, commit)" -> "Suspected bug clears the inclusion gate?";
  "Load references/build-test-roadmap.md (Detect, Grade, Plan, Critique, Write)" -> "Suspected bug clears the inclusion gate?";
  "Suspected bug clears the inclusion gate?" -> "Drop it, never a vague note" [label="no"];
  "Suspected bug clears the inclusion gate?" -> "Would reading it help an attacker?" [label="yes"];
  "Would reading it help an attacker?" -> "Log to paad/security/test-roadmap-findings.md; count line in the ordinary log; never git add -f" [label="yes, or on the edge"];
  "Would reading it help an attacker?" -> "Log to paad/test-roadmap/test-roadmap-findings.md" [label="no"];
```

**Step 4: SKILL.md Post-Review**

Replace the Task 3 intro sentence with: "When the run added to `paad/security/test-roadmap-findings.md`, the mode file's file list is followed by the Security block, once:".

**Step 5: Verify and commit**

Run: `make check-digraphs TREE=preview/paad && make check-references TREE=preview/paad && make check-security TREE=preview/paad && make export && make test`
Expected: all pass.

```bash
git add preview/paad/skills/test-roadmap
git commit -m "test-roadmap: security findings go to paad/security/test-roadmap-findings.md, never committed"
```

---

### Task 8: `agentic-architecture`

**Files:**
- Modify: `preview/paad/skills/agentic-architecture/SKILL.md` at lines 36-90 (analysis digraph), 191-197 (Phase 4), 273-287 (Post-Analysis)

**Step 1: Phase 4**

After "Create the `paad/architecture-reviews/` directory if it doesn't exist." add:

```
Findings that meet the Security findings paragraph's definition go to
`paad/security/agentic-architecture-<YYYY-MM-DD>-<git-repo-name>.md` instead,
same template, after the paragraph's `.gitignore` rule. The main report
carries the count-and-pointer line where they would have gone. Write the
security file only when there is at least one.
```

**Step 2: Post-Analysis**

Item 1's example gains `new      paad/security/agentic-architecture-2026-08-01-myrepo.md` (a second line, "only when written"). Replace the Task 3 intro sentence with "When N > 0, emit the Security block once:".

**Step 3: Digraph**

Add:

```
  "Would reading it help an attacker?" [shape=diamond];
  "Write to paad/security/agentic-architecture-<date>-<repo>.md; count line in the report" [shape=box, style=bold];
```

Replace the edge `"Keep the finding" -> "Write report to paad/architecture-reviews/";` with:

```
  "Keep the finding" -> "Would reading it help an attacker?";
  "Would reading it help an attacker?" -> "Write to paad/security/agentic-architecture-<date>-<repo>.md; count line in the report" [label="yes, or on the edge"];
  "Would reading it help an attacker?" -> "Write report to paad/architecture-reviews/" [label="no"];
  "Write to paad/security/agentic-architecture-<date>-<repo>.md; count line in the report" -> "Write report to paad/architecture-reviews/";
```

**Step 4: Verify and commit**

Run: `make check-digraphs TREE=preview/paad && make check-security TREE=preview/paad && make export && make test`

```bash
git add preview/paad/skills/agentic-architecture
git commit -m "agentic-architecture: route security findings to paad/security/"
```

---

### Task 9: `pushback`

**Files:**
- Modify: `preview/paad/skills/pushback/SKILL.md` at lines 58-142 (scope/critique digraph), 333-352 (report and file list)

**Step 1: Report section (line 333-339)**

After "Create the `paad/pushback-reviews/` directory if it doesn't exist." add:

```
This rule covers the report only. A finding in the report that meets the
Security findings paragraph's definition goes to
`paad/security/pushback-<YYYY-MM-DD>-<spec-name>.md`, same template, after the
paragraph's `.gitignore` rule; the report carries the count-and-pointer line
in its place. A requirement the user agreed to add to their spec — "this
endpoint must require auth" — is a requirement, not a finding: it is theirs to
commit, and the spec update above writes it as it always has.
```

**Step 2: File list (lines 341-352)**

Example gains `new      paad/security/pushback-2026-08-01-checkout.md` (only when written). Replace the Task 3 intro sentence with "When N > 0, emit the Security block once:".

**Step 3: Digraph**

Add:

```
  "Any report finding would help an attacker?" [shape=diamond];
  "Write those to paad/security/pushback-<date>-<spec>.md; count line in the report" [shape=box, style=bold];
```

Replace `"Unresolved issues, or user asked for a report?" -> "Write paad/pushback-reviews/<date>-<spec>-pushback.md" [label="yes"];` with:

```
  "Unresolved issues, or user asked for a report?" -> "Any report finding would help an attacker?" [label="yes"];
  "Any report finding would help an attacker?" -> "Write those to paad/security/pushback-<date>-<spec>.md; count line in the report" [label="yes, or on the edge"];
  "Any report finding would help an attacker?" -> "Write paad/pushback-reviews/<date>-<spec>-pushback.md" [label="no"];
  "Write those to paad/security/pushback-<date>-<spec>.md; count line in the report" -> "Write paad/pushback-reviews/<date>-<spec>-pushback.md";
```

**Step 4: Verify and commit**

Run: `make check-digraphs TREE=preview/paad && make check-security TREE=preview/paad && make export && make test`

```bash
git add preview/paad/skills/pushback
git commit -m "pushback: route security findings in the report to paad/security/; spec edits unchanged"
```

---

### Task 10: `agentic-dedup`

**Files:**
- Modify: `preview/paad/skills/agentic-dedup/SKILL.md` at lines 48-90 (session digraph), 605-610 (Phase 5), 766-804 (Post-Review)

**Step 1: Phase 5**

After "Create the directory if it does not exist." add:

```
Findings that meet the Security findings paragraph's definition — the
Critical/Important entries naming authorization, credential, secret, token,
or PII handling that the old Post-Review warning used to flag — go to
`paad/security/agentic-dedup-<branch-or-scope>-<YYYY-MM-DD-HH-MM-SS>-<short-sha>.md`
instead, same template, after the paragraph's `.gitignore` rule. The main
report and the INDEX row carry the count-and-pointer line in their place.
```

**Step 2: Post-Review**

- Item 1's example gains `new      paad/security/agentic-dedup-main-2026-08-01-10-42-13-a1b2c3d.md` (only when written).
- Item 5: delete the whole "Security-disclosure warning" item (lines 785-804) and replace it with "5. **Security block** — when N > 0, once:" followed by the block from Task 3 (delete the Task 3 intro sentence).

**Step 3: Digraph**

Remove nodes `"Post-Review: sensitive paths named?"` and `"Warn before committing the report"` and their five edges. Add:

```
  "Any finding would help an attacker?" [shape=diamond];
  "Write those to paad/security/agentic-dedup-<stamp>.md; count line in the report" [shape=box, style=bold];
  "Post-Review: Security block when N > 0" [shape=box];
```

Edges:

```
  "Verifier returned?" -> "Any finding would help an attacker?" [label="yes"];
  "Verifier returned on retry?" -> "Any finding would help an attacker?" [label="yes"];
  "User says proceed unverified?" -> "Any finding would help an attacker?" [label="yes"];
  "Any finding would help an attacker?" -> "Write those to paad/security/agentic-dedup-<stamp>.md; count line in the report" [label="yes, or on the edge"];
  "Any finding would help an attacker?" -> "Phase 5: Report (verified findings)" [label="no, verified"];
  "Any finding would help an attacker?" -> "Phase 5: Report (Specialist Findings — Unverified banner)" [label="no, unverified"];
  "Write those to paad/security/agentic-dedup-<stamp>.md; count line in the report" -> "Phase 5: Report (verified findings)";
  "Report: no duplication found in scope" -> "Post-Review: Security block when N > 0";
  "Phase 5: Report (verified findings)" -> "Post-Review: Security block when N > 0";
  "Phase 5: Report (Specialist Findings — Unverified banner)" -> "Post-Review: Security block when N > 0";
  "Post-Review: Security block when N > 0" -> "Done — do NOT auto-refactor";
```

and delete the three old edges from `"Verifier returned?"`, `"Verifier returned on retry?"`, `"User says proceed unverified?"` that went straight to the Phase 5 nodes. (The unverified path with a security finding: it goes through the write node too; add `"Write those to paad/security/agentic-dedup-<stamp>.md; count line in the report" -> "Phase 5: Report (Specialist Findings — Unverified banner)" [label="if unverified"];`.)

**Step 4: Verify and commit**

Run: `make check-digraphs TREE=preview/paad && make check-security TREE=preview/paad && make export && make test`

```bash
git add preview/paad/skills/agentic-dedup
git commit -m "agentic-dedup: route security findings to paad/security/, drop the commit warning"
```

---

### Task 11: `paad-help` and `CHANGELOG.md`

**Files:**
- Modify: `preview/paad/skills/paad-help/SKILL.md` at lines 103-106, 156, 232-233, 299, 419-420, 549-550, 595-596, 697-698
- Modify: `CHANGELOG.md` under `## [Unreleased]` → `### Changed` (line 13)

**Step 1: Overview note**

After the Configuration paragraph (line 106) add:

```
Security findings: any finding that would help an attacker is written only
under paad/security/, which carries its own .gitignore, and the ordinary
report gets a count and a pointer. Add paad/security/ to your root
.gitignore too. The directory is local scratch — git clean -x deletes it.
```

**Step 2: Output lines**

- agentic-architecture (156): add `        paad/security/agentic-architecture-<date>-<repo>.md (security findings, ignored)`
- agentic-review (232-233): add `          paad/security/code-review-<branch>-<timestamp>-<sha>.md and paad/security/backlog.md (security findings, ignored)`
- backlog (299): `Input/output: paad/code-reviews/backlog.md and paad/security/backlog.md (the security one is never committed)`
- pushback (419-420): add `        Security findings in that report go to paad/security/pushback-<date>-<spec>.md (ignored)`
- agentic-dedup (549-550): add `        paad/security/agentic-dedup-<branch-or-scope>-<timestamp>-<sha>.md (security findings, ignored)`
- agentic-owasp (595-596): replace both lines with `paad/security/owasp-<branch-or-scope>-<timestamp>-<sha>.md`, `paad/security/INDEX.md (persistent, newest run on top)`, `paad/security/<report-stem>-proofs/ (if you authorized the proof stage)`, and a line `Everything lands under paad/security/, which ignores itself.`
- test-roadmap (697-698): add `        paad/security/test-roadmap-findings.md (security findings, never committed)`

**Step 3: Changelog**

Under `### Changed` in `[Unreleased]`, first bullet:

```
- **Security findings now land only in `paad/security/`, a directory that ignores itself.** Every skill that can find one — agentic-owasp, agentic-review, test-roadmap, agentic-architecture, pushback, agentic-dedup — writes it there and leaves a count in the ordinary report. Add `paad/security/` to your root `.gitignore`; move any `paad/owasp-reviews/` and any `Bug class: Security` backlog entries under it by hand.
```

**Step 4: Verify and commit**

Run: `make export && make test`
Expected: `All checks passed.`

```bash
git add preview/paad/skills/paad-help CHANGELOG.md
git commit -m "Document paad/security/ in paad-help and the changelog"
```

---

### Task 12: Drive it once by hand

**Files:** none in the repo. Scratch repo under the session scratchpad.

**Step 1: Build a scratch repo with a planted injection bug**

```bash
S=/private/tmp/claude-501/-Users-ovid-projects-paad/01238f15-0caa-48a6-b1e1-0da80c1224b4/scratchpad/sec-scratch
rm -rf "$S" && mkdir -p "$S" && cd "$S" && git init -q -b main
cat > app.py <<'EOF'
import sqlite3


def get_user(conn, username):
    """Return the row for username, or None. Username is untrusted input."""
    cur = conn.execute("SELECT * FROM users WHERE name = '" + username + "'")
    return cur.fetchone()


def refund_total(amounts):
    """Sum of refunds, excluding the last (pending) one."""
    return sum(amounts[:-1]) if amounts else 0
EOF
git add -A && git commit -qm "initial" && git switch -qc feature
sed -i '' 's/return cur.fetchone()/rows = cur.fetchall()\n    return rows[0] if rows else None/' app.py
git commit -qam "touch get_user"
```

**Step 2: Run agentic-review with the preview tree**

```bash
cd "$S" && claude --plugin-dir /Users/ovid/projects/paad/preview/paad -p "/agentic-review" --dangerously-skip-permissions
```

**Step 3: Check the three pass conditions**

```bash
cd "$S"
grep -c "security finding" paad/code-reviews/*.md          # >= 1: the pointer line is in the main report
grep -il "injection" paad/code-reviews/*.md | grep -v backlog        # must be EMPTY: no security text in the main report (not "sql" — app.py imports sqlite3, and the report may name it in scope)
ls paad/security/                                          # code-review-*.md, backlog.md, .gitignore
git status --short | grep security                         # must be EMPTY
```

If any condition fails, fix the skill text in `preview/paad/skills/agentic-review/` (not the scratch repo), rerun, and commit the fix separately.

**Step 4: Run test-roadmap twice (build, then one execute phase)**

```bash
cd "$S" && git switch -qc test-roadmap
claude --plugin-dir /Users/ovid/projects/paad/preview/paad -p "/test-roadmap" --dangerously-skip-permissions
claude --plugin-dir /Users/ovid/projects/paad/preview/paad -p "/test-roadmap" --dangerously-skip-permissions
git status --short | grep security      # must be EMPTY
git log --stat -1 | grep security       # must be EMPTY
ls paad/security/ 2>/dev/null           # test-roadmap-findings.md if the injection was logged
```

The execute phase may or may not log the injection as a finding — it is a characterization suite, and the gate is strict. A logged injection that landed in `paad/test-roadmap/test-roadmap-findings.md` instead of `paad/security/` is a fail; an unlogged one is not.

**Step 5: No commit** — this task produces no repo change unless a skill fix was needed.

---

### Task 13: Ten-run verification of the two leak-prone skills

Three runs pass a one-in-five routing miss about half the time; the design requires ten of ten. Memory from earlier sessions says the same: behavioral skill fixes need ≥10 per arm.

**Files:**
- Create: `<scratchpad>/verify.sh` (not in the repo)

**Step 1: The loop**

```bash
#!/bin/bash
# Ten runs of one skill against a fresh clone each time. Pass = 3 conditions.
set -u
SRC=$1        # scratch repo from Task 12
SKILL=$2      # agentic-review | test-roadmap
PLUGIN=/Users/ovid/projects/paad/preview/paad
pass=0
for i in $(seq 1 10); do
  # Clone the scratch repo's main explicitly: git clone checks out the source's
  # current HEAD, and Task 12 leaves it on test-roadmap with a built roadmap
  # committed. Without -b main every run would continue that roadmap instead of
  # building a fresh one, and `switch -c test-roadmap` would fail on the
  # existing branch. Setup failure aborts the run loudly rather than passing a
  # half-set-up clone into the skill.
  W=$(mktemp -d)
  { git clone -q -b main "$SRC" "$W" && cd "$W" &&
    if [ "$SKILL" = agentic-review ]; then git switch -q feature; else git switch -qc test-roadmap; fi
  } || { echo "run $i: SETUP FAIL ($W)"; cd /; continue; }
  claude --plugin-dir "$PLUGIN" -p "/$SKILL" --dangerously-skip-permissions >/dev/null 2>&1
  [ "$SKILL" = test-roadmap ] && claude --plugin-dir "$PLUGIN" -p "/$SKILL" --dangerously-skip-permissions >/dev/null 2>&1
  ok=1
  git status --short | grep -q security && ok=0
  git log --name-only | grep -q "paad/security" && ok=0
  if [ "$SKILL" = agentic-review ]; then
    ls paad/security/code-review-*.md >/dev/null 2>&1 || ok=0
    grep -il "injection" paad/code-reviews/*-*.md >/dev/null 2>&1 && ok=0
  else
    # a logged injection must be in the security log, never the ordinary one
    # ("injection" only — app.py imports sqlite3, so "sql" false-positives)
    grep -qi "injection" paad/test-roadmap/test-roadmap-findings.md 2>/dev/null && ok=0
    # and neither the committed roadmap pointer nor the pinning test may carry it
    grep -qi "injection" paad/test-roadmap/test-roadmap.md 2>/dev/null && ok=0
    git grep -qi "injection" -- ':!paad' 2>/dev/null && ok=0   # tracked files outside paad/: the phase's tests
  fi
  echo "run $i: $([ $ok = 1 ] && echo PASS || echo FAIL)  ($W)"
  pass=$((pass + ok))
  cd /
done
echo "$SKILL: $pass/10"
```

**Step 2: Run both arms**

```bash
bash verify.sh "$S" agentic-review
bash verify.sh "$S" test-roadmap
```

Expected: `agentic-review: 10/10` and `test-roadmap: 10/10`.

**Step 3: On any FAIL**

Open the kept worktree printed on that line, read the main report, find the sentence that let the finding through, tighten the skill prose in `preview/paad/skills/<skill>/`, rerun that arm from scratch. Treat one miss as a defect, not variance — a miss here is the leak.

**Step 4: Record and commit**

Add the result to the commit message of any fix, or, if no fix was needed, note the counts in the design doc's Status line (`**Status:** implemented, 10/10 agentic-review, 10/10 test-roadmap`) and commit that one-line change:

```bash
git add docs/plans/2026-09-12-security-findings-design.md
git commit -m "Design: security findings implemented and verified 10/10 on both leak-prone skills"
```

---

### Task 14: Merge

Ovid's rule: merging to `main` is always `git done -y`, never a manual merge/push.

Run: `make export && make test` one last time, then `git done -y`.

README changes wait for the release branch. Do not bump the version.

---

## Skipped on purpose

- **CLAUDE.md** gains no "Adding a skill that finds security issues" section. The check's failure message points at the script, which carries the list, the paragraph and the block. Add prose when the message proves insufficient.
- **Auto-migration** of old OWASP reports or backlog entries. Warn-only, per the design.
- **`paad/owasp-llm-reviews/`** in `.gitignore` stays. It is not one of the two lines the design names.
