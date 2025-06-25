# aura_agent/tools.py

import os
import re
import json
from datetime import datetime
from typing import List
from . import config
from .task import Task
from .fs_utils import read_file, write_file, list_files

# --- High-Level Cognitive & Communication Tools ---

def answer_user(answer: str) -> str:
    """
    Provides a direct, final answer to the user in the console.
    """
    print(f"\n[AURA]: {answer}")
    return "Success: Answer provided to the user."

def search_code(query: str) -> str:
    """Performs a text search across the agent's source code."""
    matches = []
    try:
        for root, _, files in os.walk(config.CODE_PATH):
            if any(d in root for d in ['.git', '__pycache__', 'vault']): continue
            for file in files:
                if file.endswith(('.py', '.md', '.toml')):
                    filepath = os.path.join(root, file)
                    try:
                        # --- FIX: Changed the open() call to use keyword arguments for encoding and errors ---
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            for i, line in enumerate(f, 1):
                                if query in line:
                                    matches.append({"file": os.path.relpath(filepath, config.CODE_PATH), "line": i, "content": line.strip()})
                    except IOError: continue
        return json.dumps(matches, indent=2)
    except Exception as e: return f"Error searching code: {str(e)}"

def write_journal(content: str) -> str:
    """Writes a timestamped entry to the agent's journal."""
    safe_title = "".join(x for x in content[:30] if x.isalnum() or x in " _-").strip().replace(" ", "_")
    filename = f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}_{safe_title}.md"
    return write_file(os.path.join('2-Journal', filename), content)

def get_latest_journal_entry() -> str:
    """
    Finds and returns the content of the most recent journal entry.
    """
    journal_path = '2-Journal'
    try:
        files_json = list_files(journal_path)
        if files_json.startswith("Error:"):
            return "No journal entries found."
        
        files = json.loads(files_json)
        if not files:
            return "No journal entries found."
        
        journal_files = sorted([f for f in files if f.endswith('.md')], reverse=True)
        if not journal_files:
            return "No journal entries found."
            
        latest_entry_path = os.path.join(journal_path, journal_files[0])
        return read_file(latest_entry_path)
    except Exception as e:
        return f"Error reading latest journal entry: {e}"

def read_task_queue() -> str:
    """Reads and parses the task queue markdown file into JSON."""
    content = read_file("3-Task_Queue.md")
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

def update_task_queue(tasks: List[dict]) -> str:
    """Overwrites the task queue with a new list of tasks."""
    try:
        task_objects = [Task(**task_data) for task_data in tasks]
        content = "# Task Queue\n\n" + "\n".join(str(t) for t in task_objects)
        return write_file("3-Task_Queue.md", content, overwrite=True)
    except Exception as e:
        return f"Error: Invalid task data provided. Details: {e}"