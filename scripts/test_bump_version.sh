#!/usr/bin/env bash
# Test scripts/bump_version.py against synthetic plugin/marketplace/SKILL.md
# fixtures. Each subtest builds a minimal fake-repo tree under a tmpdir,
# runs the bumper, and asserts post-conditions on file contents and exit
# status.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/bump_version.py"

if [ ! -f "$SCRIPT" ]; then
    echo "FAIL: cannot find script at $SCRIPT"
    exit 1
fi

pass_count=0
fail_count=0

# Build a synthetic repo at $1 with plugin version $2 and given SKILL.md
# announce-line versions ($3, $4, ...). All SKILL.md filenames default to
# "foo" and "bar" — extend if you need more.
build_fixture() {
    local root="$1"
    local plugin_ver="$2"
    local foo_announce="${3:-$plugin_ver}"
    local bar_announce="${4:-$plugin_ver}"

    mkdir -p "$root/.claude-plugin"
    mkdir -p "$root/plugins/paad/.claude-plugin"
    mkdir -p "$root/plugins/paad/skills/foo"
    mkdir -p "$root/plugins/paad/skills/bar"

    cat > "$root/.claude-plugin/marketplace.json" <<EOF
{
  "name": "paad",
  "metadata": {
    "description": "fixture",
    "version": "$plugin_ver"
  },
  "plugins": [
    {
      "name": "paad",
      "source": "./plugins/paad",
      "version": "$plugin_ver"
    }
  ]
}
EOF

    cat > "$root/plugins/paad/.claude-plugin/plugin.json" <<EOF
{
  "name": "paad",
  "description": "fixture",
  "version": "$plugin_ver"
}
EOF

    cat > "$root/plugins/paad/skills/foo/SKILL.md" <<EOF
---
name: foo
description: fixture
---

**On invocation:** announce "Running paad:foo v$foo_announce" before anything else.
EOF

    cat > "$root/plugins/paad/skills/bar/SKILL.md" <<EOF
---
name: bar
description: fixture
---

**On invocation:** announce "Running paad:bar v$bar_announce" before anything else.
EOF
}

# Assert a file exists and contains a specific substring; print PASS/FAIL.
assert_contains() {
    local label="$1" file="$2" needle="$3"
    if [ ! -f "$file" ]; then
        echo "  FAIL [$label]: file not found: $file"
        return 1
    fi
    if grep -qF -- "$needle" "$file"; then
        return 0
    else
        echo "  FAIL [$label]: '$needle' not in $file"
        return 1
    fi
}

assert_not_contains() {
    local label="$1" file="$2" needle="$3"
    if [ ! -f "$file" ]; then
        echo "  FAIL [$label]: file not found: $file"
        return 1
    fi
    if grep -qF -- "$needle" "$file"; then
        echo "  FAIL [$label]: '$needle' should not be in $file"
        return 1
    fi
    return 0
}

run_subtest() {
    local name="$1"
    shift
    local sub_fail=0

    if "$@"; then
        :
    else
        sub_fail=1
    fi

    if [ "$sub_fail" -eq 0 ]; then
        echo "PASS: $name"
        pass_count=$((pass_count + 1))
    else
        echo "FAIL: $name"
        fail_count=$((fail_count + 1))
    fi
}

# Track all sandbox dirs for cleanup-on-exit even if a test aborts mid-way.
SANDBOXES=()
cleanup_sandboxes() {
    local d
    for d in "${SANDBOXES[@]:-}"; do
        if [ -n "$d" ] && [ -d "$d" ]; then
            rm -rf "$d"
        fi
    done
    return 0
}
trap cleanup_sandboxes EXIT

new_sandbox() {
    local d
    d="$(mktemp -d)"
    SANDBOXES+=("$d")
    printf '%s' "$d"
}

