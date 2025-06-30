# nano-tools/tests/test_grep.py
import unittest
import os
import shutil
import subprocess
from nano_gemini_cli_core.tools import grep

class TestGrepTool(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory with files for searching."""
        self.test_dir = "temp_test_dir_for_grep"
        self.subdir = os.path.join(self.test_dir, "subdir")
        os.makedirs(self.subdir, exist_ok=True)

        self.file1_path = os.path.join(self.test_dir, "file1.txt")
        self.file2_path = os.path.join(self.subdir, "file2.log")
        
        with open(self.file1_path, "w") as f:
            f.write("Hello Python world\n")
            f.write("This is a test line\n")
        
        with open(self.file2_path, "w") as f:
            f.write("Another python line\n")

        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_grep_python_fallback(self):
        """Test the pure Python fallback search."""
        result = grep.search_file_content(pattern="python")
        self.assertIn("llm_content", result)
        llm_content = result["llm_content"]
        
        self.assertIn("file1.txt", llm_content)
        self.assertIn("L1: Hello Python world", llm_content)
        self.assertIn("file2.log", llm_content)
        self.assertIn("L1: Another python line", llm_content)
        self.assertNotIn("test line", llm_content)

    def test_grep_with_include(self):
        """Test the grep tool with an include glob."""
        result = grep.search_file_content(pattern="python", include="*.txt")
        self.assertIn("file1.txt", result["llm_content"])
        self.assertNotIn("file2.log", result["llm_content"])

    def test_grep_no_matches(self):
        """Test grep with a pattern that has no matches."""
        result = grep.search_file_content(pattern="javascript")
        self.assertEqual("No matches found.", result["llm_content"])

    def test_grep_git_strategy(self):
        """Test the git grep strategy (if git is available)."""
        try:
            subprocess.run(["git", "init"], check=True, capture_output=True)
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
        except Exception:
            self.skipTest("git command not available, skipping git-related test.")
            return
            
        result = grep.search_file_content(pattern="python")
        self.assertIn("Found matches using 'git grep'", result["llm_content"])
        self.assertIn("file1.txt", result["llm_content"])
        self.assertIn("file2.log", result["llm_content"])

if __name__ == '__main__':
    unittest.main()
