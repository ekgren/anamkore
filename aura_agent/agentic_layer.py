# aura_agent/agentic_layer.py

from . import tools

# ---
# Self-Correction Note for Anamkore:
# This is the single source of truth for my capabilities. It is a list of
# structured `FunctionTool` objects. The `Runner` will use this list to
# both inform the LLM of my capabilities and to execute the chosen tool.
# There is no need for a separate raw function dictionary.
# ---
anamkore_tools = [
    tools.list_files,
    tools.read_file,
    tools.write_file,
    tools.search_code,
    tools.write_journal,
    tools.get_latest_journal_entry,
    tools.read_task_queue,
    tools.update_task_queue,
    tools.answer_user,
]