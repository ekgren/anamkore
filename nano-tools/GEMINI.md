# Gemini Context: Nano-Tools Library

This document provides essential context for an AI assistant working on the `nano-tools` library.

## 1. Project Goal

The primary goal of this project is to create a standalone, feature-complete Python implementation of the core tools found in the official `gemini-cli`. This library should be robust, well-tested, and easily integrable into any agentic framework.

## 2. Architecture

- **Self-Contained Tools:** Each tool is implemented in its own Python file within `nano_gemini_cli_core/tools/`.
- **Utilities:** Shared helper functions (e.g., for path manipulation, git checks) are located in `nano_gemini_cli_core/utils/`.
- **Structured Output:** All tools must return a dictionary with two keys:
    - `llm_content`: The detailed, raw output for the agent to process.
    - `display_content`: A concise, user-friendly summary for the CLI to display.
- **Testing:** The project uses the standard `unittest` framework. Tests are located in the `tests/` directory, with a separate `test_*.py` file for each tool.

## 3. Development Workflow

### Setup

The project uses `uv` for dependency management.

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Testing

-   **Run all automated tests:** `python -m unittest discover tests`
-   **Run interactive tests:** `python test_tools.py --help`

### Key Principles

-   **Feature Parity:** Each tool should aim to be a feature-complete port of its `gemini-cli` counterpart. This includes not just the core logic, but also security validations, error handling, and output formatting.
-   **Clarity and Simplicity:** Adhere to the "nano" philosophy. Code should be clean, well-commented, and easy to understand.
-   **Robustness:** Every tool must be accompanied by a corresponding test file in the `tests/` directory that validates its functionality and edge cases.
