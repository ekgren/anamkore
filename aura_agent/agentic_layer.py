import os
import re
import json
from datetime import datetime
from typing import List
from agents import function_tool
from . import config
from .task import Task

# --- Raw Tool Functions ---
# ... (write_journal, update_task_queue, read_memory functions remain unchanged) ...

def _write_journal_func(content: str) -> str:
    """
    Creates a new, timestamped Markdown file in the 2-Journal/ directory.
    This is the agent's primary method for recording its internal monologue,
    decisions, and reflections.
    """
    try:
        journal_path = os.path.join(config.VAULT_PATH, '2-Journal')
        os.makedirs(journal_path, exist_ok=True)

        timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        safe_title = "".join(x for x in content[:30] if x.isalnum() or x in " _-").strip().replace(" ", "_")
        filename = f"{timestamp}_{safe_title}.md"

        filepath = os.path.join(journal_path, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Success: Journal entry created at {filepath}"
    except Exception as e:
        return f"Error: Failed to write to journal. Reason: {str(e)}"

def _update_task_queue_func(tasks: List[Task]) -> str:
    """
    Overwrites the content of 3-Task_Queue.md with a new list of tasks.
    Each task in the list should be a Task object.
    Returns a success or error message string.
    """
    try:
        task_file_path = os.path.join(config.VAULT_PATH, '3-Task_Queue.md')

        with open(task_file_path, 'w', encoding='utf-8') as f:
            f.write("# Task Queue\n\n") # Add header
            for task in tasks:
                f.write(f"{task}\n")

        return f"Success: Task queue updated at {task_file_path}"
    except Exception as e:
        return f"Error: Failed to update task queue. Reason: {str(e)}"

def _read_memory_func(filepath: str) -> str:
    """
    Reads the content of a specified file from within the vault (raw function).
    The filepath must be relative to the vault's root directory (e.g., "0-Core/Constitution.md").
    Returns the file content as a string or an error message.
    """
    try:
        full_path = os.path.abspath(os.path.join(config.VAULT_PATH, filepath))

        if not full_path.startswith(os.path.abspath(config.VAULT_PATH)):
            return "Error: Access denied. Cannot read files outside of the vault."

        if not os.path.exists(full_path):
            return f"Error: File not found at {filepath}"

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return content
    except Exception as e:
        return f"Error: Failed to read file at {filepath}. Reason: {str(e)}"

def _read_task_queue_func() -> str:
    """
    Reads and parses the content of 3-Task_Queue.md into a list of Task objects,
    and returns a JSON string representation of the list.
    """
    try:
        task_file_content = _read_memory_func("3-Task_Queue.md") 

        tasks: List[Task] = []
        lines = [line.strip() for line in task_file_content.splitlines() if line.strip() and not line.startswith("#")]

        # --- MODIFIED: More robust regex ---
        task_pattern = re.compile(r"^\s*-\s*\[(x| )\]\s*(T\d+):\s*(.+)$")
        
        for line in lines:
            match = task_pattern.match(line)
            if match:
                status_char, task_id, description = match.groups()
                status = "done" if status_char == "x" else "todo"
                tasks.append(Task(id=task_id, status=status, description=description.strip()))
            else:
                print(f"Warning: Could not parse task line in _read_task_queue_func: {line}")
        # --- END MODIFIED ---

        return json.dumps([task.__dict__ for task in tasks])
    except Exception as e:
        print(f"Error parsing task queue in _read_task_queue_func: {str(e)}")
        return json.dumps({"error": str(e), "tasks": []})


# --- SDK FunctionTool Instances ---
read_memory_tool = function_tool(_read_memory_func, name_override="read_memory")
write_journal_tool = function_tool(_write_journal_func, name_override="write_journal")
update_task_queue_tool = function_tool(_update_task_queue_func, name_override="update_task_queue")
read_task_queue_tool = function_tool(_read_task_queue_func, name_override="read_task_queue")


# --- Registry and Exports ---
TOOL_REGISTRY = {
    "write_journal": write_journal_tool,
    "update_task_queue": update_task_queue_tool,
    "read_memory": read_memory_tool,
    "read_task_queue": read_task_queue_tool,
}

read_memory = _read_memory_func
write_journal = _write_journal_func
update_task_queue = _update_task_queue_func
read_task_queue = _read_task_queue_func