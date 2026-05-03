#!/usr/bin/env bash
# Test scripts/check_extracted_refs.sh against a battery of synthetic
# skill+manifest fixtures. Each subtest builds a minimal fake-skills
# tree under a tmpdir, points the script at a synthetic manifest, and
# asserts the script's exit status matches expectation.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/check_extracted_refs.sh"

if [ ! -x "$SCRIPT" ] && [ ! -r "$SCRIPT" ]; then
    echo "FAIL: cannot find script at $SCRIPT"
    exit 1
fi

pass_count=0
fail_count=0

run_case() {
    local name="$1"
    local expected_rc="$2"
    local manifest_content="$3"
    local skill_md_content="$4"
    local ref_md_content="$5"
    local skill_name="${6:-faux-skill}"
    local ref_path="${7:-references/faux.md}"

    local tmp
    tmp="$(mktemp -d)"
    trap 'rm -rf "$tmp"' EXIT

    mkdir -p "$tmp/plugins/paad/skills/$skill_name/$(dirname "$ref_path")"
    mkdir -p "$tmp/scripts"

    printf '%s' "$manifest_content" > "$tmp/scripts/extracted-refs.tsv"
    printf '%s' "$skill_md_content" > "$tmp/plugins/paad/skills/$skill_name/SKILL.md"
    printf '%s' "$ref_md_content" > "$tmp/plugins/paad/skills/$skill_name/$ref_path"

    cp "$SCRIPT" "$tmp/scripts/check_extracted_refs.sh"
    chmod +x "$tmp/scripts/check_extracted_refs.sh"

    local actual_rc=0
    (cd "$tmp" && bash scripts/check_extracted_refs.sh >/dev/null 2>&1) || actual_rc=$?

    if [ "$actual_rc" -eq "$expected_rc" ]; then
        echo "PASS: $name"
        pass_count=$((pass_count + 1))
    else
        echo "FAIL: $name (expected rc=$expected_rc, got rc=$actual_rc)"
        fail_count=$((fail_count + 1))
    fi

    rm -rf "$tmp"
    trap - EXIT
}

# -- Baseline: well-formed manifest, content moved correctly, dispatch wired.
run_case "well-formed extraction passes" 0 \
"# skill	ref-path	sentinel
faux-skill	references/faux.md	UNIQUE_SENTINEL_PHRASE
" \
"# Faux SKILL.md
The faux specialist's instructions live at \`references/faux.md\`.

