#!/usr/bin/env python3
"""Check the shared 'Security findings' paragraph and the paad/security/ allowlist.

Six skills can produce a finding that would help an attacker. Each carries one
paragraph and one Post-Review block, copied verbatim because skills have no
include mechanism; this script is what keeps the copies identical. It also
fails any skill outside the allowlist that names paad/security/, so a new
skill cannot start writing there without joining the list.

On a tree in which no skill carries the paragraph or names paad/security/,
the paragraph check is skipped: a shipped tree that predates the feature can only acquire it through
promotion. Partial adoption fails. The allowlist is enforced regardless: a tree
that predates paad/security/ cannot name it, so the scan costs nothing.

The shipped tree (plugins/) is held to the paragraph its own producers share,
not to PARAGRAPH: between a change to PARAGRAPH and the next promotion it
legitimately carries the old text. That is sound because plugins/ changes only
by promotion, and preview/ is held to PARAGRAPH.

Every skill that writes under paad/ also carries SYMLINK verbatim: the reviewed
repository can commit a symlink at any of those paths. It follows the same
skip, partial-adoption and shipped-tree rules as PARAGRAPH, keyed on its own
marker.
"""

import pathlib
import shutil
import sys
import tempfile

PARAGRAPH = (
    "**Security findings:** a finding is security-related if reading it would help an attacker — "
    "any OWASP Top 10:2025 category, and anything in a payment, tenant-isolation, or "
    "secret-handling path; on the edge, treat it as security. Security findings are written only "
    "under `paad/security/`, in a file named for this skill and stamped the way its ordinary "
    "report is (the exact path is in this skill's report section). Before the first write of a "
    "run, check that `paad` and `paad/security`, each where it exists, is a real directory and "
    "not a symlink (`test -d` and `test ! -L`); that `paad/security/.gitignore` exists, is a "
    "regular file, and contains the single line `*` — create it if absent, never rewrite it if "
    "present; and that `git ls-files paad/security` — no trailing slash, which would miss a "
    "tracked file or symlink — lists nothing. If any of these checks fails, if that file cannot "
    "be written, or if a later write there fails, write no security finding and no count line: "
    "tell the user what you found, ask whether to hold the findings or put them in the ordinary "
    "report, and say that in place of the Security block. Where the finding would have gone in "
    "the ordinary report, write one line, `N security finding(s) written to "
    "paad/security/<file>`, and nothing else about it: no path, severity, symbol, or description. "
    "Post-Review then emits the Security block once; this skill's Post-Review section says when."
)

BLOCK = """Security: N finding(s) in paad/security/<file> (new|updated).
paad/security/.gitignore keeps the directory out of git. Deleting that file or `git add -f` bypasses it.
Also list paad/security/ in your root .gitignore, or in .git/info/exclude to keep the rule local and unmentioned.
If anything under paad/security/ was ever committed, ignoring it now does not remove it from history.
paad/security/ is scratch, not state: it exists only on this machine, `git clean -x` deletes it, and nothing brings it back."""

SYMLINK = (
    "**Symlinked output paths:** the repository under review can commit a symlink where this "
    "skill writes, sending the write to a path it chose, possibly outside the repository. Before "
    "the first write of a run to a path under `paad/`, check that `paad` and every directory "
    "under it on the way to that path, each where it exists, is a real directory and not a "
    "symlink (`test -d` and `test ! -L`), and that the file, if it exists, is not a symlink "
    "(`test ! -L`); check each later file the same way before its first write. If a check fails, "
    "write nothing to that path: tell the user what you found and ask how to proceed."
)

PRODUCERS = {
    "agentic-owasp", "agentic-review", "test-roadmap",
    "agentic-architecture", "pushback", "agentic-dedup",
}
# Readers may name the path but carry no paragraph: they consume what producers wrote.
READERS = {"paad-help", "backlog", "fix-architecture"}
ALLOWED = PRODUCERS | READERS
# Every skill that writes under paad/. handoff writes handoff.md at the root and carries its own check.
WRITERS = PRODUCERS | {"agentic-a11y", "alignment", "backlog", "fix-architecture"}
MARKER = "**Security findings:**"
SYM_MARKER = "**Symlinked output paths:**"
PATH = "paad/security/"


def _normalize(text):
    return "\n".join(line.strip() for line in text.splitlines())


def _shipped_paragraph(skill_md, names=PRODUCERS, marker=MARKER, default=PARAGRAPH):
    """The paragraph line as the first skill in names that has one carries it."""
    for name in sorted(names):
        for line in skill_md.get(name, "").splitlines():
            if line.strip().startswith(marker):
                return line.strip()
    return default


