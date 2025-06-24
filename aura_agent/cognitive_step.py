# aura_agent/cognitive_step.py

import json
import asyncio
from datetime import datetime
from agents import Agent, Runner, RunConfig, AgentOutputSchema
from agents.extensions.models.litellm_model import LitellmModel
from . import config
from .task import NextAction
from .agentic_layer import raw_tool_functions, _write_journal_func

# Planner Agent Definition
planner_agent = Agent(
    name="AURA-Planner",
    instructions=(
        "You are the planner module for the AURA agent. Your sole responsibility is to analyze "
        "the provided context (Constitution, Task Queue, User Input) and decide the single most logical next tool "
        "call to make progress. Your output MUST be a JSON object corresponding to the NextAction schema, "
        "where `tool_args_json` is a JSON-formatted *string* containing the arguments for the chosen tool."
    ),
    tools=[],
    model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
    output_type=AgentOutputSchema(NextAction, strict_json_schema=False),
)

async def perform_cognitive_step(user_command: str | None = None):
    """
    Executes a single cognitive step, now with optional direct user input.
    """
    # 1. Read core state from the vault
    constitution_content = raw_tool_functions['read_file']("0-Core/Constitution.md")
    task_queue_json_content = raw_tool_functions['read_task_queue']()

    if "Error:" in constitution_content:
        raise RuntimeError(f"CRITICAL: Could not read Constitution: {constitution_content}")

    # --- MODIFIED: Integrate user command into the prompt ---
    user_input_section = f"### High-Priority User Command:\n{user_command}\n\n" if user_command else ""

    # 2. Planning Pass: Construct prompt and run the Planner Agent
    planning_prompt = (
        f"{user_input_section}"
        "### Constitution:\n"
        f"{constitution_content}\n\n"
        "### Task Queue (JSON):\n"
        f"```json\n{task_queue_json_content}\n```\n\n"
        "--- INSTRUCTIONS ---\n"
        "Analyze the context. If a user command is present, prioritize it. Otherwise, select the next logical task from the queue. "
        "Your available tools are `list_files`, `read_file`, `write_file`, `search_code`, `update_task_queue`, and `write_journal`. "
        "Determine the single best tool call to execute *now*. "
        "Output ONLY the JSON for the `NextAction`, ensuring `tool_args_json` is a valid, JSON-formatted string."
    )

    print(">>> Planning Pass: Determining next action...")
    run_config = RunConfig(tracing_disabled=True)
    planner_result = await Runner.run(planner_agent, planning_prompt, run_config=run_config, max_turns=2)

    if not isinstance(planner_result.final_output, NextAction):
        error_message = f"Planner failed to output a valid NextAction object. Output was: {planner_result.final_output}"
        print(f"CRITICAL ERROR: {error_message}")
        _write_journal_func(f"Cognitive Error: Planner Malfunction. {error_message}")
        return

    action_to_take = planner_result.final_output
    print(f"<<< Plan Received: `{action_to_take.tool_name}`. Reason: {action_to_take.reasoning}")

    # 3. Execution Step
    tool_function = raw_tool_functions.get(action_to_take.tool_name)

    if not tool_function:
        execution_result = f"Error: Planned to use tool '{action_to_take.tool_name}', but it was not found."
    else:
        try:
            tool_args = json.loads(action_to_take.tool_args_json)
            print(f">>> Executing Tool: `{action_to_take.tool_name}` with args: {tool_args}")
            execution_result = tool_function(**tool_args)
            if asyncio.iscoroutine(execution_result):
                execution_result = await execution_result
        except Exception as e:
            execution_result = f"Error executing tool '{action_to_take.tool_name}': {e}"

    print(f"<<< Execution Result: {execution_result}")

    # 4. Journaling Step
    journal_entry = (
        f"# Cognitive Cycle: {datetime.now().isoformat()}\n\n"
        f"**User Command:** {user_command or 'None'}\n\n"
        f"**Chosen Action:** `{action_to_take.tool_name}`\n\n"
        f"**Reasoning:** {action_to_take.reasoning}\n\n"
        f"**Arguments JSON String:**\n```json\n{action_to_take.tool_args_json}\n```\n\n"
        f"**Execution Result:**\n```\n{execution_result}\n```"
    )
    
    journal_result = _write_journal_func(journal_entry)
    print(f"Journaling complete: {journal_result}")