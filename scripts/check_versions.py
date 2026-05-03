#!/usr/bin/env python3
"""Verify that marketplace.json (metadata + every plugin entry) and
plugin.json all carry the same version literal.

Walks every entry in marketplace.json's plugins[] array, not just
plugins[0], so a future second-plugin marketplace can't drift silently.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

MARKETPLACE_PATH = Path(".claude-plugin/marketplace.json")
PLUGIN_PATH = Path("plugins/paad/.claude-plugin/plugin.json")


def fail(msg: str) -> "None":
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    if not PLUGIN_PATH.exists():
        fail(f"plugin.json not found at {PLUGIN_PATH}")
    if not MARKETPLACE_PATH.exists():
        fail(f"marketplace.json not found at {MARKETPLACE_PATH}")

    try:
        plugin_data = json.loads(PLUGIN_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"plugin.json is not valid JSON: {exc}")
    try:
        marketplace_data = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"marketplace.json is not valid JSON: {exc}")

    plugin_ver = plugin_data.get("version")
    if not plugin_ver:
        fail("plugin.json has no 'version' field")

    meta_ver = marketplace_data.get("metadata", {}).get("version")
    if not meta_ver:
        fail("marketplace.json has no metadata.version field")

    plugin_entries = marketplace_data.get("plugins") or []
    if not plugin_entries:
        fail("marketplace.json has no plugins[] entries")

    mismatches: list[str] = []
    if meta_ver != plugin_ver:
        mismatches.append(
            f"marketplace.metadata.version ({meta_ver}) != plugin.json ({plugin_ver})"
        )
    for i, p in enumerate(plugin_entries):
        entry_ver = p.get("version", "<missing>")
        if entry_ver != plugin_ver:
            mismatches.append(
                f"marketplace.plugins[{i}].version ({entry_ver}) != plugin.json ({plugin_ver})"
            )

    if mismatches:
        print("FAIL: Version mismatch", file=sys.stderr)
        for m in mismatches:
            print(f"  {m}", file=sys.stderr)
        return 1

    print(
        f"Versions match: {plugin_ver} "
        f"(metadata + {len(plugin_entries)} plugin entry/entries + plugin.json)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
