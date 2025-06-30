# nano-tools/test_tools.py
import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Annotated
import os

# --- Import all our tools ---
# We assume this script is run from the root of the 'nano-tools' directory
# and that the package is installed in editable mode.
from nano_gemini_cli_core.tools.edit import _replace_impl as replace
from nano_gemini_cli_core.tools.glob import _glob_impl as glob
from nano_gemini_cli_core.tools.grep import _search_file_content_impl as search_file_content
from nano_gemini_cli_core.tools.ls import _list_directory_impl as list_directory
from nano_gemini_cli_core.tools.read_file import _read_file_impl as read_file
from nano_gemini_cli_core.tools.shell import _run_shell_command_impl as run_shell_command
from nano_gemini_cli_core.tools.write_file import _write_file_impl as write_file

app = typer.Typer(help="A CLI to test the nano-gemini-cli tools in a standalone fashion.")
console = Console()

def _print_result(result: dict | str):
    """Prints the structured result from a tool call in a nice format."""
    if isinstance(result, str):
        console.print(result)
        return

    table = Table(title="Tool Call Result")
    table.add_column("Output Type", style="cyan")
    table.add_column("Content", style="magenta")

    table.add_row("Display Content", result.get('display_content', 'N/A'))
    table.add_row("LLM Content", result.get('llm_content', 'N/A'))
    
    console.print(table)

@app.command(name="ls")
def test_ls(path: Annotated[str, typer.Option(help="The path to list.")] = '.'):
    """Tests the list_directory tool."""
    console.print(f"[bold]Testing 'list_directory' on path: '{path}'[/bold]\n")
    result = list_directory(path=path)
    _print_result(result)

@app.command(name="read-file")
def test_read_file(file_path: Annotated[str, typer.Argument(help="The file to read.")]):
    """Tests the read_file tool."""
    console.print(f"[bold]Testing 'read_file' on file: '{file_path}'[/bold]\n")
    # Ensure we use an absolute path as the tool expects
    abs_path = os.path.abspath(file_path)
    result = read_file(absolute_path=abs_path)
    _print_result(result)

@app.command(name="glob")
def test_glob(pattern: Annotated[str, typer.Option(help="The glob pattern.")]):
    """Tests the glob tool."""
    console.print(f"[bold]Testing 'glob' with pattern: '{pattern}'[/bold]\n")
    result = glob(pattern=pattern)
    _print_result(result)

@app.command(name="grep")
def test_grep(pattern: Annotated[str, typer.Option(help="The regex pattern.")], path: Annotated[str, typer.Option(help="The path to search.")] = '.'):
    """Tests the search_file_content tool."""
    console.print(f"[bold]Testing 'grep' with pattern: '{pattern}' in '{path}'[/bold]\n")
    result = search_file_content(pattern=pattern, path=path)
    _print_result(result)

@app.command(name="edit")
def test_edit(
    file_path: Annotated[str, typer.Option(help="The file to edit.")],
    old_string: Annotated[str, typer.Option(help="The string to replace.")],
    new_string: Annotated[str, typer.Option(help="The new string.")],
):
    """Tests the replace tool."""
    console.print(f"[bold]Testing 'edit' on file: '{file_path}'[/bold]\n")
    abs_path = os.path.abspath(file_path)
    result = replace(file_path=abs_path, old_string=old_string, new_string=new_string)
    _print_result(result)


@app.command(name="write-file")
def test_write_file(
    file_path: Annotated[str, typer.Option(help="The file to write to.")],
    content: Annotated[str, typer.Option(help="The content to write.")],
):
    """Tests the write_file tool."""
    console.print(f"[bold]Testing 'write_file' on file: '{file_path}'[/bold]\n")
    abs_path = os.path.abspath(file_path)
    result = write_file(file_path=abs_path, content=content)
    _print_result(result)

@app.command(name="shell")
def test_shell(command: Annotated[str, typer.Argument(help="The shell command to run.")]):
    """Tests the run_shell_command tool."""
    console.print(f"[bold]Testing 'shell' with command: '{command}'[/bold]\n")
    # This tool is async, so we need to run it in an event loop
    import asyncio
    result = asyncio.run(run_shell_command(command=command))
    _print_result(result)


if __name__ == "__main__":
    app()
