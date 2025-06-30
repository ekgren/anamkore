# nano-tools/nano_gemini_cli_core/tools/glob.py
import os
import glob as py_glob
import time
import fnmatch
from agents import function_tool
from typing import List, Optional, Dict
from ..utils.git_utils import is_git_repository
from ..utils.paths import shorten_path
import subprocess

def _get_git_ignored_files(path: str) -> List[str]:
    """Returns a list of absolute paths for files ignored by git."""
    if not is_git_repository(path):
        return []
    try:
        result = subprocess.run(
            ['git', 'ls-files', '--others', '--ignored', '--exclude-standard'],
            cwd=path, capture_output=True, text=True, check=True
        )
        return [os.path.abspath(os.path.join(path, f)) for f in result.stdout.strip().split('\n') if f]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

def _sort_file_entries(entries: List[str]) -> List[str]:
    """
    Sorts file entries based on recency and then alphabetically.
    """
    now_timestamp = time.time()
    recency_threshold_s = 24 * 60 * 60

    def sort_key(file_path):
        try:
            mtime = os.path.getmtime(file_path)
            is_recent = (now_timestamp - mtime) < recency_threshold_s
            if is_recent:
                return (1, -mtime)
            else:
                return (0, file_path)
        except FileNotFoundError:
            return (0, file_path)

    return sorted(entries, key=sort_key, reverse=True)

def _glob_impl(pattern: str, path: str = '.', case_sensitive: bool = False, respect_git_ignore: bool = True) -> Dict[str, str]:
    """
    Core implementation for finding files matching a glob pattern.
    """
    try:
        search_path = os.path.join(path, pattern)
        
        # Perform a case-insensitive glob first
        all_files = py_glob.glob(search_path, recursive=True)
        
        # If case_sensitive is True, filter the results
        if case_sensitive:
            # We need to construct the full pattern for fnmatchcase
            full_pattern = os.path.join(os.path.abspath(path), pattern)
            all_files = [f for f in all_files if fnmatch.fnmatchcase(os.path.abspath(f), full_pattern)]

        files_only = [f for f in all_files if os.path.isfile(f)]

        if respect_git_ignore:
            ignored_files = set(_get_git_ignored_files(path))
            if ignored_files:
                files_only = [f for f in files_only if os.path.abspath(f) not in ignored_files]

        if not files_only:
            msg = f"No files found matching pattern: {pattern}"
            return {"llm_content": msg, "display_content": msg}

        sorted_files = _sort_file_entries(files_only)
        
        llm_content = "\n".join(sorted_files)
        display_content = f"Found {len(sorted_files)} matching file(s)."
        
        return {"llm_content": llm_content, "display_content": display_content}
        
    except Exception as e:
        error_msg = f"An error occurred during glob operation: {e}"
        return {"llm_content": error_msg, "display_content": error_msg}

@function_tool
def glob(pattern: str, path: str = '.', case_sensitive: bool = False, respect_git_ignore: bool = True) -> Dict[str, str]:
    """
    Finds all pathnames matching a specified pattern, with intelligent sorting and gitignore support.

    Args:
        pattern: The glob pattern to search for (e.g., 'src/**/*.py', '*.md').
        path: The directory to search in. Defaults to the current directory.
        case_sensitive: If True, the search will be case-sensitive. Defaults to False.
        respect_git_ignore: If True, files and directories ignored by git will be excluded. Defaults to True.
        
    Returns:
        A dictionary containing 'llm_content' for the agent and 'display_content' for the user.
    """
    return _glob_impl(pattern, path, case_sensitive, respect_git_ignore)