# -- Happy path: bump 1.0.0 -> 2.0.0 rewrites all five sites.
test_happy_path() {
    local tmp
    tmp="$(new_sandbox)"
    build_fixture "$tmp" "1.0.0"
    if ! (cd "$tmp" && python3 "$SCRIPT" 2.0.0 >/dev/null 2>&1); then
        echo "  FAIL: bumper exited nonzero"
        return 1
    fi
    local ok=0
    assert_contains "plugin.json"            "$tmp/plugins/paad/.claude-plugin/plugin.json"  '"version": "2.0.0"' || ok=1
    assert_not_contains "plugin.json (old)"  "$tmp/plugins/paad/.claude-plugin/plugin.json"  '"version": "1.0.0"' || ok=1
    assert_contains "marketplace metadata"   "$tmp/.claude-plugin/marketplace.json"          '"version": "2.0.0"' || ok=1
    assert_not_contains "marketplace (old)"  "$tmp/.claude-plugin/marketplace.json"          '"version": "1.0.0"' || ok=1
    assert_contains "foo SKILL.md"           "$tmp/plugins/paad/skills/foo/SKILL.md"         'Running paad:foo v2.0.0' || ok=1
    assert_contains "bar SKILL.md"           "$tmp/plugins/paad/skills/bar/SKILL.md"         'Running paad:bar v2.0.0' || ok=1
    return $ok
}
run_subtest "happy path: bump rewrites plugin.json + marketplace metadata + plugins[0] + every SKILL.md" test_happy_path

# -- Idempotent: bumping to the current version exits 0 with no changes.
test_idempotent() {
    local tmp
    tmp="$(new_sandbox)"
    build_fixture "$tmp" "1.5.0"
    if ! (cd "$tmp" && python3 "$SCRIPT" 1.5.0 >/dev/null 2>&1); then
        echo "  FAIL: idempotent bump exited nonzero"
        return 1
    fi
    return 0
}
run_subtest "idempotent: bump to current version is a clean no-op" test_idempotent

# -- Invalid version grammar: rejected before any mutation.
test_invalid_grammar() {
    local tmp
    tmp="$(new_sandbox)"
    build_fixture "$tmp" "1.0.0"
    if (cd "$tmp" && python3 "$SCRIPT" "not-a-version" >/dev/null 2>&1); then
        echo "  FAIL: bumper accepted invalid version"
        return 1
    fi
    # Verify no mutation occurred.
    assert_contains "plugin.json untouched" "$tmp/plugins/paad/.claude-plugin/plugin.json" '"version": "1.0.0"' || return 1
    return 0
}
run_subtest "invalid version grammar: rejected, no mutation" test_invalid_grammar

# -- F-6 guard: SKILL.md announce-line divergence (smart-quote contamination,
# hand-edit drift, etc.) is detected pre-flight, preventing partial mutation.
test_skill_md_divergence() {
    local tmp
    tmp="$(new_sandbox)"
    # foo's announce line says v1.0.0, bar's says v9.9.9 (divergent).
    build_fixture "$tmp" "1.0.0" "1.0.0" "9.9.9"
    if (cd "$tmp" && python3 "$SCRIPT" 2.0.0 >/dev/null 2>&1); then
        echo "  FAIL: bumper succeeded despite SKILL.md divergence"
        return 1
    fi
    # Pre-flight failure must mean no file was mutated.
    assert_contains "plugin.json untouched"  "$tmp/plugins/paad/.claude-plugin/plugin.json"  '"version": "1.0.0"' || return 1
    assert_contains "foo SKILL.md untouched" "$tmp/plugins/paad/skills/foo/SKILL.md"         'Running paad:foo v1.0.0' || return 1
    assert_contains "bar SKILL.md untouched" "$tmp/plugins/paad/skills/bar/SKILL.md"         'Running paad:bar v9.9.9' || return 1
    return 0
}
run_subtest "F-6: SKILL.md divergence detected pre-flight, no partial mutation" test_skill_md_divergence

# -- Missing argument: usage error.
test_missing_arg() {
    local tmp
    tmp="$(new_sandbox)"
    build_fixture "$tmp" "1.0.0"
    if (cd "$tmp" && python3 "$SCRIPT" >/dev/null 2>&1); then
        echo "  FAIL: bumper accepted missing version arg"
        return 1
    fi
    return 0
}
run_subtest "missing version argument: usage error" test_missing_arg

echo ""
echo "Summary: $pass_count passed, $fail_count failed."
[ "$fail_count" -eq 0 ]
