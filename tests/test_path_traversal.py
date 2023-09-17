import unittest
import tempfile
import shutil
import os
import json
import sqlite3
from src.chatgpt_tool import ChatGPTTool
from .test_import import ImportTestCase
from .data_generator import DataGenerator

class TestDataTraveral(ImportTestCase):

    # Database info functions in ChatGPTTool():
    #
    # get_table_names(cursor)
    # get_column_names(cursor, table_name)
    # get_table_count(cursor, table_name)
    # table_exists(cursor, table_name)
    # check_row_in_table(table_name, condition_field, condition_value)
    # query_table(table_name, condition_field=None, condition_value=None, fetch_one=False)
    # query_single_value(table_name, condition_field, condition_value, value_field)

    def test_import_empty_json_file(self):
        # Test importing an empty JSON file
        empty_file_path = self.create_temp_json_file({}, 'empty.json')

        # The database should be empty now, with only the schema table present

        self.tool.import_data(self.tool.db_path, empty_file_path)

        # Check if the database has changed or if any tables have new rows
        with self.cursor_context() as cursor:
            result = self.tool.table_exists(cursor, "empty")
            self.assertFalse(result)

    def test_import_single_json_object(self):
        # Test importing a JSON object
        data = {'id': 'alice', 'email': 'alice@example.com'}
        file_path = self.create_temp_json_file(data, 'single.json')

        self.tool.import_data(self.tool.db_path, file_path)

        # Query the database to check if the data was imported
        email = self.tool.query_single_value("single", "id", "alice", "email")
        self.assertEqual(email, 'alice@example.com')

    def test_import_empty_json_list(self):
        # Test importing an empty JSON list
        data = []
        file_path = self.create_temp_json_file(data, 'empty_list.json')

        self.tool.import_data(self.tool.db_path, file_path)

        with self.cursor_context() as cursor:
            self.assertFalse(self.tool.table_exists(cursor, "empty_list"))

    def test_import_json_list_with_objects(self):
        # Test importing a JSON list containing objects
        data = [
            {'id': 'bob', 'email': 'bob@example.com'},
            {'id': 'carol', 'email': 'carol@example.com'}
        ]
        file_path = self.create_temp_json_file(data, 'list_with_objects.json')

        self.tool.import_data(self.tool.db_path, file_path)

        # Query the database to check if the data was imported
        result_bob = self.tool.query_table("list_with_objects", "id", 'bob', fetch_one=True)
        self.assertEqual(result_bob, data[0])

        email_carol = self.tool.query_single_value("list_with_objects", "id", 'carol', "email")
        self.assertEqual(email_carol, data[1]["email"])

    def test_import_single_json_file(self):
        # Test importing from a single JSON file
        data = {'id': 'alice', 'email': 'alice@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+14165551212'}
        file_path = self.create_temp_json_file(data, 'user.json')

        self.tool.import_data(self.tool.db_path, file_path)

        # Query the database to fetch the data and compare
        result = self.tool.query_table("user", "id", 'alice', fetch_one=False)
        self.assertEqual(result, [data])

    def test_import_single_html_file(self):
        conversations = [DataGenerator.generate_conversation() for _ in range(5)]
        json_data = json.dumps(conversations)
        script_content = f"jsonData = {json_data}"
        file_path = self.create_temp_html_file(script_content, 'chat.html')

        self.tool.import_data(self.tool.db_path, file_path)

        with self.cursor_context() as cursor:
            self.assertFalse(self.tool.table_exists(cursor, "chat"))
            self.assertTrue(self.tool.table_exists(cursor, "conversations"))

    def test_import_zip_with_single_json_file(self):
        # Test importing from a ZIP archive containing a single JSON file
        data = {'user.json': {'id': 'bob', 'email': 'bob@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+16175556666'}}
        zip_path = self.create_temp_zip_archive(data, 'archive.zip')

        self.tool.import_data(self.tool.db_path, zip_path)
        # Perform assertions to check if the data is imported correctly
        with self.cursor_context() as cursor:
            self.assertFalse(self.tool.table_exists(cursor, "archive"))
        result = self.tool.query_table("user", "id", 'bob', fetch_one=True)
        self.assertEqual(result, data['user.json'])

    def test_import_zip_with_multiple_json_files(self):
        # Test importing from a ZIP archive containing multiple JSON files
        data = {'user1.json': {'id': 'carol', 'email': 'carol@example.com', 'chatgpt_plus_user': 'true', 'phone_number': '+13051234567'},
                'user2.json': {'id': 'dave', 'email': 'dave@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+4125552023'}}
        zip_path = self.create_temp_zip_archive(data, 'archive.zip')

        self.tool.import_data(self.tool.db_path, zip_path)
        # Perform assertions to check if the data is imported correctly
        with self.cursor_context() as cursor:
            self.assertFalse(self.tool.table_exists(cursor, "archive"))
        self.assertTrue(self.tool.check_row_in_table("user1", "id", "carol"))
        self.assertTrue(self.tool.check_row_in_table("user2", "id", "dave"))

    def test_import_directory_with_json_files(self):
        # Test importing from a directory containing JSON files
        data1 = {'id': 'emma', 'email': 'emma@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+19876543210'}
        data2 = {'id': 'frank', 'email': 'frank@example.com', 'chatgpt_plus_user': 'true', 'phone_number': '+12345678901'}
        data_dir = os.path.join(self.data_dir, 'json_data')
        os.makedirs(data_dir)
        self.create_temp_json_file(data1, os.path.join(data_dir, 'user1.json'))
        self.create_temp_json_file(data2, os.path.join(data_dir, 'user2.json'))

        self.tool.import_data(self.tool.db_path, data_dir)
        self.assertTrue(self.tool.check_row_in_table("user1", "id", "emma"))
        self.assertTrue(self.tool.check_row_in_table("user2", "id", "frank"))

    def test_import_directory_with_archives(self):
        # Test importing from a directory containing ZIP archives
        data1 = {'id': 'grace', 'email': 'grace@example.com', 'chatgpt_plus_user': 'false', 'phone_number': '+9876543210'}
        data2 = {'id': 'harry', 'email': 'harry@example.com', 'chatgpt_plus_user': 'true', 'phone_number': '+11112222333'}
        data_dir = os.path.join(self.data_dir, 'zip_data')
        os.makedirs(data_dir)
        self.create_temp_zip_archive({'user.json': data1}, os.path.join(data_dir, 'archive1.zip'))
        self.create_temp_zip_archive({'user.json': data2}, os.path.join(data_dir, 'archive2.zip'))

        self.tool.import_data(self.tool.db_path, data_dir)
        self.assertTrue(self.tool.check_row_in_table("user", "id", "grace"))
        self.assertTrue(self.tool.check_row_in_table("user", "id", "harry"))

if __name__ == '__main__':
    unittest.main()
