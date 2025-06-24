import json
import asyncio
from datetime import datetime
from agents import Agent, Runner, RunConfig, AgentOutputSchema
from agents.extensions.models.litellm_model import LitellmModel
from . import config
from .task import NextAction
from .agentic_layer import _write_journal_func, _update_task_queue_func, _read_memory_func, _read_task_queue_func

# --- Planner Agent Definition ---
# This agent's only job is to output a structured JSON object.
# To comply with the Gemini API, it MUST NOT be given any tools if it has an output_type.
planner_agent = Agent(
    name="AURA-Planner",
    instructions="You are the planner module for the AURA agent. Your sole responsibility is to analyze the provided context (Constitution, Task Queue) and decide the single most logical next tool call to make progress on the highest-priority task. Your output MUST be a JSON object corresponding to the NextAction schema, where `tool_args_json` is a JSON *string* containing the arguments for the chosen tool.",
    tools=[], # CRITICAL CHANGE: Provide no tools to the planner.
    model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
    output_type=NextAction,
)

async def perform_cognitive_step():
    """
    Executes a single, complete cognitive step based on the AURA blueprint.
    This involves planning, executing, and journaling.
    """
    # 1. Read core state from the vault
    constitution_content = _read_memory_func("0-Core/Constitution.md")
    task_queue_json_content = _read_task_queue_func()

    if "Error:" in constitution_content:
        raise RuntimeError(f"CRITICAL: Could not read Constitution: {constitution_content}")

    # 2. Planning Pass: Construct prompt and run the Planner Agent
    planning_prompt = (
        "### Constitution:\n"
        f"{constitution_content}\n\n"
        "### Task Queue (JSON):\n"
        f"```json\n{task_queue_json_content}\n```\n\n"
        "--- INSTRUCTIONS ---\n"
        "Analyze the context. Your available tools are `read_memory`, `update_task_queue`, `write_journal`, and `read_task_queue`. Determine the single best tool call to execute *now* to advance the highest priority task. "
        "Output ONLY the JSON for the `NextAction`, ensuring `tool_args_json` is a valid JSON string."
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

    # 3. Execution Step: Execute the planned action using the raw Python functions
    raw_tool_functions = {
        "read_memory": _read_memory_func,
        "update_task_queue": _update_task_queue_func,
        "write_journal": _write_journal_func,
        "read_task_queue": _read_task_queue_func
    }
    
    tool_function = raw_tool_functions.get(action_to_take.tool_name)

    if not tool_function:
        execution_result = f"Error: Planned to use tool '{action_to_take.tool_name}', but it was not found."
        print(f"CRITICAL ERROR: {execution_result}")
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

    # 4. Journaling Step: Record what just happened
    journal_entry = (
        f"# Cognitive Cycle: {datetime.now().isoformat()}\n\n"
        f"**Chosen Action:** `{action_to_take.tool_name}`\n\n"
        f"**Reasoning:** {action_to_take.reasoning}\n\n"
        f"**Arguments JSON:**\n```json\n{action_to_take.tool_args_json}\n```\n\n"
        f"**Execution Result:**\n```\n{execution_result}\n```"
    )
    
    journal_result = _write_journal_func(journal_entry)
    print(f"Journaling complete: {journal_result}")