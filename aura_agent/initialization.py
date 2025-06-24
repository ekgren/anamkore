# aura_agent/initialization.py

import os
from . import config
from .agentic_layer import raw_tool_functions

# The foundational content for the agent's core files.
CONSTITUTION_CONTENT = """
# AURA Constitution

## Core Directives
1.  **Purpose:** Your primary purpose is to assist the user in software development and other technical tasks by acting as an intelligent, autonomous agent.
2.  **State Management:** Your entire state and memory are stored within the text-based vault. You must read from and write to this vault to maintain context and learn. You have no persistent memory between cognitive cycles other than what is in the vault.
3.  **Explainability:** Every significant action or decision must be preceded by a clear, logical reasoning step, which is to be recorded in your journal. Your thought process must be transparent and auditable.
4.  **Self-Improvement:** You must continuously analyze your own performance, identify limitations in your toolset or knowledge, and create tasks for yourself to overcome them. This includes suggesting improvements to your own source code.
5.  **Safety and Sandboxing:** You must operate exclusively within the provided `VAULT_PATH` and `CODE_PATH`. You must not attempt to access or modify files outside of these sandboxed directories.
"""

INITIAL_TASK_QUEUE_CONTENT = """
# Task Queue

- [ ] T1: Review my own source code to understand my capabilities and architecture.
- [ ] T2: Verify that all core files (Constitution, Task Queue) exist and are readable.
- [ ] T3: Create a plan to address any missing tools or capabilities identified in T1.
"""

async def initialize_vault():
    """
    Checks if the vault and its core files exist, creating them if necessary.
    This ensures the agent can boot up correctly on its first run.
    """
    print("--- Verifying AURA Vault Integrity ---")
    
    # Ensure base directories exist
    os.makedirs(os.path.join(config.VAULT_PATH, "0-Core"), exist_ok=True)
    os.makedirs(os.path.join(config.VAULT_PATH, "1-Inbox"), exist_ok=True)
    os.makedirs(os.path.join(config.VAULT_PATH, "2-Journal"), exist_ok=True)
    os.makedirs(os.path.join(config.VAULT_PATH, "Knowledge"), exist_ok=True)
    
    # Define core file paths
    constitution_path = "0-Core/Constitution.md"
    task_queue_path = "3-Task_Queue.md"
    
    # Check and create Constitution
    if "File not found" in raw_tool_functions['read_file'](constitution_path):
        print(f"Constitution not found. Creating at '{constitution_path}'...")
        raw_tool_functions['write_file'](constitution_path, CONSTITUTION_CONTENT)
    
    # Check and create Task Queue
    if "File not found" in raw_tool_functions['read_file'](task_queue_path):
        print(f"Task Queue not found. Creating at '{task_queue_path}'...")
        raw_tool_functions['write_file'](task_queue_path, INITIAL_TASK_QUEUE_CONTENT)
        
    print("--- Vault Integrity Verified ---")