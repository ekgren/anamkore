# aura_agent/main.py

import asyncio
from .cognitive_step import perform_cognitive_step
from .initialization import initialize_vault_sync

async def main():
    """
    The main, interactive, user-driven loop of the Anamkore agent.
    """
    # Use the synchronous version for setup
    initialize_vault_sync()
    
    print("\n--- Anamkore Core Loop Activating ---")
    print("Provide a natural language command or press Enter to run a background task. Type 'exit' to quit.")
    
    cycle_count = 0
    while True:
        cycle_count += 1
        
        try:
            user_input = input(f"\n[Cycle {cycle_count}] >>> ")
            if user_input.strip().lower() == 'exit':
                print("--- Anamkore shutdown sequence initiated by user. ---")
                break

            # All input is now treated as a natural language command for the cognitive step.
            # The direct command parser has been removed for architectural purity.
            await perform_cognitive_step(user_command=user_input.strip() or None)

        except (KeyboardInterrupt, EOFError):
            print("\n--- Anamkore shutdown sequence initiated by user. ---")
            break
        except Exception as e:
            print(f"\n--- A CRITICAL ERROR OCCURRED IN THE CORE LOOP ---")
            print(f"Error: {e}")
            print("Attempting to recover on the next cycle...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- Anamkore shutdown sequence initiated by user. ---")