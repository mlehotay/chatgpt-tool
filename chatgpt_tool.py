import argparse
import json
import os
import shutil
import sqlite3
import doctest
import zipfile

"""
ChatGPT Tool

ChatGPT Tool is a command-line utility for importing ChatGPT conversations from the ChatGPT export JSON format and managing them in a SQLite database.

See README.md for more information.
"""

class ChatGPTTool:
    DEFAULT_DB_NAME = "chatgpt.db"
    DEFAULT_DATA_DIRECTORY = "data"

# init

    def __init__(self):
        self.parser = argparse.ArgumentParser(description="ChatGPT Tool")
        self.subparsers = self.parser.add_subparsers(title="subcommands", dest="subcommand")

        self.setup_import_command()
        self.setup_print_command()
        self.setup_delete_command()
        self.setup_help_command()
        self.setup_info_command()
        self.setup_test_command()
        self.setup_export_command()
        self.setup_conversation_command()
        self.setup_inspect_command()

# setup subcommands

    def setup_import_command(self):
        # Create the 'import' subcommand parser
        import_parser = self.subparsers.add_parser("import", help="Import JSON data into the SQLite database")
        import_parser.add_argument("-d", "--db-name", type=str, default=self.DEFAULT_DB_NAME, help="SQLite database name")
        import_parser.add_argument("-f", "--data-directory", type=str, default=self.DEFAULT_DATA_DIRECTORY, help="Data directory to import (JSON format)")

    def setup_print_command(self):
        # Create the 'print' subcommand parser
        print_parser = self.subparsers.add_parser("print", help="Print the content of the SQLite database tables")
        print_parser.add_argument("-d", "--db-name", type=str, default=self.DEFAULT_DB_NAME, help="SQLite database name")

    def setup_delete_command(self):
        # Create the 'delete' subcommand parser
        delete_parser = self.subparsers.add_parser("delete", help="Delete the SQLite database file")
        delete_parser.add_argument("-d", "--db-name", type=str, default=self.DEFAULT_DB_NAME, help="SQLite database name")

    def setup_help_command(self):
        # Create the 'help' subcommand parser
        help_parser = self.subparsers.add_parser("help", help="Show usage information for the tool")
        help_subparsers = help_parser.add_subparsers(title="subcommands", dest="subcommand")

        # Add subparsers for each subcommand
        import_help_parser = help_subparsers.add_parser("import", help="Show usage information for the import subcommand")
        print_help_parser = help_subparsers.add_parser("print", help="Show usage information for the print subcommand")
        delete_help_parser = help_subparsers.add_parser("delete", help="Show usage information for the delete subcommand")
        help_help_parser = help_subparsers.add_parser("help", help="Show usage information for the help subcommand")
        info_help_parser = help_subparsers.add_parser("info", help="Show usage information for the info subcommand")
        test_help_parser = help_subparsers.add_parser("test", help="Show usage information for the test subcommand")

    def setup_info_command(self):
        # Create the 'info' subcommand parser
        info_parser = self.subparsers.add_parser("info", help="Display statistics about the database and the data")
        info_parser.add_argument("-d", "--db-name", type=str, default=self.DEFAULT_DB_NAME, help="SQLite database name")

    def setup_test_command(self):
        # Create the 'test' subcommand parser
        test_parser = self.subparsers.add_parser("test", help="Run the doctests")
        test_parser.add_argument("-v", "--verbose", action="store_true", help="Display verbose output")

