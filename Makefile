SKILLS_DIR := plugins/paad/skills
SKILL_DIRS := $(wildcard $(SKILLS_DIR)/*)
SKILL_NAMES := $(notdir $(SKILL_DIRS))

.PHONY: help test validate check-versions check-skill-versions check-digraphs check-help check-readme check-frontmatter bump-version

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-22s %s\n", $$1, $$2}'

test: validate check-versions check-skill-versions check-digraphs check-help check-readme check-frontmatter ## Run all checks
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
