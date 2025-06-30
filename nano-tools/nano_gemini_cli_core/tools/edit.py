# nano-tools/nano_gemini_cli_core/tools/edit.py
import os
import json
from typing import Optional, Dict
from openai_agents import function_tool
import litellm
from ..utils.paths import shorten_path

def _is_path_within_root(path_to_check: str, root_directory: str) -> bool:
    """Checks if a path is within the root directory."""
    abs_root = os.path.abspath(root_directory)
    abs_path = os.path.abspath(path_to_check)
    return os.path.commonpath([abs_root, abs_path]) == abs_root

def _run_correction_agent(file_path: str, old_string: str, new_string: str, file_content: str) -> Optional[str]:
    """If the initial replacement fails, this function calls the LLM to correct the 'old_string'."""
    print("Initial replacement failed. Attempting to correct with an agentic loop...")
    
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
            model="gemini/gemini-1.5-flash-latest",
            messages=[{"role": "user", "content": correction_prompt}],
            response_format={"type": "json_object"}
        )
        corrected_json = json.loads(response.choices[0].message.content)
        corrected_string = corrected_json.get("corrected_string")
        
        if corrected_string and corrected_string in file_content:
            print(f"Agentic loop succeeded. Found corrected string.")
            return corrected_string
        else:
            print("Agentic loop failed: Corrected string not found in file.")
            return None
            
    except Exception as e:
        print(f"An unexpected error occurred during the agentic correction loop: {e}")
        return None

@function_tool
def replace(file_path: str, old_string: str, new_string: str, expected_replacements: int = 1) -> Dict[str, str]:
    """
    Replaces a specified number of occurrences of a string in a file.

    Args:
        file_path: The absolute path to the file to modify. Must be within the project's root directory.
        old_string: The exact string to be replaced.
        new_string: The string to replace the old_string with.
        expected_replacements: The number of times the old_string is expected to be found and replaced.
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
        actual_occurrences = content.count(string_to_replace)
        
        if actual_occurrences == 0 and expected_replacements > 0:
            corrected_string = _run_correction_agent(abs_file_path, old_string, new_string, content)
            if corrected_string:
                string_to_replace = corrected_string
                actual_occurrences = content.count(string_to_replace)
            else:
                error_msg = "Error: The string to replace was not found, and the agentic correction failed."
                return {"llm_content": error_msg, "display_content": error_msg}

        if actual_occurrences != expected_replacements:
            error_msg = f"Error: Expected {expected_replacements} occurrences, but found {actual_occurrences}."
            return {"llm_content": error_msg, "display_content": error_msg}
            
        new_content = content.replace(string_to_replace, new_string, expected_replacements)
        
        with open(abs_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        msg = f"Successfully replaced {expected_replacements} occurrence(s) in {file_path}."
        return {"llm_content": msg, "display_content": f"Replaced {expected_replacements} occurrence(s) in {shorten_path(file_path)}."}

    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        return {"llm_content": error_msg, "display_content": error_msg}
