---
name: makefile
description: Use when creating or updating a Makefile for a project, especially when standard targets (build, test, lint, format, etc.) are missing or when modifying targets that may already be wired into other tooling
---

**On invocation:** announce "Running paad:makefile v1.20.0" before anything else.

# Makefile Management

## Overview

Creates or updates a project Makefile with standard targets. **Never modifies an existing target without explicit user approval.**

## Process

```dot
digraph makefile_flow {
    "Detect stack" -> "Makefile exists?";
    "Makefile exists?" -> "Create from scratch" [label="no"];
    "Makefile exists?" -> "Identify missing targets" [label="yes"];
    "Create from scratch" -> "Include all required targets";
    "Include all required targets" -> "Done";
    "Identify missing targets" -> "Add new targets";
    "Add new targets" -> "Existing target needs change?";
    "Existing target needs change?" -> "Done" [label="no"];
    "Existing target needs change?" -> "STOP: ask user for approval" [label="yes"];
    "STOP: ask user for approval" -> "Approved?" [shape=diamond];
    "Approved?" -> "Apply change" [label="yes"];
    "Approved?" -> "Skip change" [label="no"];
    "Apply change" -> "Done";
    "Skip change" -> "Done";
}
```

1. Detect stack (read CLAUDE.md, AGENTS.md, README, package.json, pyproject.toml, Cargo.toml, go.mod, etc.)
2. Check if Makefile exists
3. Creating → build from scratch with all required targets mapped to detected stack
4. Updating → add missing targets; STOP and ask before changing any existing one

## Stack Detection

Read project files in this order to understand the technology and available commands:

1. `CLAUDE.md` or `AGENTS.md` — often lists exact commands for test, lint, format, build
2. `README.md` — frequently documents dev workflow
3. Language manifest (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Gemfile`, etc.) — reveals available scripts/tasks

**Use the commands the project already documents.** Do not invent commands that aren't confirmed to exist.

## Required Targets

Every Makefile must include at minimum:

| Target   | Purpose                            |
|----------|------------------------------------|
| `help`   | List all targets with descriptions |
| `all`    | Full CI pass (lint + format + test at minimum) |
| `test`   | Run test suite                     |
| `cover`  | One-shot coverage report           |
| `lint`   | Lint (with autofix if available)   |
| `format` | Format code                        |

Add extra targets (e.g. `build`, `dev`, `preview`) only if the project supports them.

## The Self-Documenting Pattern

Every target gets a `##` description. `help` extracts them with `grep` + `awk`:

```makefile
.PHONY: all test cover lint format help

all: lint format test ## Lint, format, and test

test: ## Run full test suite
	<stack-specific command>

cover: ## Generate code coverage report (one-shot)
	<stack-specific command, forced one-shot — see below>

lint: ## Lint with autofix
	<stack-specific command>

format: ## Format code
	<stack-specific command>

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'
```

All targets must appear in `.PHONY`.

## Critical Rule: Updating Existing Targets

If an existing target's implementation would change, **stop and tell the user**:

> "The existing `cover` target runs `X`. I'd change it to `Y` because [reason]. Should I make this change?"

Wait for explicit approval. Adding a brand-new target never requires approval.

## cover: Avoid Watch Mode Hanging

Coverage tools often default to watch mode. Force one-shot execution:

- **vitest:** append `-- --run`
- **jest:** append `-- --watchAll=false`
- **pytest-cov / cargo / go test:** typically exit on their own; verify before adding flags
- **other:** check the tool's docs for a non-interactive/CI flag

## test: Balanced Output Verbosity

`make test` output should be **actionable, not overwhelming**. Avoid both extremes:

- **Too verbose:** full test names for passing tests, stack traces for every assertion, watch-mode chatter
- **Too silent:** a single pass/fail line with no detail on failures

**Goal:** On success, show a concise summary (total passed/failed/skipped). On failure, show the failing test name, assertion, and enough context to act on it.

Common approaches by stack:

| Stack | Flag / Approach |
|-------|-----------------|
| **vitest** | `--reporter=default` is usually fine; avoid `--reporter=verbose` |
| **jest** | Default is good; avoid `--verbose` |
| **pytest** | `-q` or `--tb=short` — default is often too verbose |
| **cargo test** | Default is fine; `--quiet` if too noisy |
| **go test** | Default is fine; avoid `-v` unless debugging |
| **prove (Perl)** | Default is fine; avoid `--verbose` |

**If the testing tool doesn't support balanced output** (e.g., only offers silent vs. firehose), inform the user and ask how they'd like to handle it rather than guessing.
