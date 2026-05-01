#!/usr/bin/env bash
# Verify each row in scripts/extracted-refs.tsv represents a correctly
# extracted reference: ref file exists, sentinel moved out of SKILL.md
# into the ref file, and SKILL.md dispatch references the ref path.
set -euo pipefail

MANIFEST="scripts/extracted-refs.tsv"
SKILLS_ROOT="plugins/paad/skills"

if [ ! -f "$MANIFEST" ]; then
    echo "FAIL: manifest not found at $MANIFEST"
    exit 1
fi

fail=0
row=0
while IFS=$'\t' read -r skill ref_path sentinel; do
    # skip blanks and comments
    case "$skill" in
        ''|'#'*) continue ;;
    esac
    row=$((row + 1))
    skill_md="$SKILLS_ROOT/$skill/SKILL.md"
    ref_file="$SKILLS_ROOT/$skill/$ref_path"

    if [ ! -f "$skill_md" ]; then
        echo "FAIL [row $row, $skill]: SKILL.md not found at $skill_md"
        fail=1
        continue
    fi
    if [ ! -f "$ref_file" ]; then
        echo "FAIL [row $row, $skill]: ref file not found at $ref_file"
        fail=1
        continue
    fi
    if grep -qF -- "$sentinel" "$skill_md"; then
        echo "FAIL [row $row, $skill]: sentinel still present in SKILL.md ('$sentinel')"
        fail=1
    fi
    if ! grep -qF -- "$sentinel" "$ref_file"; then
        echo "FAIL [row $row, $skill]: sentinel missing from ref file ('$sentinel')"
        fail=1
    fi
    if ! grep -qF -- "$ref_path" "$skill_md"; then
        echo "FAIL [row $row, $skill]: ref path '$ref_path' not referenced anywhere in SKILL.md"
        fail=1
    fi
done < "$MANIFEST"

if [ "$fail" -eq 1 ]; then
    exit 1
fi

echo "All $row extracted reference(s) verified."
