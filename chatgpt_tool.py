import argparse
import json
import os
import shutil
import sqlite3


class ChatGPTTool:
    DEFAULT_DB_NAME = "chatgpt.db"
    DEFAULT_DATA_DIRECTORY = "data"

    def __init__(self):
        self.parser = argparse.ArgumentParser(description="ChatGPT Tool")
        self.subparsers = self.parser.add_subparsers(title="subcommands", dest="subcommand")

        self.setup_import_command()
        self.setup_print_command()

    def setup_import_command(self):
        # Create the 'import' subcommand parser
        import_parser = self.subparsers.add_parser("import", help="Import JSON data into the SQLite database")
        import_parser.add_argument("-d", "--db-name", type=str, default=self.DEFAULT_DB_NAME, help="SQLite database name")
        import_parser.add_argument("-f", "--data-files", type=str, nargs="*", default=None, help="Data files to import (JSON format)")

    def setup_print_command(self):
        # Create the 'print' subcommand parser
        print_parser = self.subparsers.add_parser("print", help="Print the content of the SQLite database tables")
        print_parser.add_argument("-d", "--db-name", type=str, default=self.DEFAULT_DB_NAME, help="SQLite database name")

    def import_data(self, db_name, data_files):
        data_files = data_files or self.get_data_files()
        if not data_files:
            print("Error: No JSON data files found.")
            return

        self.import_json_data_to_sqlite(db_name, data_files)

    def get_data_files(self):
        if not os.path.exists(self.DEFAULT_DATA_DIRECTORY):
            return []

        data_files = [os.path.join(self.DEFAULT_DATA_DIRECTORY, file) for file in os.listdir(self.DEFAULT_DATA_DIRECTORY) if
                      file.endswith(".json")]
        return data_files

    def import_json_data_to_sqlite(self, db_name, data_files):
        conn = sqlite3.connect(db_name)
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
                if json_data:
                    first_object = json_data[0]
                    id_field_name = next((key for key in first_object.keys() if key.lower() == "id"), None)
                    if not id_field_name:
                        print(f"Skipping import for file: {file_path} (no 'id' field found)")
                        continue
                    column_names = first_object.keys()
            else:
                id_field_name = next((key for key in json_data.keys() if key.lower() == "id"), None)
                if not id_field_name:
                    print(f"Skipping import for file: {file_path} (no 'id' field found)")
                    continue
                column_names = json_data.keys()

            # Create a table for the current data
            create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            for column_name in column_names:
                create_table_query += f"{column_name} TEXT,"
            create_table_query = create_table_query.rstrip(',')
            create_table_query += f", CONSTRAINT unique_{table_name} UNIQUE ({id_field_name}))"
            cursor.execute(create_table_query)

            # Insert data into the table
            if isinstance(json_data, list):
                for item in json_data:
                    values = tuple(str(value) for value in item.values())
                    insert_query = f"INSERT OR IGNORE INTO {table_name} ({','.join(item.keys())}) VALUES ({','.join(['?'] * len(values))})"
                    cursor.execute(insert_query, values)
            else:
                values = tuple(str(value) for value in json_data.values())
                if len(column_names) != len(values):
                    print(f"Skipping import for file: {file_path} (column count mismatch)")
                    continue
                insert_query = f"INSERT OR IGNORE INTO {table_name} ({','.join(json_data.keys())}) VALUES ({','.join(['?'] * len(values))})"
                cursor.execute(insert_query, values)

        conn.commit()
        conn.close()

    def print_tables(self, db_name):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        truncation_length = self.get_truncation_length()

        # Get the table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        # Print the tables and their content
        for table in tables:
            table_name = table[0]
            print(f"Table: {table_name}")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            print(self.truncate_string(str(column_names), truncation_length))
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            for row in rows:
                print(self.truncate_string(str(row), truncation_length))
            print()

        conn.close()

    def truncate_string(self, string, max_length):
        if len(string) <= max_length:
            return string
        return string[:max_length-3] + "..."

    def get_truncation_length(self):
        terminal_size = shutil.get_terminal_size(fallback=(80, 24))
        return terminal_size.columns - 3  # Subtract 3 to account for ellipsis

    def run(self):
        args = self.parser.parse_args()

        if args.subcommand == "import":
            print("Action: Import")
            self.import_data(args.db_name, args.data_files)
        elif args.subcommand == "print":
            print("Action: Print tables")
            self.print_tables(args.db_name)
        else:
            # No subcommand specified, try to import using default settings
            print("Action: Import using default settings")
            self.import_data(self.DEFAULT_DB_NAME, None)

if __name__ == "__main__":
    tool = ChatGPTTool()
    tool.run()
