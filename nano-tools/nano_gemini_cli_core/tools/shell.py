# nano-tools/nano_gemini_cli_core/tools/shell.py
import os
import sys
import asyncio
import subprocess
import tempfile
import time
from typing import Optional, Set, Callable, Awaitable

from openai_agents import function_tool

# --- Whitelist for approved commands ---
# In a real application, this would be part of a larger context object.
# For this self-contained tool, we'll use a global set.
COMMAND_WHITELIST: Set[str] = set()

def _is_path_within_root(path_to_check: str, root_directory: str) -> bool:
    """Checks if a path is within the root directory."""
    abs_root = os.path.abspath(root_directory)
    abs_path = os.path.abspath(path_to_check)
    return os.path.commonpath([abs_root, abs_path]) == abs_root

async def _stream_subprocess(
    command: str, 
    cwd: str, 
    update_callback: Callable[[str], Awaitable[None]]
) -> dict:
    """
    Executes a command and streams its output in real-time.
    Also handles background PID discovery.
    """
    is_windows = sys.platform == "win32"
    
    # --- Background PID Discovery Setup ---
    pgrep_file = ""
    if not is_windows:
        # Create a temporary file to store PIDs from pgrep
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            pgrep_file = tmp.name
        
        # Wrap the user's command to discover background PIDs
        # This is a direct port of the logic from gemini-cli's shell.ts
        original_command = command.strip()
        if not original_command.endswith('&'):
            original_command += ';'
        
        wrapped_command = (
            f"{{ {original_command} }}; "
            f"__code=$?; "
            f"pgrep -g 0 > {pgrep_file} 2>/dev/null; "
            f"exit $__code;"
        )
    else:
        wrapped_command = command

    # --- Process Execution with asyncio ---
    process = await asyncio.create_subprocess_shell(
        wrapped_command,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        preexec_fn=None if is_windows else os.setsid
    )

    async def read_stream(stream, stream_name):
        """Reads and forwards a stream (stdout/stderr) line by line."""
        while True:
            line = await stream.readline()
            if not line:
                break
            await update_callback(f"[{stream_name}] {line.decode().strip()}")
    
    # Start reading stdout and stderr concurrently
    await asyncio.gather(
        read_stream(process.stdout, "STDOUT"),
        read_stream(process.stderr, "STDERR")
    )

    returncode = await process.wait()

    # --- PID Discovery and Cleanup ---
    background_pids = []
    if not is_windows and os.path.exists(pgrep_file):
        with open(pgrep_file, 'r') as f:
            pids = [int(pid) for pid in f.read().strip().split('\n') if pid.isdigit()]
            # Exclude the main shell process PID
            background_pids = [pid for pid in pids if pid != process.pid]
        os.remove(pgrep_file)

    return {
        "returncode": returncode,
        "background_pids": background_pids,
        "pgid": None if is_windows else process.pid
    }

@function_tool
async def run_shell_command(
    command: str, 
    directory: Optional[str] = None,
    # In a real app, the CLI would pass a callback. We simulate it here.
    # For nano-tools, we'll just print to the console.
    update_callback: Optional[Callable[[str], Awaitable[None]]] = None
) -> str:
    """
    Executes a shell command, streams its output, and reports background processes.

    Args:
        command: The shell command to execute.
        directory: The directory to run the command in. Must be a relative path.
    """
    # --- Whitelist Check ---
    command_root = command.strip().split(' ')[0]
    if command_root in COMMAND_WHITELIST:
        print(f"Command '{command_root}' is whitelisted, skipping confirmation.")
    else:
        # In a real CLI, this is where you would prompt the user for confirmation.
        # For this library, we'll simulate auto-approval but show the concept.
        print(f"Confirmation would be required for: '{command}'")
        # Example of how a CLI would add to the whitelist:
        # if user_approves_always:
        #     COMMAND_WHITELIST.add(command_root)

    root_directory = os.getcwd()
    target_dir = os.path.abspath(os.path.join(root_directory, directory)) if directory else root_directory

    if not _is_path_within_root(target_dir, root_directory):
        return f"Error: Directory '{directory}' is outside the project root."

    async def default_callback(line: str):
        """A default callback that just prints the output."""
        print(line)

    callback = update_callback or default_callback

    try:
        result = await _stream_subprocess(command, target_dir, callback)
        
        # --- Structured Output ---
        output_parts = [
            f"Command: {command}",
            f"Directory: {directory or '(root)'}",
            f"Exit Code: {result['returncode']}",
            f"Process Group ID: {result['pgid'] or '(N/A on Windows)'}",
            f"Background PIDs: {result['background_pids'] or '(none)'}"
        ]
        return "\n---\n".join(output_parts)

    except Exception as e:
        return f"An unexpected error occurred: {e}"
