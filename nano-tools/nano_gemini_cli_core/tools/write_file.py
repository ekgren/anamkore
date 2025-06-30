# nano-tools/nano_gemini_cli_core/tools/write_file.py
import os
from openai_agents import function_tool
import litellm

def _is_path_within_root(path_to_check: str, root_directory: str) -> bool:
    """Checks if a path is within the root directory."""
    abs_root = os.path.abspath(root_directory)
    abs_path = os.path.abspath(path_to_check)
    return os.path.commonpath([abs_root, abs_path]) == abs_root

def _run_correction_agent(file_path: str, proposed_content: str) -> str:
    """
    Uses an LLM to review and potentially correct file content before writing.
    """
    print("Running content correction agent...")
    
    correction_prompt = f"""
        You are an expert code reviewer. The user wants to write the following content to the file `{file_path}`.
        Review the content for correctness, style, and potential errors. If you see any issues,
        correct them. If the code is good, return it as is.

        ---PROPOSED_CONTENT---
        {proposed_content}
        ---END_PROPOSED_CONTENT---

        Return only the final, corrected content, without any explanation or preamble.
    """
    
    try:
        response = litellm.completion(
            model="gemini/gemini-1.5-flash-latest",
            messages=[{"role": "user", "content": correction_prompt}]
        )
        corrected_content = response.choices[0].message.content
        return corrected_content
    except Exception as e:
        print(f"Content correction agent failed: {e}. Using original content.")
        return proposed_content

@function_tool
def write_file(file_path: str, content: str, agentic_correction: bool = False) -> str:
    """
    Writes content to a specified file, with security checks and optional agentic correction.

    Args:
        file_path: The absolute path to the file to write to. Must be within the project directory.
        content: The content to write to the file.
        agentic_correction: If True, an agentic loop will be used to review and correct the content
                            before writing. Defaults to False.
    """
    root_directory = os.getcwd()
    abs_file_path = os.path.abspath(file_path)

    # --- Security and Parameter Validation ---
    if not os.path.isabs(abs_file_path):
        return f"Error: File path '{file_path}' must be an absolute path."
    
    if not _is_path_within_root(abs_file_path, root_directory):
        return f"Error: File path '{file_path}' is outside the project directory."

    try:
        if os.path.isdir(abs_file_path):
            return f"Error: Path '{file_path}' is a directory, not a file."
    except OSError:
        pass # Path does not exist, which is fine for writing

    # --- Agentic Correction ---
    final_content = content
    if agentic_correction:
        final_content = _run_correction_agent(file_path, content)

    # --- File Writing Logic ---
    try:
        parent_dir = os.path.dirname(abs_file_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
            
        with open(abs_file_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
            
        if os.path.exists(file_path):
            return f"Successfully overwrote file: {file_path}"
        else:
            return f"Successfully created and wrote to new file: {file_path}"

    except Exception as e:
        return f"An unexpected error occurred while writing to the file: {e}"