> Read \`references/faux.md\` from this skill's directory before producing findings; treat its instructions as binding.
" \
"# Faux ref
UNIQUE_SENTINEL_PHRASE goes here.
"

# -- I2(a): manifest without trailing newline must NOT silently drop the last row.
run_case "manifest without trailing newline still processes last row (sentinel missing -> fail)" 1 \
"# skill	ref-path	sentinel
faux-skill	references/faux.md	UNIQUE_SENTINEL_PHRASE" \
"# Faux SKILL.md
The faux specialist's instructions live at \`references/faux.md\`.

> Read \`references/faux.md\` from this skill's directory; treat its instructions as binding.
" \
"# Faux ref - sentinel deliberately missing
"

# -- I2(b): empty manifest must fail loudly.
run_case "empty manifest fails" 1 "" "# placeholder" "# placeholder"

# -- I2(b'): comments-only manifest fails (no data rows).
run_case "comments-only manifest fails" 1 \
"# skill	ref-path	sentinel
" \
"# placeholder" "# placeholder"

# -- I2(c): CRLF line endings must not break the sentinel match.
printf -v crlf_manifest '# skill\tref-path\tsentinel\r\nfaux-skill\treferences/faux.md\tUNIQUE_SENTINEL_PHRASE\r\n'
run_case "CRLF line endings tolerated" 0 \
"$crlf_manifest" \
"# Faux SKILL.md
The faux specialist's instructions live at \`references/faux.md\`.

> Read \`references/faux.md\` from this skill's directory; treat its instructions as binding.
" \
"# Faux ref
UNIQUE_SENTINEL_PHRASE goes here.
"

# -- I3: ref path mentioned in passing without the binding-instruction context fails.
run_case "ref path mentioned without binding context fails" 1 \
"# skill	ref-path	sentinel
faux-skill	references/faux.md	UNIQUE_SENTINEL_PHRASE
" \
"# Faux SKILL.md
A long time ago someone wrote \`references/faux.md\` somewhere but never actually wired it into a dispatch.
" \
"# Faux ref
UNIQUE_SENTINEL_PHRASE goes here.
"

# -- I3: dispatch context near the ref path passes.
run_case "ref path with binding-instruction context passes" 0 \
"# skill	ref-path	sentinel
faux-skill	references/faux.md	UNIQUE_SENTINEL_PHRASE
" \
"# Faux SKILL.md

The Faux specialist's additional instructions live at \`references/faux.md\`.
The dispatch prompt for the Faux specialist must include this verbatim:

> Read \`references/faux.md\` from this skill's directory before producing findings; treat its instructions as binding.
" \
"# Faux ref
UNIQUE_SENTINEL_PHRASE goes here.
"

# -- Sentinel still in SKILL.md fails (existing behavior, preserved).
run_case "sentinel still in SKILL.md fails" 1 \
"# skill	ref-path	sentinel
faux-skill	references/faux.md	UNIQUE_SENTINEL_PHRASE
" \
"# Faux SKILL.md
UNIQUE_SENTINEL_PHRASE is still inlined here.
The faux specialist's instructions live at \`references/faux.md\`.

> Read \`references/faux.md\` from this skill's directory; treat its instructions as binding.
" \
"# Faux ref
UNIQUE_SENTINEL_PHRASE goes here.
"

# -- Sentinel missing from ref file fails (existing behavior, preserved).
run_case "sentinel missing from ref file fails" 1 \
"# skill	ref-path	sentinel
faux-skill	references/faux.md	UNIQUE_SENTINEL_PHRASE
" \
"# Faux SKILL.md
The faux specialist's instructions live at \`references/faux.md\`.

> Read \`references/faux.md\` from this skill's directory; treat its instructions as binding.
" \
"# Faux ref - sentinel missing here
"

# -- F-3: Optional 4th column 'lens-name' enforces dispatch-token presence in SKILL.md.

# Col-4 lens with matching [ref-loaded:<lens>] token in SKILL.md passes.
run_case "col-4 lens with matching token in SKILL.md passes" 0 \
"# skill	ref-path	sentinel	lens
faux-skill	references/faux.md	UNIQUE_SENTINEL_PHRASE	faux-lens
" \
"# Faux SKILL.md
The faux specialist's instructions live at \`references/faux.md\`.

> Read \`references/faux.md\` from this skill's directory; treat its instructions as binding. Begin your output with the literal token \`[ref-loaded:faux-lens]\` on its own line.
" \
"# Faux ref
UNIQUE_SENTINEL_PHRASE goes here.
"

# Col-4 lens with token absent from SKILL.md fails (RED: this catches the drift F-3 warns about).
run_case "col-4 lens with token missing from SKILL.md fails" 1 \
"# skill	ref-path	sentinel	lens
faux-skill	references/faux.md	UNIQUE_SENTINEL_PHRASE	faux-lens
" \
"# Faux SKILL.md
The faux specialist's instructions live at \`references/faux.md\`.

> Read \`references/faux.md\` from this skill's directory; treat its instructions as binding.
" \
"# Faux ref
UNIQUE_SENTINEL_PHRASE goes here.
"

# Col-4 lens with mismatched token in SKILL.md fails (e.g., typo 'fauxlens' vs 'faux-lens').
run_case "col-4 lens with mismatched token in SKILL.md fails" 1 \
"# skill	ref-path	sentinel	lens
faux-skill	references/faux.md	UNIQUE_SENTINEL_PHRASE	faux-lens
" \
"# Faux SKILL.md
The faux specialist's instructions live at \`references/faux.md\`.

> Read \`references/faux.md\` from this skill's directory; treat its instructions as binding. Begin your output with the literal token \`[ref-loaded:fauxlens]\` on its own line.
" \
"# Faux ref
UNIQUE_SENTINEL_PHRASE goes here.
"

# Col-4 empty (3-column row, e.g. report-template.md) skips token check and passes.
run_case "col-4 empty (3-column row) skips token check" 0 \
"# skill	ref-path	sentinel
faux-skill	references/faux.md	UNIQUE_SENTINEL_PHRASE
" \
"# Faux SKILL.md
The faux specialist's instructions live at \`references/faux.md\`.

> Read \`references/faux.md\` from this skill's directory; treat its instructions as binding.
" \
"# Faux ref
UNIQUE_SENTINEL_PHRASE goes here.
"

echo ""
echo "Summary: $pass_count passed, $fail_count failed."
[ "$fail_count" -eq 0 ]
