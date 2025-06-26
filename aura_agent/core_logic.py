# aura_agent/core_logic.py

import os
import re
import json
from datetime import datetime
from typing import List
from . import config
from .task import Task, TaskModel

# ---
# Self-Correction Note for Anamkore:
# The previous pathing logic was fundamentally flawed. It assumed all paths were
# relative to the project root, not the vault root. This version corrects all
# file operations to be based on the `config.VAULT_PATH`, ensuring the agent
# correctly interacts with its memory.
# ---

def _get_sandboxed_path(relative_path: str) -> str:
    """A simplified but crucial sandboxing function to ensure path safety."""
    if ".." in relative_path:
        raise ValueError("Path traversal is not allowed.")
    return os.path.abspath(os.path.join(config.VAULT_PATH, relative_path))

def _list_files(path: str) -> str:
    full_path = _get_sandboxed_path(path)
    try:
        if not os.path.isdir(full_path): return f"Error: '{path}' is not a valid directory."
        return json.dumps(os.listdir(full_path))
    except Exception as e: return f"Error listing files in '{path}': {str(e)}"

def _read_file(path: str) -> str:
    full_path = _get_sandboxed_path(path)
    try:
        if not os.path.exists(full_path): return f"Error: File not found at '{path}'."
        if not os.path.isfile(full_path): return f"Error: Path '{path}' is a directory."
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f: return f.read()
    except Exception as e: return f"Error reading file '{path}': {str(e)}"

def _write_file(path: str, content: str, overwrite: bool = False) -> str:
    allowed_dirs = ['1-Inbox', '2-Journal', 'Knowledge']
    if not any(path.startswith(d) for d in allowed_dirs):
        return f"Error: Access denied. Can only write to {allowed_dirs} directories inside the vault."
    full_path = _get_sandboxed_path(path)
    try:
        if not overwrite and os.path.exists(full_path):
            return f"Error: File '{path}' already exists. Use overwrite=True."
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f: f.write(content)
        return f"Success: Wrote {len(content)} bytes to '{path}'."
    except Exception as e: return f"Error writing to file '{path}': {str(e)}"

def _search_code(query: str) -> str:
    matches = []
    try:
        for root, _, files in os.walk(config.CODE_PATH):
            if any(d in root for d in ['.git', '__pycache__', 'vault']): continue
            for file in files:
                if file.endswith(('.py', '.md', '.toml')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            for i, line in enumerate(f, 1):
                                if query in line:
                                    matches.append({"file": os.path.relpath(filepath, config.CODE_PATH), "line": i, "content": line.strip()})
                    except IOError: continue
        return json.dumps(matches, indent=2)
    except Exception as e: return f"Error searching code: {str(e)}"

def _write_journal(content: str) -> str:
    safe_title = "".join(x for x in content[:30] if x.isalnum() or x in " _-").strip().replace(" ", "_")
    filename = f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_{safe_title}.md"
    return _write_file(os.path.join('2-Journal', filename), content)

def _get_latest_journal_entry(summary_only: bool = False) -> str:
    """Gets the latest journal entry. Can return full entry or summary only."""
    journal_path = '2-Journal'
    full_journal_path = _get_sandboxed_path(journal_path)
    try:
        if not os.path.exists(full_journal_path): return "No journal entries found."
        files = os.listdir(full_journal_path)
        if not files: return "No journal entries found."
        journal_files = sorted([f for f in files if f.endswith('.md')], reverse=True)
        if not journal_files: return "No journal entries found."
        
        latest_entry_content = _read_file(os.path.join(journal_path, journal_files[0]))
        
        if summary_only:
            # --- NEW: Logic to extract only the summary part of the journal ---
            summary_match = re.search(r"## Reflection & Synthesis\n(.*?)\n## Full Trace", latest_entry_content, re.DOTALL)
            if summary_match:
                # Add user command for context
                command_match = re.search(r"\*\*User Command:\*\* (.*)", latest_entry_content)
                user_command = command_match.group(1).strip() if command_match else "None"
                return f"Last User Command: {user_command}\nLast Reflection:\n{summary_match.group(1).strip()}"
            else:
                # Fallback for critical failure logs that don't have the full structure
                return "\n".join(latest_entry_content.splitlines()[:10]) # Return first 10 lines
        
        return latest_entry_content
    except Exception as e: return f"Error reading latest journal entry: {e}"

def _read_task_queue() -> str:
    content = _read_file("3-Task_Queue.md")
    if content.startswith("Error:"): return json.dumps({"error": content, "tasks": []})
    tasks: List[Task] = []
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
    task_pattern = re.compile(r"^\s*-\s*\[(x| )\]\s*(T\d+):\s*(.+)$")
    for line in lines:
        match = task_pattern.match(line)
        if match:
            status_char, task_id, description = match.groups()
            tasks.append(Task(id=task_id, status="done" if status_char == "x" else "todo", description=description.strip()))
    return json.dumps([task.__dict__ for task in tasks])

def _update_task_queue(tasks: List[TaskModel]) -> str:
    try:
        task_objects = [Task(id=t.id, status=t.status, description=t.description) for t in tasks]
        content = "# Task Queue\n\n" + "\n".join(str(t) for t in task_objects)
        return _write_file("3-Task_Queue.md", content, overwrite=True)
    except Exception as e: return f"Error: Invalid task data provided. Details: {e}"

def _answer_user(answer: str) -> str:
    print(f"\n[ANAMKORE]: {answer}")
    return "Success: Answer provided to the user."