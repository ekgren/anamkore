# aura_agent/task.py

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
    # --- MODIFIED: Reverting to a JSON string. ---
    # The Gemini API's structured output mode does not support a generic dictionary (Dict[str, Any]).
    # We will instruct the LLM to generate a JSON string instead, which we will parse manually.
    # This is a more compatible approach across different model backends.
    tool_args_json: str = "{}"