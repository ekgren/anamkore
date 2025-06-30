# Gemini Context: Nano-GeminiCLI

This document provides essential context for an AI assistant working on the `nano-gemini-cli` project. Adhering to these principles is critical for maintaining the project's clean, minimal, and robust architecture.

## 1. High-Level Architecture

This project follows a modular, client-server design:

-   **`core` Package (`packages/nano_gemini_cli_core`):** The backend engine.
    -   Its public API is the `NanoGeminiClient` class in `client.py`.
    -   This client manages the agent's state, history, and context.
    -   It defines all tools and the dynamic system prompt.
    -   It can be run as a standalone conversational server via `server.py`.

-   **`cli` Package (`packages/nano_gemini_cli`):** The user-facing frontend.
    -   It is built around a `TUI` (Text-based User Interface) class in `main.py`.
    -   It is a "thin client": its primary job is to render events from the `core` and handle user input.
    -   It contains the command dispatcher for special inputs.

## 2. The Interaction Model

The `cli`'s `TUI` class is the entry point for all user interaction.

1.  **Command Dispatcher:** The `TUI` first inspects the user's prompt for prefixes:
    -   **`/` commands** (e.g., `/help`, `/quit`) are handled by the `slash_command` processor.
    -   **`!` commands** (e.g., `!ls -l`) are handled by the `shell_command` processor, which directly executes the command.
    -   **`@` commands** (e.g., `summarize @README.md`) are handled by the `at_command` processor, which reads the file and expands the prompt.

2.  **Default Conversational Flow:** If no prefix is detected, the prompt is sent to the `NanoGeminiClient`'s `send_message_stream` method. The `TUI` then renders the stream of events (thinking, tool calls, text chunks) that it yields.

## 3. Agent-to-Agent Communication

The project supports true agent-to-agent conversation.

-   **Server Mode:** The `core` package can be run as a server (`uv run python -m nano_gemini_cli_core.server`). This exposes a `/chat` endpoint that accepts prompts and returns complete, natural language responses.
-   **Client Tool:** The `ask_remote_agent` tool allows one agent to send a prompt to another agent's `/chat` endpoint and get its response. This enables complex, multi-agent workflows like debugging.

## 4. Development Workflow with `uv`

This project uses `uv` for fast and efficient dependency management.

1.  **Create and activate the virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```
2.  **Install packages in editable mode:**
    ```bash
    uv pip install -e ./packages/nano_gemini_cli_core
    uv pip install -e ./packages/nano_gemini_cli
    ```
3.  **Running the CLI:**
    ```bash
    uv run python -m nano_gemini_cli.main
    ```

## 5. Adding New Tools: The `@function_tool` Pattern

This is the **only** correct way to add new tools to the agent.

1.  **Create a File:** Add a new Python file for the tool in `packages/nano_gemini_cli_core/tools/`.
2.  **Decorate the Function:** Add the **`@function_tool`** decorator from `openai_agents` to your function.
3.  **Use Type Hints & Docstrings:** The SDK automatically generates the tool's schema from your function's signature.
    -   **Type Hints** (`arg: str`) define the argument types.
    -   The **main docstring** becomes the tool's high-level description.
    -   The **`Args:` section** of the docstring provides the description for each specific argument.
4.  **Define Return Type:** The function should return a dictionary with two keys: `{"llm_content": "...", "display_content": "..."}`.
5.  **Register the Tool:** Import your new decorated function in `packages/nano_gemini_cli_core/client.py` and add the function object directly to the `tools` list in the `_create_agent` method.

## 6. Key Principles & Rules

-   **Strict Separation of Concerns:** `core` is for logic, `cli` is for presentation.
-   **Use the SDK's Primitives:** Use the `Runner` class for execution and the `@function_tool` decorator for tool definition.
-   **Docstrings Are the API:** The agent's understanding of a tool comes *directly* from its docstring and type hints.
-   **The `cli` Renders, the `core` Thinks:** The `cli`'s job is to handle user input and render the event stream from the `NanoGeminiClient`. All state and logic should be encapsulated in the `core`.
-   **User Is in Control:** The `cli` must always prompt for confirmation before executing any tool call that modifies the file system or runs a shell command.
