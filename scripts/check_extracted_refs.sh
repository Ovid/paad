#!/usr/bin/env bash
# Verify each row in scripts/extracted-refs.tsv represents a correctly
# extracted reference: ref file exists, sentinel moved out of SKILL.md
# into the ref file, and SKILL.md dispatch references the ref path
# anchored next to a binding-instruction context.
set -euo pipefail

MANIFEST="scripts/extracted-refs.tsv"
SKILLS_ROOT="plugins/paad/skills"

if [ ! -f "$MANIFEST" ]; then
    echo "FAIL: manifest not found at $MANIFEST"
    exit 1
fi

fail=0
row=0
# `|| [ -n "$skill" ]` keeps the loop running on the final line of a
# manifest with no trailing newline (`read` returns nonzero on partial-
# line EOF).
# Column 4 (lens) is optional: empty for refs read directly by the
# orchestrator (e.g. report-template.md), non-empty for refs dispatched
# to a subagent that must echo `[ref-loaded:<lens>]` at the top of its
# output. When non-empty, this script enforces that SKILL.md's dispatch
# contains the literal `[ref-loaded:<lens>]` token — catching drift
# between the manifest's recorded lens and the orchestrator's actual
# dispatch instruction (which would silently break verifier routing).
while IFS=$'\t' read -r skill ref_path sentinel lens || [ -n "$skill" ]; do
    # strip stray CR from any field (Windows-edited TSVs)
    skill="${skill%$'\r'}"
    ref_path="${ref_path%$'\r'}"
    sentinel="${sentinel%$'\r'}"
    lens="${lens%$'\r'}"

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
    # Anchored dispatch-presence check: require the ref path AND the word
    # "binding" on the same line of SKILL.md. The skill's own conventions
    # in notes/convert-skills.md fix the dispatch wording to either
    # "treat its instructions as binding" (subagent dispatch) or
    # "instructions are binding" (parent self-read), both of which carry
    # the discriminator "binding" co-located with the ref path. A passing
    # mention without the binding context fails this check.
    if ! awk -v path="$ref_path" 'index($0, path) && /binding/ { found=1; exit } END { exit (found ? 0 : 1) }' "$skill_md"; then
        echo "FAIL [row $row, $skill]: ref path '$ref_path' is not co-located with a binding-instruction phrase in SKILL.md (must appear on a line that also contains 'binding')"
        fail=1
    fi
    if [ -n "$lens" ]; then
        token="[ref-loaded:$lens]"
        if ! grep -qF -- "$token" "$skill_md"; then
            echo "FAIL [row $row, $skill]: dispatch token '$token' not found in SKILL.md (lens column requires SKILL.md to contain the literal '[ref-loaded:<lens>]' token)"
            fail=1
        fi
    fi
done < "$MANIFEST"

if [ "$row" -eq 0 ]; then
    echo "FAIL: manifest contains zero data rows"
    exit 1
fi

if [ "$fail" -eq 1 ]; then
    exit 1
fi

echo "All $row extracted reference(s) verified."
