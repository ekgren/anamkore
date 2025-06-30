# nano-tools/tests/test_ls.py
import unittest
import os
import shutil
from nano_gemini_cli_core.tools import ls

class TestLsTool(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.test_dir = "temp_test_dir_for_ls"
        os.makedirs(self.test_dir, exist_ok=True)
        # Create some files and directories
        with open(os.path.join(self.test_dir, "file1.txt"), "w") as f:
            f.write("hello")
        os.makedirs(os.path.join(self.test_dir, "subdir1"))
        with open(os.path.join(self.test_dir, "subdir1", "file2.txt"), "w") as f:
            f.write("world")

    def tearDown(self):
        """Clean up the temporary directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_list_directory_contents(self):
        """Test that the ls tool correctly lists the contents of a directory."""
        result = ls.list_directory(path=self.test_dir)
        
        # The tool should return a dictionary with llm_content and display_content
        self.assertIsInstance(result, dict)
        self.assertIn("llm_content", result)
        
        llm_content = result["llm_content"]
        
        # Check that the output contains the expected files and directories
        self.assertIn("[DIR] subdir1", llm_content)
        self.assertIn("file1.txt", llm_content)
        
        # Check that it does not list contents of subdirectories
        self.assertNotIn("file2.txt", llm_content)

    def test_list_empty_directory(self):
        """Test that the ls tool handles empty directories correctly."""
        empty_dir = os.path.join(self.test_dir, "empty_subdir")
        os.makedirs(empty_dir)
        
        result = ls.list_directory(path=empty_dir)
        self.assertIn("is empty", result["display_content"])

    def test_invalid_path(self):
        """Test that the ls tool handles invalid paths correctly."""
        invalid_path = "non_existent_directory"
        result = ls.list_directory(path=invalid_path)
        self.assertIn("Error", result["display_content"])

if __name__ == '__main__':
    unittest.main()
