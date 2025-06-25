# aura_agent/fs_utils.py

import os
import json
from . import config

# --- Sandboxing Logic ---
SANDBOX_MAP = {
    "aura_agent": config.CODE_PATH, "README.md": config.CODE_PATH, "pyproject.toml": config.CODE_PATH, ".python-version": config.CODE_PATH,
    "0-Core": config.VAULT_PATH, "1-Inbox": config.VAULT_PATH, "2-Journal": config.VAULT_PATH,
    "3-Task_Queue.md": config.VAULT_PATH, "4-Async_Mailbox.md": config.VAULT_PATH, "Knowledge": config.VAULT_PATH,
}

def get_sandboxed_path(relative_path: str) -> str | None:
    """
    Validates and resolves a relative path to an absolute path within the sandboxed environment.
    Returns the absolute path if valid and within the sandbox, otherwise returns None.
    """
    # Normalize the path to resolve any '..' components and handle OS-specific separators.
    normalized_path = os.path.normpath(relative_path)

    # Security check: Prohibit absolute paths and directory traversal.
    if os.path.isabs(normalized_path) or ".." in normalized_path.split(os.sep):
        return None
    
    # Determine the base path (vault or code) from the first component of the relative path.
    first_part = normalized_path.split(os.sep)[0]
    if first_part == '.':
        base_path = config.VAULT_PATH
    else:
        base_path = SANDBOX_MAP.get(first_part)

    # If the first part does not map to a known sandbox area, deny access.
    if not base_path:
        return None
        
    # Construct the full, absolute path.
    full_path = os.path.abspath(os.path.join(base_path, normalized_path))
    
    # Final security check: Ensure the resolved path is still within the intended base path.
    if os.path.commonpath([base_path, full_path]) != base_path:
        return None
        
    return full_path

# --- Low-Level File System Tools ---

def list_files(path: str) -> str:
    """Lists files in a sandboxed directory."""
    full_path = get_sandboxed_path(path)
    if not full_path: return f"Error: Access denied or invalid path '{path}'."
    try:
        if not os.path.isdir(full_path): return f"Error: '{path}' is not a valid directory."
        return json.dumps(os.listdir(full_path))
    except Exception as e: return f"Error listing files in '{path}': {str(e)}"

def read_file(path: str) -> str:
    """Reads a file from the sandbox."""
    full_path = get_sandboxed_path(path)
    if not full_path: return f"Error: Access denied or invalid path '{path}'."
    try:
        if not os.path.exists(full_path): return f"Error: File not found at '{path}'."
        if not os.path.isfile(full_path): return f"Error: Path '{path}' is a directory, not a file."
        with open(full_path, 'r', encoding='utf-8') as f: return f.read()
    except Exception as e: return f"Error reading file '{path}': {str(e)}"

def write_file(path: str, content: str, overwrite: bool = False) -> str:
    """Writes to a file in the sandbox."""
    full_path = get_sandboxed_path(path)
    if not full_path: return f"Error: Access denied or invalid path '{path}'."
    try:
        if not overwrite and os.path.exists(full_path):
            return f"Error: File '{path}' already exists. Use overwrite=True to replace it."
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f: f.write(content)
        return f"Success: Wrote {len(content)} bytes to '{path}'."
    except Exception as e: return f"Error writing to file '{path}': {str(e)}"