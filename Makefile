SKILLS_DIR := plugins/paad/skills
SKILL_DIRS := $(wildcard $(SKILLS_DIR)/*)
SKILL_NAMES := $(notdir $(SKILL_DIRS))

.PHONY: help test validate check-versions check-skill-versions check-digraphs check-help check-readme check-frontmatter check-references check-dispatch-sites check-announce check-export-current bump-version export release tag

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-22s %s\n", $$1, $$2}'

test: validate check-versions check-skill-versions check-digraphs check-help check-readme check-frontmatter check-references check-dispatch-sites check-announce check-export-current ## Run all checks
	@echo "All checks passed."

validate: ## Validate marketplace and all plugins
	@claude plugin validate .
	@for dir in plugins/*/; do \
		echo "Validating $$dir..."; \
		claude plugin validate "$$dir" || exit 1; \
	done

check-versions: ## Check package and plugin versions match
	@package_ver=$$(python3 -c "import json; print(json.load(open('package.json'))['version'])"); \
	marketplace_ver=$$(python3 -c "import json; print(json.load(open('.claude-plugin/marketplace.json'))['plugins'][0]['version'])"); \
	plugin_ver=$$(python3 -c "import json; print(json.load(open('plugins/paad/.claude-plugin/plugin.json'))['version'])"); \
	if [ "$$package_ver" != "$$marketplace_ver" ] || [ "$$package_ver" != "$$plugin_ver" ]; then \
		echo "FAIL: Version mismatch — package.json ($$package_ver), marketplace.json ($$marketplace_ver), plugin.json ($$plugin_ver)"; \
		exit 1; \
	fi; \
	echo "Versions match: $$package_ver"

check-skill-versions: ## Check every SKILL.md announces the correct version
	@plugin_ver=$$(python3 -c "import json; print(json.load(open('plugins/paad/.claude-plugin/plugin.json'))['version'])"); \
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
	echo "All skills announce v$$plugin_ver."

bump-version: ## Bump version across package and plugin manifests and all SKILL.md (usage: make bump-version VERSION=X.Y.Z)
	@if [ -z "$(VERSION)" ]; then \
		echo "Usage: make bump-version VERSION=X.Y.Z"; \
		exit 1; \
	fi
	@case "$(VERSION)" in \
		[0-9]*.[0-9]*.[0-9]*) ;; \
		*) echo "FAIL: VERSION must be in X.Y.Z form (got $(VERSION))"; exit 1 ;; \
	esac
	@old_ver=$$(python3 -c "import json; print(json.load(open('plugins/paad/.claude-plugin/plugin.json'))['version'])"); \
	if [ "$$old_ver" = "$(VERSION)" ]; then \
		echo "Already at $(VERSION). Nothing to do."; \
		exit 0; \
	fi; \
	echo "Bumping $$old_ver -> $(VERSION)..."; \
	sed -i.bak 's|^  "version": "[^"]*"|  "version": "$(VERSION)"|' package.json && rm -f package.json.bak; \
	sed -i.bak 's|"version": "[^"]*"|"version": "$(VERSION)"|' plugins/paad/.claude-plugin/plugin.json && rm -f plugins/paad/.claude-plugin/plugin.json.bak; \
	sed -i.bak 's|^      "version": "[^"]*"|      "version": "$(VERSION)"|' .claude-plugin/marketplace.json && rm -f .claude-plugin/marketplace.json.bak; \
	for dir in $(SKILL_DIRS); do \
		name=$$(basename "$$dir"); \
		file="$$dir/SKILL.md"; \
		sed -i.bak "s|Running paad:$$name v$$old_ver\"|Running paad:$$name v$(VERSION)\"|g" "$$file" && rm -f "$$file.bak"; \
	done; \
	echo "Bumped to $(VERSION)."

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
	@python3 scripts/roll_changelog.py $(VERSION)
	@$(MAKE) --no-print-directory bump-version VERSION=$(VERSION)
	@$(MAKE) --no-print-directory export
	@$(MAKE) --no-print-directory test
	@echo ""
	@echo "Release $(VERSION) prepared. Review the diff, then:"
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

