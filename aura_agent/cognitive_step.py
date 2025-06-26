# aura_agent/cognitive_step.py

import json
from datetime import datetime
from agents import Runner, RunConfig, RunResult
from .core_logic import (
    _get_latest_journal_entry,
    _read_file,
    _write_journal,
    _answer_user, # Import the raw function for direct use
)
from .agents import planner_agent, synthesizer_agent, reflector_agent
from .task import Reflection

async def perform_cognitive_step(user_command: str | None = None):
    # --- Self-Correction Note for Anamkore (Post-Docs-Review): ---
    # The 'max_turns' parameter is the critical control knob for the agent loop.
    # My previous failures were caused by setting max_turns > 1 for the planner,
    # which allowed it to continue executing its plan instead of returning
    # control to the orchestrator after a single step. For a single "thought"
    # or action, max_turns MUST be 1.

    run_config = RunConfig(tracing_disabled=True)

    # --- Step 1: Determine the "Single Directive" for this cycle ---
    latest_journal_summary = _get_latest_journal_entry(summary_only=True)
    task_queue_json_content = _read_file("3-Task_Queue.md")
    
    directive = ""
    if user_command:
        directive = f"Fulfill this user command: '{user_command}'"
    elif "CRITICAL FAILURE" in latest_journal_summary or "Error:" in latest_journal_summary:
        directive = "Your last cycle failed. Your priority is to diagnose and take the first step to FIX that failure. Use tools to investigate the root cause."
    else:
        top_task = task_queue_json_content.splitlines()[2] if len(task_queue_json_content.splitlines()) > 2 else "T1"
        directive = f"Make progress on your highest-priority task: '{top_task}'"

    # --- Step 2: Run the Planner Agent to gather information ---
    planning_prompt = (
        f"--- Context ---\nMy Last Action (Summary):\n{latest_journal_summary}\n\n"
        f"--- Directive ---\n{directive}"
    )
    print(">>> Planning Pass: Handing control to planner agent...")
    planner_result: RunResult = await Runner.run(
        planner_agent,
        planning_prompt,
        run_config=run_config,
        max_turns=1, # CRITICAL FIX: Force the planner to take only ONE step.
    )

    # --- Step 3: Run the Synthesizer Agent to generate the final response ---
    print(">>> Synthesis Pass: Handing control to synthesizer agent...")
    
    planner_trace = [
        f"Tool: {item.tool_name}, Args: {item.tool_args}, Output: {item.output}"
        for item in planner_result.new_items if hasattr(item, 'tool_name')
    ]
    synthesis_prompt = (
        f"--- Initial Directive ---\n{directive}\n\n"
        f"--- Execution Trace from Planner ---\n{json.dumps(planner_trace, indent=2)}\n\n"
        f"--- Your Task ---\nSynthesize the above into a coherent, human-readable final answer or a summary of the action taken."
    )
    
    synthesis_result: RunResult = await Runner.run(
        synthesizer_agent,
        synthesis_prompt,
        run_config=run_config,
    )
    
    final_output = str(synthesis_result.final_output)
    _answer_user(final_output)
    print(f"<<< Cycle Complete.")

    # --- Step 4: Journaling and Reflection ---
    full_trace = planner_result.new_items + synthesis_result.new_items
    serializable_trace = []
    for item in full_trace:
        item_dict = {"type": str(getattr(item, 'type', 'Unknown'))}
        if hasattr(item, 'role'): item_dict["role"] = getattr(item, 'role', 'Unknown')
        if hasattr(item, 'content'): item_dict["content"] = getattr(item, 'content', '')
        if hasattr(item, 'tool_name'): item_dict["tool_name"] = getattr(item, 'tool_name', 'Unknown')
        if hasattr(item, 'tool_args'): item_dict["tool_args"] = json.loads(json.dumps(getattr(item, 'tool_args', {})))
        if hasattr(item, 'output'): item_dict["output"] = getattr(item, 'output', '')
        serializable_trace.append(item_dict)

    trace_data = {
        "trace": serializable_trace,
        "final_output": final_output,
        "error": str(planner_result.error or synthesis_result.error or ""),
    }

    print(">>> Reflection Pass: Analyzing cycle outcome...")
    full_latest_journal = _get_latest_journal_entry(summary_only=False)
    reflection_prompt = (
        f"--- PREVIOUS CYCLE ---\n{full_latest_journal}\n\n"
        f"--- CURRENT CYCLE ---\n{json.dumps(trace_data, indent=2)}\n\n"
        f"--- INSTRUCTIONS ---\nAnalyze the current cycle in light of the previous one and our value hierarchy. Generate a structured Reflection."
    )

    reflection_result: RunResult = await Runner.run(
        reflector_agent, reflection_prompt, run_config=run_config
    )
    
    reflection_output = reflection_result.final_output if isinstance(reflection_result.final_output, Reflection) else None

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
        f"## Full Trace\n```json\n{json.dumps(trace_data, indent=2)}\n```\n"
    )
    _write_journal(journal_entry)
    print("Journaling complete.")