# nano-tools/nano_gemini_cli_core/tools/memory_tool.py
import os
from openai_agents import function_tool

# --- Constants matching the gemini-cli implementation ---
GEMINI_CONFIG_DIR = ".gemini"
DEFAULT_CONTEXT_FILENAME = "GEMINI.md"
MEMORY_SECTION_HEADER = "## Gemini Added Memories"

def get_global_memory_file_path() -> str:
    """Gets the path to the global memory file."""
    return os.path.join(os.path.expanduser("~"), GEMINI_CONFIG_DIR, DEFAULT_CONTEXT_FILENAME)

def _ensure_newline_separation(content: str) -> str:
    """Ensures there's a blank line before appending new sections."""
    if not content:
        return ""
    if content.endswith("\n\n"):
        return ""
    if content.endswith("\n"):
        return "\n"
    return "\n\n"

@function_tool
def save_memory(fact: str) -> str:
    """
    Saves a specific fact to the global long-term memory file (~/.gemini/GEMINI.md).
    This is useful for remembering user preferences or key details across sessions.

    Args:
        fact: The fact to remember. Should be a clear, self-contained statement.
    """
    if not fact or not isinstance(fact, str) or not fact.strip():
        return "Error: The 'fact' parameter must be a non-empty string."

    memory_file_path = get_global_memory_file_path()
    
    try:
        # Ensure the ~/.gemini directory exists
        os.makedirs(os.path.dirname(memory_file_path), exist_ok=True)
        
        # Sanitize the fact to be saved
        processed_fact = fact.strip().lstrip("- ").strip()
        new_memory_item = f"- {processed_fact}"

        # Read existing content, or start fresh if file doesn't exist
        try:
            with open(memory_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            content = ""

        header_index = content.find(MEMORY_SECTION_HEADER)

        if header_index == -1:
            # Header not found, append header and then the entry
            separator = _ensure_newline_separation(content)
            content += f"{separator}{MEMORY_SECTION_HEADER}\n{new_memory_item}\n"
        else:
            # Header found, find where to insert the new memory entry
            # Find the start of the next section to correctly delimit the memory section
            start_of_section_content = header_index + len(MEMORY_SECTION_HEADER)
            next_header_index = content.find("\n## ", start_of_section_content)
            
            if next_header_index == -1:
                # Memory section is at the end of the file
                section_content = content[start_of_section_content:].rstrip()
                section_content += f"\n{new_memory_item}"
                content = content[:start_of_section_content] + section_content + "\n"
            else:
                # Memory section is in the middle of the file
                before_section = content[:start_of_section_content]
                section_content = content[start_of_section_content:next_header_index].rstrip()
                after_section = content[next_header_index:]
                
                section_content += f"\n{new_memory_item}"
                content = before_section + section_content + "\n\n" + after_section

        with open(memory_file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Okay, I've remembered that: \"{processed_fact}\""

    except Exception as e:
        return f"Error saving fact to memory: {e}"