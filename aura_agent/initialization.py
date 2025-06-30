# aura_agent/initialization.py

import os
from . import config

# ---
# Self-Correction Note for Anamkore:
# This script's role is to ensure the agent's dynamic runtime state can be
# created from scratch. The static, foundational context (Core, Knowledge)
# is now managed by the git repository.
# ---

STRATEGIC_TASK_QUEUE_CONTENT = """
# Task Queue

- [ ] T1: Create a new tool file at `aura_agent/task_tools.py`.
- [ ] T2: Add the basic function definition for `task_complete(task_id: str)` to the new `aura_agent/task_tools.py` file.
- [ ] T3: Import the new `task_complete` tool into `aura_agent/agentic_layer.py` and add it to the `anamkore_tools` list.
- [ ] T4: Implement the full logic for the `task_complete` tool.
"""

INITIAL_ASYNC_MAILBOX_CONTENT = """
# Asynchronous Mailbox
This file is a communication channel for the user to leave non-urgent messages or answers for AURA. AURA will check this file at the beginning of each cognitive cycle.
"""

INITIAL_CURRENT_TASK_CONTENT = "" # This file starts empty.

def initialize_vault_sync():
    """
    Synchronous function to check and create the dynamic vault files needed at runtime.
    This is safer for a simple initialization script.
    """
    print("--- Verifying Anamkore Vault Integrity ---")

    # These are the directories for DYNAMIC state. The static ones are in git.
    required_dirs = [
        os.path.join(config.VAULT_PATH, "1-Inbox"),
        os.path.join(config.VAULT_PATH, "2-Journal"),
    ]

    # These are the DYNAMIC state files.
    files_to_create = {
        "3-Task_Queue.md": STRATEGIC_TASK_QUEUE_CONTENT,
        "4-Async_Mailbox.md": INITIAL_ASYNC_MAILBOX_CONTENT,
        "5-Current_Task.md": INITIAL_CURRENT_TASK_CONTENT,
    }

    # First, ensure the root vault directory exists.
    if not os.path.exists(config.VAULT_PATH):
        os.makedirs(config.VAULT_PATH, exist_ok=True)

    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"Runtime directory not found. Creating '{os.path.relpath(dir_path, config.CODE_PATH)}'...")
            os.makedirs(dir_path, exist_ok=True)

    for file_path, default_content in files_to_create.items():
        full_file_path = os.path.join(config.VAULT_PATH, file_path)
        if not os.path.exists(full_file_path):
            print(f"Runtime file not found. Creating '{file_path}'...")
            with open(full_file_path, 'w', encoding='utf-8') as f:
                f.write(default_content)

    print("--- Vault Integrity Verified ---")

if __name__ == "__main__":
    initialize_vault_sync()