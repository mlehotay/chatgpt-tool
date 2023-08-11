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
        self.tool = ChatGPTTool()

    def tearDown(self):
        # Remove the temporary directory and its contents
        shutil.rmtree(self.data_dir)

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

    def test_import_single_json_file(self):
        # Test importing from a single JSON file
        data = {'id': 'alice', 'email': 'alice@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+14165551212'}
        file_path = self.create_temp_json_file(data, 'user.json')

        self.tool.import_data(file_path)
        # Perform assertions to check if the data is imported correctly

    def test_import_single_html_file(self):
        # Test importing from a single HTML file with JSON data
        html_content = '<script type="application/json">{"id": "eve", "email": "eve@example.com"}</script>'
        file_path = self.create_temp_html_file(html_content, 'user.html')

        self.tool.import_data(file_path)
        # Perform assertions to check if the data is imported correctly

    def test_import_zip_with_single_json_file(self):
        # Test importing from a ZIP archive containing a single JSON file
        data = {'user.json': {'id': 'bob', 'email': 'bob@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+16175556666'}}
        zip_path = self.create_temp_zip_archive(data, 'archive.zip')

        self.tool.import_data(zip_path)
        # Perform assertions to check if the data is imported correctly

    def test_import_zip_with_multiple_json_files(self):
        # Test importing from a ZIP archive containing multiple JSON files
        data = {'user1.json': {'id': 'carol', 'email': 'carol@example.com', 'chatgpt_plus_user': 'true', 'phone_number': '+13051234567'},
                'user2.json': {'id': 'dave', 'email': 'dave@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+4125552023'}}
        zip_path = self.create_temp_zip_archive(data, 'archive.zip')

        self.tool.import_data(zip_path)
        # Perform assertions to check if the data is imported correctly

    def test_import_directory_with_json_files(self):
        # Test importing from a directory containing JSON files
        data1 = {'id': 'emma', 'email': 'emma@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+19876543210'}
        data2 = {'id': 'frank', 'email': 'frank@example.com', 'chatgpt_plus_user': 'true', 'phone_number': '+12345678901'}
        data_dir = os.path.join(self.data_dir, 'json_data')
        os.makedirs(data_dir)
        self.create_temp_json_file(data1, 'user1.json')
        self.create_temp_json_file(data2, 'user2.json')

        self.tool.import_data(data_dir)
        # Perform assertions to check if the data is imported correctly

    def test_import_directory_with_archives(self):
        # Test importing from a directory containing ZIP archives
        data1 = {'id': 'grace', 'email': 'grace@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+9876543210'}
        data2 = {'id': 'harry', 'email': 'harry@example.com', 'chatgpt_plus_user': 'true', 'phone_number': '+11112222333'}
        data_dir = os.path.join(self.data_dir, 'zip_data')
        os.makedirs(data_dir)
        self.create_temp_zip_archive({'user.json': data1}, 'archive1.zip')
        self.create_temp_zip_archive({'user.json': data2}, 'archive2.zip')

        self.tool.import_data(data_dir)
        # Perform assertions to check if the data is imported correctly

if __name__ == '__main__':
    unittest.main()