def check(skills_dir, shipped=None):
    """Return None to skip the tree, else a list of problem strings."""
    skills_dir = pathlib.Path(skills_dir)
    if shipped is None:
        shipped = "plugins" in skills_dir.parts
    skill_md = {
        d.name: (d / "SKILL.md").read_text(encoding="utf-8")
        for d in sorted(skills_dir.iterdir())
        if (d / "SKILL.md").is_file()
    }
    # Gate on the path too: stripping the paragraph from every producer must fail,
    # not skip, while the tree still routes findings to paad/security/.
    adopted = any(MARKER in text or PATH in text for text in skill_md.values())

    problems = []
    if adopted:
        paragraph = _shipped_paragraph(skill_md) if shipped else PARAGRAPH
        for name in sorted(PRODUCERS):
            text = _normalize(skill_md.get(name, ""))
            if paragraph not in text:
                problems.append(f"{name}: the Security findings paragraph is missing or not verbatim")
            if _normalize(BLOCK) not in text:
                problems.append(f"{name}: the Post-Review Security block is missing or not verbatim")
    sym_adopted = any(SYM_MARKER in text for text in skill_md.values())
    if sym_adopted:
        sym = _shipped_paragraph(skill_md, WRITERS, SYM_MARKER, SYMLINK) if shipped else SYMLINK
        for name in sorted(WRITERS):
            if sym not in _normalize(skill_md.get(name, "")):
                problems.append(f"{name}: the Symlinked output paths paragraph is missing or not verbatim")
    for d in sorted(skills_dir.iterdir()):
        if d.name in ALLOWED or not d.is_dir():
            continue
        for md in sorted(d.rglob("*.md")):
            if PATH in md.read_text(encoding="utf-8"):
                problems.append(f"{md.relative_to(skills_dir)}: names {PATH} but {d.name} is not in the allowlist")
    if not adopted and not sym_adopted and not problems:
        return None
    return problems


def _write_skill(root, name, body):
    (root / name).mkdir()
    (root / name / "SKILL.md").write_text(body, encoding="utf-8")


def self_test():
    good = f"---\nname: x\n---\n\n{PARAGRAPH}\n\n{SYMLINK}\n\n## Post-Review\n\n   ```\n" + \
        "\n".join("   " + line for line in BLOCK.splitlines()) + "\n   ```\n"
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        _write_skill(root, "vibe", "---\nname: vibe\n---\nnothing here\n")
        assert check(root) is None, "tree without the marker must be skipped"

        _write_skill(root, "handoff", "---\nname: handoff\n---\nnothing here\n")
        (root / "handoff" / "references").mkdir()
        (root / "handoff" / "references" / "x.md").write_text("writes paad/security/handoff.md\n", encoding="utf-8")
        assert check(root) == ["handoff/references/x.md: names paad/security/ but handoff is not in the allowlist"], check(root)
        shutil.rmtree(root / "handoff")

        _write_skill(root, "backlog", "---\nname: backlog\n---\nreads paad/security/\n")
        assert not any("allowlist" in p for p in check(root)), check(root)

        for name in PRODUCERS:
            _write_skill(root, name, good)
        assert check(root) == [f"{n}: the Symlinked output paths paragraph is missing or not verbatim"
                               for n in sorted(WRITERS - PRODUCERS)], check(root)
        for name in WRITERS - PRODUCERS:
            (root / name).mkdir(exist_ok=True)
            (root / name / "SKILL.md").write_text(f"---\nname: {name}\n---\n\n{SYMLINK}\n", encoding="utf-8")
        assert check(root) == [], check(root)
        (root / "alignment" / "SKILL.md").write_text("---\nname: alignment\n---\n", encoding="utf-8")
        assert check(root) == ["alignment: the Symlinked output paths paragraph is missing or not verbatim"], check(root)
        (root / "alignment" / "SKILL.md").write_text(f"---\nname: alignment\n---\n\n{SYMLINK}\n", encoding="utf-8")

        (root / "pushback" / "SKILL.md").write_text(good.replace("(new|updated)", "(new)"), encoding="utf-8")
        assert any(p.startswith("pushback: the Post-Review") for p in check(root)), check(root)
        (root / "pushback" / "SKILL.md").write_text(good, encoding="utf-8")

        (root / "test-roadmap" / "SKILL.md").write_text(good.replace("secret-handling", "secret handling"), encoding="utf-8")
        assert any(p.startswith("test-roadmap: the Security findings paragraph") for p in check(root)), check(root)
        (root / "test-roadmap" / "SKILL.md").write_text(good, encoding="utf-8")

        # The shipped tree may carry a former paragraph, but all six copies must agree.
        former = good.replace("secret-handling", "secret handling")
        for name in PRODUCERS:
            (root / name / "SKILL.md").write_text(former, encoding="utf-8")
        assert check(root, shipped=True) == [], check(root, shipped=True)
        assert len(check(root)) == len(PRODUCERS), check(root)
        (root / "pushback" / "SKILL.md").write_text(good, encoding="utf-8")
        assert len(check(root, shipped=True)) == 1, check(root, shipped=True)
        for name in PRODUCERS:
            (root / name / "SKILL.md").write_text(good, encoding="utf-8")

        _write_skill(root, "handoff", "---\nname: handoff\n---\nwrites paad/security/handoff.md\n")
        assert check(root) == ["handoff/SKILL.md: names paad/security/ but handoff is not in the allowlist"], check(root)
        shutil.rmtree(root / "handoff")

        # Stripping the paragraph from every producer at once must fail, not skip:
        # the tree still names paad/security/, so it has adopted the feature.
        for name in PRODUCERS:
            stripped = good.replace(PARAGRAPH, "").replace(BLOCK.splitlines()[0], "")
            (root / name / "SKILL.md").write_text(stripped + "\nwrites paad/security/x.md\n", encoding="utf-8")
        result = check(root)
        assert result is not None and len(result) == 2 * len(PRODUCERS), result
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
        print(f"{tree}: SKIP check-security — no skill carries the Security findings paragraph or names paad/security/ (predates it).")
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
