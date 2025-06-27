
# AURA Agentic Tools Specification

This document outlines the tools available to the AURA agent. It serves as a reference for both the agent's self-understanding and for human operators.

## I. Core Memory & Filesystem Tools

### `list_files(path: str) -> str`
- **Description:** Lists all files and directories within a specified path in the sandboxed environment.
- **Returns:** A JSON-formatted string representing a list of filenames.

### `read_file(path: str) -> str`
- **Description:** Reads the full content of a specified file.
- **Returns:** The content of the file as a string, or an error message.

### `write_file(path: str, content: str, overwrite: bool = False) -> str`
- **Description:** Writes content to a specified file. Creates parent directories if they don't exist.
- **Returns:** A success or error message string.

### `search_code(query: str) -> str`
- **Description:** Performs a simple text search across all files in the `aura_agent` source code directory.
- **Returns:** A JSON-formatted string of matches.

## II. Cognitive & State Management Tools

### `write_journal(content: str) -> str`
- **Description:** Creates a new, timestamped entry in the `2-Journal/` directory.
- **Returns:** A success or error message string.

### `read_task_queue() -> str`
- **Description:** Reads and parses the task queue markdown file into JSON.
- **Returns:** A JSON-formatted string representing the list of all tasks.

### `update_task_queue(tasks: List[dict]) -> str`
- **Description:** Overwrites the task queue with a new list of tasks.
- **Returns:** A success or error message string.

## III. Communication Tools

### `answer_user(answer: str) -> str`
- **Description:** Provides a final, direct answer to the user in the console.
- **Returns:** A success message confirming the answer was provided.
