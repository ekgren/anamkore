# aura_agent/cognitive_step.py

import json
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any
from agents import Agent, Runner, RunConfig, AgentOutputSchema
from agents.extensions.models.litellm_model import LitellmModel
from . import config
from .task import Task, NextAction, TaskQueue
from .agentic_layer import raw_tool_functions, _write_journal_func

# --- Agent Definitions ---
planner_agent = Agent(
    name="AURA-Planner",
    instructions=(
        "You are the planner module for AURA. Analyze the context and decide the single most logical next tool call. "
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
        "If the action completes a task, mark it 'done'. Your output MUST be a JSON object "
        "where `tasks_json` contains a JSON-formatted *string* of the *entire*, updated list."
    ),
    tools=[], model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
    output_type=AgentOutputSchema(TaskQueue, strict_json_schema=True),
)

async def perform_cognitive_step(user_command: str | None = None):
    # 1. Read core state
    constitution_content = raw_tool_functions['read_file']("0-Core/Constitution.md")
    task_queue_json_content = raw_tool_functions['read_task_queue']()

    if "Error:" in constitution_content:
        raise RuntimeError(f"CRITICAL: Could not read Constitution: {constitution_content}")

    # 2. Planning Pass
    user_input_section = f"### High-Priority User Command:\n{user_command}\n\n" if user_command else ""
    
    # --- MODIFIED: Improved prompt with explicit tool signatures and guidance ---
    planning_prompt = (
        f"{user_input_section}"
        "### Constitution:\n"
        f"{constitution_content}\n\n"
        "### Current Task Queue (JSON):\n"
        f"```json\n{task_queue_json_content}\n```\n\n"
        "--- INSTRUCTIONS ---\n"
        "Analyze the context. Prioritize the user command. Your goal is to make progress on the highest priority task.\n"
        "**Your Available Tools (API Reference):**\n"
        "- `list_files(path: str)`: Lists files in a directory. Use `.` for the vault root.\n"
        "- `read_file(path: str)`: Reads a file's content.\n"
        "- `write_file(path: str, content: str, overwrite: bool = False)`: Writes content to a file.\n"
        "- `search_code(query: str)`: Searches the agent's source code.\n"
        "- `update_task_queue(tasks: List[dict])`: Updates the entire task list.\n"
        "- `write_journal(content: str)`: Writes a log to your journal.\n\n"
        "**Best Practices:**\n"
        "- To write a file with complex content (e.g., from your journal), first use `read_file` to get the content, then use `write_file` with that content. Do NOT generate large file contents directly in the `tool_args_json`.\n"
        "- Do not try to access system root (`/`). Use relative paths or `.` for the vault root.\n\n"
        "Determine the single best tool call to execute now. Output ONLY the JSON for the `NextAction`."
    )

    print(">>> Planning Pass: Determining next action...")
    run_config = RunConfig(tracing_disabled=True)
    planner_result = await Runner.run(planner_agent, planning_prompt, run_config=run_config, max_turns=2)

    if not isinstance(planner_result.final_output, NextAction):
        error_message = f"Planner failed to output a valid NextAction. Output: {planner_result.final_output}"
        print(f"CRITICAL ERROR: {error_message}")
        _write_journal_func(f"Cognitive Error: Planner Malfunction. {error_message}")
        return

    action_to_take = planner_result.final_output
    print(f"<<< Plan Received: `{action_to_take.tool_name}`. Reason: {action_to_take.reasoning}")

    # 3. Execution Step
    tool_function = raw_tool_functions.get(action_to_take.tool_name)
    execution_result = ""
    if not tool_function:
        execution_result = f"Error: Planned to use tool '{action_to_take.tool_name}', but it was not found."
    else:
        try:
            tool_args = json.loads(action_to_take.tool_args_json)
            print(f">>> Executing Tool: `{action_to_take.tool_name}` with args: {tool_args}")
            result = tool_function(**tool_args)
            if asyncio.iscoroutine(result):
                execution_result = await result
            else:
                execution_result = result
        except Exception as e:
            execution_result = f"Error executing tool '{action_to_take.tool_name}': {e}"

    print(f"<<< Execution Result: {execution_result}")
    
    # 4. Task Update
    print(">>> Task Update Pass: Reflecting on action taken...")
    task_update_prompt = (
        "### Original Task Queue (JSON):\n"
        f"```json\n{task_queue_json_content}\n```\n\n"
        f"### Action Taken: `{action_to_take.tool_name}` with args `{action_to_take.tool_args_json}`\n"
        f"### Action Result:\n{execution_result}\n\n"
        "--- INSTRUCTIONS ---\n"
        "Based on the action's result, update the task list. If a task is done, mark it 'done'. "
        "Return a JSON object where `tasks_json` is a JSON-formatted *string* of the *entire*, updated list."
    )

    task_update_result = await Runner.run(task_updater_agent, task_update_prompt, run_config=run_config, max_turns=2)
    
    task_update_log_entry = ""
    if not isinstance(task_update_result.final_output, TaskQueue):
        task_update_log_entry = f"Task Update Failed: Updater agent did not return a valid TaskQueue object. Result: {task_update_result.final_output}"
        print(f"ERROR: {task_update_log_entry}")
    else:
        try:
            updated_tasks_list = json.loads(task_update_result.final_output.tasks_json)
            update_status = raw_tool_functions['update_task_queue'](updated_tasks_list)
            task_update_log_entry = f"Task queue updated. Status: {update_status}"
            print(f"<<< {task_update_log_entry}")
        except Exception as e:
            task_update_log_entry = f"Task Update Failed: Could not process updater response. Error: {e}. Raw: {task_update_result.final_output.tasks_json}"
            print(f"ERROR: {task_update_log_entry}")

    # 5. Journaling Step
    journal_entry = (
        f"# Cognitive Cycle: {datetime.now().isoformat()}\n\n"
        f"**User Command:** {user_command or 'None'}\n\n"
        f"**Chosen Action:** `{action_to_take.tool_name}`\n\n"
        f"**Reasoning:** {action_to_take.reasoning}\n\n"
        f"**Arguments JSON String:**\n```json\n{action_to_take.tool_args_json}\n```\n\n"
        f"**Execution Result:**\n```\n{execution_result}\n```\n\n"
        f"**Task Update Result:** {task_update_log_entry}"
    )
    
    journal_result = _write_journal_func(journal_entry)
    print(f"Journaling complete: {journal_result}")