# aura_agent/agentic_layer.py

import os
import re
import json
from datetime import datetime
from typing import List
from agents import function_tool
from . import config
from .task import Task

# --- Helper function for security ---
def _is_path_safe(base_path: str, target_path: str) -> bool:
    """Checks if the target_path is within the allowed base_path."""
    abs_base = os.path.abspath(base_path)
    # --- MODIFIED: Correctly join the base path BEFORE resolving the absolute path. ---
    # This prevents the target_path from being resolved relative to the
    # current working directory, fixing the bug where files were created outside the vault.
    abs_target = os.path.abspath(os.path.join(abs_base, target_path))
    return os.path.commonpath([abs_base, abs_target]) == abs_base

# --- NEW & IMPROVED Raw Tool Functions ---

def _list_files_func(path: str) -> str:
    """
    Lists files and directories within a given path, sandboxed to the vault or code directories.
    """
    # Determine the correct base directory (code or vault)
    if _is_path_safe(config.CODE_PATH, path):
        base = config.CODE_PATH
    elif _is_path_safe(config.VAULT_PATH, path):
        base = config.VAULT_PATH
    else:
        # Fallback to vault path if path is simple (e.g., ".")
        # This is a safe fallback for top-level directory listing.
        base = config.VAULT_PATH
        if not _is_path_safe(base, path):
             return f"Error: Access denied. Path '{path}' is outside of the allowed directories."

    try:
        full_path = os.path.join(base, path)
        if not os.path.isdir(full_path):
            return f"Error: '{path}' is not a valid directory."
        
        files = os.listdir(full_path)
        return json.dumps(files)
    except Exception as e:
        return f"Error listing files in '{path}': {str(e)}"

def _read_file_func(filepath: str) -> str:
    """
    Reads the content of a specified file from within the vault or code directory.
    """
    # Determine the correct base directory
    if _is_path_safe(config.CODE_PATH, filepath):
        base = config.CODE_PATH
    elif _is_path_safe(config.VAULT_PATH, filepath):
        base = config.VAULT_PATH
    else:
        return f"Error: Access denied. Cannot read file '{filepath}'."

    try:
        full_path = os.path.join(base, filepath)
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found at '{filepath}'."
    except Exception as e:
        return f"Error reading file '{filepath}': {str(e)}"

def _write_file_func(filepath: str, content: str, overwrite: bool = False) -> str:
    """
    Writes or overwrites a file within the vault or code directory.
    """
    # Determine the correct base directory
    if _is_path_safe(config.CODE_PATH, filepath):
        base = config.CODE_PATH
    elif _is_path_safe(config.VAULT_PATH, filepath):
        base = config.VAULT_PATH
    else:
        # Default to vault for new file creation if path is simple
        base = config.VAULT_PATH
        if not _is_path_safe(base, filepath):
            return f"Error: Access denied. Cannot write to file '{filepath}'."

    try:
        full_path = os.path.join(base, filepath)
        if not overwrite and os.path.exists(full_path):
            return f"Error: File '{filepath}' already exists. Use overwrite=True to replace it."
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: Wrote {len(content)} bytes to '{filepath}'."
    except Exception as e:
        return f"Error writing to file '{filepath}': {str(e)}"

def _search_code_func(query: str) -> str:
    """
    Performs a simple text search across all files in the agent's source code directory.
    """
    matches = []
    try:
        for root, _, files in os.walk(config.CODE_PATH):
            if '.git' in root or '__pycache__' in root or 'vault' in root:
                continue
            for file in files:
                if file.endswith(('.py', '.md', '.txt', '.toml')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            for line_num, line in enumerate(f, 1):
                                if query in line:
                                    relative_path = os.path.relpath(filepath, config.CODE_PATH)
                                    matches.append({
                                        "file": relative_path,
                                        "line": line_num,
                                        "content": line.strip()
                                    })
                    except (IOError, UnicodeDecodeError):
                        continue # Skip files we can't read
        return json.dumps(matches, indent=2)
    except Exception as e:
        return f"Error searching code: {str(e)}"

# --- Existing Functions (Kept for compatibility for now) ---
def _write_journal_func(content: str) -> str:
    # Ensure journal entries are always written to the vault
    journal_dir = os.path.join(config.VAULT_PATH, '2-Journal')
    os.makedirs(journal_dir, exist_ok=True)
    filename = f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.md"
    return _write_file_func(os.path.join('2-Journal', filename), content)

def _read_task_queue_func() -> str:
    content = _read_file_func("3-Task_Queue.md")
    if content.startswith("Error:"):
        return json.dumps({"error": content, "tasks": []})
    
    tasks: List[Task] = []
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
    task_pattern = re.compile(r"^\s*-\s*\[(x| )\]\s*(T\d+):\s*(.+)$")
    
    for line in lines:
        match = task_pattern.match(line)
        if match:
            status_char, task_id, description = match.groups()
            status = "done" if status_char == "x" else "todo"
            tasks.append(Task(id=task_id, status=status, description=description.strip()))
    return json.dumps([task.__dict__ for task in tasks])

def _update_task_queue_func(tasks: List[dict]) -> str:
    """Takes a list of task dictionaries and writes them to the queue."""
    task_objects = [Task(**task_data) for task_data in tasks]
    content = "# Task Queue\n\n" + "\n".join(str(t) for t in task_objects)
    return _write_file_func("3-Task_Queue.md", content, overwrite=True)

# The definitive dictionary of all available raw functions
raw_tool_functions = {
    "list_files": _list_files_func,
    "read_file": _read_file_func,
    "write_file": _write_file_func,
    "search_code": _search_code_func,
    "write_journal": _write_journal_func,
    "read_task_queue": _read_task_queue_func,
    "update_task_queue": _update_task_queue_func,
}