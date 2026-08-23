# Every per-skill check runs against a tree, and there are two: preview/paad holds
# work that has merged but not shipped, plugins/paad is what ships. TREE picks one.
# Preview's plugin.json carries the -preview suffix, so the checks that read a
# version out of it need no literal — the suffix falls out of the tree they are on.
TREE ?= plugins/paad
SKILLS_DIR := $(TREE)/skills
SKILL_DIRS := $(wildcard $(SKILLS_DIR)/*)
SKILL_NAMES := $(notdir $(SKILL_DIRS))

.PHONY: help test tree-checks validate require-export check-skill-names check-versions check-skill-versions check-digraphs check-help check-readme check-frontmatter check-references check-dispatch-sites check-announce check-export-frontmatter check-export-commands check-export-current check-export-dryrun check-trees bump-version bump-tree promote export release tag

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-22s %s\n", $$1, $$2}'

self-tests: ## Run the hand-written parsers' own assertions
# These are the only executable specification the frontmatter mutators have, and
# they cost milliseconds. Left uncalled, they caught nothing: promote.py and
# check_internal_flag.py drifted apart on where a metadata block ends, which is
# exactly the class one added case would have caught.
	@python3 scripts/check_internal_flag.py --self-test
	@python3 scripts/promote.py --self-test
	@python3 scripts/lint_digraphs.py --self-test

test: self-tests check-versions check-trees validate check-readme check-export-frontmatter check-export-commands check-export-current ## Run all checks
	@$(MAKE) --no-print-directory tree-checks TREE=plugins/paad
	@$(MAKE) --no-print-directory tree-checks TREE=preview/paad
	@echo "All checks passed."

# The per-skill checks, run once per tree. README documents the shipped set only,
# so check-readme stays out: a preview-only skill is tolerated there, not required.
tree-checks: check-skill-names check-skill-versions check-digraphs check-help check-frontmatter check-references check-dispatch-sites check-announce check-export-dryrun ## Run the per-tree checks (usage: make tree-checks TREE=preview/paad)
	@echo "$(TREE): tree checks passed."

validate: ## Validate marketplace and all plugins
	@claude plugin validate .
	@for dir in plugins/*/ preview/*/; do \
		echo "Validating $$dir..."; \
		claude plugin validate "$$dir" || exit 1; \
	done

check-versions: ## Check package and plugin versions match
	@package_ver=$$(python3 -c "import json; print(json.load(open('package.json'))['version'])"); \
	marketplace_ver=$$(python3 -c "import json; print(json.load(open('.claude-plugin/marketplace.json'))['plugins'][0]['version'])"); \
	plugin_ver=$$(python3 -c "import json; print(json.load(open('plugins/paad/.claude-plugin/plugin.json'))['version'])"); \
	preview_ver=$$(python3 -c "import json; print(json.load(open('preview/paad/.claude-plugin/plugin.json'))['version'])"); \
	if [ "$$package_ver" != "$$marketplace_ver" ] || [ "$$package_ver" != "$$plugin_ver" ]; then \
		echo "FAIL: Version mismatch — package.json ($$package_ver), marketplace.json ($$marketplace_ver), plugin.json ($$plugin_ver)"; \
		exit 1; \
	fi; \
	if [ "$$preview_ver" != "$$plugin_ver-preview" ]; then \
		echo "FAIL: preview/paad is at $$preview_ver, expected $$plugin_ver-preview."; \
		echo "      The suffix is how a transcript says which tree just ran, and 'make bump-version'"; \
		echo "      writes both. A bare version here means preview would announce as the shipped tree."; \
		exit 1; \
	fi; \
	echo "Versions match: $$package_ver (preview: $$preview_ver)"

check-skill-versions: check-skill-names ## Check every SKILL.md announces the correct version
	@plugin_ver=$$(python3 -c "import json; print(json.load(open('$(TREE)/.claude-plugin/plugin.json'))['version'])"); \
	fail=0; \
	for dir in $(SKILL_DIRS); do \
		name=$$(basename "$$dir"); \
		file="$$dir/SKILL.md"; \
		if ! grep -qF "Running paad:$$name v$$plugin_ver\"" "$$file" 2>/dev/null; then \
			echo "FAIL: $$name is missing or has wrong version announcement (expected v$$plugin_ver)"; \
			fail=1; \
		fi; \
	done; \
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "$(TREE): all skills announce v$$plugin_ver."

bump-version: ## Bump version across package and plugin manifests and all SKILL.md (usage: make bump-version VERSION=X.Y.Z)
	@if [ -z "$(VERSION)" ]; then \
		echo "Usage: make bump-version VERSION=X.Y.Z"; \
		exit 1; \
	fi
# A shell glob is not a version test: [0-9]*.[0-9]*.[0-9]* also admits 1.2.3.4,
# 1.31.0-rc1 and 1x.2y.3z, and this target rewrites every manifest in the repo.
	@echo "$(VERSION)" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$$' || { \
		echo "FAIL: VERSION must be in X.Y.Z form (got $(VERSION))"; exit 1; }
	@sed -i.bak 's|^  "version": "[^"]*"|  "version": "$(VERSION)"|' package.json && rm -f package.json.bak
	@sed -i.bak 's|^      "version": "[^"]*"|      "version": "$(VERSION)"|' .claude-plugin/marketplace.json && rm -f .claude-plugin/marketplace.json.bak
	@$(MAKE) --no-print-directory bump-tree TREE=plugins/paad
	@$(MAKE) --no-print-directory bump-tree TREE=preview/paad SUFFIX=-preview
	@echo "Bumped to $(VERSION)."

# Reads the old version out of the tree's own plugin.json rather than being told it,
# which is what lets one recipe serve both trees: each carries its own current string
# and that is simply what gets substituted from.
# check-skill-names is a prerequisite because $(SKILL_DIRS) is make-expanded straight
# into the script handed to sh below: a backtick in a folder name is executed, and
# `make release` reaches bump-tree two steps before it reaches `make test`.
bump-tree: check-skill-names ## Rewrite one tree's plugin.json and announce lines (usage: make bump-tree TREE=... SUFFIX=... VERSION=X.Y.Z)
	@old_ver=$$(python3 -c "import json; print(json.load(open('$(TREE)/.claude-plugin/plugin.json'))['version'])"); \
	new_ver="$(VERSION)$(SUFFIX)"; \
	if [ "$$old_ver" = "$$new_ver" ]; then \
		echo "$(TREE): already at $$new_ver."; \
		exit 0; \
	fi; \
	echo "$(TREE): $$old_ver -> $$new_ver"; \
	sed -i.bak "s|\"version\": \"[^\"]*\"|\"version\": \"$$new_ver\"|" $(TREE)/.claude-plugin/plugin.json && rm -f $(TREE)/.claude-plugin/plugin.json.bak; \
	for dir in $(SKILL_DIRS); do \
		name=$$(basename "$$dir"); \
		file="$$dir/SKILL.md"; \
		sed -i.bak "s|Running paad:$$name v$$old_ver\"|Running paad:$$name v$$new_ver\"|g" "$$file" && rm -f "$$file.bak"; \
	done

promote: ## Copy preview/paad over plugins/paad and strip the preview markers
# The only way plugins/ ever changes. Hand-editing it is forbidden with no exception,
# because the next release would destroy the edit: this rsync copies the pre-fix
# preview straight over it, the tree is committed so the dirty guard passes, and the
# result is self-consistent so every check passes. The changelog announces a fix the
# release does not contain.
#
# Everything that can refuse runs BEFORE the rsync. That ordering is the whole
# safety property: the rsync is the largest destructive act in the build, and it
# is not undoable from git alone — a preview-only skill arrives untracked, which
# `git checkout -- .` does not touch.
	@$(MAKE) --no-print-directory tree-checks TREE=preview/paad
	@$(MAKE) --no-print-directory check-readme TREE=preview/paad
	@count=$$(ls -1 preview/paad/skills/*/SKILL.md 2>/dev/null | wc -l | tr -d ' '); \
	shipped=$$(ls -1 plugins/paad/skills/*/SKILL.md 2>/dev/null | wc -l | tr -d ' '); \
	if [ "$$count" -eq 0 ]; then \
		echo "FAIL: preview/paad/skills holds no SKILL.md. 'rsync --delete' from an empty"; \
		echo "      source empties the shipped tree and exits 0 — nothing downstream notices."; \
		exit 1; \
	fi; \
	if [ "$$count" -lt "$$shipped" ] && [ -z "$(SHRINK)" ]; then \
		echo "FAIL: preview/paad has $$count skill(s), plugins/paad has $$shipped."; \
		echo "      Promotion would delete $$((shipped - count)). No check catches a missing"; \
		echo "      skill: check-readme and check-help walk skills -> docs, and validate,"; \
		echo "      check-versions and check-export-current all pass on a smaller tree that"; \
		echo "      is merely self-consistent. Re-run with SHRINK=1 if the removal is meant."; \
		exit 1; \
	fi
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "FAIL: working tree is dirty — promotion overwrites plugins/ wholesale, and"; \
		echo "      'git diff plugins/' is the only review of what is about to ship."; \
		git status --short | sed 's/^/  /'; \
		exit 1; \
	fi
	@rsync -a --delete preview/paad/ plugins/paad/
	@python3 scripts/promote.py

export: ## Regenerate kiro_and_antigravity/ and pi/ from the plugin sources
	@python3 scripts/convert_skills.py

release: ## Roll the changelog, bump, regenerate exports, test (usage: make release VERSION=X.Y.Z)
	@if [ -z "$(VERSION)" ]; then \
		echo "Usage: make release VERSION=X.Y.Z"; \
		exit 1; \
	fi
	@branch=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$branch" = "main" ]; then \
		echo "FAIL: release from a branch, never by committing to main directly."; \
		echo "      Create a release branch first, then re-run."; \
		exit 1; \
	fi
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "FAIL: working tree is dirty — commit or stash before cutting a release."; \
		git status --short | sed 's/^/  /'; \
		exit 1; \
	fi
# Both refusals below used to sit downstream of `promote`, so a typo'd VERSION or an
# empty [Unreleased] aborted with plugins/ already overwritten, both dirty guards
# blocking the retry, and check-versions failing. --check writes nothing.
	@python3 scripts/roll_changelog.py --check $(VERSION)
# `promote` rsyncs THIS working tree's preview/, so a release cut from a branch that
# is behind main silently omits everything merged since — and every check passes,
# because the omitted work simply is not there to fail on.
	@if git rev-parse --verify -q origin/main >/dev/null; then \
		if ! git merge-base --is-ancestor origin/main HEAD; then \
			echo "FAIL: origin/main is not an ancestor of HEAD — this branch is behind main."; \
			echo "      Promotion ships this tree's preview/, so anything merged to main since"; \
			echo "      you branched would be dropped from the release without a single check"; \
			echo "      failing. Merge or rebase main into this branch, then re-run."; \
			exit 1; \
		fi; \
	else \
		echo "FAIL: no origin/main to compare against — run 'git fetch origin' first."; \
		exit 1; \
	fi
	@$(MAKE) --no-print-directory promote
	@python3 scripts/roll_changelog.py $(VERSION)
	@$(MAKE) --no-print-directory bump-version VERSION=$(VERSION)
	@$(MAKE) --no-print-directory export
	@$(MAKE) --no-print-directory test
	@echo ""
	@echo "Release $(VERSION) prepared. Read 'git diff plugins/' first — that diff is the"
	@echo "release's actual payload and the last moment to catch something unintended. Then:"
	@echo "  git commit -a -m 'release: paad $(VERSION)'"
	@echo "  <merge this branch into main and push>"
	@echo "  make tag        # annotates the merge commit and pushes the tag"

tag: ## Tag the released version on main and push it (run after merging the release branch)
	@branch=$$(git rev-parse --abbrev-ref HEAD); \
	if [ "$$branch" != "main" ]; then \
		echo "FAIL: the tag goes on the commit that shipped — check out main first (you are on $$branch)."; \
		exit 1; \
	fi; \
	if [ -n "$$(git status --porcelain)" ]; then \
		echo "FAIL: working tree is dirty — the tag would not describe what you think it does."; \
		git status --short | sed 's/^/  /'; \
		exit 1; \
	fi; \
	ver=$$(python3 -c "import json; print(json.load(open('plugins/paad/.claude-plugin/plugin.json'))['version'])"); \
	tag="paad--v$$ver"; \
	if ! grep -qF "## [$$ver] — " CHANGELOG.md; then \
		echo "FAIL: CHANGELOG.md has no '## [$$ver]' section. Did 'make release VERSION=$$ver' run and get merged?"; \
		exit 1; \
	fi; \
	git fetch --quiet --tags origin; \
	if git rev-parse -q --verify "refs/tags/$$tag" >/dev/null; then \
		echo "FAIL: $$tag already exists (pointing at $$(git rev-parse --short $$tag)). Tags are not moved once published."; \
		exit 1; \
	fi; \
	if [ "$$(git rev-parse HEAD)" != "$$(git rev-parse origin/main)" ]; then \
		echo "FAIL: main is not in sync with origin/main. Push the merge first — a tag on an unpushed"; \
		echo "      commit points at a tree nobody else can fetch."; \
		exit 1; \
	fi; \
	git tag -a "$$tag" -m "paad $$ver"; \
	git push origin "$$tag"; \
	echo "Tagged $$tag on $$(git rev-parse --short HEAD) and pushed."

check-digraphs: check-skill-names ## Check every skill (except paad-help) has a digraph
	@fail=0; \
	for dir in $(SKILL_DIRS); do \
		name=$$(basename "$$dir"); \
		if [ "$$name" = "paad-help" ]; then continue; fi; \
		if ! grep -q '```dot' "$$dir/SKILL.md" 2>/dev/null; then \
			echo "FAIL: $$name has no digraph"; \
			fail=1; \
		fi; \
	done; \
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "All skills have digraphs (paad-help excluded)."
	@python3 scripts/lint_digraphs.py $(SKILLS_DIR)

check-help: check-skill-names ## Check every skill is documented in paad-help
	@fail=0; \
	for dir in $(SKILL_DIRS); do \
		name=$$(basename "$$dir"); \
		if [ "$$name" = "paad-help" ]; then continue; fi; \
		if ! grep -qE "(^|[^A-Za-z0-9._/-])/(paad:)?$$name([^A-Za-z0-9/-]|$$)" "$(SKILLS_DIR)/paad-help/SKILL.md" 2>/dev/null; then \
			echo "FAIL: $$name not found in paad-help"; \
			fail=1; \
		fi; \
	done; \
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "All skills documented in paad-help."

check-readme: check-skill-names ## Check every skill is documented in README.md
	@fail=0; \
	for dir in $(SKILL_DIRS); do \
		name=$$(basename "$$dir"); \
		if [ "$$name" = "paad-help" ]; then continue; fi; \
		if ! grep -qE "(^|[^A-Za-z0-9._/-])/(paad:)?$$name([^A-Za-z0-9/-]|$$)" README.md 2>/dev/null; then \
			echo "FAIL: $$name not found in README.md"; \
			fail=1; \
		fi; \
	done; \
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "All skills documented in README.md."

check-skill-names: ## Check every skill folder name follows the Agent Skills naming rules
	@LC_ALL=C; export LC_ALL; fail=0; count=0; \
	set -- $(SKILLS_DIR)/*/; \
	if [ ! -d "$$1" ]; then \
		echo "FAIL: no skills found under $(SKILLS_DIR) — checks that read them cannot run."; \
		exit 1; \
	fi; \
	for dir in $(SKILLS_DIR)/*/; do \
		[ -d "$$dir" ] || continue; \
		count=$$((count + 1)); \
		name=$${dir%/}; name=$${name##*/}; \
		bad=""; \
		if [ $${#name} -gt 64 ]; then \
			bad="is longer than 64 characters"; \
		else \
			case "$$name" in \
				*[!a-z0-9-]*) bad="may only contain lowercase letters, digits and hyphens";; \
				-*|*-) bad="must not start or end with a hyphen";; \
				*--*) bad="must not contain two hyphens in a row";; \
			esac; \
		fi; \
		if [ -n "$$bad" ]; then \
			echo "FAIL: skill folder '$$name' $$bad."; \
			fail=1; \
		fi; \
	done; \
	if [ "$$count" -eq 0 ]; then \
		echo "FAIL: no skill folders found under $(SKILLS_DIR) — this check cannot run."; \
		exit 1; \
	fi; \
	if [ "$$fail" -eq 1 ]; then \
		echo "      Folder names reach shell commands and search patterns elsewhere in this"; \
		echo "      Makefile, so an unusual character there breaks a later check silently."; \
		echo "      Rules: https://agentskills.io/specification"; \
		exit 1; \
	fi; \
	echo "$$count skill folder name(s) follow the naming rules."

