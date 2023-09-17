import unittest
import tempfile
import shutil
import os
import json
import sqlite3
from contextlib import contextmanager
from src.chatgpt_tool import ChatGPTTool

class ImportTestCase(unittest.TestCase):

    def setUp(self):
        self.data_dir = tempfile.mkdtemp()
        self.db_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.db_dir, "test_db.sqlite")
        self.tool = ChatGPTTool(self.db_path)
        self.conn = sqlite3.connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.data_dir)
        shutil.rmtree(self.db_dir)

    @contextmanager
    def cursor_context(self):
        cursor = self.conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def create_empty_file(self, file_name):
        file_path = os.path.join(self.data_dir, file_name)
        open(file_path, 'w').close()  # Create an empty file
        return file_path

    def create_temp_json_file(self, data, file_name):
        file_path = os.path.join(self.data_dir, file_name)
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return file_path

    def create_temp_zip_archive(self, data, archive_name):
        zip_path = os.path.join(self.data_dir, archive_name)
        with tempfile.TemporaryDirectory() as temp_dir:
            for file_name, content in data.items():
                file_path = os.path.join(temp_dir, file_name)
                with open(file_path, 'w') as f:
                    json.dump(content, f)
            shutil.make_archive(zip_path[:-4], 'zip', temp_dir)
        return zip_path

    def create_temp_html_file(self, script_content, file_name):
        html_tags = [
            "<html>",
            "<head>",
            "<title>Test HTML</title>",
            "</head>",
            "<body>",
            "<script>",
            script_content,
            "</script>",
            "</body>",
            "</html>"
        ]

        html_content = "\n".join(html_tags)

        file_path = os.path.join(self.data_dir, file_name)
        with open(file_path, 'w') as f:
            f.write(html_content)

        return file_path

class TestImportTestCase(ImportTestCase):

    # these are arbitrary expected results for demonstration
    ENCODING_OPTIONS = ['UTF-8', 'ISO-8859-1', 'CP437']
    SQLITE_MAJOR_VERSION = 3
    SQLITE_MINOR_VERSION_THRESHOLD = 17

    def test_cursor_in_try_block(self):
        # Get a cursor for reading
        cursor = self.conn.cursor()
        try:
            # Perform operations using cursor
            cursor.execute("PRAGMA encoding;")
            encoding = cursor.fetchone()[0]
        finally:
            cursor.close() # Close the cursor
        # Make assertions
        self.assertTrue(encoding in self.ENCODING_OPTIONS, f"Unexpected encoding: {encoding}")

    def test_cursor_with_context_manager(self):
        # Perform operations using cursor
        with self.cursor_context() as cursor:
            # Use cursor in this block
            cursor.execute("SELECT sqlite_version();")
            version_string = cursor.fetchone()[0]
            version_parts = version_string.strip().split(".")
            major_version = int(version_parts[0])
            minor_version = int(version_parts[1])
            patch_version = int(version_parts[2])
        # Make assertions
        self.assertEqual(major_version, self.SQLITE_MAJOR_VERSION)
        self.assertTrue(minor_version > self.SQLITE_MINOR_VERSION_THRESHOLD)

if __name__ == '__main__':
    unittest.main()
