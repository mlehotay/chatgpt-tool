import argparse
import json
import os
import sqlite3
import zipfile

"""
ChatGPT Tool

ChatGPT Tool is a command-line utility for importing ChatGPT conversations from JSON and managing them in a SQLite database.

"""

class ChatGPTTool:
    DEFAULT_DB_NAME = "chatgpt.db"
    DEFAULT_DATA_PATH = "data"

    # init
    ###########################################################################

    def __init__(self):
        self.parser = argparse.ArgumentParser(prog="chatgpt_tool", description="ChatGPT Tool")
        self.parser.add_argument("subcommand", choices=["import", "show", "delete", "info", "export", "conversation", "inspect"], help="Subcommand")
        self.parser.add_argument("path", nargs="?", default=self.DEFAULT_DATA_PATH, help="Filepath or directory for import (default: data)")

    # import
    ###########################################################################

    def import_data(self, data_path):
        data_files = self.get_data_files(data_path)

        if not data_files:
            print("Error: No JSON data files found.")
            return

        conn = sqlite3.connect(self.DEFAULT_DB_NAME)
        cursor = conn.cursor()

        for i, file_path in enumerate(data_files):
            print(f"Importing data from: {file_path}")

            table_name = f"data_{i}"

            if file_path.endswith(".zip"):
                if not zipfile.is_zipfile(file_path):
                    print(f"Error: Invalid zip file: {file_path}")
                    continue

                with zipfile.ZipFile(file_path, "r") as zip_file:
                    json_files = [name for name in zip_file.namelist() if name.endswith(".json")]
                    json_data = []

                    for json_file in json_files:
                        with zip_file.open(json_file) as file:
                            json_data.append(json.load(file))

                    self.import_json_data_to_sqlite(cursor, table_name, json_data)
            else:
                with open(file_path) as file:
                    json_data = json.load(file)
                    self.import_json_data_to_sqlite(cursor, table_name, json_data)

        conn.commit()
        conn.close()

    def get_data_files(self, data_path):
        if not os.path.exists(data_path):
            print(f"Error: Data path not found: {data_path}")
            return []

        if os.path.isfile(data_path):
            return [data_path]

        data_files = [os.path.join(data_path, file) for file in os.listdir(data_path) if file.endswith(".json")]
        return data_files

    def import_json_data_to_sqlite(self, cursor, table_name, json_data):
        # Check if the JSON data is empty
        if not json_data:
            print(f"Skipping import for table: {table_name} (empty JSON data)")
            return

        # Check if the JSON data is a list or a single object
        if isinstance(json_data, list):
            if not json_data:
                print(f"Skipping import for table: {table_name} (empty JSON data)")
                return

            first_object = json_data[0]
            id_field_name = next((key for key in first_object.keys() if key.lower() == "id"), None)
            if not id_field_name:
                print(f"Skipping import for table: {table_name} (no 'id' field found)")
                return
            column_names = first_object.keys()
        else:
            id_field_name = next((key for key in json_data.keys() if key.lower() == "id"), None)
            if not id_field_name:
                print(f"Skipping import for table: {table_name} (no 'id' field found)")
                return
            column_names = json_data.keys()

        # Create a table for the current data
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({id_field_name} TEXT PRIMARY KEY,"
        for column_name in column_names:
            if column_name.lower() != id_field_name.lower():
                create_table_query += f"{column_name} TEXT,"
        create_table_query = create_table_query.rstrip(',')
        create_table_query += ")"
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
                print(f"Skipping import for table: {table_name} (column count mismatch)")
                return
            insert_query = f"INSERT OR IGNORE INTO {table_name} ({','.join(json_data.keys())}) VALUES ({','.join(['?'] * len(values))})"
            cursor.execute(insert_query, values)

    # show
    ###########################################################################

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

    # delete
    ###########################################################################

    def delete_database(self, db_name):
        try:
            os.remove(db_name)
            print(f"Deleted database: {db_name}")
        except FileNotFoundError:
            print(f"Database not found: {db_name}")

    # info
    ###########################################################################

    def info(self, db_name):
        # Connect to the database
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Retrieve statistics about the tables
        tables = self.get_table_names(cursor)
        table_stats = []
        for table in tables:
            table_stats.append((table, self.get_table_count(cursor, table)))

        # Display the statistics
        print("Database Information:")
        print(f"Database Name: {db_name}")
        print(f"Number of Tables: {len(tables)}")
        print()

        print("Table Statistics:")
        for table, count in table_stats:
            print(f"Table Name: {table}")
            print(f"Number of Rows: {count}")
            print()

        # Close the database connection
        conn.close()

    # export
    ###########################################################################

    def export_conversations(self, db_name, output_directory=None):
        output_directory = output_directory or self.DEFAULT_DATA_PATH

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        tables = self.get_table_names(cursor)

        for table in tables:
            json_data = self.export_table_as_json(cursor, table)

            if json_data:
                output_file = os.path.join(output_directory, f"{table}.json")

                with open(output_file, "w") as file:
                    json.dump(json_data, file, indent=4)

                print(f"Exported conversations from table: {table}")

        conn.close()

    def export_table_as_json(self, cursor, table_name):
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        column_names = [column[0] for column in cursor.description]
        json_data = []

        for row in rows:
            conversation = dict(zip(column_names, row))
            json_data.append(conversation)

        return json_data

    # conversation
    ###########################################################################

    def print_conversation(self, db_name, table_name, conversation_id):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (conversation_id,))
        row = cursor.fetchone()

        if row:
            column_names = [column[0] for column in cursor.description]
            conversation = dict(zip(column_names, row))

            print(f"Conversation ID: {conversation_id}")
            for key, value in conversation.items():
                print(f"{key}: {value}")
        else:
            print(f"Conversation not found: {conversation_id}")

        conn.close()

    # inspect
    ###########################################################################

    def inspect_data(self, data_path=None):
        data_path = data_path or self.DEFAULT_DATA_PATH

        if not os.path.exists(data_path):
            print(f"Error: Data directory not found: {data_path}")
            return

        data_files = self.get_data_files(data_path)

        if not data_files:
            print("Error: No JSON data files found.")
            return

        for i, file_path in enumerate(data_files):
            print(f"Inspecting data from: {file_path}")

            if file_path.endswith(".zip"):
                if not zipfile.is_zipfile(file_path):
                    print(f"Error: Invalid zip file: {file_path}")
                    continue

                with zipfile.ZipFile(file_path, "r") as zip_file:
                    json_files = [name for name in zip_file.namelist() if name.endswith(".json")]

                if not json_files:
                    print("Error: No JSON data files found in the zip file.")
                    continue

                for json_file in json_files:
                    with zip_file.open(json_file) as file:
                        json_data = json.load(file)
                        self.inspect_json_data(json_data)
            else:
                with open(file_path) as file:
                    json_data = json.load(file)
                    self.inspect_json_data(json_data)

    def inspect_json_data(self, json_data):
        # Add your inspection logic here
        # For example, you can print the schema, number of records, or any other relevant information
        print(f"Schema: {list(json_data[0].keys())}")
        print(f"Number of Records: {len(json_data)}")
        # ...

    # utility functions
    ###########################################################################

    def truncate_string(self, string, max_length):
        if len(string) <= max_length:
            return string
        return string[:max_length-3] + "..."

    def get_truncation_length(self):
        terminal_size = shutil.get_terminal_size(fallback=(80, 24))
        return terminal_size.columns - 3  # Subtract 3 to account for ellipsis

    # database functions
    ###########################################################################

    def get_table_names(self, cursor):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in cursor.fetchall()]

    def get_table_count(self, cursor, table_name):
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        return cursor.fetchone()[0]

    # run
    ###########################################################################

    def run(self):
        args = self.parser.parse_args()

        if args.subcommand == "import":
            print("Action: Import")
            self.import_data(args.path)
        elif args.subcommand == "show":
            print("Action: Display database tables")
            self.print_tables()
        elif args.subcommand == "delete":
            print("Action: Delete database")
            self.delete_database()
        elif args.subcommand == "info":
            print("Action: Display database information")
            self.info()
        elif args.subcommand == "export":
            print("Action: Export conversations")
            self.export_conversations(args.path)
        elif args.subcommand == "conversation":
            print("Action: Print conversation")
            self.print_conversation(args.path)
        elif args.subcommand == "inspect":
            print("Action: Inspect data files")
            self.inspect_data(args.path)
        else:
            # No subcommand specified, display usage information
            self.parser.print_help()

# main
###############################################################################

if __name__ == "__main__":
    tool = ChatGPTTool()
    tool.run()
