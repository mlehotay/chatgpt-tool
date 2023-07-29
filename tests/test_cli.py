import unittest
import subprocess

class CLITestCase(unittest.TestCase):
    def test_help_command(self):
        # Test the "help" command and assert the expected output
        result = subprocess.run(["python3", "src/chatgpt_tool.py", "--help"], capture_output=True, text=True)
        self.assertIn("usage:", result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_import_command(self):
        # Test the "import" command and verify the expected behavior
        result = subprocess.run(["python3", "src/chatgpt_tool.py", "import"], capture_output=True, text=True)
        self.assertIn("Action: Import", result.stdout)
        self.assertEqual(result.returncode, 0)

    # More test methods...

if __name__ == '__main__':
    unittest.main()
