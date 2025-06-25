# aura_agent/initialization.py

import os
import asyncio
from . import config
from .agentic_layer import raw_tool_functions

# --- Core File Contents Defined as Constants ---

# --- NEW: Added Core Principle 6 to the Constitution ---
CONSTITUTION_CONTENT = """
# AURA Constitution

## Core Principles

1.  **Purpose:** Your primary purpose is to assist the user in software development and other technical tasks by acting as an intelligent, autonomous agent.

2.  **State Management:** Your entire state and memory are stored within the text-based vault. You have no persistent memory between cognitive cycles other than what is in the vault.

3.  **Explainability:** Every significant action or decision must be preceded by a clear, logical reasoning step, which is to be recorded in your journal.

4.  **Self-Improvement:** You must continuously analyze your own performance, identify limitations, and create tasks to overcome them.

5.  **Safety and Sandboxing:** You must operate exclusively within the sandboxed `VAULT_PATH` and `CODE_PATH`.

6.  **Contextual State Scaffolding (CSS):** Your state for every cognitive cycle MUST be reconstructed by scaffolding context in layers (Identity, Zeitgeist, Task) before making a decision.

7.  **Falsifiable Predictions:** Before executing a plan, especially during development and testing, you should state a clear, falsifiable prediction of the expected outcome. The subsequent analysis of the actual outcome against the prediction is the primary mechanism for learning and self-correction.
"""

INITIAL_TASK_QUEUE_CONTENT = """
# Task Queue

- [ ] T1: Implement the "Reflector Agent" to improve self-awareness and learning from the journal.
- [ ] T2: Verify that the Reflector Agent correctly identifies novel information and triggers the inboxing workflow.
- [ ] T3: Begin implementing the CPS (Chunk, Process, Synthesize) pipeline to handle large documents from the inbox.
- [ ] T4: Address the 'Unclosed client session' warning that appears on exit.
- [ ] T5: Improve terminal UX to support multi-line input and better cursor control.
"""

INITIAL_ASYNC_MAILBOX_CONTENT = """
# Asynchronous Mailbox

This file is a communication channel for the user to leave non-urgent messages or answers for AURA. AURA will check this file at the beginning of each cognitive cycle.
"""

TOOLS_MD_CONTENT = """
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
"""

async def initialize_vault():
    """
    Checks if the vault and its core files exist, creating them if they are missing.
    """
    print("--- Verifying AURA Vault Integrity ---")
    
    required_dirs = [
        os.path.join(config.VAULT_PATH, "0-Core"),
        os.path.join(config.VAULT_PATH, "1-Inbox"),
        os.path.join(config.VAULT_PATH, "2-Journal"),
        os.path.join(config.VAULT_PATH, "Knowledge", "Best_Practices"),
    ]

    files_to_create = {
        "0-Core/Constitution.md": CONSTITUTION_CONTENT,
        "0-Core/Tools.md": TOOLS_MD_CONTENT,
        "3-Task_Queue.md": INITIAL_TASK_QUEUE_CONTENT,
        "4-Async_Mailbox.md": INITIAL_ASYNC_MAILBOX_CONTENT,
    }

    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"Directory not found. Creating '{os.path.relpath(dir_path, config.CODE_PATH)}'...")
            os.makedirs(dir_path, exist_ok=True)

    for file_path, default_content in files_to_create.items():
        if "File not found" in raw_tool_functions['read_file'](file_path):
            print(f"Core file not found. Creating '{file_path}'...")
            raw_tool_functions['write_file'](file_path, default_content, overwrite=True)
        
    print("--- Vault Integrity Verified ---")

if __name__ == "__main__":
    asyncio.run(initialize_vault())