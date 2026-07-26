SKILLS_DIR := plugins/paad/skills
SKILL_DIRS := $(wildcard $(SKILLS_DIR)/*)
SKILL_NAMES := $(notdir $(SKILL_DIRS))

.PHONY: help test validate check-versions check-skill-versions check-digraphs check-help check-readme check-frontmatter check-references check-dispatch-sites check-export-current bump-version

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-22s %s\n", $$1, $$2}'

test: validate check-versions check-skill-versions check-digraphs check-help check-readme check-frontmatter check-references check-dispatch-sites check-export-current ## Run all checks
	@echo "All checks passed."

validate: ## Validate marketplace and all plugins
	@claude plugin validate .
	@for dir in plugins/*/; do \
		echo "Validating $$dir..."; \
		claude plugin validate "$$dir" || exit 1; \
	done

check-versions: ## Check marketplace.json and plugin.json versions match
	@marketplace_ver=$$(python3 -c "import json; print(json.load(open('.claude-plugin/marketplace.json'))['plugins'][0]['version'])"); \
	plugin_ver=$$(python3 -c "import json; print(json.load(open('plugins/paad/.claude-plugin/plugin.json'))['version'])"); \
	if [ "$$marketplace_ver" != "$$plugin_ver" ]; then \
		echo "FAIL: Version mismatch — marketplace.json ($$marketplace_ver) != plugin.json ($$plugin_ver)"; \
		exit 1; \
	fi; \
	echo "Versions match: $$plugin_ver"

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

bump-version: ## Bump version across plugin.json, marketplace.json, and all SKILL.md (usage: make bump-version VERSION=X.Y.Z)
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
	sed -i.bak 's|"version": "[^"]*"|"version": "$(VERSION)"|' plugins/paad/.claude-plugin/plugin.json && rm -f plugins/paad/.claude-plugin/plugin.json.bak; \
	sed -i.bak 's|^      "version": "[^"]*"|      "version": "$(VERSION)"|' .claude-plugin/marketplace.json && rm -f .claude-plugin/marketplace.json.bak; \
	for dir in $(SKILL_DIRS); do \
		name=$$(basename "$$dir"); \
		file="$$dir/SKILL.md"; \
		sed -i.bak "s|Running paad:$$name v$$old_ver\"|Running paad:$$name v$(VERSION)\"|g" "$$file" && rm -f "$$file.bak"; \
	done; \
	echo "Bumped to $(VERSION)."

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

check-dispatch-sites: ## Check every specialist/verifier dispatch site names the read-only subagent
	@fail=0; \
	for pair in agentic-review:2 agentic-dedup:2 agentic-a11y:3 agentic-architecture:2; do \
		name=$${pair%:*}; want=$${pair#*:}; \
		file="$(SKILLS_DIR)/$$name/SKILL.md"; \
		if [ ! -f "$$file" ]; then \
			echo "FAIL: $$name has no SKILL.md (expected $$want dispatch site(s) in it)"; \
			fail=1; \
			continue; \
		fi; \
		got=$$(grep -cF 'subagent_type: paad:paad-analyst' "$$file" || true); \
		if [ "$$got" != "$$want" ]; then \
			echo "FAIL: $$name names paad:paad-analyst at $$got dispatch site(s), expected $$want (if this change is intentional, update the counts in check-dispatch-sites)"; \
			fail=1; \
		fi; \
	done; \
	counts=$$(grep -rcF 'subagent_type: paad:paad-analyst' "$(SKILLS_DIR)" | grep -v ':0$$' || true); \
	total=$$(echo "$$counts" | awk -F: '{n+=$$2} END {print n+0}'); \
	if [ "$$total" != "9" ]; then \
		echo "FAIL: expected 9 dispatch sites across $(SKILLS_DIR), found $$total (if this change is intentional, update the counts in check-dispatch-sites). Sites found:"; \
		echo "$$counts" | sed 's/^/  /'; \
		fail=1; \
	fi; \
	if grep -rqF 'subagent_type' kiro_and_antigravity/skills 2>/dev/null; then \
		echo "FAIL: 'subagent_type' survived into the export — neutralize() in scripts/convert_skills.py did not match this dispatch site's wording. Occurrences:"; \
		grep -rnF 'subagent_type' kiro_and_antigravity/skills | sed 's/^/  /'; \
		fail=1; \
	fi; \
	if [ "$$fail" -eq 1 ]; then exit 1; fi; \
	echo "All 9 dispatch sites name paad:paad-analyst (review 2, dedup 2, a11y 3, architecture 2); none leaked into the export."

check-export-current: ## Check kiro_and_antigravity/ matches a fresh export of the skills
	@tmp=$$(mktemp -d); \
	mkdir -p "$$tmp/plugins" "$$tmp/scripts"; \
	cp -R plugins/paad "$$tmp/plugins/"; \
	cp scripts/convert_skills.py "$$tmp/scripts/"; \
	if ! (cd "$$tmp" && python3 scripts/convert_skills.py) >/dev/null 2>"$$tmp/err"; then \
		echo "FAIL: scripts/convert_skills.py errored:"; \
		sed 's/^/  /' "$$tmp/err"; \
		rm -rf "$$tmp"; \
		exit 1; \
	fi; \
	if ! diff -ru kiro_and_antigravity "$$tmp/kiro_and_antigravity" >"$$tmp/export.diff" 2>&1; then \
		echo "FAIL: kiro_and_antigravity/ is stale — a skill changed but the export was not regenerated."; \
		echo "      Fix with: python3 scripts/convert_skills.py   (then commit the result)"; \
		head -40 "$$tmp/export.diff" | sed 's/^/  /'; \
		rm -rf "$$tmp"; \
		exit 1; \
	fi; \
	rm -rf "$$tmp"; \
	echo "Export in kiro_and_antigravity/ is current."
