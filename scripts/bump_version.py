#!/usr/bin/env python3
"""Bump the paad plugin version across plugin.json, marketplace.json, and
every plugins/paad/skills/*/SKILL.md announce line.

Usage: python3 scripts/bump_version.py X.Y.Z

Discipline:
- Validates X.Y.Z grammar before touching anything.
- Refuses to run if the three current version sources disagree (plugin.json,
  marketplace.metadata.version, marketplace.plugins[i].version). Run
  `make check-versions` to diagnose.
- No-ops cleanly if the target version already matches the current.
- Pre-flight checks every SKILL.md for the expected announce-line BEFORE
  mutating anything. A divergent SKILL.md aborts the run with no partial
  state.
- Re-reads every file post-mutation and verifies the new version is
  present in the right places.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
MARKETPLACE_PATH = Path(".claude-plugin/marketplace.json")
PLUGIN_PATH = Path("plugins/paad/.claude-plugin/plugin.json")
SKILLS_DIR = Path("plugins/paad/skills")


def fail(msg: str) -> "None":
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: bump_version.py X.Y.Z", file=sys.stderr)
        return 1
    new_ver = argv[1]
    if not VERSION_RE.match(new_ver):
        fail(f"VERSION must be in X.Y.Z form (got {new_ver!r})")

    if not PLUGIN_PATH.exists():
        fail(f"plugin.json not found at {PLUGIN_PATH}")
    if not MARKETPLACE_PATH.exists():
        fail(f"marketplace.json not found at {MARKETPLACE_PATH}")

    try:
        plugin_data = json.loads(PLUGIN_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"plugin.json is not valid JSON: {exc}")
    except (OSError, UnicodeDecodeError) as exc:
        fail(f"cannot read plugin.json: {exc}")
    try:
        marketplace_data = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"marketplace.json is not valid JSON: {exc}")
    except (OSError, UnicodeDecodeError) as exc:
        fail(f"cannot read marketplace.json: {exc}")

    plugin_ver = plugin_data.get("version")
    marketplace_meta_ver = marketplace_data.get("metadata", {}).get("version")
    marketplace_plugins = marketplace_data.get("plugins") or []

    if not plugin_ver:
        fail("plugin.json has no 'version' field")
    if not marketplace_meta_ver:
        fail("marketplace.json has no metadata.version field")
    if not marketplace_plugins:
        fail("marketplace.json has no plugins[] entries")

    # Bumper assumes single-source-of-version marketplace: every plugin entry
    # in marketplace.json shares one version (which equals plugin.json's).
    # Multi-version marketplaces need a different bumper design.
    versions: dict[str, str] = {
        "plugin.json": plugin_ver,
        "marketplace.metadata.version": marketplace_meta_ver,
    }
    for i, p in enumerate(marketplace_plugins):
        versions[f"marketplace.plugins[{i}].version"] = p.get("version", "<missing>")
    if len(set(versions.values())) > 1:
        details = ", ".join(f"{k}={v}" for k, v in versions.items())
        fail(
            "version sources disagree before bump: "
            f"{details}. Run 'make check-versions' first."
        )

    old_ver = plugin_ver

    if old_ver == new_ver:
        print(f"Already at {new_ver}. Nothing to do.")
        return 0

    # --- Pre-flight: every SKILL.md must contain the expected announce-line.
    skill_files: list[tuple[str, Path]] = []
    if SKILLS_DIR.is_dir():
        for skill_dir in sorted(SKILLS_DIR.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if skill_md.is_file():
                skill_files.append((skill_dir.name, skill_md))

    if not skill_files:
        fail(f"no SKILL.md files found under {SKILLS_DIR}")

    pre_flight_errors: list[str] = []
    for name, path in skill_files:
        expected_old = f'Running paad:{name} v{old_ver}"'
        if expected_old not in path.read_text():
            pre_flight_errors.append(
                f"{path}: missing announce-line literal '{expected_old}'"
            )
    if pre_flight_errors:
        for err in pre_flight_errors:
            print(f"FAIL: {err}", file=sys.stderr)
        fail(
            "pre-flight: one or more files lack the expected old-version "
            "literal — refusing to mutate"
        )

    # --- Mutate. JSON files: targeted text-replace anchored on the literal
    # `"version": "<old>"` field. Both marketplace fields hold the same
    # value (validated above), so a global replace updates both. Counting
    # occurrences first guards against unrelated `"version": "X.Y.Z"`
    # strings appearing inside descriptions or other text.
    print(f"Bumping {old_ver} -> {new_ver}...")
    old_lit = f'"version": "{old_ver}"'
    new_lit = f'"version": "{new_ver}"'

    plugin_text = PLUGIN_PATH.read_text()
    plugin_count = plugin_text.count(old_lit)
    if plugin_count != 1:
        fail(
            f"plugin.json: expected exactly 1 occurrence of {old_lit}, "
            f"found {plugin_count}"
        )
    PLUGIN_PATH.write_text(plugin_text.replace(old_lit, new_lit))

    expected_marketplace_count = 1 + len(marketplace_plugins)  # metadata + each plugin
    marketplace_text = MARKETPLACE_PATH.read_text()
    actual_marketplace_count = marketplace_text.count(old_lit)
    if actual_marketplace_count != expected_marketplace_count:
        fail(
            f"marketplace.json: expected {expected_marketplace_count} occurrences "
            f"of {old_lit} (metadata + {len(marketplace_plugins)} plugin entry/entries), "
            f"found {actual_marketplace_count}"
        )
    MARKETPLACE_PATH.write_text(marketplace_text.replace(old_lit, new_lit))

    for name, path in skill_files:
        old_announce = f'Running paad:{name} v{old_ver}"'
        new_announce = f'Running paad:{name} v{new_ver}"'
        text = path.read_text()
        new_text = text.replace(old_announce, new_announce)
        if new_text == text:
            # Should be impossible given pre-flight, but fail defensively.
            fail(
                f"{path}: pre-flight passed but replace was a no-op "
                "(filesystem race?)"
            )
        path.write_text(new_text)

    # --- Post-condition: re-read everything and verify the new version
    # landed in the expected places.
    post_errors: list[str] = []
    plugin2 = json.loads(PLUGIN_PATH.read_text())
    if plugin2.get("version") != new_ver:
        post_errors.append(
            f"plugin.json version is {plugin2.get('version')!r} after mutation, "
            f"expected {new_ver!r}"
        )
    marketplace2 = json.loads(MARKETPLACE_PATH.read_text())
    if marketplace2.get("metadata", {}).get("version") != new_ver:
        post_errors.append(
            "marketplace.metadata.version is "
            f"{marketplace2.get('metadata', {}).get('version')!r} after mutation, "
            f"expected {new_ver!r}"
        )
    for i, p in enumerate(marketplace2.get("plugins", [])):
        if p.get("version") != new_ver:
            post_errors.append(
                f"marketplace.plugins[{i}].version is {p.get('version')!r} after "
                f"mutation, expected {new_ver!r}"
            )
    for name, path in skill_files:
        expected_new = f'Running paad:{name} v{new_ver}"'
        if expected_new not in path.read_text():
            post_errors.append(
                f"{path}: missing announce-line literal '{expected_new}' "
                "after mutation"
            )
    if post_errors:
        for err in post_errors:
            print(f"FAIL: {err}", file=sys.stderr)
        fail("post-condition check failed — bumper left files in inconsistent state")

    print(f"Bumped to {new_ver}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
