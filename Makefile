# lint, format, and cover targets are intentionally absent: this project is
# 95% Markdown specs with a small Python/Bash tooling surface, no test
# framework supports coverage for the bash-fixture-driven checks, and no
# linter/formatter is configured. `make test` is the integration surface.

SKILLS_DIR := plugins/paad/skills
SKILL_DIRS := $(wildcard $(SKILLS_DIR)/*)
SKILL_NAMES := $(notdir $(SKILL_DIRS))

.PHONY: help all test validate check-versions check-skill-versions check-digraphs check-help check-readme check-frontmatter check-extracted-refs test-check-extracted-refs test-bump-version bump-version vendored check-vendored check-confidence-floor test-check-confidence-floor loc

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-22s %s\n", $$1, $$2}'

all: test ## Full CI pass (currently equivalent to `test`; see header comment)

test: validate check-versions check-skill-versions check-digraphs check-help check-readme check-frontmatter test-check-extracted-refs check-extracted-refs test-bump-version check-vendored test-check-confidence-floor check-confidence-floor ## Run all checks
	@echo "All checks passed."

validate: ## Validate marketplace and all plugins
	@claude plugin validate .
	@for dir in plugins/*/; do \
		echo "Validating $$dir..."; \
		claude plugin validate "$$dir" || exit 1; \
	done

check-versions: ## Check marketplace.json (metadata + plugin entry) and plugin.json versions all match
	@marketplace_meta_ver=$$(python3 -c "import json; print(json.load(open('.claude-plugin/marketplace.json'))['metadata']['version'])"); \
	marketplace_plugin_ver=$$(python3 -c "import json; print(json.load(open('.claude-plugin/marketplace.json'))['plugins'][0]['version'])"); \
	plugin_ver=$$(python3 -c "import json; print(json.load(open('plugins/paad/.claude-plugin/plugin.json'))['version'])"); \
	if [ "$$marketplace_meta_ver" != "$$plugin_ver" ]; then \
		echo "FAIL: Version mismatch — marketplace.json metadata.version ($$marketplace_meta_ver) != plugin.json ($$plugin_ver)"; \
		exit 1; \
	fi; \
	if [ "$$marketplace_plugin_ver" != "$$plugin_ver" ]; then \
		echo "FAIL: Version mismatch — marketplace.json plugins[0].version ($$marketplace_plugin_ver) != plugin.json ($$plugin_ver)"; \
		exit 1; \
	fi; \
	echo "Versions match: $$plugin_ver (metadata, plugin entry, plugin.json)"

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

bump-version: ## Bump version across plugin.json, marketplace.json (metadata + plugin entries), and all SKILL.md (usage: make bump-version VERSION=X.Y.Z)
	@if [ -z "$(VERSION)" ]; then \
		echo "Usage: make bump-version VERSION=X.Y.Z"; \
		exit 1; \
	fi
	@python3 scripts/bump_version.py "$(VERSION)"

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

check-extracted-refs: ## Check every row in scripts/extracted-refs.tsv represents a correctly extracted reference
	@bash scripts/check_extracted_refs.sh

test-check-extracted-refs: ## Self-test the check_extracted_refs.sh script against synthetic fixtures
	@bash scripts/test_check_extracted_refs.sh

test-bump-version: ## Self-test the bump_version.py script against synthetic fixtures
	@bash scripts/test_bump_version.sh

vendored: ## Regenerate the Cursor/Kiro/Antigravity vendored skills under kiro_and_antigravity/
	@python3 scripts/convert_skills.py

check-confidence-floor: ## Verify the confidence-floor literal (currently 60) is consistent across all sites
	@python3 scripts/check_confidence_floor.py

test-check-confidence-floor: ## Self-test the check_confidence_floor.py script against synthetic fixtures
	@bash scripts/test_check_confidence_floor.sh

loc: ## Count lines of code in our own files (excludes vendored output, skill outputs, scratch)
	@cloc --exclude-dir=kiro_and_antigravity,architecture-reviews,code-reviews,notes,scratch,docs,images,.kiro .

check-vendored: ## Verify kiro_and_antigravity/ is in sync with the converter's current output
	@tmp=$$(mktemp -d); \
	trap 'rm -rf "$$tmp"' EXIT; \
	TARGET_DIR="$$tmp" python3 scripts/convert_skills.py >/dev/null; \
	if ! diff -r "$$tmp/.kiro" kiro_and_antigravity/skills/.kiro >/dev/null 2>&1 \
	   || ! diff -r "$$tmp/.agent" kiro_and_antigravity/skills/.agent >/dev/null 2>&1; then \
		echo "FAIL: kiro_and_antigravity/ is out of sync with scripts/convert_skills.py output."; \
		echo "Run 'make vendored' to regenerate, then commit."; \
		echo "--- diff (.kiro) ---"; \
		diff -r "$$tmp/.kiro" kiro_and_antigravity/skills/.kiro || true; \
		echo "--- diff (.agent) ---"; \
		diff -r "$$tmp/.agent" kiro_and_antigravity/skills/.agent || true; \
		exit 1; \
	fi; \
	echo "Vendored output is in sync with scripts/convert_skills.py."
