# nano-tools/nano_gemini_cli_core/tools/edit.py
import os
import json
import re
from typing import Optional, Dict, Any
from agents import function_tool
import litellm
from ..utils.paths import shorten_path

CORRECTION_CACHE: Dict[str, Dict[str, Any]] = {}

def _is_path_within_root(path_to_check: str, root_directory: str) -> bool:
    """Checks if a path is within the root directory."""
    abs_root = os.path.abspath(root_directory)
    abs_path = os.path.abspath(path_to_check)
    return os.path.commonpath([abs_root, abs_path]) == abs_root

def _over_unescaping(s: str) -> str:
    """Handles common LLM escaping issues."""
    return s.replace('\`', '`')

def _run_correction_agent(
    file_path: str, old_string: str, new_string: str, file_content: str
) -> Optional[Dict[str, Any]]:
    """If the initial replacement fails, this function calls the LLM to correct the 'old_string'."""
    cache_key = f"{file_path}:{old_string}:{new_string}"
    if cache_key in CORRECTION_CACHE:
        return CORRECTION_CACHE[cache_key]

    print("Initial replacement failed. Attempting to correct with an agentic loop...")
    
    unescaped_old_string = _over_unescaping(old_string)
    occurrences = len(re.findall(re.escape(unescaped_old_string), file_content))
    
    if occurrences > 0:
        result = {
            "params": {"old_string": unescaped_old_string, "new_string": new_string},
            "occurrences": occurrences,
        }
        CORRECTION_CACHE[cache_key] = result
        return result

    correction_prompt = f"""
        You are an expert code editor. Your task is to correct an `old_string` that failed to be replaced in a file because it didn't exactly match the file's content.
        The user wanted to replace this text:
        ---OLD_STRING---
        {old_string}
        ---END_OLD_STRING---
        With this new text:
        ---NEW_STRING---
        {new_string}
        ---END_NEW_STRING---
        However, the `old_string` was not found in the file. Here is the full content of the file (`{file_path}`):
        ---FILE_CONTENT---
        {file_content}
        ---END_FILE_CONTENT---
        Your job is to analyze the original `old_string` and the `file_content` to find the segment of text that the user *most likely* intended to replace. It might have subtle differences in whitespace, comments, or surrounding characters.
        Respond with a JSON object containing the corrected string that EXACTLY matches the file content. The JSON object should have a single key, "corrected_string".
        Example Response:
        {{
          "corrected_string": "the exact text from the file to be replaced"
        }}
    """
    
    try:
        response = litellm.completion(
            model="gemini/gemini-2.5-flash-lite-preview-06-17",
            messages=[{"role": "user", "content": correction_prompt}],
            response_format={"type": "json_object"}
        )
        corrected_json = json.loads(response.choices[0].message.content)
        corrected_old_string = corrected_json.get("corrected_string")
        
        if not corrected_old_string or corrected_old_string not in file_content:
            print("Agentic loop failed: Corrected string not found in file.")
            return None

        print(f"Agentic loop succeeded. Found corrected string.")
        
        corrected_occurrences = len(re.findall(re.escape(corrected_old_string), file_content))
        
        diff = len(corrected_old_string) - len(old_string)
        corrected_new_string = new_string + (' ' * diff if diff > 0 else '')

        result = {
            "params": {
                "old_string": corrected_old_string,
                "new_string": corrected_new_string,
            },
            "occurrences": corrected_occurrences,
        }
        CORRECTION_CACHE[cache_key] = result
        return result
            
    except Exception as e:
        print(f"An unexpected error occurred during the agentic correction loop: {e}")
        return None

def _replace_impl(file_path: str, old_string: str, new_string: str, expected_replacements: int = 1) -> Dict[str, str]:
    """
    Core implementation for replacing a string in a file.
    """
    root_directory = os.getcwd()
    abs_file_path = os.path.abspath(file_path)

    if not os.path.isabs(abs_file_path):
        error_msg = f"Error: File path '{file_path}' must be an absolute path."
        return {"llm_content": error_msg, "display_content": error_msg}
    
    if not _is_path_within_root(abs_file_path, root_directory):
        error_msg = f"Error: File path '{file_path}' must be within the project directory."
        return {"llm_content": error_msg, "display_content": error_msg}

    file_exists = os.path.exists(abs_file_path)

    if old_string == "" and not file_exists:
        try:
            parent_dir = os.path.dirname(abs_file_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(abs_file_path, 'w', encoding='utf-8') as f:
                f.write(new_string)
            msg = f"Successfully created new file: {file_path}"
            return {"llm_content": msg, "display_content": f"Created {shorten_path(file_path)}"}
        except Exception as e:
            error_msg = f"Error creating file: {e}"
            return {"llm_content": error_msg, "display_content": error_msg}

    if old_string == "" and file_exists:
        error_msg = f"Error: Attempted to create a file that already exists at '{file_path}'."
        return {"llm_content": error_msg, "display_content": error_msg}

    if not file_exists:
        error_msg = f"Error: File not found at '{file_path}'."
        return {"llm_content": error_msg, "display_content": error_msg}

    try:
        with open(abs_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        string_to_replace = old_string
        string_to_write = new_string
        actual_occurrences = len(re.findall(re.escape(string_to_replace), content))
        
        if actual_occurrences == 0 and expected_replacements > 0:
            correction_result = _run_correction_agent(abs_file_path, old_string, new_string, content)
            if correction_result:
                string_to_replace = correction_result["params"]["old_string"]
                string_to_write = correction_result["params"]["new_string"]
                actual_occurrences = correction_result["occurrences"]
            else:
                error_msg = "Error: The string to replace was not found, and the agentic correction failed."
                return {"llm_content": error_msg, "display_content": error_msg}

        if actual_occurrences != expected_replacements:
            error_msg = f"Error: Expected {expected_replacements} occurrences, but found {actual_occurrences}."
            return {"llm_content": error_msg, "display_content": error_msg}
            
        new_content = content.replace(string_to_replace, string_to_write, expected_replacements)
        
        with open(abs_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        msg = f"Successfully replaced {expected_replacements} occurrence(s) in {file_path}."
        return {"llm_content": msg, "display_content": f"Replaced {expected_replacements} occurrence(s) in {shorten_path(file_path)}."}

    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        return {"llm_content": error_msg, "display_content": error_msg}

@function_tool
def replace(file_path: str, old_string: str, new_string: str, expected_replacements: int = 1) -> Dict[str, str]:
    """
    Replaces text within a file. By default, replaces a single occurrence, 
    but can replace multiple occurrences when `expected_replacements` is specified. 
    This tool requires providing significant context around the change to ensure precise targeting. 
    Always use the read_file tool to examine the file's current content before attempting a text replacement.

    Args:
        file_path (str): The absolute path to the file to modify. Must start with '/'.
        old_string (str): The exact literal text to replace. For single replacements, include at least 3 lines of context BEFORE and AFTER the target text, matching whitespace and indentation precisely. If this string matches multiple locations, or does not match exactly, the tool will fail.
        new_string (str): The exact literal text to replace `old_string` with. Ensure the resulting code is correct and idiomatic.
        expected_replacements (int): Number of replacements expected. Defaults to 1. Use when you want to replace multiple occurrences.
    """
    return _replace_impl(file_path, old_string, new_string, expected_replacements)
