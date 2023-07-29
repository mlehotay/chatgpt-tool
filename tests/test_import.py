import unittest
import tempfile
import shutil
import os
import sys
import json

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

    def test_import_zip_with_single_json_file(self):
        # Test importing from a ZIP archive containing a single JSON file
        data = {'id': 'bob', 'email': 'bob@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+16175556666'}
        zip_path = self.create_temp_zip_archive({'user.json': data}, 'archive.zip')

        self.tool.import_data(zip_path)
        # Perform assertions to check if the data is imported correctly

    def test_import_zip_with_multiple_json_files(self):
        # Test importing from a ZIP archive containing multiple JSON files
        data1 = {'id': 'carol', 'email': 'carol@example.com', 'chatgpt_plus_user': 'true', 'phone_number': '+13051234567'}
        data2 = {'id': 'dave', 'email': 'dave@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+4125552023'}
        zip_path = self.create_temp_zip_archive({'user1.json': data1, 'user2.json': data2}, 'archive.zip')

        self.tool.import_data(zip_path)
        # Perform assertions to check if the data is imported correctly

if __name__ == '__main__':
    unittest.main()
