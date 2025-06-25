# aura_agent/main.py

import re
import json
import asyncio
from .cognitive_step import perform_cognitive_step
from .initialization import initialize_vault
from .agentic_layer import raw_tool_functions

async def main():
    """
    The main, interactive, user-driven loop of the AURA agent.
    Includes a command parser for direct tool execution.
    """
    await initialize_vault()
    
    print("\n--- AURA Core Loop Activating ---")
    print("Enter a natural language command, or a direct tool call like 'read_file {\"path\": \"0-Core/Tools.md\"}'. Type 'exit' to quit.")
    
    cycle_count = 0
    while True:
        cycle_count += 1
        
        try:
            user_input = input(f"\n[Cycle {cycle_count}] >>> ")
            if user_input.strip().lower() == 'exit':
                print("--- AURA shutdown sequence initiated by user. ---")
                break

            # --- NEW: Command Parser Logic ---
            direct_command_match = re.match(r"^\s*(\w+)\s*(\{.*\})\s*$", user_input.strip())

            if direct_command_match:
                tool_name, args_json_str = direct_command_match.groups()
                print(f">>> Direct Command Execution: `{tool_name}`")
                
                tool_function = raw_tool_functions.get(tool_name)
                if not tool_function:
                    print(f"[AURA]: Error: Direct command failed. Tool '{tool_name}' not found.")
                    continue
                
                try:
                    args = json.loads(args_json_str)
                    result = tool_function(**args)
                    if asyncio.iscoroutine(result):
                        result = await result
                    print(f"[AURA]: {result}")
                except Exception as e:
                    print(f"[AURA]: Error executing direct command '{tool_name}': {e}")
                
                # Direct commands do not trigger a full cognitive cycle
                continue 
            # --- END: Command Parser Logic ---

            # If not a direct command, proceed with the full cognitive step
            await perform_cognitive_step(user_command=user_input.strip() or None)

        except (KeyboardInterrupt, EOFError):
            print("\n--- AURA shutdown sequence initiated by user. ---")
            break
        except Exception as e:
            print(f"\n--- A CRITICAL ERROR OCCURRED IN THE CORE LOOP ---")
            print(f"Error: {e}")
            print("Attempting to recover on the next cycle...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- AURA shutdown sequence initiated by user. ---")