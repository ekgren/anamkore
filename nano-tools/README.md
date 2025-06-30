# Nano-Tools: A Standalone Tool Library for Gemini CLI

This project contains a standalone Python library of tools designed to be used by an AI agent, specifically mirroring the core toolset of the `gemini-cli`.

## About

This library provides a feature-complete, "nano"-style implementation of the core tools from `gemini-cli`, including tools for file system interaction, shell command execution, and web searching. Each tool is designed to be robust, secure, and easily integrated into an agentic framework like `openai-agents-python`.

## Features

- **File System Tools:** `read_file`, `write_file`, `edit` (replace), `ls`, `glob`, `read_many_files`.
- **Shell Execution:** A secure `run_shell_command` tool with process group management.
- **Web Tools:** `web_fetch` and an API-integrated `google_web_search`.
- **Memory:** A `save_memory` tool for long-term fact storage.
- **Structured Output:** All tools return a dictionary with `llm_content` (for the agent) and `display_content` (for the user).
- **Full Test Suite:** Includes a comprehensive `unittest` suite to ensure reliability.

## Getting Started

### Installation

It is recommended to use `uv` for fast dependency management.

1.  **Create and activate a virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```

2.  **Install dependencies:**
    ```bash
    uv pip install -r requirements.txt
    ```

### Running Tests

This library includes both an interactive test script and a full `unittest` suite.

1.  **Interactive Testing:**
    Use the `test_tools.py` script to test individual tools from the command line.
    ```bash
    python test_tools.py --help
    python test_tools.py ls --path ./nano_gemini_cli_core
    ```

2.  **Automated Testing:**
    Run the full suite of automated tests.
    ```bash
    python -m unittest discover tests
    ```
