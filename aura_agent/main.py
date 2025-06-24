import asyncio
import time
from agents import Agent, Runner, set_tracing_disabled, RunConfig
from agents.extensions.models.litellm_model import LitellmModel
from . import config
from .agentic_layer import read_memory, read_task_queue, TOOL_REGISTRY

async def main_loop():
    """
    The main, continuous, and persistent loop of the AURA agent.
    """
    print("Initializing AURA with OpenAI Agents SDK...")
    set_tracing_disabled(True)
    print("Default OpenAI tracing disabled.")

    model_instance = LitellmModel(
        model=config.GEMINI_PRO_MODEL,
        api_key=config.API_KEY
    )
    print(f"Model instance created for: {config.GEMINI_PRO_MODEL}")

    aura_agent = Agent(
        name="AURA",
        instructions="You are AURA, an autonomous agent. Your core directives are in your Constitution. Your goals are in your Task Queue. You will be given a context including these documents. Your task is to determine the single next action to take to progress on your highest priority task, and then output a single, precise tool call to perform that action. Do not output any other text.",
        tools=list(TOOL_REGISTRY.values()),
        model=model_instance,
    )
    
    run_configuration = RunConfig(tracing_disabled=True)
    
    print("\n--- AURA Core Loop Activated ---")
    while True:
        try:
            # --- CONTEXTUAL STATE SCAFFOLDING (CSS) ---
            print("\n--- New Cognitive Cycle ---")
            
            # 1. Read core state from the vault
            constitution_content = read_memory("0-Core/Constitution.md")
            task_queue_json_content = read_task_queue()

            if "Error:" in constitution_content:
                print(f"CRITICAL ERROR: Could not read Constitution. Shutting down. Reason: {constitution_content}")
                break

            # 2. Construct the prompt for this cycle
            current_prompt = (
                "### AURA Constitution:\n"
                f"{constitution_content}\n\n"
                "### Current Task Queue (JSON format):\n"
                f"```json\n{task_queue_json_content}\n```\n\n"
                "--- Instructions for this turn ---\n"
                "Based on your Constitution and the Task Queue, determine the single best action to perform *right now* to make progress on the highest priority task. "
                "Formulate your response as a single, precise tool call. "
                "Do NOT include any conversational text or explanation, only the tool call."
            )

            print(f"Executing cognitive step with {len(current_prompt)} characters of context.")
            
            # 3. Run the agent for one turn sequence
            result = await Runner.run(
                aura_agent,
                current_prompt,
                run_config=run_configuration,
                max_turns=3 # A single logical step should not take more than a few turns.
            )
            
            # 4. Log the outcome of the agent's action
            print("\n--- Cognitive Step Complete ---")
            print(f"Final Output (Result of Agent's Decision):\n---\n{result.final_output}\n---")

            # 5. Wait before starting the next cycle to avoid rapid looping and high API costs.
            print("\nPausing for 10 seconds before next cycle...")
            time.sleep(10)

        except Exception as e:
            print(f"\n--- A CRITICAL ERROR OCCURRED IN THE CORE LOOP ---")
            print(f"Error: {e}")
            print("The agent will attempt to recover after a 30-second pause.")
            time.sleep(30)


if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\n--- AURA shutdown sequence initiated by user. ---")