#!/usr/bin/env python3
"""Tests for KB-Brain deterministic tooling."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
import kb_brain  # noqa: E402


class KbBrainTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="kb-brain-test-"))
        self.root = self.tmp / "repo"
        self.root.mkdir()
        (self.root / "docs").mkdir()
        (self.root / "docs" / "architecture.md").write_text("# Stable architecture\n", encoding="utf-8")
        (self.root / "Makefile").write_text("help:\n\t@echo hi\n", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_cmd(self, *argv: str) -> int:
        return kb_brain.main(["--root", str(self.root), *argv])

    def test_init_creates_structure_idempotent_no_docs_ingest(self) -> None:
        self.assertEqual(self.run_cmd("init", "standard"), 0)
        kb = self.root / "kb-brain"
        for section in kb_brain.TOP_SECTIONS:
            self.assertTrue((kb / section).is_dir(), section)
        self.assertTrue((kb / "tech-debt" / "LEDGER.md").exists())
        self.assertTrue((kb / "work" / "ACTIVE.md").exists())
        self.assertTrue((kb / "templates" / "finding.md").exists())
        self.assertTrue((self.root / "scripts" / "kb_brain.py").exists())
        makefile = (self.root / "Makefile").read_text(encoding="utf-8")
        self.assertIn("kb-index:", makefile)

        # docs untouched / not ingested as records
        self.assertTrue((self.root / "docs" / "architecture.md").exists())
        self.assertFalse((kb / "architecture" / "architecture.md").exists())
        self.assertEqual(list((kb / "architecture").glob("*.md")), [])
        self.assertNotIn(
            "# Stable architecture",
            (kb / "README.md").read_text(encoding="utf-8"),
        )

        # idempotent
        self.assertEqual(self.run_cmd("init", "standard"), 0)
        self.assertEqual(makefile.count("kb-index:"), (self.root / "Makefile").read_text(encoding="utf-8").count("kb-index:"))

    def test_start_level_dirs_and_collision_safe_ids(self) -> None:
        self.run_cmd("init")
        self.assertEqual(self.run_cmd("start", "auth-migration"), 0)
        active = self.root / "kb-brain" / "work" / "active"
        workspaces = list(active.iterdir())
        self.assertEqual(len(workspaces), 1)
        ws = workspaces[0]
        self.assertTrue(ws.name.endswith("auth-migration"))
        for name in ("TASK.md", "INDEX.md", "CONTEXT.md", "ASSIGNMENTS.md", "PROMOTION.md"):
            self.assertTrue((ws / name).exists(), name)
        for dirname in ("findings", "questions", "decisions", "failures", "conflicts", "handoffs"):
            self.assertTrue((ws / dirname).is_dir(), dirname)
        self.assertFalse((ws / "assumptions").exists())

        self.assertEqual(self.run_cmd("start", "auth-migration", "strict"), 0)
        ids = sorted(p.name for p in active.iterdir())
        self.assertEqual(len(ids), 2)
        self.assertTrue(any(name.endswith("auth-migration-2") for name in ids))
        strict_ws = next(p for p in active.iterdir() if p.name.endswith("auth-migration-2"))
        self.assertTrue((strict_ws / "assumptions").is_dir())
        self.assertTrue((strict_ws / "dependencies").is_dir())
        self.assertTrue((strict_ws / "scope-changes").is_dir())

        active_md = (self.root / "kb-brain" / "work" / "ACTIVE.md").read_text(encoding="utf-8")
        self.assertIn("auth-migration", active_md)
        self.assertIn("Lead:", active_md)
        self.assertNotIn("## conflicts", active_md.lower())

    def test_refuse_lower_than_repo_default(self) -> None:
        self.run_cmd("init", "standard")
        self.assertEqual(self.run_cmd("start", "too-low", "minimal"), 2)

    def test_routing_unique_ids_and_check(self) -> None:
        self.run_cmd("init")
        self.run_cmd("start", "parser")
        task = next((self.root / "kb-brain" / "work" / "active").iterdir()).name
        self.assertEqual(
            self.run_cmd("new", "findings", "Import order bug", "--task", task),
            0,
        )
        self.assertEqual(
            self.run_cmd("new", "improvements", "Extract shared validator"),
            0,
        )
        self.assertEqual(
            self.run_cmd("new", "tech-debt", "Legacy parser dual path"),
            0,
        )
        findings = list((self.root / "kb-brain" / "work" / "active" / task / "findings").glob("F-*.md"))
        self.assertEqual(len(findings), 1)
        improvements = list((self.root / "kb-brain" / "improvements").glob("I-*.md"))
        self.assertEqual(len(improvements), 1)
        self.assertTrue((self.root / "kb-brain" / "tech-debt" / "LEDGER.md").exists())
        ledger = (self.root / "kb-brain" / "tech-debt" / "LEDGER.md").read_text(encoding="utf-8")
        self.assertIn("TD-001", ledger)
        self.assertEqual(self.run_cmd("check"), 0)

        # duplicate id detection
        dup = findings[0].parent / "F-001-duplicate.md"
        dup.write_text(findings[0].read_text(encoding="utf-8"), encoding="utf-8")
        self.assertEqual(self.run_cmd("check"), 1)

    def test_answered_question_without_owner(self) -> None:
        self.run_cmd("init")
        self.run_cmd("start", "qtest")
        task = next((self.root / "kb-brain" / "work" / "active").iterdir()).name
        self.run_cmd("new", "questions", "What is the timeout?", "--task", task)
        q = next((self.root / "kb-brain" / "work" / "active" / task / "questions").glob("Q-*.md"))
        text = q.read_text(encoding="utf-8")
        text = text.replace("status: open", "status: resolved")
        text = text.replace("owner: task-lead", "owner: ")
        # remove owner line value
        text = text.replace("\nowner: \n", "\n")
        if "owner:" in text:
            lines = []
            for line in text.splitlines():
                if line.startswith("owner:"):
                    continue
                lines.append(line)
            text = "\n".join(lines) + "\n"
        text = text.replace("Unanswered. Do not invent an answer.", "Forty-two.")
        q.write_text(text, encoding="utf-8")
        self.assertEqual(self.run_cmd("check"), 1)

    def test_close_seal_mutation_and_amend(self) -> None:
        self.run_cmd("init")
        self.run_cmd("start", "seal-me")
        task = next((self.root / "kb-brain" / "work" / "active").iterdir()).name
        self.run_cmd("new", "findings", "Observed flake", "--task", task)
        self.assertEqual(self.run_cmd("close", task), 0)
        closed = self.root / "kb-brain" / "work" / "closed" / task
        self.assertTrue((closed / "SEAL.json").exists())
        self.assertTrue((closed / "CLOSEOUT.md").exists())
        self.assertFalse((self.root / "kb-brain" / "work" / "active" / task).exists())
        seal = json.loads((closed / "SEAL.json").read_text(encoding="utf-8"))
        self.assertIn("files", seal)
        self.assertNotIn("SEAL.json", seal["files"])
        self.assertNotIn("INDEX.md", seal["files"])

        finding = next(closed.joinpath("findings").glob("F-*.md"))
        # mutation detected
        finding.write_text(finding.read_text(encoding="utf-8") + "\nTampered\n", encoding="utf-8")
        self.assertEqual(self.run_cmd("check"), 1)

        # restore from seal by rewriting original content is hard; re-close path —
        # instead amend after fixing: recreate clean closed workspace
        shutil.rmtree(self.root / "kb-brain")
        self.run_cmd("init")
        self.run_cmd("start", "seal-me")
        task = next((self.root / "kb-brain" / "work" / "active").iterdir()).name
        self.run_cmd("new", "findings", "Observed flake", "--task", task)
        self.run_cmd("close", task)
        closed = self.root / "kb-brain" / "work" / "closed" / task
        finding = next(closed.joinpath("findings").glob("F-*.md"))
        rel = finding.relative_to(closed).as_posix()
        self.assertEqual(self.run_cmd("amend", task, rel, "Clarify flake note"), 0)
        amend = list((closed / "amendments").glob("AM-*.md"))
        self.assertEqual(len(amend), 1)
        index = (closed / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("amended", index.lower())
        self.assertEqual(self.run_cmd("check"), 0)

        # rename sealed file
        finding.rename(finding.with_name("renamed.md"))
        self.assertEqual(self.run_cmd("check"), 1)

    def test_brief_preserves_brief_and_candidate_not_approved(self) -> None:
        self.run_cmd("init")
        self.assertEqual(self.run_cmd("brief-init", "checkout", "Checkout redesign"), 0)
        brief = self.root / "kb-brain" / "briefs" / "checkout" / "BRIEF.md"
        original = brief.read_text(encoding="utf-8")
        self.assertEqual(self.run_cmd("brief-milestone", "checkout", "Guest cart"), 0)
        self.assertEqual(self.run_cmd("brief-spec", "checkout", "M-001"), 0)
        self.assertEqual(brief.read_text(encoding="utf-8"), original)
        specs = list((self.root / "kb-brain" / "specs" / "checkout").glob("*-spec.md"))
        self.assertEqual(len(specs), 1)
        meta, body = kb_brain.parse_frontmatter(specs[0].read_text(encoding="utf-8"))
        self.assertEqual(meta.get("status"), "review-needed")
        self.assertIn("Unapproved candidate specification", body)
        self.assertNotEqual(meta.get("status"), "approved-spec")

        # milestone advanced only to review-needed
        m = next((self.root / "kb-brain" / "briefs" / "checkout" / "milestones").glob("M-001-*.md"))
        mmeta, _ = kb_brain.parse_frontmatter(m.read_text(encoding="utf-8"))
        self.assertEqual(mmeta.get("status"), "review-needed")

        index = (self.root / "kb-brain" / "briefs" / "checkout" / "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("M-001", index)
        self.assertIn("review-needed", index)


if __name__ == "__main__":
    unittest.main()
