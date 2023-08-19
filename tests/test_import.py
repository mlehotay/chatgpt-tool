import unittest
import tempfile
import shutil
import os
import json
import zipfile

from src.chatgpt_tool import ChatGPTTool

class ImportTestCase(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory to simulate data files
        self.data_dir = tempfile.mkdtemp()
        self.db_dir = tempfile.mkdtemp()  # Create a directory for the temporary database
        self.db_name = "test_db.sqlite"
        self.db_path = os.path.join(self.db_dir, self.db_name)
        self.tool = ChatGPTTool(self.db_path)  # Pass the temp database path to the tool

    def tearDown(self):
        # Remove the temporary directory and its contents
        shutil.rmtree(self.data_dir)
        shutil.rmtree(self.db_dir)  # Remove the temporary database directory

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
        html_content = f"""
        <html>
        <head>
            <title>Test HTML</title>
        </head>
        <body>
            <script type="application/json">
                {script_content}
            </script>
        </body>
        </html>
        """
        file_path = os.path.join(self.data_dir, file_name)
        with open(file_path, 'w') as f:
            f.write(html_content)

        return file_path

    def test_import_empty_json_file(self):
        # Test importing an empty JSON file
        empty_file_path = self.create_temp_json_file({}, 'empty.json')

        self.tool.import_data(self.tool.DB_NAME, empty_file_path)

        # Query the database to check if the data was imported
        result = self.tool.query_table("user", "id", 'alice')
        self.assertIsNone(result)

    def test_import_single_json_object(self):
        # Test importing a JSON object
        data = {'id': 'alice', 'email': 'alice@example.com'}
        file_path = self.create_temp_json_file(data, 'single.json')

        self.tool.import_data(self.tool.DB_NAME, file_path)

        # Query the database to check if the data was imported
        result = self.tool.query_table("user", "id", 'alice')
        self.assertEqual(result['email'], 'alice@example.com')

    def test_import_empty_json_list(self):
        # Test importing an empty JSON list
        data = []
        file_path = self.create_temp_json_file(data, 'empty_list.json')

        self.tool.import_data(self.tool.DB_NAME, file_path)

        # Query the database to check if the data was imported
        result = self.tool.query_table("user", "id", 'alice')
        self.assertIsNone(result)

    def test_import_json_list_with_objects(self):
        # Test importing a JSON list containing objects
        data = [
            {'id': 'bob', 'email': 'bob@example.com'},
            {'id': 'carol', 'email': 'carol@example.com'}
        ]
        file_path = self.create_temp_json_file(data, 'list_with_objects.json')

        self.tool.import_data(self.tool.DB_NAME, file_path)

        # Query the database to check if the data was imported
        result_bob = self.tool.query_table("user", "id", 'bob')
        self.assertEqual(result_bob['email'], 'bob@example.com')

        result_carol = self.tool.query_table("user", "id", 'carol')
        self.assertEqual(result_carol['email'], 'carol@example.com')

    def test_import_single_json_file(self):
        # Test importing from a single JSON file
        data = {'id': 'alice', 'email': 'alice@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+14165551212'}
        file_path = self.create_temp_json_file(data, 'user.json')

        self.tool.import_data(self.tool.DB_NAME, file_path)

        # Query the database to fetch the data and compare
        result = self.tool.query_table("user", "id", "alice")
        self.assertEqual(result['id'], 'alice')
        self.assertEqual(result['email'], 'alice@example.com')
        # ... assert other fields

    def test_import_single_html_file(self):
        script_content = json.dumps({'id': 'eve', 'email': 'eve@example.com'})
        file_path = self.create_temp_html_file(script_content, 'user.html')

        self.tool.import_data(self.tool.DB_NAME, file_path)
        # Perform assertions to check if the data is imported correctly

    def test_import_zip_with_single_json_file(self):
        # Test importing from a ZIP archive containing a single JSON file
        data = {'user.json': {'id': 'bob', 'email': 'bob@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+16175556666'}}
        zip_path = self.create_temp_zip_archive(data, 'archive.zip')

        self.tool.import_data(self.tool.DB_NAME, zip_path)
        # Perform assertions to check if the data is imported correctly

    def test_import_zip_with_multiple_json_files(self):
        # Test importing from a ZIP archive containing multiple JSON files
        data = {'user1.json': {'id': 'carol', 'email': 'carol@example.com', 'chatgpt_plus_user': 'true', 'phone_number': '+13051234567'},
                'user2.json': {'id': 'dave', 'email': 'dave@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+4125552023'}}
        zip_path = self.create_temp_zip_archive(data, 'archive.zip')

        self.tool.import_data(self.tool.DB_NAME, zip_path)
        # Perform assertions to check if the data is imported correctly

    def test_import_directory_with_json_files(self):
        # Test importing from a directory containing JSON files
        data1 = {'id': 'emma', 'email': 'emma@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+19876543210'}
        data2 = {'id': 'frank', 'email': 'frank@example.com', 'chatgpt_plus_user': 'true', 'phone_number': '+12345678901'}
        data_dir = os.path.join(self.data_dir, 'json_data')
        os.makedirs(data_dir)
        self.create_temp_json_file(data1, 'user1.json')
        self.create_temp_json_file(data2, 'user2.json')

        self.tool.import_data(self.tool.DB_NAME, data_dir)
        # Perform assertions to check if the data is imported correctly

    def test_import_directory_with_archives(self):
        # Test importing from a directory containing ZIP archives
        data1 = {'id': 'grace', 'email': 'grace@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+9876543210'}
        data2 = {'id': 'harry', 'email': 'harry@example.com', 'chatgpt_plus_user': 'true', 'phone_number': '+11112222333'}
        data_dir = os.path.join(self.data_dir, 'zip_data')
        os.makedirs(data_dir)
        self.create_temp_zip_archive({'user.json': data1}, 'archive1.zip')
        self.create_temp_zip_archive({'user.json': data2}, 'archive2.zip')

        self.tool.import_data(self.tool.DB_NAME, data_dir)
        # Perform assertions to check if the data is imported correctly

if __name__ == '__main__':
    unittest.main()
