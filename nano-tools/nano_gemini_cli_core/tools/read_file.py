# nano-tools/nano_gemini_cli_core/tools/read_file.py
import os
from agents import function_tool
from typing import Optional, List, Dict
import fnmatch
from ..utils.paths import shorten_path

def _is_path_within_root(path_to_check: str, root_directory: str) -> bool:
    """Checks if a path is within the root directory."""
    abs_root = os.path.abspath(root_directory)
    abs_path = os.path.abspath(path_to_check)
    return os.path.commonpath([abs_root, abs_path]) == abs_root

def _get_gemini_ignored_patterns(root_directory: str) -> List[str]:
    """Reads patterns from a .geminiignore file in the root directory."""
    ignore_file = os.path.join(root_directory, ".geminiignore")
    if not os.path.exists(ignore_file):
        return []
    with open(ignore_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def _read_file_impl(absolute_path: str, offset: Optional[int] = None, limit: Optional[int] = None) -> Dict[str, str]:
    """
    Core implementation for reading file content.
    """
    root_directory = os.getcwd()

    if not os.path.isabs(absolute_path):
        error_msg = f"Error: File path must be absolute. You provided '{absolute_path}'."
        return {"llm_content": error_msg, "display_content": error_msg}
    
    if not _is_path_within_root(absolute_path, root_directory):
        error_msg = f"Error: File path '{absolute_path}' is outside the project directory."
        return {"llm_content": error_msg, "display_content": error_msg}

    if (offset is not None and offset < 0) or (limit is not None and limit <= 0):
        error_msg = "Error: 'offset' must be non-negative and 'limit' must be positive."
        return {"llm_content": error_msg, "display_content": error_msg}
        
    if offset is not None and limit is None:
        error_msg = "Error: 'offset' cannot be used without 'limit'."
        return {"llm_content": error_msg, "display_content": error_msg}

    ignored_patterns = _get_gemini_ignored_patterns(root_directory)
    relative_path = os.path.relpath(absolute_path, root_directory)
    if any(fnmatch.fnmatch(relative_path, pattern) for pattern in ignored_patterns):
        error_msg = f"Error: File '{relative_path}' is ignored by a .geminiignore rule."
        return {"llm_content": error_msg, "display_content": error_msg}

    try:
        with open(absolute_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        content_to_return = "".join(lines)
        display_message = f"Read {len(lines)} lines from {shorten_path(relative_path)}."

        if offset is not None and limit is not None:
            start = offset
            end = offset + limit
            paginated_lines = lines[start:end]
            
            if not paginated_lines:
                content_to_return = f"Content from lines {start}-{end} is empty or out of bounds."
            else:
                content_to_return = "".join(paginated_lines)
            
            display_message = f"Read {len(paginated_lines)} lines (from {start}-{end}) from {shorten_path(relative_path)}."

        return {"llm_content": content_to_return, "display_content": display_message}

    except FileNotFoundError:
        error_msg = f"Error: File not found at '{absolute_path}'"
        return {"llm_content": error_msg, "display_content": error_msg}
    except Exception as e:
        error_msg = f"An unexpected error occurred while reading the file: {e}"
        return {"llm_content": error_msg, "display_content": error_msg}

@function_tool
def read_file(absolute_path: str, offset: Optional[int] = None, limit: Optional[int] = None) -> Dict[str, str]:
    """
    Reads and returns the content of a specified file, with support for pagination.

    Args:
        absolute_path: The absolute path to the file to read. Must be within the project directory.
        offset: The 0-based line number to start reading from. Requires 'limit' to be set.
        limit: The maximum number of lines to read. Use with 'offset' for pagination.
        
    Returns:
        A dictionary containing 'llm_content' for the agent and 'display_content' for the user.
    """
    return _read_file_impl(absolute_path, offset, limit)
