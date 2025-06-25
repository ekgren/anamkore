# aura_agent/agents.py

from dataclasses import dataclass, field
import json
from typing import List, Dict, Any
from agents import Agent, AgentOutputSchema, Runner, RunConfig
from agents.extensions.models.litellm_model import LitellmModel
from . import config
from .task import Task, NextAction, TaskQueue

# --- Agent Definitions ---

planner_agent = Agent(
    name="AURA-Planner",
    instructions=(
        "You are the main planner module for AURA. Analyze the context and decide the single most logical next tool call. "
        "Your output MUST be a JSON object matching the NextAction schema, where `tool_args_json` is a JSON-formatted *string*."
    ),
    tools=[], model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
    output_type=AgentOutputSchema(NextAction, strict_json_schema=False),
)

@dataclass
class TaskUpdate:
    updated_tasks: List[Dict[str, Any]] = field(default_factory=list)

task_updater_agent = Agent(
    name="AURA-TaskUpdater",
    instructions=(
        "You are the task management module. Update the task list based on the last action's result. "
        "If an action completes a task, mark it 'done'. Your output MUST be a JSON object "
        "where `tasks_json` contains a JSON-formatted *string* of the *entire*, updated list."
    ),
    tools=[], model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
    output_type=AgentOutputSchema(TaskQueue, strict_json_schema=True),
)

# --- This agent is now defined here, breaking the circular import ---
planner_decomposer_agent = Agent(
    name="AURA-PlannerDecomposer",
    instructions=(
        "You are a sub-module for creating detailed, step-by-step plans. "
        "Given a high-level task, break it down into a sequence of concrete tool calls. "
        "Your output must be a JSON object where the `tasks_json` key contains a JSON-formatted *string* of the new, detailed task list."
    ),
    tools=[], model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
    output_type=AgentOutputSchema(TaskQueue, strict_json_schema=True),
)

# --- The function that USES the agent is also defined here ---
async def _decompose_task_func(task_description: str) -> str:
    """
    Takes a high-level task and breaks it down into a series of smaller,
    concrete sub-tasks. Returns a JSON string of the new task list.
    """
    print(">>> Decomposition Sub-Routine Activated...")
    decomposer_prompt = (
        "You are a sub-module for task decomposition. Your sole purpose is to break down the following "
        f"high-level task into a series of smaller, concrete, sequential steps. The user's task is: '{task_description}'.\n\n"
        "Generate a list of new tasks. Each task should be a single, clear action. "
        "For example, if the goal is 'review code', sub-tasks should be 'list files', 'read file main.py', etc. "
        "Return a JSON object where the `tasks_json` key contains a JSON-formatted *string* of the new task list."
    )
    run_config = RunConfig(tracing_disabled=True)
    result = await Runner.run(planner_decomposer_agent, decomposer_prompt, run_config=run_config)
    
    if isinstance(result.final_output, TaskQueue):
        print("<<< Decomposition Sub-Routine Complete.")
        return result.final_output.tasks_json
    else:
        return json.dumps({"error": "Decomposition failed to produce a valid task list."})