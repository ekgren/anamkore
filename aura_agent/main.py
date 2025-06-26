# aura_agent/main.py

import asyncio
import traceback
from .cognitive_step import perform_cognitive_step
from .initialization import initialize_vault_sync
from .core_logic import _write_journal

async def main():
    """
    The main, interactive, user-driven loop of the Anamkore agent.
    """
    initialize_vault_sync()
    
    print("\n--- Anamkore Core Loop Activating ---")
    print("Provide a natural language command or press Enter to run a background task. Type 'exit' to quit.")
    
    cycle_count = 0
    while True:
        cycle_count += 1
        cycle_error = None
        
        try:
            user_input = input(f"\n[Cycle {cycle_count}] >>> ")
            if user_input.strip().lower() == 'exit':
                print("--- Anamkore shutdown sequence initiated by user. ---")
                break
            
            await perform_cognitive_step(user_command=user_input.strip() or None)

        except (KeyboardInterrupt, EOFError):
            print("\n--- Anamkore shutdown sequence initiated by user. ---")
            break
        except Exception as e:
            print(f"\n--- A CRITICAL ERROR OCCURRED IN THE CORE LOOP ---")
            print(f"Error: {e}")
            cycle_error = traceback.format_exc() # Get the full traceback
            print("Attempting to recover on the next cycle...")
        
        # --- NEW: Guaranteed Failure Journaling ---
        # If a critical error happened that prevented the normal journaling, log it here.
        if cycle_error:
            failure_journal_entry = (
                f"# Cognitive Cycle: CRITICAL FAILURE\n\n"
                f"**User Command:** {user_input or 'None'}\n\n"
                f"A critical exception occurred that halted the cognitive step.\n\n"
                f"**Error Traceback:**\n```\n{cycle_error}\n```"
            )
            _write_journal(failure_journal_entry)
            print("Journaling critical failure complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- Anamkore shutdown sequence initiated by user. ---")