# aura_agent/cognitive_step.py

import json
from datetime import datetime
from agents import Runner, RunConfig, RunResult
from .core_logic import (
    _get_latest_journal_entry,
    _read_file,
    _write_file,
    _write_journal,
    _answer_user,
)
from .agents import planner_agent, synthesizer_agent, reflector_agent
from .task import Reflection

def _create_summarized_planner_output(output: str, max_len: int = 1500) -> str:
    """Creates a summarized version of the planner output to prevent context pollution."""
    if len(output) > max_len:
        return f"Tool execution was successful. Output was too large to be included in context. (First {max_len} chars):\n{output[:max_len]}..."
    return output

async def perform_cognitive_step(user_command: str | None = None):
    run_config = RunConfig(tracing_disabled=True)
    latest_journal_summary = _get_latest_journal_entry(summary_only=True)
    
    # --- FINAL, ROBUST ORCHESTRATOR LOGIC ---
    directive = ""
    
    # Priority 1: Handle direct user commands
    if user_command:
        directive = f"The user has given a direct command: '{user_command}'"
    
    # Priority 2: Handle critical failures
    elif "Error:" in latest_journal_summary:
        directive = "The last cycle failed. Your priority is to diagnose and take the first step to FIX that failure."
        
    # Priority 3: Continue working on the current task
    else:
        current_task_content = _read_file("5-Current_Task.md")
        if not current_task_content.startswith("Error:") and current_task_content.strip():
            directive = f"Your current task is: '{current_task_content.strip()}'. Take the next logical step to continue its implementation."
            
        # --- THE MISSING LINK ---
        # Priority 4: If the last action was reading the task queue, process it.
        # We check for keys that are unique to the task queue JSON output.
        elif '"id"' in latest_journal_summary and '"status"' in latest_journal_summary:
             directive = (
                "Your last action was reading the task queue, and its content is in your context. "
                "Your new directive is to take the first 'todo' task from that list and write its full description "
                "to the `5-Current_Task.md` file using the `write_file` tool. Ensure you overwrite the file."
            )

        # Priority 5: Default action is to read the task queue.
        else:
            directive = "You have no active task. Your directive is to call the `read_task_queue` tool."

    # --- PLANNER ---
    planning_prompt = (
        f"--- Context ---\nMy Last Action (Summary & Planner Output):\n{latest_journal_summary}\n\n"
        f"--- Directive ---\n{directive}"
    )
    print("\n" + "="*50)
    print(">>> Planning Pass...")
    print(f"--- PROMPT FOR PLANNER ---\n{planning_prompt}\n--------------------------")
    
    planner_result: RunResult = await Runner.run(planner_agent, planning_prompt, run_config=run_config)
    planner_output = str(planner_result.final_output)

    # --- SYNTHESIZER ---
    synthesis_prompt = (
        f"--- Initial Directive ---\n{directive}\n\n"
        f"--- Planner Output ---\n{planner_output}\n\n"
        f"--- Your Task ---\nSynthesize the above into a coherent, human-readable summary."
    )
    print("\n" + "="*50)
    print(">>> Synthesis Pass...")
    
    synthesis_result: RunResult = await Runner.run(synthesizer_agent, synthesis_prompt, run_config=run_config)
    synthesizer_output = str(synthesis_result.final_output)
    _answer_user(synthesizer_output)
    print(f"<<< Cycle Complete.")

    # --- JOURNALING with CONTEXT SANITIZATION ---
    summarized_planner_output = _create_summarized_planner_output(planner_output)
    trace_data = {
        "directive": directive,
        "planner_output": summarized_planner_output,
        "synthesizer_output": synthesizer_output,
    }
    journal_entry = f"# Cognitive Cycle: {datetime.now().isoformat()}\n\n**Directive:** {directive}\n\n**Synthesizer Output:**\n{synthesizer_output}\n\n## Trace\n```json\n{json.dumps(trace_data, indent=2)}\n```\n"
    _write_journal(journal_entry)
    print("Journaling complete.")