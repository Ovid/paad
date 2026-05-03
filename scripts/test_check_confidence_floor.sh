#!/usr/bin/env bash
# Test scripts/check_confidence_floor.py against synthetic SKILL.md/refs
# trees containing consistent vs. inconsistent floor literals.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/check_confidence_floor.py"

if [ ! -f "$SCRIPT" ]; then
    echo "FAIL: cannot find script at $SCRIPT"
    exit 1
fi

pass_count=0
fail_count=0

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

run_subtest() {
    local name="$1"
    shift
    if "$@"; then
        echo "PASS: $name"
        pass_count=$((pass_count + 1))
    else
        echo "FAIL: $name"
        fail_count=$((fail_count + 1))
    fi
}

# -- Consistent: every site uses the same floor literal -> exit 0.
test_consistent() {
    local tmp; tmp="$(new_sandbox)"
    mkdir -p "$tmp/foo/references"
    cat > "$tmp/foo/SKILL.md" <<'EOF'
Specialist instruction: Only report findings with confidence >= 60.
EOF
    cat > "$tmp/foo/references/verifier.md" <<'EOF'
Drop findings below 60% confidence.
EOF
    cat > "$tmp/foo/references/spec.md" <<'EOF'
If you cannot articulate all three, drop the finding — confidence is below 60 by definition.
EOF
    if ! python3 "$SCRIPT" "$tmp" >/dev/null 2>&1; then
        echo "  FAIL: consistent state should pass"
        return 1
    fi
    return 0
}
run_subtest "consistent floor across sites passes" test_consistent

# -- Inconsistent: one site uses 70, others use 60 -> exit 1.
test_inconsistent() {
    local tmp; tmp="$(new_sandbox)"
    mkdir -p "$tmp/foo/references"
    cat > "$tmp/foo/SKILL.md" <<'EOF'
Specialist instruction: Only report findings with confidence >= 60.
EOF
    cat > "$tmp/foo/references/verifier.md" <<'EOF'
Drop findings below 70% confidence.
EOF
    if python3 "$SCRIPT" "$tmp" >/dev/null 2>&1; then
        echo "  FAIL: inconsistent floor (60 vs 70) should fail"
        return 1
    fi
    return 0
}
run_subtest "inconsistent floor (60 vs 70) fails" test_inconsistent

# -- Zero sites matched: patterns may have rotted away or all sites removed -> exit 1.
test_no_matches() {
    local tmp; tmp="$(new_sandbox)"
    mkdir -p "$tmp/foo"
    cat > "$tmp/foo/SKILL.md" <<'EOF'
This file talks about nothing related to confidence floors at all.
EOF
    if python3 "$SCRIPT" "$tmp" >/dev/null 2>&1; then
        echo "  FAIL: zero-match scan should fail"
        return 1
    fi
    return 0
}
run_subtest "zero-match scan fails (guards against silent pattern rot)" test_no_matches

# -- Cap-confidence variant: 'Cap confidence at 60' must match the same floor.
test_cap_phrasing() {
    local tmp; tmp="$(new_sandbox)"
    mkdir -p "$tmp/foo"
    cat > "$tmp/foo/SKILL.md" <<'EOF'
Only report findings with confidence >= 60.
- Cap confidence at 60 when the bug requires a precondition.
EOF
    if ! python3 "$SCRIPT" "$tmp" >/dev/null 2>&1; then
        echo "  FAIL: cap-confidence at 60 should match floor 60"
        return 1
    fi
    return 0
}
run_subtest "cap-confidence phrasing recognized" test_cap_phrasing

# -- Cap-confidence drift: cap value differs from floor.
test_cap_drift() {
    local tmp; tmp="$(new_sandbox)"
    mkdir -p "$tmp/foo"
    cat > "$tmp/foo/SKILL.md" <<'EOF'
Only report findings with confidence >= 60.
- Cap confidence at 70 when the bug requires a precondition.
EOF
    if python3 "$SCRIPT" "$tmp" >/dev/null 2>&1; then
        echo "  FAIL: cap (70) drifting from floor (60) should fail"
        return 1
    fi
    return 0
}
run_subtest "cap-confidence drift detected" test_cap_drift

# -- S18 strict: all patterns matched -> --strict passes.
test_strict_all_patterns_matched() {
    local tmp; tmp="$(new_sandbox)"
    mkdir -p "$tmp/foo"
    cat > "$tmp/foo/SKILL.md" <<'EOF'
Only report findings with confidence >= 60.
Drop findings below 60 confidence.
- Cap confidence at 60 when the bug requires a precondition.
We refuse below 60% confidence overall, and confidence is below 60 means dropped.
EOF
    if ! python3 "$SCRIPT" --strict "$tmp" >/dev/null 2>&1; then
        echo "  FAIL: --strict with all 5 patterns matched should pass"
        return 1
    fi
    return 0
}
run_subtest "--strict passes when every FLOOR_PATTERN matches at least once" test_strict_all_patterns_matched

# -- S18 strict: only some patterns match -> --strict fails (catches pattern rot).
test_strict_partial_pattern_rot() {
    local tmp; tmp="$(new_sandbox)"
    mkdir -p "$tmp/foo"
    cat > "$tmp/foo/SKILL.md" <<'EOF'
Only report findings with confidence >= 60.
EOF
    if python3 "$SCRIPT" --strict "$tmp" >/dev/null 2>&1; then
        echo "  FAIL: --strict with only 1/5 patterns matched should fail"
        return 1
    fi
    # Sanity: same scan without --strict still passes (subset is OK by default).
    if ! python3 "$SCRIPT" "$tmp" >/dev/null 2>&1; then
        echo "  FAIL: non-strict with 1 matching pattern should pass"
        return 1
    fi
    return 0
}
run_subtest "--strict fails on partial pattern rot; default-mode tolerates subset" test_strict_partial_pattern_rot

# -- S9 read failure: unreadable file under scan root produces a clean fail (not a stack trace).
test_unreadable_file_fails_cleanly() {
    local tmp; tmp="$(new_sandbox)"
    mkdir -p "$tmp/foo"
    cat > "$tmp/foo/SKILL.md" <<'EOF'
Only report findings with confidence >= 60.
EOF
    cat > "$tmp/foo/unreadable.md" <<'EOF'
placeholder
EOF
    chmod 000 "$tmp/foo/unreadable.md"
    local rc=0
    local output
    output="$(python3 "$SCRIPT" "$tmp" 2>&1)" || rc=$?
    chmod 644 "$tmp/foo/unreadable.md"  # restore so cleanup can rm
    if [ "$rc" -eq 0 ]; then
        echo "  FAIL: unreadable file should produce non-zero exit"
        return 1
    fi
    if ! grep -q "FAIL: cannot read" <<<"$output"; then
        echo "  FAIL: expected 'FAIL: cannot read' diagnostic, got: $output"
        return 1
    fi
    return 0
}
# Skip on root (chmod 000 doesn't block root reads).
if [ "$(id -u)" -ne 0 ]; then
    run_subtest "unreadable file produces clean FAIL not stack trace" test_unreadable_file_fails_cleanly
fi

echo ""
echo "Summary: $pass_count passed, $fail_count failed."
[ "$fail_count" -eq 0 ]
