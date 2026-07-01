"""Shared body-cleaning core for the PAAD skill generators.

This module owns the *single* definition of WHICH sections are kept or dropped
when a `plugins/paad/skills/<name>/SKILL.md` is transformed into a copy-source
skill. Two generators consume it:

  * `convert_skills.py`      -> the legacy Kiro/Antigravity tree (strips
                                cross-skill `/paad:` references entirely).
  * `build-kiro-power.py`    -> the Kiro power (written in a later task; will
                                rewrite `/paad:` references to `#<name>` instead
                                of stripping them).

Both share the section-splitting, section-exclusion, path-neutralization, and
whitespace-collapsing behavior so the two generators can never disagree about
which sections survive. The only intended difference is the per-section
`/paad:` handling, which is injected via `paad_ref_transform`.

`clean_body()` is intentionally pure (string in -> string out, no file I/O) so
it is directly unit-testable.
"""

import re

# Single source of truth for the section headers that are dropped from every
# generated skill. Both generators import this; do NOT copy-paste the names.
EXCLUDED_SECTIONS = [
    "Arguments",
    "Input Resolution",
    "Pre-flight Checks",
    "Document classification",
]

# Single source of truth for the skills excluded from BOTH generators. `help`
# becomes POWER.md's index (and the legacy tree's, via convert_skills.py);
# `makefile` is intentionally omitted to keep the two generators' skill sets
# byte-for-byte identical. Both generators and the golden-output test import
# this; do NOT copy-paste the names — the design REQUIRES the two generators'
# skill sets stay identical, and a duplicated literal has no parity guard.
SKIP_NAMES = frozenset({"help", "makefile"})


def neutralize_paad_paths(body):
    """Rewrite `paad/...` output paths to neutral `.reviews/...` paths.

    Shared by both generators: the copy-source skills must not reference the
    plugin's own `paad/` review directories. NOTE: this is NOT a seam — path
    neutralization is fixed and identical for both generators. Only
    `paad_ref_transform` (the `/paad:` handling) is meant to vary between them.
    """
    body = body.replace("paad/architecture-reviews/", ".reviews/architecture/")
    body = body.replace("paad/code-reviews/", ".reviews/code/")
    body = body.replace("paad/pushback-reviews/", ".reviews/pushback/")
    body = body.replace("paad/alignment-reviews/", ".reviews/alignment/")
    body = body.replace("paad/", ".reviews/")
    return body


def strip_paad_references(body):
    """Legacy `/paad:` handling: drop whole lines, then any stray mentions.

    This is the default `paad_ref_transform` and reproduces `convert_skills.py`
    exactly. The power generator will supply a different transform that rewrites
    `/paad:<name>` to `#<name>` instead of removing it.
    """
    # Remove entire lines containing /paad: (usually follow-up suggestions or
    # command examples).
    body = re.sub(r'^.*\/paad:[a-z0-9-]+.*$', '', body, flags=re.MULTILINE)
    # Additional cleanup for any remaining /paad: mentions just in case.
    body = re.sub(r'\(?/paad:[a-z0-9-]+\)?', '', body)
    return body


def clean_body(content, excluded_sections=None,
               paad_ref_transform=strip_paad_references):
    """Transform a raw SKILL.md `content` string into a cleaned skill body.

    `excluded_sections` defaults to the module-level `EXCLUDED_SECTIONS` via a
    None sentinel (avoids the mutable-default-argument pitfall).

    The pipeline is:
      1. Split into sections by `##`+ headers.
      2. Drop sections whose header matches any `excluded_sections` entry.
      3. For each kept section: neutralize `paad/` paths, apply
         `paad_ref_transform` to its `/paad:` references, and trim trailing
         whitespace.
      4. Collapse runs of 3+ newlines and ensure a single trailing newline.

    Steps 1-2 (which sections survive) are shared and fixed across generators;
    only `paad_ref_transform` is meant to vary.
    """
    if excluded_sections is None:
        excluded_sections = EXCLUDED_SECTIONS

    # Split into sections by headers (##). The capturing group keeps each
    # header line as its own element so we can re-pair headers with bodies.
    parts = re.split(r'\n(##+ .*)', content)

    # parts[0] is everything before the first ##.
    cleaned_content = parts[0]

    # Process header/body pairs.
    for i in range(1, len(parts), 2):
        header_line = parts[i]
        body = parts[i + 1]

        header_text = re.sub(r'^##+\s*', '', header_line).strip()

        # Skip unwanted sections.
        if any(uh in header_text for uh in excluded_sections):
            continue

        # Neutralize "paad/" paths to ".reviews/".
        body = neutralize_paad_paths(body)

        # Apply the generator-specific /paad: reference handling.
        body = paad_ref_transform(body)

        # Clean up trailing whitespace and excessive newlines.
        body = body.rstrip() + "\n"

        cleaned_content += "\n" + header_line + body

    # Final cleanup for consecutive empty lines.
    cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content).strip() + "\n"

    return cleaned_content
