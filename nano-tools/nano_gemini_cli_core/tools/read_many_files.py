# nano-tools/nano_gemini_cli_core/tools/read_many_files.py
import os
import glob as py_glob
from agents import function_tool
from typing import List, Optional
from ..utils.git_utils import is_git_repository
import subprocess

DEFAULT_EXCLUDES = [
    '**/node_modules/**', '**/__pycache__/**', '**/.git/**', '**/.vscode/**',
    '**/dist/**', '**/build/**', '**/*.pyc', '**/*.pyo', '**/*.bin'
]

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

def _read_many_files_impl(
    paths: List[str], 
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    respect_git_ignore: bool = True
) -> Dict[str, str]:
    """
    Core implementation for reading and concatenating file contents.
    """
    root_directory = os.getcwd()
    all_patterns = paths + (include or [])
    
    # Combine user-provided excludes with defaults
    all_excludes = set(DEFAULT_EXCLUDES + (exclude or []))
    
    # --- File Discovery ---
    found_files = set()
    for pattern in all_patterns:
        # Ensure the pattern is joined with the root for searching
        search_pattern = os.path.join(root_directory, pattern)
        matched_files = py_glob.glob(search_pattern, recursive=True)
        for f in matched_files:
            if os.path.isfile(f):
                found_files.add(os.path.abspath(f))

    # --- Filtering ---
    files_to_read = []
    git_ignored_files = set(_get_git_ignored_files(root_directory)) if respect_git_ignore else set()

    for f_path in found_files:
        # Git ignore check
        if f_path in git_ignored_files:
            continue
        
        # Exclusion check
        is_excluded = False
        for pattern in all_excludes:
            if py_glob.fnmatch.fnmatch(f_path, os.path.join(root_directory, pattern)):
                is_excluded = True
                break
        if is_excluded:
            continue
            
        files_to_read.append(f_path)

    if not files_to_read:
        msg = "No files found matching the specified criteria."
        return {"llm_content": msg, "display_content": msg}

    # --- Content Reading and Formatting ---
    final_content = []
    for file_path in sorted(list(files_to_read)):
        relative_path = os.path.relpath(file_path, root_directory)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            final_content.append(f"--- {relative_path} ---\n{content}")
        except Exception as e:
            final_content.append(f"--- {relative_path} ---\nError reading file: {e}")
            
    llm_output = "\n\n".join(final_content)
    display_output = f"Read and combined {len(files_to_read)} file(s)."
    
    return {"llm_content": llm_output, "display_content": display_output}

@function_tool
def read_many_files(
    paths: List[str], 
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    respect_git_ignore: bool = True
) -> Dict[str, str]:
    """
    Reads and concatenates the content of multiple files matching glob patterns.

    Args:
        paths: A list of glob patterns or file paths to search for.
        include: A list of additional glob patterns to include.
        exclude: A list of glob patterns to exclude from the results.
        respect_git_ignore: If True, files ignored by git will be excluded. Defaults to True.
    """
    return _read_many_files_impl(paths, include, exclude, respect_git_ignore)