# nano-tools/tests/test_glob.py
import unittest
import os
import shutil
from nano_gemini_cli_core.tools import glob

class TestGlobTool(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory with a file structure for glob testing."""
        self.test_dir = "temp_test_dir_for_glob"
        self.subdir = os.path.join(self.test_dir, "subdir")
        os.makedirs(self.subdir, exist_ok=True)

        self.file1 = os.path.join(self.test_dir, "file1.py")
        self.file2 = os.path.join(self.test_dir, "file2.txt")
        self.file3 = os.path.join(self.subdir, "file3.py")
        
        with open(self.file1, "w") as f: f.write("pass")
        with open(self.file2, "w") as f: f.write("pass")
        with open(self.file3, "w") as f: f.write("pass")

        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_glob_simple_pattern(self):
        """Test a simple glob pattern for a specific file type."""
        result = glob.glob(pattern="*.txt")
        self.assertIn("file2.txt", result["llm_content"])
        self.assertNotIn("file1.py", result["llm_content"])

    def test_glob_recursive_pattern(self):
        """Test a recursive glob pattern."""
        result = glob.glob(pattern="**/*.py")
        llm_content = result["llm_content"]
        
        # Use os.path.join to create platform-agnostic paths for checking
        expected_file1 = os.path.join("file1.py") # Relative to test_dir
        expected_file3 = os.path.join("subdir", "file3.py")
        
        self.assertIn(expected_file1, llm_content)
        self.assertIn(expected_file3, llm_content)
        self.assertNotIn("file2.txt", llm_content)
        self.assertIn("Found 2", result["display_content"])

    def test_glob_no_matches(self):
        """Test a glob pattern that matches no files."""
        result = glob.glob(pattern="*.md")
        self.assertIn("No files found", result["display_content"])

    def test_glob_respect_gitignore(self):
        """Test that glob respects a .gitignore file."""
        with open(".gitignore", "w") as f:
            f.write("*.txt\n")
            
        # This requires the git_utils._get_git_ignored_files to be tested,
        # but we can test the end-to-end behavior here.
        # We need to initialize a git repo for the gitignore to be respected.
        try:
            subprocess.run(["git", "init"], check=True, capture_output=True)
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
        except Exception:
            self.skipTest("git command not available, skipping git-related test.")
            return

        result = glob.glob(pattern="**/*", respect_git_ignore=True)
        self.assertNotIn("file2.txt", result["llm_content"])
        self.assertIn("file1.py", result["llm_content"])

if __name__ == '__main__':
    import subprocess
    unittest.main()
