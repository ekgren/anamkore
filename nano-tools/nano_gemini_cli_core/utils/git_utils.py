# nano-tools/nano_gemini_cli_core/utils/git_utils.py
import os

def is_git_repository(directory: str) -> bool:
    """
    Checks if a directory is within a git repository by searching for a .git file or directory.
    This method does not require the 'git' command to be installed.

    Args:
        directory: The directory to start searching from.

    Returns:
        True if the directory is in a git repository, False otherwise.
    """
    try:
        current_dir = os.path.abspath(directory)
        
        while True:
            git_path = os.path.join(current_dir, '.git')
            if os.path.exists(git_path):
                return True
            
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:
                # Reached the root of the filesystem
                break
                
            current_dir = parent_dir
            
        return False
    except Exception:
        # If any filesystem error occurs, assume not a git repo
        return False

def find_git_root(directory: str) -> str | None:
    """
    Finds the root directory of a git repository by searching for a .git file or directory.

    Args:
        directory: The directory to start searching from.

    Returns:
        The git repository root path, or None if not in a git repository.
    """
    try:
        current_dir = os.path.abspath(directory)
        
        while True:
            git_path = os.path.join(current_dir, '.git')
            if os.path.exists(git_path):
                return current_dir
            
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:
                break
                
            current_dir = parent_dir
            
        return None
    except Exception:
        return None