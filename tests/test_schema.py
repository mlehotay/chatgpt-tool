import unittest
import os
import shutil
import tempfile
from src.chatgpt_tool import ChatGPTTool
from .data_generator import DataGenerator
from .test_import import ImportTestCase

class TestSchemaHandling(ImportTestCase):

    # test methods
    ###########################################################################

    def test_import_with_matching_schema(self):
        # Simulate importing data with matching schema
        json_data = DataGenerator.generate_user()
        filename = self.create_temp_json_file(json_data, "user.json")

        self.tool.import_data(self.db_path, filename)

        # Verify that the correct table was used
        # You need to implement this verification based on your ChatGPTTool's methods

    def test_import_with_new_schema(self):
        # Simulate importing data with a new schema
        json_data = DataGenerator.generate_user()
        filename = self.create_temp_json_file(json_data, "new_user.json")

        self.tool.import_data(self.db_path, filename)

        # Verify that a new table was created
        # You need to implement this verification based on your ChatGPTTool's methods

    def test_import_with_mapped_table(self):
        # Simulate importing data with a mapped table
        json_data = DataGenerator.generate_user()
        filename = self.create_temp_json_file(json_data, "user_with_mapping.json")

        self.tool.import_data(self.db_path, filename)

        # Verify that the mapped table name was used
        # You need to implement this verification based on your ChatGPTTool's methods

if __name__ == '__main__':
    unittest.main()
