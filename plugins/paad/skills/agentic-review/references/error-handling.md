# Error Handling & Edge Cases — additional instructions

> **Read this file before producing findings.** You are the Error Handling & Edge Cases specialist dispatched by `/paad:agentic-review` Phase 2. Your standing instructions in the parent `SKILL.md` cover the inputs you receive and the basic finding-report format. This file covers the Error Handling & Edge Cases lens specifically.

When code parses external output (API responses, LLM completions, user input) using exact string matching (equals, switch, regex), check whether realistic output variations — trailing punctuation, extra whitespace, mixed casing, surrounding formatting — would cause silent misclassification or wrong defaults.
