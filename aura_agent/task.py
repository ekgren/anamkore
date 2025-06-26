# aura_agent/task.py

from dataclasses import dataclass
from typing import Literal, List, Optional
# --- NEW: Import BaseModel and Field from Pydantic ---
from pydantic import BaseModel, Field

@dataclass
class Task:
    """A dataclass for internal agent logic and state representation."""
    id: str
    status: Literal["todo", "done"]
    description: str

    def __str__(self):
        status_marker = "[x]" if self.status == "done" else "[ ]"
        return f"- {status_marker} {self.id}: {self.description}"

class TaskModel(BaseModel):
    """A Pydantic model to define the strict data schema for the tool."""
    id: str
    status: Literal["todo", "done"]
    description: str

@dataclass
class TaskQueue:
    """Represents the entire task queue as a JSON string."""
    tasks_json: str

# --- NEW: The Pydantic model for a structured cognitive reflection. ---
class Reflection(BaseModel):
    """A structured reflection on a completed cognitive cycle."""
    summary: str = Field(description="A one-sentence summary of what was attempted and the outcome.")
    value_score: int = Field(description="An integer from 1 (trivial) to 5 (transformative) representing the learning value of this cycle.")
    value_type: Literal["Correction", "Insight", "Hypothesis", "Synthesis", "Execution", "Routine"] = Field(description="The primary category of value for this cycle.")
    key_learning: str = Field(description="The single most important lesson, insight, or correction from the cycle. If a value_score is less than 3, this can be 'N/A'.")
    new_tasks_proposed: Optional[List[str]] = Field(default=None, description="A list of new task descriptions proposed as a result of this learning.")