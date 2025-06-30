# nano-tools/nano_gemini_cli_core/tools/grep.py
import os
import re
import subprocess
import shutil
import fnmatch
from typing import Optional, List, Dict
from agents import function_tool
from ..utils.git_utils import is_git_repository

def _parse_grep_output(output: str, base_path: str) -> Dict[str, List[str]]:
    """Parses raw grep output into a dictionary grouped by file path."""
    matches_by_file: Dict[str, List[str]] = {}
    for line in output.strip().split('\n'):
        if not line:
            continue
        
        parts = line.split(':', 2)
        if len(parts) < 3:
            continue
            
        file_path, line_num, line_content = parts
        
        # Ensure the file path is relative to the search path for consistency
        full_path = os.path.join(base_path, file_path)
        relative_path = os.path.relpath(full_path, base_path)

        if relative_path not in matches_by_file:
            matches_by_file[relative_path] = []
        
        matches_by_file[relative_path].append(f"L{line_num}: {line_content.strip()}")
        
    return matches_by_file

def _format_matches(matches_by_file: Dict[str, List[str]], pattern: str) -> Dict[str, str]:
    """Formats the parsed matches into a final, readable string."""
    total_matches = sum(len(lines) for lines in matches_by_file.values())
    match_term = "match" if total_matches == 1 else "matches"
    
    llm_output = [f"Found {total_matches} {match_term} for pattern \"{pattern}\":\n---"]
    
    for file_path, lines in sorted(matches_by_file.items()):
        llm_output.append(f"File: {file_path}")
        llm_output.extend(lines)
        llm_output.append("---")
        
    display_output = f"Found {total_matches} {match_term} in {len(matches_by_file)} file(s) for pattern '{pattern}'."
    
    return {"llm_content": "\n".join(llm_output), "display_content": display_output}

def _search_file_content_impl(pattern: str, path: str = '.', include: Optional[str] = None) -> Dict[str, str]:
    """
    Core implementation for searching file content.
    """
    search_path = os.path.abspath(path)
    if not os.path.isdir(search_path):
        msg = f"Error: The specified path '{path}' is not a valid directory."
        return {"llm_content": msg, "display_content": msg}

    # --- Strategy 1: git grep ---
    if shutil.which('git') and is_git_repository(search_path):
        try:
            command = ['git', 'grep', '--untracked', '-n', '-E', '--ignore-case', pattern]
            if include:
                command.extend(['--', include])
            
            process = subprocess.run(command, cwd=search_path, capture_output=True, text=True, encoding='utf-8')
            if process.returncode == 0 and process.stdout:
                parsed = _parse_grep_output(process.stdout, search_path)
                return _format_matches(parsed, pattern)
            elif process.returncode == 1:
                msg = "No matches found."
                return {"llm_content": msg, "display_content": msg}
        except Exception:
            pass # Fall through to other strategies

    # --- Strategy 2: System grep ---
    if shutil.which('grep'):
        try:
            command = ['grep', '-r', '-n', '-H', '-E', '--exclude-dir=.git', '--exclude-dir=node_modules', pattern, '.']
            process = subprocess.run(command, cwd=search_path, capture_output=True, text=True, encoding='utf-8')
            if process.returncode == 0 and process.stdout:
                parsed = _parse_grep_output(process.stdout, search_path)
                return _format_matches(parsed, pattern)
            elif process.returncode == 1:
                msg = "No matches found."
                return {"llm_content": msg, "display_content": msg}
        except Exception:
            pass # Fall through to Python fallback

    # --- Strategy 3: Pure Python Fallback ---
    matches_by_file: Dict[str, List[str]] = {}
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        msg = f"Error: Invalid regular expression: {e}"
        return {"llm_content": msg, "display_content": msg}

    for root, _, files in os.walk(search_path):
        if '.git' in root.split(os.sep) or 'node_modules' in root.split(os.sep):
            continue
        for filename in files:
            if include and not fnmatch.fnmatch(filename, include):
                continue
            
            file_path = os.path.join(root, filename)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            relative_path = os.path.relpath(file_path, search_path)
                            if relative_path not in matches_by_file:
                                matches_by_file[relative_path] = []
                            matches_by_file[relative_path].append(f"L{line_num}: {line.strip()}")
            except Exception:
                continue
    
    if not matches_by_file:
        msg = "No matches found."
        return {"llm_content": msg, "display_content": msg}

    return _format_matches(matches_by_file, pattern)

@function_tool
def search_file_content(pattern: str, path: str = '.', include: Optional[str] = None) -> Dict[str, str]:
    """
    Searches for a regular expression pattern within file contents.

    This tool uses a prioritized search strategy:
    1. `git grep`: If the search directory is a Git repository and `git` is available. This is the fastest method.
    2. System `grep`: If `git` is not applicable, it uses the system's `grep` command.
    3. Python fallback: If neither `git` nor `grep` is available, it performs a manual search.

    Args:
        pattern: The regular expression (regex) pattern to search for.
        path: The directory to search in. Defaults to the current directory.
        include: A glob pattern to filter which files are searched (e.g., "*.py", "src/**/*.js").
    
    Returns:
        A formatted string of the search results or a message if no matches are found.
    """
    return _search_file_content_impl(pattern, path, include)