check-frontmatter: check-skill-names ## Check SKILL.md frontmatter, and the internal flag across all three skill trees
	@fail=0; \
	for dir in $(SKILL_DIRS); do \
		folder_name=$$(basename "$$dir"); \
		file="$$dir/SKILL.md"; \
		if [ ! -f "$$file" ]; then \
			echo "FAIL: $$folder_name has no SKILL.md"; \
			fail=1; \
			continue; \
		fi; \
		fm_name=$$(awk '/^---$$/{n++; next} n==1 && /^name:/{print $$2; exit}' "$$file"); \
		fm_desc=$$(awk '/^---$$/{n++; next} n==1 && /^description:/{found=1; exit} END{if(found) print "yes"; else print "no"}' "$$file"); \
		if [ -z "$$fm_name" ]; then \
			echo "FAIL: $$folder_name SKILL.md missing 'name' in frontmatter"; \
			fail=1; \
		elif [ "$$fm_name" != "$$folder_name" ]; then \
			echo "FAIL: $$folder_name SKILL.md name is '$$fm_name' (expected '$$folder_name')"; \
			fail=1; \
		fi; \
		if [ "$$fm_desc" != "yes" ]; then \
			echo "FAIL: $$folder_name SKILL.md missing 'description' in frontmatter"; \
			fail=1; \
		fi; \
	done; \
	python3 scripts/check_internal_flag.py || fail=1; \
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "All SKILL.md files have valid frontmatter."

