# aura_agent/main.py

import asyncio
from .cognitive_step import perform_cognitive_step
from .initialization import initialize_vault  # <-- Import the new function

async def main():
    """
    The main, interactive, user-driven loop of the AURA agent.
    """
    # --- MODIFIED: Run initialization before starting the main loop ---
    await initialize_vault()
    
    print("\n--- AURA Core Loop Activating ---")
    
    cycle_count = 0
    while True:
        cycle_count += 1
        
        try:
            user_input = input(f"\n[Cycle {cycle_count}] >>> ")
            if user_input.strip().lower() == 'exit':
                print("--- AURA shutdown sequence initiated by user. ---")
                break
            
            # Pass user command to the cognitive step. If empty, it will process background tasks.
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
        # This handles Ctrl+C more gracefully if pressed while waiting for input.
        print("\n--- AURA shutdown sequence initiated by user. ---")