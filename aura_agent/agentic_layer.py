# aura_agent/agentic_layer.py

from .fs_utils import list_files, read_file, write_file
from .tools import (
    answer_user, 
    search_code, 
    write_journal, 
    get_latest_journal_entry, 
    read_task_queue, 
    update_task_queue
)

# The comprehensive dictionary of all available tools.
raw_tool_functions = {
    # Filesystem Tools
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,

    # Cognitive & State Tools
    "search_code": search_code,
    "write_journal": write_journal,
    # --- FIX: The new tool is now correctly registered in the dictionary. ---
    "get_latest_journal_entry": get_latest_journal_entry,
    "read_task_queue": read_task_queue,
    "update_task_queue": update_task_queue,
    
    # Communication Tools
    "answer_user": answer_user,
}