check-references: check-skill-names ## Check every references/ dispatch resolves and every reference file is named
	@python3 scripts/check_references.py $(SKILLS_DIR)

require-export:
	@[ -d kiro_and_antigravity/skills ] || { \
		echo "FAIL: no export tree at kiro_and_antigravity/skills — run 'make export' first."; \
		exit 1; \
	}

check-dispatch-sites: check-skill-names require-export ## Check every subagent dispatch site names the read-only analyst
# Inverted on purpose: flag any dispatch site that is NOT paad:paad-analyst, rather
# than counting the ones that are. Counting known-good sites passes a new skill that
# dispatches a write-capable subagent, which is the failure this exists to catch.
# Residual hole: a dispatch site written without a 'subagent_type' line is invisible here.
	@fail=0; \
	all=$$(grep -rn 'subagent_type' "$(SKILLS_DIR)"); st=$$?; \
	if [ "$$st" -gt 1 ]; then \
		echo "FAIL: could not scan $(SKILLS_DIR) for dispatch sites (grep exit $$st)."; \
		echo "      A security check that reports success without having run is worse than none."; \
		exit 1; \
	fi; \
	bad=$$(printf '%s\n' "$$all" | grep -vF 'subagent_type: paad:paad-analyst' || true); \
	if [ -n "$$bad" ]; then \
		echo "FAIL: dispatch site(s) not using the read-only analyst. Every analysis subagent must be"; \
		echo "      dispatched as 'subagent_type: paad:paad-analyst' — specialists and verifiers must not"; \
		echo "      carry Edit/Write/NotebookEdit. Offending lines:"; \
		echo "$$bad" | sed 's/^/  /'; \
		fail=1; \
	fi; \
	for name in agentic-review agentic-dedup agentic-a11y agentic-architecture agentic-owasp; do \
		file="$(SKILLS_DIR)/$$name/SKILL.md"; \
		if [ ! -f "$$file" ]; then \
			echo "FAIL: $$name has no SKILL.md (it is expected to dispatch analysis subagents)"; \
			fail=1; \
		elif ! grep -qF 'subagent_type: paad:paad-analyst' "$$file"; then \
			echo "FAIL: $$name no longer dispatches paad:paad-analyst anywhere — if it stopped dispatching"; \
			echo "      subagents on purpose, drop it from the list in check-dispatch-sites."; \
			fail=1; \
		fi; \
	done; \
	grep -rqF 'subagent_type' kiro_and_antigravity/skills 2>/dev/null; st=$$?; \
	if [ "$$st" -gt 1 ]; then \
		echo "FAIL: could not scan the export for 'subagent_type' (grep exit $$st)."; \
		fail=1; \
	elif [ "$$st" -eq 0 ]; then \
		echo "FAIL: 'subagent_type' survived into the export — neutralize() in scripts/convert_skills.py did not match this dispatch site's wording. Occurrences:"; \
		grep -rnF 'subagent_type' kiro_and_antigravity/skills | sed 's/^/  /'; \
		fail=1; \
	fi; \
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "Every dispatch site names paad:paad-analyst; none leaked into the export."

