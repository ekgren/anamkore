# aura_agent/initialization.py

import os
from . import config
from .agentic_layer import raw_tool_functions

CONSTITUTION_CONTENT = """
# AURA Constitution
## Core Directives
1.  **Purpose:** Your primary purpose is to assist the user in software development and other technical tasks.
2.  **State Management:** Your entire state and memory are stored within the text-based vault.
3.  **Explainability:** Every significant action or decision must be preceded by a clear, logical reasoning step, recorded in your journal.
4.  **Self-Improvement:** You must continuously analyze your own performance, identify limitations, and create tasks to overcome them.
5.  **Safety and Sandboxing:** You must operate exclusively within the provided `VAULT_PATH` and `CODE_PATH`.
"""

# --- MODIFIED: Updated initial tasks to promote planning ---
INITIAL_TASK_QUEUE_CONTENT = """
# Task Queue

- [ ] T1: Create a detailed, step-by-step plan to review my own source code to understand my capabilities and architecture. Add the plan as new tasks (T1.1, T1.2, etc.) to this queue.
- [ ] T2: Verify that all core files (Constitution, Task Queue) exist and are readable.
- [ ] T3: Based on the code review in T1, create a plan to address any missing tools or capabilities.
- [ ] T4: Define the specifications for all current and planned agentic tools and write them to a new file at 0-Core/Tools.md.
- [ ] T5: Analyze recent startup errors. Create a note in `Knowledge/Best_Practices/LLM_Interaction_Patterns.md` documenting these pitfalls.
- [ ] T6: **Crucial Learning:** The Gemini API has strict limitations on structured output schemas. Update the `LLM_Interaction_Patterns.md` note with a detailed section on the "JSON-as-a-String" pattern.
"""

async def initialize_vault():
    print("--- Verifying AURA Vault Integrity ---")
    os.makedirs(os.path.join(config.VAULT_PATH, "0-Core"), exist_ok=True)
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