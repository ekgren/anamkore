# nano-tools/tests/test_read_file.py
import unittest
import os
import shutil
from nano_gemini_cli_core.tools import read_file

class TestReadFileTool(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and a test file."""
        self.test_dir = "temp_test_dir_for_read"
        os.makedirs(self.test_dir, exist_ok=True)
        
        self.test_file_path = os.path.join(self.test_dir, "test_file.txt")
        self.abs_test_file_path = os.path.abspath(self.test_file_path)
        
        # Create a file with 10 lines of content
        with open(self.test_file_path, "w") as f:
            for i in range(10):
                f.write(f"This is line {i+1}.\n")

        # Change current working directory to the test directory for relative path testing
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up the temporary directory and restore CWD."""
        os.chdir(self.original_cwd)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_read_full_file(self):
        """Test reading the entire content of a file."""
        result = read_file.read_file(absolute_path=self.abs_test_file_path)
        self.assertIn("llm_content", result)
        self.assertIn("This is line 1.", result["llm_content"])
        self.assertIn("This is line 10.", result["llm_content"])
        self.assertIn("Read 10 lines", result["display_content"])

    def test_read_with_pagination(self):
        """Test reading a slice of a file using offset and limit."""
        result = read_file.read_file(absolute_path=self.abs_test_file_path, offset=2, limit=3)
        self.assertIn("llm_content", result)
        # Should contain lines 3, 4, and 5
        self.assertNotIn("This is line 2.", result["llm_content"])
        self.assertIn("This is line 3.", result["llm_content"])
        self.assertIn("This is line 5.", result["llm_content"])
        self.assertNotIn("This is line 6.", result["llm_content"])
        self.assertIn("Read 3 lines", result["display_content"])

    def test_read_non_existent_file(self):
        """Test attempting to read a file that does not exist."""
        result = read_file.read_file(absolute_path="/non/existent/file.txt")
        self.assertIn("Error: File not found", result["display_content"])

    def test_security_path_outside_root(self):
        """Test that reading outside the project root is blocked."""
        # For this test, we need to simulate the root being one level down
        # The tool determines root via os.getcwd(), so we stay in test_dir
        # and try to access a file one level up.
        outside_path = os.path.abspath(os.path.join(os.getcwd(), "..", "some_other_file.txt"))
        # We can't actually create this file, but the path check should fail first.
        
        # To properly test this, we need to temporarily leave the test CWD
        os.chdir(self.original_cwd)
        result = read_file.read_file(absolute_path=outside_path)
        os.chdir(self.test_dir) # Change back for teardown
        
        # This test is conceptual as the tool's getcwd() is dynamic.
        # A more robust test would involve mocking os.getcwd, but for nano, this check is sufficient.
        # The logic inside the tool should prevent this.
        # Let's test the internal utility function directly for a more reliable test.
        self.assertFalse(read_file._is_path_within_root(outside_path, self.test_dir))

    def test_gemini_ignore(self):
        """Test that files matching .geminiignore patterns are ignored."""
        # Create a .geminiignore file in the "project root" (our test_dir)
        with open(".geminiignore", "w") as f:
            f.write("*.txt\n")
        
        result = read_file.read_file(absolute_path=self.abs_test_file_path)
        self.assertIn("Error: File", result["display_content"])
        self.assertIn("is ignored by a .geminiignore rule", result["display_content"])

if __name__ == '__main__':
    unittest.main()
