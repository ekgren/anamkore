import asyncio
from .cognitive_step import perform_cognitive_step

async def main():
    """
    The main, continuous, and persistent loop of the AURA agent.
    """
    print("\n--- AURA Core Loop Activating ---")
    
    cycle_count = 0
    while True:
        cycle_count += 1
        print(f"\n{'='*10} AURA Cognitive Cycle #{cycle_count} {'='*10}")
        try:
            await perform_cognitive_step()
            print("--- Cognitive Cycle Finished. Starting next cycle immediately. ---")
            
        except Exception as e:
            print(f"\n--- A CRITICAL ERROR OCCURRED IN THE CORE LOOP ---")
            print(f"Error: {e}")
            # The agent will now attempt to recover on the next loop cycle immediately.
            print("Attempting to recover on the next cycle...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- AURA shutdown sequence initiated by user. ---")