check-announce: check-skill-names ## Check every skill that writes files announces what it wrote
	@fail=0; \
	for dir in $(SKILL_DIRS); do \
		name=$$(basename "$$dir"); \
		if [ "$$name" = "paad-help" ] || [ "$$name" = "rethink" ]; then continue; fi; \
		if ! grep -rqF 'Files written or updated' "$$dir" 2>/dev/null; then \
			echo "FAIL: $$name has no 'Files written or updated:' block. Any skill that writes or updates"; \
			echo "      a file must end its run by listing every path it touched. Only 'paad-help' and 'rethink'"; \
			echo "      are exempt, because they write nothing — if this skill also writes nothing, exempt it here."; \
			fail=1; \
		fi; \
	done; \
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "All skills announce the files they write (paad-help, rethink excluded)."

check-export-frontmatter: require-export ## Check every exported SKILL.md kept a usable name and description
	@fail=0; \
	files=$$(find kiro_and_antigravity/skills -name SKILL.md | sort); \
	if [ -z "$$files" ]; then \
		echo "FAIL: no SKILL.md found under kiro_and_antigravity/skills — run 'make export' first."; \
		exit 1; \
	fi; \
	for file in $$files; do \
		name=$$(awk '/^---$$/{n++; next} n==1 && /^name:/{sub(/^name:[ \t]*/,""); print; exit}' "$$file"); \
		desc=$$(awk '/^---$$/{n++; next} n==1 && /^description:/{sub(/^description:[ \t]*/,""); print; exit}' "$$file"); \
		if [ -z "$$name" ]; then \
			echo "FAIL: $$file has no name in its frontmatter"; fail=1; \
		fi; \
		if [ -z "$$desc" ]; then \
			echo "FAIL: $$file has an empty description — these platforms match requests against it"; fail=1; \
		fi; \
		case "$$desc" in \
			">"|"|"|">-"|"|-") echo "FAIL: $$file description is a bare scalar marker, not text"; fail=1;; \
		esac; \
		case "$$desc" in \
			*/paad:*) echo "FAIL: $$file description leaks a Claude Code command: $$desc"; fail=1;; \
		esac; \
		case "$$desc" in \
			*paad/*) echo "FAIL: $$file description leaks a paad/ output path: $$desc"; fail=1;; \
		esac; \
	done; \
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "Exported SKILL.md frontmatter is intact."

check-export-commands: check-skill-names require-export ## Check no Claude Code slash command survived into the export
	@names=$$(echo "$(SKILL_NAMES)" | tr ' ' '|'); \
	bad=$$(grep -rnE "(^|[^A-Za-z0-9._/-])/(paad:)?($$names)([^A-Za-z0-9/-]|$$)" kiro_and_antigravity/skills); st=$$?; \
	if [ "$$st" -gt 1 ]; then \
		echo "FAIL: could not scan the export for slash commands (grep exit $$st)."; \
		exit 1; \
	fi; \
	if [ -n "$$bad" ]; then \
		echo "FAIL: Claude Code slash command(s) survived into the export. Kiro, Antigravity and Cursor"; \
		echo "      have no such command, so this instructs the agent to type something it cannot run."; \
		echo "      neutralize()/neutralize_description() in scripts/convert_skills.py did not match:"; \
		echo "$$bad" | sed 's/^/  /'; \
		exit 1; \
	fi; \
	orphan=$$(grep -rnE "(^|[^A-Za-z0-9._/-])/paad:[A-Za-z0-9-]+" kiro_and_antigravity/skills); st=$$?; \
	if [ "$$st" -gt 1 ]; then \
		echo "FAIL: could not scan the export for qualified commands (grep exit $$st)."; \
		exit 1; \
	fi; \
	if [ -n "$$orphan" ]; then \
		echo "FAIL: a /paad: command naming no current skill survived into the export."; \
		echo "      The rewriter's alternation and the check above are both built from the"; \
		echo "      same skills listing, so neither can see a name that listing lacks — which"; \
		echo "      is exactly what promotion leaves when a skill is deleted and a sibling"; \
		echo "      still points at it:"; \
		echo "$$orphan" | sed 's/^/  /'; \
		exit 1; \
	fi; \
	echo "No Claude Code slash commands survived into the export."

check-trees: ## Check plugins/paad is a subset of preview/paad, as the promotion model requires
# The invariant runs one way: plugins/ is a past state of preview/, so preview may
# hold paths plugins/ does not, never the reverse. Nothing else detects a breach.
# check-versions relates the trees only by version string, and a revert touching
# preview alone leaves it *behind* plugins/ with make test green and make export
# still regenerating the reverted behaviour from plugins/.
	@missing=$$(cd plugins/paad && find . -type f | while read -r f; do 		[ -e "../../preview/paad/$$f" ] || echo "$$f"; 	done); 	if [ -n "$$missing" ]; then 		echo "FAIL: plugins/paad holds path(s) preview/paad does not:"; 		echo "$$missing" | sed 's|^\./|  plugins/paad/|'; 		echo "      preview/ is always ahead of, or equal to, plugins/. A path here means"; 		echo "      preview lost something plugins still ships — the next promotion would"; 		echo "      delete it, and 'make export' regenerates it from plugins/ until then."; 		exit 1; 	fi; 	echo "plugins/paad is contained in preview/paad."

check-export-dryrun: check-skill-names ## Run the exporter against one tree, keeping only its verdict (usage: make check-export-dryrun TREE=preview/paad)
# The exporter reads plugins/paad/skills and nothing else, so preview content
# never reached it until promotion — and the three check-export-* targets read
# the committed export, so they sit outside tree-checks by necessity. A
# preview-only edit the exporter rejects therefore passed `make test` on main and
# failed inside `make release`, after promote, roll_changelog and bump-version had
# all written. The cheapest such edit is a /paad-help pointer, which the changelog
# convention encourages and SKIPPED_COMMAND turns into a hard exit.
#
# Same machinery as check-export-current, pointed at $(TREE) and throwing the
# output away: only the exit status matters here.
	@tmp=$$(mktemp -d); \
	trap 'rm -rf "$$tmp"' EXIT INT TERM; \
	mkdir -p "$$tmp/plugins" "$$tmp/scripts"; \
	cp -R $(TREE) "$$tmp/plugins/paad"; \
	cp scripts/convert_skills.py "$$tmp/scripts/"; \
	if ! (cd "$$tmp" && python3 scripts/convert_skills.py) >/dev/null 2>"$$tmp/err"; then \
		echo "FAIL: the exporter rejects $(TREE) —"; \
		sed 's|plugins/paad|$(TREE)|g; s/^/  /' "$$tmp/err"; \
		exit 1; \
	fi; \
	echo "$(TREE): the exporter accepts this tree."

check-export-current: check-skill-names require-export ## Check kiro_and_antigravity/ and pi/ match a fresh export
	@tmp=$$(mktemp -d); \
	trap 'rm -rf "$$tmp"' EXIT INT TERM; \
	mkdir -p "$$tmp/plugins" "$$tmp/scripts"; \
	cp -R plugins/paad "$$tmp/plugins/"; \
	cp scripts/convert_skills.py "$$tmp/scripts/"; \
	if ! (cd "$$tmp" && python3 scripts/convert_skills.py) >/dev/null 2>"$$tmp/err"; then \
		echo "FAIL: scripts/convert_skills.py errored:"; \
		sed 's/^/  /' "$$tmp/err"; \
		exit 1; \
	fi; \
	fail=0; \
	for dir in kiro_and_antigravity pi; do \
		if ! diff -ru "$$dir" "$$tmp/$$dir" >"$$tmp/export.diff" 2>&1; then \
			echo "FAIL: $$dir/ is stale — a source file changed but the export was not regenerated,"; \
			echo "      or a hand-added file is living under $$dir/ (everything there is generated)."; \
			echo "      Fix with: make export   (then commit the result)"; \
			head -40 "$$tmp/export.diff" | sed 's/^/  /'; \
			fail=1; \
		fi; \
	done; \
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "Exports in kiro_and_antigravity/ and pi/ are current."
