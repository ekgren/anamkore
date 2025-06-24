from dataclasses import dataclass, field
from typing import Literal, Dict, Any

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
    # This will now be a JSON string, not a dictionary.
    tool_args_json: str = "{}"