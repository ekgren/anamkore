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
        "where `tasks_json` is a JSON-formatted *string* of the *entire*, updated list."
    ),
    tools=[], model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
    output_type=AgentOutputSchema(TaskQueue, strict_json_schema=True),
)

async def perform_cognitive_step(user_command: str | None = None):
    # 1. Read core state
    constitution_content = raw_tool_functions['read_file']("0-Core/Constitution.md")
    tools_content = raw_tool_functions['read_file']("0-Core/Tools.md")
    task_queue_json_content = raw_tool_functions['read_task_queue']()

    if "Error:" in constitution_content:
        raise RuntimeError(f"CRITICAL: Could not read Constitution: {constitution_content}")
    if "Error:" in tools_content:
        raise RuntimeError(f"CRITICAL: Could not read Tools.md: {tools_content}")

    # 2. Planning Pass
    user_input_section = f"### High-Priority User Command:\n{user_command}\n\n" if user_command else ""
    
    planning_prompt = (
        f"{user_input_section}"
        "### Constitution:\n"
        f"{constitution_content}\n\n"
        "### Current Task Queue (JSON):\n"
        f"```json\n{task_queue_json_content}\n```\n\n"
        "--- Standard Operating Procedures (SOPs) ---\n"
        "1.  **User Interaction:** If the user asks a question, your final action MUST be to use `answer_user` to respond directly.\n"
        "2.  **Task Management:** To update a task, first `read_task_queue`, construct the *entire new list of tasks*, then call `update_task_queue` with the complete list.\n"
        "3.  **File Operations:** To create a file, use `write_file`. Do NOT `read_file` first if you know the file doesn't exist. Use the exact argument names provided.\n\n"
        "--- AVAILABLE TOOLS ---\n"
        "You have the following tools. You MUST use the exact `tool_name` and the exact argument names specified in the function signatures.\n"
        "```markdown\n"
        f"{tools_content}\n"
        "```\n\n"
        "--- INSTRUCTIONS ---\n"
        "Analyze the context and follow the SOPs. Prioritize the user command. Determine the single best tool call to execute now. "
        "Output ONLY the JSON for the `NextAction`, ensuring `tool_args_json` is a valid JSON string."
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
            tool_args = json.loads(action_to_take.tool_args_json) if action_to_take.tool_args_json else {}
            print(f">>> Executing Tool: `{action_to_take.tool_name}` with args: {tool_args}")
            result = tool_function(**tool_args)
            execution_result = await result if asyncio.iscoroutine(result) else result
        except Exception as e:
            execution_result = f"Error executing tool '{action_to_take.tool_name}': {e}"

    print(f"<<< Execution Result (truncated): {execution_result[:200]}...")

    if execution_result.startswith("Error:"):
        if action_to_take.tool_name != 'answer_user':
             raw_tool_functions['answer_user'](f"I encountered an error trying to perform your request: {execution_result}")
        journal_entry = (f"# Cognitive Cycle FAILURE...\n**Execution Result:**\n```\n{execution_result}\n```\n")
        _write_journal_func(journal_entry)
        print("Journaling complete. Halting cycle due to error.")
        return

    # --- NEW: Synthesis Pass ---
    # If the first action was a successful read operation in response to a user,
    # perform a second pass to synthesize the answer.
    if user_command and action_to_take.tool_name in ["read_file", "list_files", "search_code"]:
        print(">>> Synthesis Pass: Deciding how to answer the user...")
        synthesis_prompt = (
            f"### User's Original Question:\n{user_command}\n\n"
            f"### Result from Initial Action (`{action_to_take.tool_name}`):\n"
            f"```\n{execution_result}\n```\n\n"
            "--- INSTRUCTIONS ---\n"
            "You have successfully retrieved the information needed. Your final step is to present this to the user. "
            "Use the `answer_user` tool. Summarize the result if it is long, but present the full content if it is short and directly answers the question. "
            "Your output must be a single `answer_user` tool call."
        )
        synthesis_result = await Runner.run(planner_agent, synthesis_prompt, run_config=run_config, max_turns=2)
        
        if isinstance(synthesis_result.final_output, NextAction) and synthesis_result.final_output.tool_name == 'answer_user':
            action_to_take = synthesis_result.final_output
            tool_args = json.loads(action_to_take.tool_args_json)
            print(f">>> Executing Synthesized Action: `{action_to_take.tool_name}`")
            execution_result = raw_tool_functions['answer_user'](**tool_args)
        else:
            print("<<< Synthesis Failed: Could not determine how to answer. Responding with raw data.")
            raw_tool_functions['answer_user'](execution_result)

    # 4. Task Update (Only run if not a user-facing answer)
    if action_to_take.tool_name == 'answer_user':
        task_update_log_entry = "No task update needed; answered user directly."
        print(f"<<< {task_update_log_entry}")
    else:
        # ... (Task update logic remains the same)
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
        if not isinstance(task_update_result.final_output, TaskQueue):
            task_update_log_entry = f"Task Update Failed: Updater agent did not return valid TaskQueue object. Result: {task_update_result.final_output}"
        else:
            try:
                updated_tasks_list = json.loads(task_update_result.final_output.tasks_json)
                update_status = raw_tool_functions['update_task_queue'](updated_tasks_list)
                task_update_log_entry = f"Task queue updated. Status: {update_status}"
            except Exception as e:
                task_update_log_entry = f"Task Update Failed: Could not process updater response. Error: {e}"
        print(f"<<< {task_update_log_entry}")


    # 5. Journaling Step
    journal_entry = (
        f"# Cognitive Cycle: {datetime.now().isoformat()}\n\n"
        f"**User Command:** {user_command or 'None'}\n\n"
        f"**Final Action:** `{action_to_take.tool_name}`\n\n"
        f"**Reasoning:** {action_to_take.reasoning}\n\n"
        f"**Arguments JSON String:**\n```json\n{action_to_take.tool_args_json}\n```\n\n"
        f"**Execution Result:**\n```\n{execution_result}\n```\n\n"
    )
    
    journal_result = _write_journal_func(journal_entry)
    print(f"Journaling complete: {journal_result}")