# import

    def setup_info_command(self):
        # Create the 'info' subcommand parser
        info_parser = self.subparsers.add_parser("info", help="Display statistics about the database and the data")

    def import_data(self, db_name, data_directory=None):
        """
        Import JSON data into the SQLite database.

        >>> # Test import with a valid JSON file
        >>> tool = ChatGPTTool()
        >>> tool.import_data("test.db", "data.json")
        Importing data from: data.json

        >>> # Test import with a non-existent data directory
        >>> tool = ChatGPTTool()
        >>> tool.import_data("test.db", "nonexistent")
        Error: Data directory not found: nonexistent

        >>> # Test import with an empty data directory
        >>> tool = ChatGPTTool()
        >>> tool.import_data("test.db", "empty_directory")
        Error: No JSON data files found.

        >>> # Test import with an invalid zip file
        >>> tool = ChatGPTTool()
        >>> tool.import_data("test.db", "invalid_zip.zip")
        Error: Invalid zip file: invalid_zip.zip

        >>> # Test import with a zip file containing no JSON files
        >>> tool = ChatGPTTool()
        >>> tool.import_data("test.db", "empty_zip.zip")
        Error: No JSON data files found in the zip file.
        """
        data_directory = data_directory or self.DEFAULT_DATA_DIRECTORY

        if not os.path.exists(data_directory):
            print(f"Error: Data directory not found: {data_directory}")
            return

        data_files = self.get_data_files(data_directory)

        if not data_files:
            print("Error: No JSON data files found.")
            return

        conn = sqlite3.connect(db_name)
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

                if not json_files:
                    print("Error: No JSON data files found in the zip file.")
                    continue

                for json_file in json_files:
                    with zip_file.open(json_file) as file:
                        json_data = json.load(file)
                        self.import_json_data_to_sqlite(cursor, table_name, json_data)
            else:
                with open(file_path) as file:
                    json_data = json.load(file)
                    self.import_json_data_to_sqlite(cursor, table_name, json_data)

        conn.commit()
        conn.close()

    def get_data_files(self, data_directory=None):
        """
        Get a list of data files in the specified directory.

        >>> # Test with a valid data directory containing JSON files
        >>> tool = ChatGPTTool()
        >>> tool.get_data_files("data")
        ['data/data1.json', 'data/data2.json']

        >>> # Test with a non-existent data directory
        >>> tool = ChatGPTTool()
        >>> tool.get_data_files("nonexistent")
        Error: Data directory not found: nonexistent
        []

        >>> # Test with a zip file containing JSON files
        >>> tool = ChatGPTTool()
        >>> tool.get_data_files("data.zip")
        ['data.zip/data1.json', 'data.zip/data2.json']

        >>> # Test with a zip file containing no JSON files
        >>> tool = ChatGPTTool()
        >>> tool.get_data_files("empty_zip.zip")
        Error: No JSON data files found in the zip file.
        []
        """
        data_directory = data_directory or self.DEFAULT_DATA_DIRECTORY

        if not os.path.exists(data_directory):
            print(f"Error: Data directory not found: {data_directory}")
            return []

        if data_directory.endswith(".zip"):
            if not zipfile.is_zipfile(data_directory):
                print(f"Error: Invalid zip file: {data_directory}")
                return []

            with zipfile.ZipFile(data_directory, "r") as zip_file:
                json_files = [file for file in zip_file.namelist() if file.endswith(".json")]

            if not json_files:
                print("Error: No JSON data files found in the zip file.")
                return []

            return [os.path.join(data_directory, json_file) for json_file in json_files]

        data_files = [os.path.join(data_directory, file) for file in os.listdir(data_directory) if file.endswith(".json")]
        return data_files

    def import_json_data_to_sqlite(self, cursor, table_name, json_data):
        """
        Import JSON data into SQLite database.

        >>> # Test import with a valid JSON data
        >>> tool = ChatGPTTool()
        >>> cursor = None  # Mock cursor object
        >>> json_data = [
        ...     {"id": 1, "name": "John Doe"},
        ...     {"id": 2, "name": "Jane Smith"}
        ... ]
        >>> tool.import_json_data_to_sqlite(cursor, "data_1", json_data)
        """
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

