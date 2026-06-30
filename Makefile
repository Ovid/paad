SKILLS_DIR := plugins/paad/skills
SKILL_DIRS := $(wildcard $(SKILLS_DIR)/*)
SKILL_NAMES := $(notdir $(SKILL_DIRS))

.PHONY: help test validate check-versions check-digraphs check-help check-readme check-frontmatter kiro check-kiro

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

test: validate check-versions check-digraphs check-help check-readme check-frontmatter check-kiro ## Run all checks
	@echo "All checks passed."

kiro: ## Regenerate the Kiro power (POWER.md + steering/)
	@python3 scripts/build-kiro-power.py

check-kiro: ## Fail if the committed Kiro power is stale or hand-edited (ignores provenance stamp)
	@python3 scripts/build-kiro-power.py --check

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
