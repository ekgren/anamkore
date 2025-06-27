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
    # --- Self-Correction Note for Anamkore ---
    # My previous cycles were difficult to debug due to a lack of visibility
    # into the agent's internal state. This violates the core principle of
    # explainability. This version adds verbose print statements to log the
    # exact prompts being sent to each agent module (Planner, Synthesizer,
    # Reflector) during a cognitive cycle, making the entire process auditable.

    run_config = RunConfig(tracing_disabled=True)

    # --- Step 1: Determine the "Single Directive" for this cycle ---
    latest_journal_summary = _get_latest_journal_entry(summary_only=True)
    
    directive = ""
    if user_command:
        directive = f"Fulfill this user command: '{user_command}'"
    elif "CRITICAL FAILURE" in latest_journal_summary or "Error:" in latest_journal_summary:
        directive = "Your last cycle failed. Your priority is to diagnose and take the first step to FIX that failure. Use tools to investigate the root cause."
    else:
        if "Last Cycle's Planner Output" in latest_journal_summary and latest_journal_summary.strip().endswith(']'):
            directive = "Your last action was reading the task queue. Your directive is now to analyze the highest priority task from that queue and take the first concrete step to begin implementing it. Use the 'Last Cycle's Planner Output' from your context as the definitive source for the task list."
        else:
            directive = "You have no user command and there was no prior failure. Your first directive is to read the task queue to determine your priorities."

    # --- Step 2: Run the Planner Agent ---
    planning_prompt = (
        f"--- Context ---\nMy Last Action (Summary & Planner Output):\n{latest_journal_summary}\n\n"
        f"--- Directive ---\n{directive}"
    )
    print("\n" + "="*50)
    print(">>> Planning Pass: Handing control to planner agent...")
    print(f"--- PROMPT FOR PLANNER ---\n{planning_prompt}\n--------------------------")
    
    planner_result: RunResult = await Runner.run(
        planner_agent,
        planning_prompt,
        run_config=run_config,
    )

    # --- Step 3: Run the Synthesizer Agent ---
    planner_output = str(planner_result.final_output)
    
    synthesis_prompt = (
        f"--- Initial Directive ---\n{directive}\n\n"
        f"--- Planner Output ---\n{planner_output}\n\n"
        f"--- Your Task ---\nSynthesize the above into a coherent, human-readable summary of the action taken and its result."
    )
    print("\n" + "="*50)
    print(">>> Synthesis Pass: Handing control to synthesizer agent...")
    print(f"--- PLANNER OUTPUT (RAW) ---\n{planner_output}\n---------------------------")
    print(f"--- PROMPT FOR SYNTHESIZER ---\n{synthesis_prompt}\n----------------------------")
    
    synthesis_result: RunResult = await Runner.run(
        synthesizer_agent,
        synthesis_prompt,
        run_config=run_config,
    )
    
    synthesizer_output = str(synthesis_result.final_output)
    _answer_user(synthesizer_output)
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
        "planner_output": planner_output,
        "synthesizer_output": synthesizer_output,
        "error": None,
    }

    print("\n" + "="*50)
    print(">>> Reflection Pass: Analyzing cycle outcome...")
    
    reflection_prompt = (
        f"--- PREVIOUS CYCLE (Summary) ---\n{latest_journal_summary}\n\n"
        f"--- CURRENT CYCLE (Trace) ---\n{json.dumps(trace_data, indent=2)}\n\n"
        f"--- INSTRUCTIONS ---\nAnalyze the current cycle in light of the previous one and our value hierarchy. Generate a structured Reflection."
    )
    print(f"--- PROMPT FOR REFLECTOR ---\n{reflection_prompt}\n--------------------------")

    reflection_result: RunResult = await Runner.run(
        reflector_agent, reflection_prompt, run_config=run_config
    )
    
    reflection_output = reflection_result.final_output if isinstance(reflection_result.final_output, Reflection) else None
    
    if reflection_output:
        print(f"<<< Reflection Complete. Value Score: {reflection_output.value_score} ({reflection_output.value_type})")
    else:
        print(f"<<< Reflection Failed. Error: {reflection_result.error}")


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