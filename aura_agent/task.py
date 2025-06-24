# aura_agent/task.py

from dataclasses import dataclass, field
from typing import Literal, Dict, Any, List

@dataclass
class Task:
    """Represents a single task in the agent's task queue."""
    id: str
    status: Literal["todo", "done"]
    description: str

    def __str__(self):
        status_marker = "[x]" if self.status == "done" else "[ ]"
        return f"- {status_marker} {self.id}: {self.description}"

@dataclass
class NextAction:
    """Represents the agent's decision for the next action to take."""
    tool_name: str
    reasoning: str
    tool_args_json: str = "{}"

# --- NEW: A dedicated dataclass for the Task Updater Agent's output ---
# This will hold the entire task list as a single JSON formatted string.
@dataclass
class TaskQueue:
    """Represents the entire task queue as a JSON string."""
    tasks_json: str