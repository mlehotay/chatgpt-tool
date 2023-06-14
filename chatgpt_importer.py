import json
import sqlite3
import argparse
import os

"""
ChatGPT Importer

Features:
- Importing JSON data to SQLite:
    - Allow importing data into the SQLite database
    - Read JSON data from specified files
    - Handle both single objects and lists of objects
    - Create tables dynamically based on the JSON data
    - Insert data into the respective tables
- Organizing JSON files in a subdirectory:
    - Assume all JSON files are located in a subdirectory for better organization
- Handling empty JSON files:
    - Check for empty JSON data and skip table creation and data insertion if the JSON data is empty
"""

class ChatGPTImporter:
    DEFAULT_DB_NAME = "chatgpt.db"
    DATA_DIRECTORY = "data"

    def __init__(self, db_name=None, data_files=None):
        self.db_name = db_name or self.DEFAULT_DB_NAME
        self.data_files = data_files

    def import_data(self):
        data_files = self.data_files or self.get_data_files()
        if not data_files:
            print("Error: No JSON data files found.")
            return

        self.import_json_data_to_sqlite(data_files)

    def get_data_files(self):
        if not os.path.exists(self.DATA_DIRECTORY):
            return []

        data_files = [os.path.join(self.DATA_DIRECTORY, file) for file in os.listdir(self.DATA_DIRECTORY) if
                      file.endswith(".json")]
        return data_files

    def import_json_data_to_sqlite(self, data_files):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        for i, file_path in enumerate(data_files):
            print(f"Importing data from: {file_path}")

            table_name = f"data_{i}"

            # Read the JSON data from the file
            with open(file_path) as file:
                json_data = json.load(file)

            # Check if the JSON data is empty
            if not json_data:
                print(f"Skipping import for file: {file_path} (empty JSON data)")
                continue

            # Check if the JSON data is a list or a single object
            if isinstance(json_data, list):
                # List of objects
                if json_data:
                    # Get the column names from the first object
                    column_names = json_data[0].keys()
            else:
                # Single object
                column_names = json_data.keys()

            # Create a table for the current data
            create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            for column_name in column_names:
                create_table_query += f"{column_name} TEXT,"
            create_table_query = create_table_query.rstrip(',')
            create_table_query += ")"
            cursor.execute(create_table_query)

            # Insert data into the table
            if isinstance(json_data, list):
                for item in json_data:
                    values = tuple(str(value) for value in item.values())
                    insert_query = f"INSERT INTO {table_name} VALUES ({','.join(['?'] * len(values))})"
                    cursor.execute(insert_query, values)
            else:
                values = tuple(str(value) for value in json_data.values())
                if len(column_names) != len(values):
                    print(f"Skipping import for file: {file_path} (column count mismatch)")
                    continue
                insert_query = f"INSERT INTO {table_name} VALUES ({','.join(['?'] * len(values))})"
                cursor.execute(insert_query, values)

        conn.commit()
        conn.close()


def main():
    parser = argparse.ArgumentParser(prog="ChatGPT Importer", description="Import conversations exported from ChatGPT")
    parser.add_argument("db_name", type=str, nargs="?", default=None,
                        help="SQLite database name (default: chatgpt.db)")
    parser.add_argument("data_files", type=str, nargs="*", default=None,
                        help="Data files to import (JSON format)")

    args = parser.parse_args()

    importer = ChatGPTImporter(args.db_name, args.data_files)
    importer.import_data()


if __name__ == "__main__":
    main()
