# nano-tools/tests/test_edit.py
import unittest
import os
import shutil
from nano_gemini_cli_core.tools import edit

class TestEditTool(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and a test file."""
        self.test_dir = "temp_test_dir_for_edit"
        os.makedirs(self.test_dir, exist_ok=True)
        
        self.test_file_path = os.path.join(self.test_dir, "test_file.txt")
        self.abs_test_file_path = os.path.abspath(self.test_file_path)
        
        self.file_content = "Hello world, this is a test.\nAnother line with world.\n"
        with open(self.test_file_path, "w") as f:
            f.write(self.file_content)

        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_simple_replace(self):
        """Test a simple find-and-replace operation."""
        result = edit.replace(
            file_path=self.abs_test_file_path,
            old_string="world",
            new_string="Python",
            expected_replacements=2
        )
        self.assertIn("Successfully replaced", result["display_content"])
        
        with open(self.test_file_path, "r") as f:
            content = f.read()
        self.assertEqual(content.count("Python"), 2)
        self.assertEqual(content.count("world"), 0)

    def test_mismatched_occurrences(self):
        """Test that the tool fails if occurrences do not match expectations."""
        result = edit.replace(
            file_path=self.abs_test_file_path,
            old_string="world",
            new_string="Python",
            expected_replacements=1 # We expect 1, but there are 2
        )
        self.assertIn("Error: Expected 1 occurrences, but found 2", result["display_content"])
        
        # Verify the file was not changed
        with open(self.test_file_path, "r") as f:
            content = f.read()
        self.assertEqual(content, self.file_content)

    def test_create_new_file(self):
        """Test that the tool creates a new file when old_string is empty."""
        new_file_path = os.path.abspath("new_file.txt")
        new_content = "This is a brand new file."
        
        result = edit.replace(
            file_path=new_file_path,
            old_string="",
            new_string=new_content
        )
        self.assertIn("Created", result["display_content"])
        
        self.assertTrue(os.path.exists(new_file_path))
        with open(new_file_path, "r") as f:
            content = f.read()
        self.assertEqual(content, new_content)

    def test_fail_on_creating_existing_file(self):
        """Test that the tool fails if trying to create a file that already exists."""
        result = edit.replace(
            file_path=self.abs_test_file_path,
            old_string="",
            new_string="some content"
        )
        self.assertIn("Error: Attempted to create a file that already exists", result["display_content"])

    # Note: Testing the agentic correction loop would require mocking the litellm API call,
    # which is out of scope for this "nano" test suite. We trust the logic and will
    # test it manually with the interactive test script.

if __name__ == '__main__':
    unittest.main()
