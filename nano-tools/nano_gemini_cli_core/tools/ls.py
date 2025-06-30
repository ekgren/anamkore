# nano-tools/nano_gemini_cli_core/tools/ls.py
import os
import fnmatch
from agents import function_tool
from typing import List, Optional, Dict
from ..utils.git_utils import is_git_repository
from ..utils.paths import shorten_path
import subprocess

def _is_path_within_root(path_to_check: str, root_directory: str) -> bool:
    """Checks if a path is within the root directory."""
    abs_root = os.path.abspath(root_directory)
    abs_path = os.path.abspath(path_to_check)
    return os.path.commonpath([abs_root, abs_path]) == abs_root

def _get_git_ignored_files(path: str) -> List[str]:
    """Returns a list of files ignored by git in the given directory."""
    if not is_git_repository(path):
        return []
    try:
        result = subprocess.run(
            ['git', 'ls-files', '--others', '--ignored', '--exclude-standard', '.'],
            cwd=path, capture_output=True, text=True, check=True
        )
        return [os.path.basename(f) for f in result.stdout.strip().split('\n') if f]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

def _list_directory_impl(path: str = '.', respect_git_ignore: bool = True, ignore: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Core implementation for listing directory contents.
    """
    root_directory = os.getcwd()
    abs_path = os.path.abspath(path)

    if not _is_path_within_root(abs_path, root_directory):
        error_msg = f"Error: Path '{path}' is outside the project directory."
        return {"llm_content": error_msg, "display_content": error_msg}
    
    if not os.path.isdir(abs_path):
        error_msg = f"Error: Path '{path}' is not a valid directory."
        return {"llm_content": error_msg, "display_content": error_msg}

    try:
        all_contents = os.listdir(abs_path)
        
        filtered_contents = []
        git_ignored_files = set(_get_git_ignored_files(abs_path)) if respect_git_ignore else set()
        
        for name in all_contents:
            if name in git_ignored_files:
                continue
            if ignore and any(fnmatch.fnmatch(name, pattern) for pattern in ignore):
                continue
            filtered_contents.append(name)

        if not filtered_contents:
            msg = f"The directory '{shorten_path(path)}' is empty."
            return {"llm_content": msg, "display_content": msg}

        dirs = sorted([d for d in filtered_contents if os.path.isdir(os.path.join(abs_path, d))])
        files = sorted([f for f in filtered_contents if os.path.isfile(os.path.join(abs_path, f))])
        
        formatted_dirs = [f"[DIR] {d}" for d in dirs]
        final_listing = formatted_dirs + files
        
        llm_content = f"Directory listing for '{path}':\n" + "\n".join(final_listing)
        display_content = f"Listed {len(final_listing)} item(s) in '{shorten_path(path)}'."
        
        return {"llm_content": llm_content, "display_content": display_content}

    except Exception as e:
        error_msg = f"An error occurred: {e}"
        return {"llm_content": error_msg, "display_content": error_msg}

@function_tool
def list_directory(path: str = '.', respect_git_ignore: bool = True, ignore: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Lists the contents of a specified directory, with gitignore support and intelligent sorting.

    Args:
        path: The absolute path to the directory to list. Defaults to the current directory.
        respect_git_ignore: If True, files and directories ignored by git will be excluded. Defaults to True.
        ignore: A list of glob patterns to ignore.
        
    Returns:
        A dictionary containing 'llm_content' for the agent and 'display_content' for the user.
    """
    return _list_directory_impl(path, respect_git_ignore, ignore)
