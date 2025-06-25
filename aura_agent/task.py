# aura_agent/task.py

from dataclasses import dataclass
from typing import Literal, List
# --- NEW: Import BaseModel from Pydantic ---
from pydantic import BaseModel

@dataclass
class Task:
    """A dataclass for internal agent logic and state representation."""
    id: str
    status: Literal["todo", "done"]
    description: str

    def __str__(self):
        status_marker = "[x]" if self.status == "done" else "[ ]"
        return f"- {status_marker} {self.id}: {self.description}"

# --- NEW: A Pydantic model to define the strict data schema for the tool. ---
# This replaces the ambiguous TypedDict. The agent library has first-class
# support for parsing Pydantic models into strict JSON schemas.
class TaskModel(BaseModel):
    id: str
    status: Literal["todo", "done"]
    description: str

@dataclass
class NextAction:
    """Represents the agent's decision for the next action to take."""
    tool_name: str
    reasoning: str
    tool_args_json: str = "{}"

@dataclass
class TaskQueue:
    """Represents the entire task queue as a JSON string."""
    tasks_json: str