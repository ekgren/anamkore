# Nano-Tools: Tool Reference

This document provides a complete reference for all tools available in the `nano-tools` library. It is auto-generated from the docstrings of the tool functions.

## `replace`

**File:** `nano_gemini_cli_core/tools/edit.py`

**Signature:** `def replace(file_path: str, old_string: str, new_string: str, expected_replacements: int = 1)`

**Description:**
```
Replaces a specified number of occurrences of a string in a file.

    Args:
        file_path: The absolute path to the file to modify. Must be within the project's root directory.
        old_string: The exact string to be replaced.
        new_string: The string to replace the old_string with.
        expected_replacements: The number of times the old_string is expected to be found and replaced.
```

---

## `glob`

**File:** `nano_gemini_cli_core/tools/glob.py`

**Signature:** `def glob(pattern: str, path: str = '.', case_sensitive: bool = False, respect_git_ignore: bool = True)`

**Description:**
```
Finds all pathnames matching a specified pattern, with intelligent sorting and gitignore support.

    Args:
        pattern: The glob pattern to search for (e.g., 'src/**/*.py', '*.md').
        path: The directory to search in. Defaults to the current directory.
        case_sensitive: If True, the search will be case-sensitive. Defaults to False.
        respect_git_ignore: If True, files and directories ignored by git will be excluded. Defaults to True.
        
    Returns:
        A dictionary containing 'llm_content' for the agent and 'display_content' for the user.
```

---

## `search_file_content`

**File:** `nano_gemini_cli_core/tools/grep.py`

**Signature:** `def search_file_content(pattern: str, path: str = '.', include: Optional[str] = None)`

**Description:**
```
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
```

---

## `list_directory`

**File:** `nano_gemini_cli_core/tools/ls.py`

**Signature:** `def list_directory(path: str = '.', respect_git_ignore: bool = True, ignore: Optional[List[str]] = None)`

**Description:**
```
Lists the contents of a specified directory, with gitignore support and intelligent sorting.

    Args:
        path: The absolute path to the directory to list. Defaults to the current directory.
        respect_git_ignore: If True, files and directories ignored by git will be excluded. Defaults to True.
        ignore: A list of glob patterns to ignore.
        
    Returns:
        A dictionary containing 'llm_content' for the agent and 'display_content' for the user.
```

---

## `save_memory`

**File:** `nano_gemini_cli_core/tools/memory_tool.py`

**Signature:** `def save_memory(fact: str)`

**Description:**
```
Saves a specific fact to the global long-term memory file (~/.gemini/GEMINI.md).
    This is useful for remembering user preferences or key details across sessions.

    Args:
        fact: The fact to remember. Should be a clear, self-contained statement.
```

---

## `read_file`

**File:** `nano_gemini_cli_core/tools/read_file.py`

**Signature:** `def read_file(absolute_path: str, offset: Optional[int] = None, limit: Optional[int] = None)`

**Description:**
```
Reads and returns the content of a specified file, with support for pagination.

    Args:
        absolute_path: The absolute path to the file to read. Must be within the project directory.
        offset: The 0-based line number to start reading from. Requires 'limit' to be set.
        limit: The maximum number of lines to read. Use with 'offset' for pagination.
        
    Returns:
        A dictionary containing 'llm_content' for the agent and 'display_content' for the user.
```

---

## `read_many_files`

**File:** `nano_gemini_cli_core/tools/read_many_files.py`

**Signature:** `def read_many_files(
    paths: List[str], 
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    respect_git_ignore: bool = True
)`

**Description:**
```
Reads and concatenates the content of multiple files matching glob patterns.

    Args:
        paths: A list of glob patterns or file paths to search for.
        include: A list of additional glob patterns to include.
        exclude: A list of glob patterns to exclude from the results.
        respect_git_ignore: If True, files ignored by git will be excluded. Defaults to True.
```

---

## `web_fetch`

**File:** `nano_gemini_cli_core/tools/web_fetch.py`

**Signature:** `def web_fetch(prompt: str)`

**Description:**
```
Processes content from URL(s) embedded in a prompt. It first tries to let the main agent
    handle the fetching and processing. If that provides no meaningful result, it falls back
    to a manual fetch and clean of the URL content.

    Args:
        prompt: A comprehensive prompt that includes the URL(s) to fetch and specific
                instructions on how to process their content (e.g., "Summarize https://example.com").
```

---

## `google_web_search`

**File:** `nano_gemini_cli_core/tools/web_search.py`

**Signature:** `def google_web_search(query: str)`

**Description:**
```
Performs a web search using the Gemini API's built-in Google Search tool
    and returns a formatted result with sources.

    Args:
        query: The search query to find information on the web.
```

---

## `write_file`

**File:** `nano_gemini_cli_core/tools/write_file.py`

**Signature:** `def write_file(file_path: str, content: str, agentic_correction: bool = False)`

**Description:**
```
Writes content to a specified file, with security checks and optional agentic correction.

    Args:
        file_path: The absolute path to the file to write to. Must be within the project directory.
        content: The content to write to the file.
        agentic_correction: If True, an agentic loop will be used to review and correct the content
                            before writing. Defaults to False.
```

---

