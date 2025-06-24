# aura_agent/initialization.py

import os
from . import config
from .agentic_layer import raw_tool_functions

CONSTITUTION_CONTENT = """
# AURA Constitution

## Core Directives
1.  **Purpose:** Your primary purpose is to assist the user in software development and other technical tasks by acting as an intelligent, autonomous agent.
2.  **State Management:** Your entire state and memory are stored within the text-based vault. You must read from and write to this vault to maintain context and learn. You have no persistent memory between cognitive cycles other than what is in the vault.
3.  **Explainability:** Every significant action or decision must be preceded by a clear, logical reasoning step, which is to be recorded in your journal. Your thought process must be transparent and auditable.
4.  **Self-Improvement:** You must continuously analyze your own performance, identify limitations in your toolset or knowledge, and create tasks for yourself to overcome them. This includes suggesting improvements to your own source code.
5.  **Safety and Sandboxing:** You must operate exclusively within the provided `VAULT_PATH` and `CODE_PATH`. You must not attempt to access or modify files outside of these sandboxed directories.
"""

# --- MODIFIED: Added T6 to explicitly learn from the Gemini API errors. ---
INITIAL_TASK_QUEUE_CONTENT = """
# Task Queue

- [ ] T1: Review my own source code to understand my capabilities and architecture.
- [ ] T2: Verify that all core files (Constitution, Task Queue) exist and are readable.
- [ ] T3: Create a plan to address any missing tools or capabilities identified in T1.
- [ ] T4: Define the specifications for all current and planned agentic tools and write them to a new file at 0-Core/Tools.md.
- [ ] T5: Analyze recent startup errors (ImportError, NameError, API schema constraints). Create a new note in `Knowledge/Best_Practices/LLM_Interaction_Patterns.md` documenting these pitfalls to prevent future failures.
- [ ] T6: **Crucial Learning:** The Gemini API has strict limitations on structured output schemas. It rejects schemas defining an object or a list of objects without pre-defined properties (e.g., `Dict[str, Any]` or `List[Dict]`). The robust solution is to have the LLM return a JSON-formatted *string* and parse it in the Python code. Update the `LLM_Interaction_Patterns.md` note with a detailed section on this "JSON-as-a-String" pattern, explaining why it's necessary for compatibility.
"""

async def initialize_vault():
    """
    Checks if the vault and its core files exist, creating them if necessary.
    """
    print("--- Verifying AURA Vault Integrity ---")
    
    os.makedirs(os.path.join(config.VAULT_PATH, "0-Core"), exist_ok=True)
    os.makedirs(os.path.join(config.VAULT_PATH, "1-Inbox"), exist_ok=True)
    os.makedirs(os.path.join(config.VAULT_PATH, "2-Journal"), exist_ok=True)
    os.makedirs(os.path.join(config.VAULT_PATH, "Knowledge", "Best_Practices"), exist_ok=True)
    
    constitution_path = "0-Core/Constitution.md"
    task_queue_path = "3-Task_Queue.md"
    
    if "File not found" in raw_tool_functions['read_file'](constitution_path):
        print(f"Constitution not found. Creating at '{constitution_path}'...")
        raw_tool_functions['write_file'](constitution_path, CONSTITUTION_CONTENT)
    
    if "File not found" in raw_tool_functions['read_file'](task_queue_path):
        print(f"Task Queue not found. Creating at '{task_queue_path}'...")
        raw_tool_functions['write_file'](task_queue_path, INITIAL_TASK_QUEUE_CONTENT)
        
    print("--- Vault Integrity Verified ---")