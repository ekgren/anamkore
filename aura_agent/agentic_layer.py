# aura_agent/agentic_layer.py

import os
import re
import json
from datetime import datetime
from typing import List
from . import config
from .task import Task

# --- Sandboxing Logic ---
SANDBOX_MAP = {
    "aura_agent": config.CODE_PATH, "README.md": config.CODE_PATH, "pyproject.toml": config.CODE_PATH, ".python-version": config.CODE_PATH,
    "0-Core": config.VAULT_PATH, "1-Inbox": config.VAULT_PATH, "2-Journal": config.VAULT_PATH,
    "3-Task_Queue.md": config.VAULT_PATH, "4-Async_Mailbox.md": config.VAULT_PATH, "Knowledge": config.VAULT_PATH,
}

def _get_sandboxed_path(relative_path: str) -> str | None:
    normalized_path = os.path.normpath(relative_path)
    if os.path.isabs(normalized_path) or ".." in normalized_path.split(os.sep):
        return None
    
    first_part = normalized_path.split(os.sep)[0]
    if first_part == '.': # Allow current directory reference
        base_path = config.VAULT_PATH
    else:
        base_path = SANDBOX_MAP.get(first_part)

    if not base_path: return None
        
    full_path = os.path.abspath(os.path.join(base_path, normalized_path))
    
    if os.path.commonpath([base_path, full_path]) != base_path:
        return None
        
    return full_path

# --- Core Tool Functions ---

def _list_files_func(path: str) -> str:
    """Lists files and directories within a given path, sandboxed to the vault or code directories."""
    full_path = _get_sandboxed_path(path)
    if not full_path:
        return f"Error: Access denied or invalid path '{path}'."

    try:
        if not os.path.isdir(full_path):
            return f"Error: '{path}' is not a valid directory."
        files = os.listdir(full_path)
        return json.dumps(files)
    except Exception as e:
        return f"Error listing files in '{path}': {str(e)}"

# --- MODIFIED: Renamed 'filepath' to 'path' ---
def _read_file_func(path: str) -> str:
    """Reads the content of a specified file from within the vault or code directory."""
    full_path = _get_sandboxed_path(path)
    if not full_path:
        return f"Error: Access denied or invalid path '{path}'."
    
    try:
        if not os.path.exists(full_path):
            return f"Error: File not found at '{path}'."
        if not os.path.isfile(full_path):
            return f"Error: Path '{path}' is a directory, not a file."
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file '{path}': {str(e)}"

# --- MODIFIED: Renamed 'filepath' to 'path' ---
def _write_file_func(path: str, content: str, overwrite: bool = False) -> str:
    """Writes or overwrites a file within the vault or code directory."""
    full_path = _get_sandboxed_path(path)
    if not full_path:
        return f"Error: Access denied or invalid path '{path}'."

    try:
        if not overwrite and os.path.exists(full_path):
            return f"Error: File '{path}' already exists. Use overwrite=True to replace it."
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: Wrote {len(content)} bytes to '{path}'."
    except Exception as e:
        return f"Error writing to file '{path}': {str(e)}"

def _search_code_func(query: str) -> str:
    matches = []
    code_path = os.path.abspath(config.CODE_PATH)
    try:
        for root, _, files in os.walk(code_path):
            if '.git' in root or '__pycache__' in root or 'vault' in root:
                continue
            for file in files:
                if file.endswith(('.py', '.md', '.toml')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                if query in line:
                                    relative_path = os.path.relpath(filepath, code_path)
                                    matches.append({"file": relative_path, "line": line_num, "content": line.strip()})
                    except IOError: continue
        return json.dumps(matches, indent=2)
    except Exception as e: return f"Error searching code: {str(e)}"

def _write_journal_func(content: str) -> str:
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    safe_title = "".join(x for x in content[:30] if x.isalnum() or x in " _-").strip().replace(" ", "_")
    filename = f"{timestamp}_{safe_title}.md"
    return _write_file_func(os.path.join('2-Journal', filename), content)

def _read_task_queue_func() -> str:
    content = _read_file_func("3-Task_Queue.md")
    if content.startswith("Error:"): return json.dumps({"error": content, "tasks": []})
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
    try:
        task_objects = [Task(**task_data) for task_data in tasks]
        content = "# Task Queue\n\n" + "\n".join(str(t) for t in task_objects)
        return _write_file_func("3-Task_Queue.md", content, overwrite=True)
    except (TypeError, KeyError) as e:
        return f"Error: Invalid task data provided. Each task must be a dictionary with 'id', 'status', and 'description'. Details: {e}"

raw_tool_functions = {
    "list_files": _list_files_func, "read_file": _read_file_func, "write_file": _write_file_func,
    "search_code": _search_code_func, "write_journal": _write_journal_func,
    "read_task_queue": _read_task_queue_func, "update_task_queue": _update_task_queue_func,
}