# print

    def print_tables(self, db_name):
        """
        Print the content of the SQLite database tables.

        >>> # Test printing tables with a valid database
        >>> tool = ChatGPTTool()
        >>> tool.print_tables("test.db")
        Table: table1
        ['id', 'name']
        ('1', 'John Doe')
        ('2', 'Jane Smith')

        Table: table2
        ['id', 'message']
        ('1', 'Hello')
        ('2', 'Hi')

        >>> # Test printing tables with a non-existent database
        >>> tool = ChatGPTTool()
        >>> tool.print_tables("nonexistent.db")
        Error: Database not found: nonexistent.db
        """
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

    def delete_database(self, db_name):
        try:
            os.remove(db_name)
            print(f"Deleted database: {db_name}")
        except FileNotFoundError:
            print(f"Database not found: {db_name}")

# info

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

# test

    def test(self, verbose):
        if verbose:
            print("Running doctests...")
        doctest.testmod(verbose=verbose)

# export

    def setup_export_command(self):
        # Create the 'export' subcommand parser
        export_parser = self.subparsers.add_parser("export", help="Export conversations from the SQLite database to JSON format")
        export_parser.add_argument("-d", "--db-name", type=str, default=self.DEFAULT_DB_NAME, help="SQLite database name")
        export_parser.add_argument("-o", "--output-directory", type=str, default=self.DEFAULT_DATA_DIRECTORY, help="Output directory to export conversations (JSON format)")

    def export_conversations(self, db_name, output_directory=None):
        output_directory = output_directory or self.DEFAULT_DATA_DIRECTORY

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

    def setup_conversation_command(self):
        # Create the 'conversation' subcommand parser
        conversation_parser = self.subparsers.add_parser("conversation", help="Print a conversation from the SQLite database")
        conversation_parser.add_argument("-d", "--db-name", type=str, default=self.DEFAULT_DB_NAME, help="SQLite database name")
        conversation_parser.add_argument("-t", "--table", type=str, required=True, help="Table name containing the conversation")
        conversation_parser.add_argument("-i", "--id", type=str, required=True, help="ID of the conversation")

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

    def setup_inspect_command(self):
        # Create the 'inspect' subcommand parser
        inspect_parser = self.subparsers.add_parser("inspect", help="Inspect data files before importing")
        inspect_parser.add_argument("-f", "--data-directory", type=str, default=self.DEFAULT_DATA_DIRECTORY, help="Data directory to inspect (JSON format)")

    def inspect_data(self, data_directory=None):
        data_directory = data_directory or self.DEFAULT_DATA_DIRECTORY

        if not os.path.exists(data_directory):
            print(f"Error: Data directory not found: {data_directory}")
            return

        data_files = self.get_data_files(data_directory)

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

    def truncate_string(self, string, max_length):
        if len(string) <= max_length:
            return string
        return string[:max_length-3] + "..."

    def get_truncation_length(self):
        terminal_size = shutil.get_terminal_size(fallback=(80, 24))
        return terminal_size.columns - 3  # Subtract 3 to account for ellipsis

# database functions

    def get_table_names(self, cursor):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in cursor.fetchall()]

    def get_table_count(self, cursor, table_name):
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        return cursor.fetchone()[0]

# run

    def run(self):
        """
        Run the ChatGPT tool.

        >>> # Test running the tool
        >>> tool = ChatGPTTool()
        >>> tool.run()
        """
        args = self.parser.parse_args()

        if args.subcommand == "import":
            print("Action: Import")
            self.import_data(args.db_name, args.data_directory)
        elif args.subcommand == "print":
            print("Action: Print tables")
            self.print_tables(args.db_name)
        elif args.subcommand == "delete":
            print("Action: Delete database")
            self.delete_database(args.db_name)
        elif args.subcommand == "info":
            print("Action: Display database information")
            self.info(args.db_name)
        elif args.subcommand == "help":
            print("Action: Display help")
            self.parser.print_help()
        elif args.subcommand == "test":
            print("Action: Run doctests")
            self.test(args.verbose)
        elif args.subcommand == "inspect":
            print("Action: Inspect data files")
            self.inspect_data(args.data_directory)
        else:
            # No subcommand specified, try to import using default settings
            print("Action: Import using default settings")
            self.import_data(self.DEFAULT_DB_NAME, None)

# main

if __name__ == "__main__":
    tool = ChatGPTTool()
    tool.run()
