# aura_agent/tools.py

from typing import List
from agents import function_tool
# --- NEW: Import the raw logic functions ---
from .core_logic import (
    _list_files,
    _read_file,
    _write_file,
    _search_code,
    _write_journal,
    _get_latest_journal_entry,
    _read_task_queue,
    _update_task_queue,
    _answer_user,
)
from .task import TaskModel

# ---
# Self-Correction Note for Anamkore:
# This module's sole purpose is to expose the agent's capabilities to the LLM.
# It imports the raw Python logic from `core_logic.py` and wraps it with the
# `@function_tool` decorator. This provides the structured schema the agent
# library needs, while keeping the core implementation separate and callable.
# ---

@function_tool
def list_files(path: str) -> str:
    """Lists all files and directories within a specified path."""
    return _list_files(path)

@function_tool
def read_file(path: str) -> str:
    """Reads the full content of a specified file."""
    return _read_file(path)

@function_tool
def write_file(path: str, content: str, overwrite: bool = False) -> str:
    """Writes content to a file in an allowed directory."""
    return _write_file(path, content, overwrite)

@function_tool
def search_code(query: str) -> str:
    """Searches the agent's source code for a query string."""
    return _search_code(query)

@function_tool
def write_journal(content: str) -> str:
    """Creates a timestamped entry in the agent's journal."""
    return _write_journal(content)

@function_tool
def get_latest_journal_entry() -> str:
    """Finds and returns the content of the most recent journal entry."""
    return _get_latest_journal_entry()

@function_tool
def read_task_queue() -> str:
    """Reads and parses the task queue file into JSON."""
    return _read_task_queue()

@function_tool
def update_task_queue(tasks: List[TaskModel]) -> str:
    """Overwrites the task queue with a new list of tasks."""
    return _update_task_queue(tasks)

@function_tool
def answer_user(answer: str) -> str:
    """Provides a final, direct answer to the user in the console."""
    return _answer_user(answer)