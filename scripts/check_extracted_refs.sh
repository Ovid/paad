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
raw_lineno=0
# `|| [ -n "$raw_line" ]` keeps the loop running on the final line of a
# manifest with no trailing newline (`read` returns nonzero on partial-
# line EOF).
# Column 4 (lens) is optional: empty for refs read directly by the
# orchestrator (e.g. report-template.md), non-empty for refs dispatched
# to a subagent that must echo `[ref-loaded:<lens>]` at the top of its
# output. When non-empty, this script enforces that SKILL.md's dispatch
# contains the literal `[ref-loaded:<lens>]` token — catching drift
# between the manifest's recorded lens and the orchestrator's actual
# dispatch instruction (which would silently break verifier routing).
while IFS= read -r raw_line || [ -n "$raw_line" ]; do
    raw_lineno=$((raw_lineno + 1))
    # strip stray CR from end of raw line (Windows-edited TSVs)
    raw_line="${raw_line%$'\r'}"

    # skip blanks and comments early (before column-count guard so the
    # header row '# skill\tref-path\tsentinel\tlens' doesn't trip it)
    case "$raw_line" in
        ''|'#'*) continue ;;
    esac

    # Column-count guard. Manifest contract: exactly 3 columns
    # (skill, ref-path, sentinel) or 4 columns with optional lens.
    # An under-column row (1-2 cols) silently parses as fields-with-
    # empty-tail and produces "ref file not found at /SKILL.md"-shape
    # diagnostics that misdirect the user. An over-column row (5+)
    # silently drops the trailing data. Both are manifest authoring
    # bugs; surface them with a clear message anchored to the line
    # number rather than the data-row index.
    field_count=$(awk -F'\t' '{print NF}' <<<"$raw_line")
    if [ "$field_count" -lt 3 ] || [ "$field_count" -gt 4 ]; then
        echo "FAIL [line $raw_lineno]: manifest row has $field_count tab-separated columns; expected 3 or 4 (skill, ref-path, sentinel, [lens])"
        echo "  raw line: $raw_line"
        fail=1
        continue
    fi

    IFS=$'\t' read -r skill ref_path sentinel lens <<<"$raw_line"
    # strip stray CR from any field (Windows-edited TSVs, defensive)
    skill="${skill%$'\r'}"
    ref_path="${ref_path%$'\r'}"
    sentinel="${sentinel%$'\r'}"
    lens="${lens%$'\r'}"

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
unset raw_line

if [ "$row" -eq 0 ]; then
    echo "FAIL: manifest contains zero data rows"
    exit 1
fi

if [ "$fail" -eq 1 ]; then
    exit 1
fi

echo "All $row extracted reference(s) verified."
