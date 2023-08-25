import unittest
import subprocess
import tempfile
import shutil

from src.chatgpt_tool import ChatGPTTool

class CLITestCase(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory to simulate data files
        self.data_dir = tempfile.mkdtemp()
        self.db_name = "test_db.sqlite"
        self.tool = ChatGPTTool()

    def tearDown(self):
        # Remove the temporary directory and its contents
        shutil.rmtree(self.data_dir)

    def test_help_command(self):
        # Test the "help" command and assert the expected output
        result = subprocess.run(["python3", "src/chatgpt_tool.py", "--help"], capture_output=True, text=True)
        self.assertIn("usage:", result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_import_command(self):
        # Test the "import" command and verify the expected behavior
        result = subprocess.run(["python3", "src/chatgpt_tool.py", "import", self.data_dir], capture_output=True, text=True)
        self.assertIn("Action: Import", result.stdout)
        self.assertEqual(result.returncode, 0)

    # More test methods...

if __name__ == '__main__':
    unittest.main()
