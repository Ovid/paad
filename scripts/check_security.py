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
