# aura_agent/main.py

import asyncio
from .cognitive_step import perform_cognitive_step
from .initialization import initialize_vault_sync

# --- NEW: Import prompt_toolkit for advanced UX ---
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

async def main():
    """
    The main, interactive, user-driven loop of the Anamkore agent,
    featuring an advanced terminal interface.
    """
    initialize_vault_sync()
    
    # --- NEW: Set up a persistent history file for the prompt ---
    history = FileHistory('.anamkore_history')
    session = PromptSession(history=history)

    print("\n--- Anamkore Core Loop Activating ---")
    print("Provide a command or press Enter for a background task. Use multi-line with Esc+Enter. Exit with Ctrl-D.")
    
    cycle_count = 0
    while True:
        cycle_count += 1
        
        try:
            # --- NEW: Use the advanced prompt session ---
            user_input = await session.prompt_async(
                f"\n[Cycle {cycle_count}] >>> ",
                multiline=True, # Allows for multi-line input
            )
            
            # The prompt_toolkit uses Ctrl-D to exit, which raises EOFError
            if user_input.strip().lower() == 'exit': # Still allow 'exit' command
                 print("--- Anamkore shutdown sequence initiated by user. ---")
                 break

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
        # This is less likely to be triggered now but kept as a fallback
        print("\n--- Anamkore shutdown sequence initiated by user. ---")