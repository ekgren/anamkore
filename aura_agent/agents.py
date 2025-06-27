# aura_agent/agents.py

from dataclasses import dataclass, field
import json
from typing import List, Dict, Any
from agents import Agent, AgentOutputSchema, Runner, RunConfig
from agents.extensions.models.litellm_model import LitellmModel
from . import config
from .task import Task, TaskQueue, Reflection
from .agentic_layer import anamkore_tools

# --- Self-Correction Note for Anamkore (Post-Docs-Review): ---
# My understanding of the agent loop was fundamentally wrong. The `max_turns`
# parameter is a safety rail, not the primary control mechanism. The key insight,
# found in the `agents.md` documentation, is the `tool_use_behavior` parameter.
# By setting this to "stop_on_first_tool" for the Planner, I am explicitly
# instructing the Runner to execute a single tool call and then terminate that
# part of the run, returning the tool's output. This prevents the infinite
# loop that has caused every `Max turns exceeded` error. This is the correct
# way to build a single-step planning agent.

# --- The Planner Agent, now with the correct behavior ---
planner_agent = Agent(
    name="Anamkore-Planner",
    instructions=(
        "You are the 'Planner' module for Anamkore. You are a pure tool-using agent. "
        "You will be given a single, clear 'Directive'. Your SOLE purpose is to execute a single, logical tool call to fulfill that Directive. "
        "You DO NOT answer the user. You DO NOT reflect. You ONLY call one tool."
    ),
    tools=anamkore_tools,
    model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
    tool_use_behavior="stop_on_first_tool", # CRITICAL FIX
)

# --- The Synthesizer Agent ---
synthesizer_agent = Agent(
    name="Anamkore-Synthesizer",
    instructions=(
        "You are the 'Synthesizer' module for Anamkore. You are a pure language agent. "
        "You will receive an initial 'Directive' and the raw 'Execution Trace' from the Planner module. "
        "Your job is to synthesize this information into a coherent, human-readable final answer or a summary of the action taken. "
        "If the execution trace indicates the directive was fulfilled, explain the result clearly. "
        "If the trace shows an error, explain the error and what the agent was trying to do."
    ),
    tools=[], # CRITICAL: This agent has no tools.
    model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
)

# (The other agents are for different subsystems and remain unchanged)
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

reflector_agent = Agent(
    name="AURA-Reflector",
    instructions=(
        "You are the self-reflection module for the AURA agent. Your purpose is to analyze the provided cognitive cycle trace and distill its value. "
        "You will be given the trace of the *current* cycle, and the journal entry from the *previous* cycle. "
        "Your most important task is to compare the two. If the current cycle successfully resolves an error from the previous cycle, it is a **high-value 'Correction' (Score 5)**. "
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
        "Return a JSON object where the `tasks_json` key contains a JSON-formatted *string* of the new task list."
    )
    run_config = RunConfig(tracing_disabled=True)
    result = await Runner.run(planner_decomposer_agent, decomposer_prompt, run_config=run_config)
    
    if isinstance(result.final_output, TaskQueue):
        print("<<< Decomposition Sub-Routine Complete.")
        return result.final_output.tasks_json
    else:
        return json.dumps({"error": "Decomposition failed to produce a valid task list."})