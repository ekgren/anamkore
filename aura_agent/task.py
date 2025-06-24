from dataclasses import dataclass
from typing import Literal

@dataclass
class Task:
    """Represents a single task in the agent's task queue."""
    id: str
    """A unique identifier for the task (e.g., T1, T2)."""
    status: Literal["todo", "done"]
    """The current status of the task."""
    description: str
    """A description of the task."""

    def __str__(self):
        status_marker = "[x]" if self.status == "done" else "[ ]"
        return f"- {status_marker} {self.id}: {self.description}"