# nano-tools/scripts/generate_tool_docs.py
import os
import re

def get_tools_info_from_parsing():
    """
    Extracts tool information by parsing the raw text of the Python files.
    This avoids complex import issues.
    """
    tools_dir = os.path.join("nano-tools", "nano_gemini_cli_core", "tools")
    tools_info = []

    for filename in sorted(os.listdir(tools_dir)):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_path = os.path.join(tools_dir, filename)
            with open(module_path, "r", encoding="utf-8") as f:
                content = f.read()

                # Use regex to find the function signature and docstring
                # This looks for "@function_tool" followed by "def function_name(signature):" and a docstring.
                match = re.search(
                    r"@function_tool\s*\ndef\s+([a-zA-Z_]\w*)\s*(\([^)]*\))[^:]*:\s*\"\"\"(.*?)\"\"\"",
                    content,
                    re.DOTALL | re.MULTILINE
                )
                
                if match:
                    name, signature, docstring = match.groups()
                    tools_info.append({
                        "name": name,
                        "module": filename[:-3],
                        "signature": signature.strip(),
                        "docstring": docstring.strip(),
                    })
    return tools_info

def generate_docs():
    """Generates the tool_reference.md file."""
    tools_info = get_tools_info_from_parsing()
    
    md_content = "# Nano-Tools: Tool Reference\n\n"
    md_content += "This document provides a complete reference for all tools available in the `nano-tools` library. It is auto-generated from the docstrings of the tool functions.\n\n"

    for tool in tools_info:
        md_content += f"## `{tool['name']}`\n\n"
        md_content += f"**File:** `nano_gemini_cli_core/tools/{tool['module']}.py`\n\n"
        md_content += f"**Signature:** `def {tool['name']}{tool['signature']}`\n\n"
        md_content += "**Description:**\n"
        md_content += f"```\n{tool['docstring']}\n```\n\n"
        md_content += "---\n\n"

    output_path = os.path.join("nano-tools", "docs", "tool_reference.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write(md_content)
        
    print(f"Successfully generated tool documentation at '{output_path}'")

if __name__ == "__main__":
    generate_docs()