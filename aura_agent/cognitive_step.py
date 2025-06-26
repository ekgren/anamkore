# aura_agent/cognitive_step.py

import json
from datetime import datetime
from agents import Runner, RunConfig, RunResult
from . import config
from .core_logic import (
    _get_latest_journal_entry as get_latest_journal_entry,
    _read_file as read_file,
    _write_journal as write_journal,
)
from .agents import planner_agent, reflector_agent
from .task import Reflection


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
        f"--- The Task ---\n"
        f"{user_input_section}"
        "You are Anamkore. Follow your instructions. Begin."
    )
    print(">>> Planning and Execution Pass: Handing control to agent runner...")

    result: RunResult = await Runner.run(
        planner_agent,
        planning_prompt,
        run_config=run_config,
        max_turns=5,
    )

    print(f"<<< Execution Complete. Final Output: {result.final_output}")

    serializable_trace = []
    for item in result.new_items:
        item_dict = {"type": str(getattr(item, 'type', 'Unknown'))}
        if hasattr(item, 'role'):
            item_dict["role"] = getattr(item, 'role', 'Unknown')
        if hasattr(item, 'tool_name'):
            item_dict["tool_name"] = getattr(item, 'tool_name', 'Unknown')
        if hasattr(item, 'tool_args'):
            item_dict["tool_args"] = json.loads(json.dumps(getattr(item, 'tool_args', {})))
        if hasattr(item, 'output'):
            item_dict["output"] = getattr(item, 'output', '')
        serializable_trace.append(item_dict)

    trace_data = {
        "trace": serializable_trace,
        "final_output": str(getattr(result, 'final_output', None)),
        "error": str(getattr(result, 'error', None)) if hasattr(result, 'error') else None,
    }

    print(">>> Reflection Pass: Analyzing cycle outcome...")

    # --- MODIFIED: The reflection prompt now includes the previous journal entry for context. ---
    reflection_prompt = (
        "You are the Reflector. Analyze the relationship between the PREVIOUS cycle and the CURRENT cycle. "
        "Your primary goal is to identify high-value learning, especially when a failure is corrected.\n\n"
        "--- PREVIOUS CYCLE (from latest journal) ---\n"
        f"{latest_journal_entry}\n\n"
        "--- CURRENT CYCLE (trace data) ---\n"
        f"```json\n{json.dumps(trace_data, indent=2)}\n```\n\n"
        "--- INSTRUCTIONS ---\n"
        "Based on our value hierarchy (5: Correction, 4: Insight/Hypothesis, 3: Synthesis, 2: Execution, 1: Routine), "
        "evaluate the CURRENT cycle in light of the PREVIOUS one. Generate a structured Reflection."
    )

    reflection_result: RunResult = await Runner.run(
        reflector_agent,
        reflection_prompt,
        run_config=run_config,
    )

    reflection_output: Reflection | None = None
    if isinstance(reflection_result.final_output, Reflection):
        reflection_output = reflection_result.final_output
        print(f"<<< Reflection Complete. Value Score: {reflection_output.value_score} ({reflection_output.value_type})")
    else:
        print(f"<<< Reflection Failed. Could not generate structured reflection. Error: {reflection_result.error}")

    reflection_section = "No reflection was generated."
    if reflection_output:
        reflection_section = (
            f"**Reflection Summary:** {reflection_output.summary}\n\n"
            f"**Value Score:** {reflection_output.value_score} ({reflection_output.value_type})\n\n"
            f"**Key Learning:**\n{reflection_output.key_learning}"
        )
        if reflection_output.new_tasks_proposed:
            tasks_str = "\n".join(f"- {task}" for task in reflection_output.new_tasks_proposed)
            reflection_section += f"\n\n**New Tasks Proposed:**\n{tasks_str}"

    journal_entry = (
        f"# Cognitive Cycle: {datetime.now().isoformat()}\n\n"
        f"**User Command:** {user_command or 'None'}\n\n"
        f"## Reflection & Synthesis\n{reflection_section}\n\n"
        f"## Full Trace\n"
        f"```json\n{json.dumps(trace_data, indent=2)}\n```\n"
    )
    write_journal(journal_entry)
    print("Journaling complete.")