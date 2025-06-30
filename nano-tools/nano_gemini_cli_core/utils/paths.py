# nano-tools/nano_gemini_cli_core/utils/paths.py
import os
import hashlib

def tildeify_path(path: str) -> str:
    """Replaces the home directory with a tilde."""
    home_dir = os.path.expanduser("~")
    if path.startswith(home_dir):
        return path.replace(home_dir, "~", 1)
    return path

def shorten_path(file_path: str, max_len: int = 35) -> str:
    """
    Shortens a path string if it exceeds maxLen, prioritizing the start and end segments.
    This is a direct port of the logic from the gemini-cli TypeScript implementation.
    """
    if len(file_path) <= max_len:
        return file_path

    try:
        drive, path_no_drive = os.path.splitdrive(file_path)
        segments = path_no_drive.split(os.sep)
        segments = [s for s in segments if s]

        if len(segments) <= 2:
            keep_len = (max_len - 3) // 2
            if keep_len <= 0:
                return "..." + file_path[-(max_len-3):]
            return f"{file_path[:keep_len]}...{file_path[-keep_len:]}"

        start_component = os.path.join(drive, segments[0])
        last_segment = segments[-1]
        
        end_part_segments = []
        current_length = len(last_segment)

        for i in range(len(segments) - 2, 0, -1):
            segment = segments[i]
            if current_length + len(os.sep) + len(segment) > max_len - len(start_component) - len("..."):
                break
            end_part_segments.insert(0, segment)
            current_length += len(os.sep) + len(segment)
        
        if not end_part_segments:
            return f"{start_component}{os.sep}...{os.sep}{last_segment}"

        middle_part = os.path.join(*end_part_segments)
        return f"{start_component}{os.sep}...{os.sep}{middle_part}{os.sep}{last_segment}"

    except Exception:
        if len(file_path) > max_len:
            return "..." + file_path[-(max_len - 3):]
        return file_path

def make_relative(target_path: str, root_directory: str) -> str:
    """Calculates the relative path from a root directory to a target path."""
    resolved_target_path = os.path.abspath(target_path)
    resolved_root_directory = os.path.abspath(root_directory)
    relative_path = os.path.relpath(resolved_target_path, resolved_root_directory)
    return relative_path or '.'

def escape_path(file_path: str) -> str:
    """Escapes spaces in a file path for shell commands."""
    return file_path.replace(' ', '\\ ')

def unescape_path(file_path: str) -> str:
    """Unescapes spaces in a file path."""
    return file_path.replace('\\ ', ' ')

def get_project_hash(project_root: str) -> str:
    """Generates a unique hash for a project based on its root path."""
    return hashlib.sha256(project_root.encode('utf-8')).hexdigest()

def get_project_temp_dir(project_root: str) -> str:
    """Generates a unique temporary directory path for a project."""
    project_hash = get_project_hash(project_root)
    return os.path.join(os.path.expanduser("~"), ".gemini", "tmp", project_hash)