check-digraphs: ## Check every skill (except help) has a digraph
	@fail=0; \
	for dir in $(SKILL_DIRS); do \
		name=$$(basename "$$dir"); \
		if [ "$$name" = "help" ]; then continue; fi; \
		if ! grep -q '```dot' "$$dir/SKILL.md" 2>/dev/null; then \
			echo "FAIL: $$name has no digraph"; \
			fail=1; \
		fi; \
	done; \
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "All skills have digraphs (help excluded)."
	@python3 scripts/lint_digraphs.py

check-help: ## Check every skill is documented in paad:help
	@fail=0; \
	for dir in $(SKILL_DIRS); do \
		name=$$(basename "$$dir"); \
		if [ "$$name" = "help" ]; then continue; fi; \
		if ! grep -q "/paad:$$name" "$(SKILLS_DIR)/help/SKILL.md" 2>/dev/null; then \
			echo "FAIL: $$name not found in paad:help"; \
			fail=1; \
		fi; \
	done; \
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "All skills documented in paad:help."

check-readme: ## Check every skill is documented in README.md
	@fail=0; \
	for dir in $(SKILL_DIRS); do \
		name=$$(basename "$$dir"); \
		if [ "$$name" = "help" ]; then continue; fi; \
		if ! grep -q "/paad:$$name" README.md 2>/dev/null; then \
			echo "FAIL: $$name not found in README.md"; \
			fail=1; \
		fi; \
	done; \
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "All skills documented in README.md."

check-frontmatter: ## Check every SKILL.md has name/description and name matches folder
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
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "All SKILL.md files have valid frontmatter."

check-references: ## Check every references/ dispatch resolves and every reference file is named
	@python3 scripts/check_references.py

check-dispatch-sites: ## Check every subagent dispatch site names the read-only analyst
# Inverted on purpose: flag any dispatch site that is NOT paad:paad-analyst, rather
# than counting the ones that are. Counting known-good sites passes a new skill that
# dispatches a write-capable subagent, which is the failure this exists to catch.
# Residual hole: a dispatch site written without a 'subagent_type' line is invisible here.
	@fail=0; \
	bad=$$(grep -rn 'subagent_type' "$(SKILLS_DIR)" | grep -vF 'subagent_type: paad:paad-analyst' || true); \
	if [ -n "$$bad" ]; then \
		echo "FAIL: dispatch site(s) not using the read-only analyst. Every analysis subagent must be"; \
		echo "      dispatched as 'subagent_type: paad:paad-analyst' — specialists and verifiers must not"; \
		echo "      carry Edit/Write/NotebookEdit. Offending lines:"; \
		echo "$$bad" | sed 's/^/  /'; \
		fail=1; \
	fi; \
	for name in agentic-review agentic-dedup agentic-a11y agentic-architecture; do \
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
	if grep -rqF 'subagent_type' kiro_and_antigravity/skills 2>/dev/null; then \
		echo "FAIL: 'subagent_type' survived into the export — neutralize() in scripts/convert_skills.py did not match this dispatch site's wording. Occurrences:"; \
		grep -rnF 'subagent_type' kiro_and_antigravity/skills | sed 's/^/  /'; \
		fail=1; \
	fi; \
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "Every dispatch site names paad:paad-analyst; none leaked into the export."

check-announce: ## Check every skill that writes files announces what it wrote
	@fail=0; \
	for dir in $(SKILL_DIRS); do \
		name=$$(basename "$$dir"); \
		if [ "$$name" = "help" ]; then continue; fi; \
		if ! grep -rqF 'Files written or updated' "$$dir" 2>/dev/null; then \
			echo "FAIL: $$name has no 'Files written or updated:' block. Any skill that writes or updates"; \
			echo "      a file must end its run by listing every path it touched. Only 'help' is exempt,"; \
			echo "      because it writes nothing — if this skill also writes nothing, exempt it here."; \
			fail=1; \
		fi; \
	done; \
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "All skills announce the files they write (help excluded)."

check-export-current: ## Check kiro_and_antigravity/ and pi/ match a fresh export
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
