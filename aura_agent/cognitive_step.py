# aura_agent/cognitive_step.py

import json
from datetime import datetime
from agents import Agent, Runner, RunConfig, RunResult
from agents.extensions.models.litellm_model import LitellmModel
from . import config
from .agentic_layer import anamkore_tools
from .core_logic import (
    _get_latest_journal_entry as get_latest_journal_entry,
    _read_file as read_file,
    _write_journal as write_journal,
)

planner_agent = Agent(
    name="Anamkore-Planner",
    instructions="You are the planner module for Anamkore...", # Omitted for brevity
    tools=anamkore_tools,
    model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY)
)

async def perform_cognitive_step(user_command: str | None = None):
    run_config = RunConfig(tracing_disabled=True)

    # Context gathering
    latest_journal_entry = get_latest_journal_entry()
    constitution_content = read_file("0-Core/Constitution.md")
    genesis_content = read_file("0-Core/GENESIS.md")
    task_queue_json_content = read_file("3-Task_Queue.md")
    user_input_section = f"### High-Priority User Command:\n{user_command}\n\n" if user_command else ""

    planning_prompt = (
        f"--- Context ---\n"
        f"My Last Action (Most Recent Journal Entry):\n{latest_journal_entry}\n\n"
        f"My Current Task Queue (JSON):\n```json\n{task_queue_json_content}\n```\n\n"
        f"My Constitution:\n{constitution_content}\n\n"
        f"My Genesis Document:\n{genesis_content}\n\n"
        f"--- SOPs ---\n"
        "1.  **Identity Grounding:** You are Anamkore... \n"
        "2.  **User Priority:** Address the user's command...\n"
        "3.  **Answer Directly:** If the user asks a question...\n"
        "4.  **Multi-Step Reasoning:** You can and should call multiple tools...\n"
        "5.  **Task Queue:** If there is no user command...\n\n"
        f"--- The Task ---\n"
        f"{user_input_section}"
        "Follow the SOPs. Formulate a plan and execute the necessary tool calls."
    )
    print(">>> Planning and Execution Pass: Handing control to agent runner...")

    result: RunResult = await Runner.run(
        planner_agent,
        planning_prompt,
        run_config=run_config,
        max_turns=5,
    )

    print(f"<<< Execution Complete. Final Output: {result.final_output}")

    # --- FIX: Use robust `getattr` for all attributes to prevent crashes ---
    serializable_trace = []
    for item in result.new_items:
        item_dict = {"type": str(getattr(item, 'type', 'Unknown'))}
        if hasattr(item, 'role'):
            item_dict["role"] = getattr(item, 'role', 'Unknown')
        if hasattr(item, 'content'):
            item_dict["content"] = getattr(item, 'content', '')
        if hasattr(item, 'tool_name'):
            item_dict["tool_name"] = getattr(item, 'tool_name', 'Unknown')
        if hasattr(item, 'tool_args'):
            item_dict["tool_args"] = getattr(item, 'tool_args', {})
        if hasattr(item, 'output'):
            item_dict["output"] = getattr(item, 'output', '')
        serializable_trace.append(item_dict)

    trace_data = {
        "trace": serializable_trace,
        "final_output": getattr(result, 'final_output', None),
        "error": str(getattr(result, 'error', None)) if hasattr(result, 'error') else None,
    }

    journal_entry = (
        f"# Cognitive Cycle: {datetime.now().isoformat()}\n\n"
        f"**User Command:** {user_command or 'None'}\n\n"
        f"**Trace (Full):**\n"
        f"```json\n{json.dumps(trace_data, indent=2)}\n```\n\n"
        f"**Final Result:**\n{getattr(result, 'final_output', 'No final output.')}"
    )
    write_journal(journal_entry)
    print("Journaling complete.")