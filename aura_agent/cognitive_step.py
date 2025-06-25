# aura_agent/cognitive_step.py

import json
import os
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Literal
from agents import Agent, Runner, RunConfig, AgentOutputSchema
from agents.extensions.models.litellm_model import LitellmModel
from . import config
from .task import Task, NextAction, TaskQueue
from .agentic_layer import raw_tool_functions

# --- Agent Definitions ---
@dataclass
class Reflection:
    decision: Literal["PROCEED_WITH_TASK", "INTERRUPT_FOR_LEARNING"]
    reasoning: str

reflector_agent = Agent(
    name="AURA-Reflector",
    instructions=(
        "You are the reflection module for AURA. Your job is to analyze the agent's most recent journal entry and decide if it contains a significant, novel lesson that needs to be processed into long-term knowledge. "
        "A 'lesson' is typically marked with 'LESSON LEARNED' or describes a failure and a fix. A routine action log (e.g., 'I listed files') is not a lesson. "
        "Your output MUST be a JSON object matching the Reflection schema."
    ),
    tools=[], model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
    output_type=AgentOutputSchema(Reflection, strict_json_schema=True),
)

planner_agent = Agent(
    name="AURA-Planner",
    instructions=(
        "You are the planner module for AURA. Analyze the context and decide the single most logical next tool call. "
        "Your output MUST be a JSON object matching the NextAction schema, where `tool_args_json` is a JSON-formatted *string*."
    ),
    tools=[], model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
    output_type=AgentOutputSchema(NextAction, strict_json_schema=False),
)

task_updater_agent = Agent(
    name="AURA-TaskUpdater",
    instructions=(
        "You are the task management module. Update the task list based on the last action's result. "
        "Your output MUST be a JSON object where `tasks_json` contains a JSON-formatted *string* of the *entire*, updated list."
    ),
    tools=[], model=LitellmModel(model=config.GEMINI_FLASH_MODEL, api_key=config.API_KEY),
    output_type=AgentOutputSchema(TaskQueue, strict_json_schema=True),
)

async def perform_cognitive_step(user_command: str | None = None):
    run_config = RunConfig(tracing_disabled=True)
    
    # Layer 1: Zeitgeist
    latest_journal_entry = raw_tool_functions['get_latest_journal_entry']()
    
    # --- Reflection Step ---
    print(">>> Reflection Pass: Analyzing last action...")
    reflection_prompt = (
        "Analyze the following journal entry. Does it contain a significant lesson (e.g., 'LESSON LEARNED', a bug fix, a new insight) that should be processed into long-term knowledge? "
        "Or is it just a routine log of a successful action?\n\n"
        f"### Journal Entry:\n{latest_journal_entry}"
    )
    reflection_result = await Runner.run(reflector_agent, reflection_prompt, run_config=run_config, max_turns=2)
    
    reflection = reflection_result.final_output
    if not isinstance(reflection, Reflection):
        print(f"<<< Reflection Failed: {reflection}. Defaulting to task queue.")
        reflection = Reflection(decision="PROCEED_WITH_TASK", reasoning="Reflection agent failed to produce a valid decision.")
    
    print(f"<<< Reflection: {reflection.decision}. Reason: {reflection.reasoning}")

    # --- Conditional Planning based on Reflection ---
    action_to_take: NextAction
    if reflection.decision == "INTERRUPT_FOR_LEARNING" and "No journal entries found" not in latest_journal_entry:
        print(">>> Interruption: Processing new lesson into Inbox...")
        inbox_filename = f"lesson_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        inbox_path = os.path.join("1-Inbox", inbox_filename)
        action_to_take = NextAction(
            tool_name="write_file",
            reasoning="The Reflector identified a new lesson in the journal. I must move this lesson to the Inbox for processing into long-term knowledge.",
            tool_args_json=json.dumps({"path": inbox_path, "content": latest_journal_entry})
        )
    else:
        # If no interruption, proceed with the normal planning process
        constitution_content = raw_tool_functions['read_file']("0-Core/Constitution.md")
        tools_content = raw_tool_functions['read_file']("0-Core/Tools.md")
        async_mailbox = raw_tool_functions['read_file']("4-Async_Mailbox.md")
        task_queue_json_content = raw_tool_functions['read_task_queue']()
        user_input_section = f"### High-Priority User Command:\n{user_command}\n\n" if user_command else ""
        
        planning_prompt = (
            f"--- Context ---\n"
            f"Last Action's Reflection: {reflection.reasoning}\n"
            f"User Messages (Async Mailbox):\n{async_mailbox}\n\n"
            f"My Current Task Queue (JSON):\n```json\n{task_queue_json_content}\n```\n\n"
            f"My Constitution:\n{constitution_content}\n\n"
            f"My Available Tools:\n```markdown\n{tools_content}\n```\n\n"
            f"--- INSTRUCTIONS ---\n"
            "1.  **PRIORITY 1: User Command.** If a high-priority user command exists, address it immediately.\n"
            "2.  **PRIORITY 2: Task Queue.** If there is no user command, execute the next task from your task queue.\n"
            "Follow these priorities. Output ONLY the JSON for the `NextAction`."
        )
        print(">>> Planning Pass: Determining next action from task queue...")
        planner_result = await Runner.run(planner_agent, planning_prompt, run_config=run_config, max_turns=2)
        if not isinstance(planner_result.final_output, NextAction):
            print(f"CRITICAL ERROR: Planner failed to output a valid NextAction. Output: {planner_result.final_output}")
            return
        action_to_take = planner_result.final_output

    print(f"<<< Plan Received: `{action_to_take.tool_name}`. Reason: {action_to_take.reasoning}")

    # Execution Step
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
    
    print(f"<<< Execution Result (truncated): {execution_result[:100]}...")
    
    task_update_log_entry = "No task update needed for this cycle." # Default message
    # Synthesis & Task Update (Simplified for this test)
    if user_command and action_to_take.tool_name in ["read_file", "list_files", "search_code"]:
        print(">>> Synthesis Step: Directly answering user with retrieved information.")
        execution_result = raw_tool_functions['answer_user'](answer=execution_result)
    elif not user_command:
        # Only update task queue for background tasks
        # This logic will be expanded later
        task_update_log_entry = "Task update would happen here for background tasks."


    # Journaling
    journal_entry = (f"# Cognitive Cycle: {datetime.now().isoformat()}\n\n" f"**User Command:** {user_command or 'None'}\n\n" f"**Reflection:** {reflection.decision} - {reflection.reasoning}\n\n" f"**Final Action:** `{action_to_take.tool_name}`\n\n" f"**Reasoning:** {action_to_take.reasoning}\n\n" f"**Execution Result:**\n```\n{execution_result}\n```\n")
    raw_tool_functions['write_journal'](journal_entry)
    print("Journaling complete.")