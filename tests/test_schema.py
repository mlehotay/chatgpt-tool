import unittest
import os
import shutil
import tempfile
from src.chatgpt_tool import ChatGPTTool
from .data_generator import DataGenerator
from .test_import import ImportTestCase

class TestSchemaHandling(ImportTestCase):

    # table_name test methods
    ###########################################################################

    def test_known_schema_with_expected_filename(self):
        # Import data with expected structure and filename
        data = DataGenerator.generate_user()
        filename = self.create_temp_json_file(data, "user.json")
        self.tool.import_data(self.db_path, filename)

        # Check that schema was added with filename as the tablename
        self.assertTrue(self.tool.check_row_in_table("schema", "table_name", "user"))

        # Check the hash code against our copy of the data
        _, column_names = self.tool.get_id_and_column_names(data)
        expected_hash = self.tool.calculate_column_names_hash(column_names)
        hash_value = self.tool.query_single_value("schema", "table_name", "user", "hash_value")
        self.assertTrue(hash_value == expected_hash)

        # Check that data was added to correct table
        result = self.tool.query_table("user", "id", data["id"], fetch_one=True)
        self.assertTrue(result and result["id"] == data["id"])

    def test_known_schema_with_novel_unexpected_filename(self):
        # Import some other data first so we learn about the schema
        data1 = DataGenerator.generate_message_feedback()
        filename = self.create_temp_json_file(data1, "message_feedback.json")
        self.tool.import_data(self.db_path, filename)

        # Make sure the schema is now known
        _, column_names = self.tool.get_id_and_column_names(data1)
        expected_hash = self.tool.calculate_column_names_hash(column_names)
        self.assertTrue(self.tool.check_row_in_table("schema", "hash_value", "expected_hash"))

        # Check that filename has not been seen before
        basename = DataGenerator.random_string()
        self.assertFalse(self.tool.check_row_in_table("schema", "table_name", basename))

        # Import the data
        data2 = DataGenerator.generate_message_feedback()
        filename = self.create_temp_json_file(data2, f"{basename}.json")
        self.tool.import_data(self.db_path, filename)

        # Check that schema was added with filename as the tablename
        self.assertTrue(self.tool.check_row_in_table("schema", "table_name", basename))

        # Check that data was added to correct table
        result = self.tool.query_table(basename, "id", data2["id"], fetch_one=True)
        self.assertTrue(result and result["id"] == data2["id"])

    def test_known_schema_with_familiar_unexpected_filename(self):
        pass

    def test_known_schema_with_mapped_filename(self):
        pass

    # schema test methods
    ###########################################################################

    def test_import_with_matching_schema(self):
        # Import some data with a known schema
        user1 = DataGenerator.generate_user('a1dd9e6ff9fb7b63ed62cde37a101145')
        filename = self.create_temp_json_file(user1, "user.json")
        self.tool.import_data(self.db_path, filename)
        self.assertTrue(self.tool.check_row_in_table("user", "id", user1["id"]))

        # Import more data with the same schema
        user2 = DataGenerator.generate_user('a1dd9e6ff9fb7b63ed62cde37a101145')
        filename = self.create_temp_json_file(user2, "user.json")
        self.tool.import_data(self.db_path, filename)
        self.assertTrue(self.tool.check_row_in_table("user", "id", user2["id"]))

    def test_import_with_new_schema(self):
        # Import some data with the old schema
        user1 = DataGenerator.generate_user()
        filename = self.create_temp_json_file(user1, "user.json")
        self.tool.import_data(self.db_path, filename)
        self.assertTrue(self.tool.check_row_in_table("user", "id", user1["id"]))

        # Import some data with a new schema
        user2 = DataGenerator.generate_user()
        user2["new_column"] = "cabbage"
        filename = self.create_temp_json_file(user2, "user.json")
        self.tool.import_data(self.db_path, filename)
        self.assertTrue(self.tool.check_row_in_table("user", "id", user2["id"]))

    def test_import_with_mapped_table(self):
        # Simulate importing data with a mapped table
        json_data = DataGenerator.generate_user()
        filename = self.create_temp_json_file(json_data, "user_with_mapping.json")

        self.tool.import_data(self.db_path, filename)

        # Verify that the mapped table name was used
        # You need to implement this verification based on your ChatGPTTool's methods

if __name__ == '__main__':
    unittest.main()
