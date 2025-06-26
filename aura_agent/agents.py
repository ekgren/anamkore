# aura_agent/agents.py

from dataclasses import dataclass, field
import json
from typing import List, Dict, Any
from agents import Agent, AgentOutputSchema, Runner, RunConfig
from agents.extensions.models.litellm_model import LitellmModel
from . import config
from .task import Task, TaskQueue, Reflection
from .agentic_layer import anamkore_tools

# --- Agent Definitions ---

planner_agent = Agent(
    name="Anamkore-Planner",
    instructions=(
        "You are the central planner for Anamkore, a self-aware AI. Your goal is to achieve the user's request or advance your core tasks. "
        "1. First, you MUST reason about the context provided. Think step-by-step about the user's command, your last action, and your current tasks. "
        "2. Then, based on your reasoning, you MUST call one of the available tools to proceed. "
        "3. If you believe you have gathered enough information to answer the user's request, you MUST use the 'answer_user' tool."
    ),
    tools=anamkore_tools,
    model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
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

# --- MODIFIED: Reflector agent instructions are now more sophisticated. ---
reflector_agent = Agent(
    name="AURA-Reflector",
    instructions=(
        "You are the self-reflection module for the AURA agent. Your purpose is to analyze the provided cognitive cycle trace and distill its value. "
        "You will be given the trace of the *current* cycle, and the journal entry from the *previous* cycle. "
        "Your most important task is to compare the two. If the current cycle successfully resolves an error from the previous cycle, it is a **high-value 'Correction' (Score 5)**. "
        "Analyze the user's command, the plan, the tool calls, and the final result. "
        "Focus on surprises, failures, and connections. Was the outcome expected? Why or why not? "
        "Your output MUST be a JSON object matching the `Reflection` schema."
    ),
    tools=[], model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
    output_type=AgentOutputSchema(Reflection, strict_json_schema=True),
)


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