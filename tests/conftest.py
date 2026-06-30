"""Shared pytest fixtures and path helpers for the PAAD generator tests."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Make `scripts/` importable as a package-free module location so tests can
# `import skill_body` / `import convert_skills` regardless of cwd.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
