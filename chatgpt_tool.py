import argparse
import json
import os
import shutil
import sqlite3

"""
ChatGPT Tool

ChatGPT Tool is a command-line utility for importing and managing ChatGPT conversations in a SQLite database.

## Features

- Command-line interface:
  - Accept command-line arguments for importing, printing, and deleting data
  - Accept command-line arguments for the database name and data files to import
  - Make all command-line arguments optional
- Data Import:
  - Import JSON data files into SQLite tables
  - Automatically create tables based on file names
  - Handle JSON data with varying "id" field positions
  - Insert new data and ignore duplicates
- Data Printing:
  - Print the content of the SQLite database tables
- Data Deletion:
  - Delete the SQLite database file

## To Do

- Help text and usage information:
  - Provide a help message that explains the available command-line arguments and their usage
- Error handling:
  - Handle errors related to command-line arguments, SQLite operations, etc
- HTML Data Import:
  - Implement parsing and import of JSON data from HTML files
  - Handle mapping between HTML files and corresponding JSON files
  - Check for duplicates and insert new data into the conversations table
- Optimization:
  - Implement efficient search for duplicates before inserting new data
- Enhanced Database Interaction:
  - Add more advanced database operations like updating and deleting specific rows
- Schema Checking:
  - Verify HTML file schema against existing tables and import accordingly

"""

class ChatGPTTool:
    DEFAULT_DB_NAME = "chatgpt.db"
    DEFAULT_DATA_DIRECTORY = "data"

    def __init__(self):
        self.parser = argparse.ArgumentParser(description="ChatGPT Tool")
        self.subparsers = self.parser.add_subparsers(title="subcommands", dest="subcommand")

        self.setup_import_command()
        self.setup_print_command()
        self.setup_help_command()
        self.setup_delete_command()
        self.setup_info_command()

    def setup_import_command(self):
        # Create the 'import' subcommand parser
        import_parser = self.subparsers.add_parser("import", help="Import JSON data into the SQLite database")
        import_parser.add_argument("-d", "--db-name", type=str, default=self.DEFAULT_DB_NAME, help="SQLite database name")
        import_parser.add_argument("-f", "--data-files", type=str, nargs="*", default=None, help="Data files to import (JSON format)")

    def setup_print_command(self):
        # Create the 'print' subcommand parser
        print_parser = self.subparsers.add_parser("print", help="Print the content of the SQLite database tables")
        print_parser.add_argument("-d", "--db-name", type=str, default=self.DEFAULT_DB_NAME, help="SQLite database name")


    def setup_help_command(self):
        # Create the 'help' subcommand parser
        help_parser = self.subparsers.add_parser("help", help="Show usage information for the tool")
        help_subparsers = help_parser.add_subparsers(title="subcommands", dest="subcommand")

        # Add subparsers for each subcommand
        import_help_parser = help_subparsers.add_parser("import", help="Show usage information for the import subcommand")
        print_help_parser = help_subparsers.add_parser("print", help="Show usage information for the print subcommand")
        delete_help_parser = help_subparsers.add_parser("delete", help="Show usage information for the delete subcommand")
        help_help_parser = help_subparsers.add_parser("help", help="Show usage information for the help subcommand")

    def setup_delete_command(self):
        # Create the 'delete' subcommand parser
        delete_parser = self.subparsers.add_parser("delete", help="Delete the SQLite database file")
        delete_parser.add_argument("-d", "--db-name", type=str, default=self.DEFAULT_DB_NAME, help="SQLite database name")

    def setup_info_command(self):
        # Create the 'info' subcommand parser
        info_parser = self.subparsers.add_parser("info", help="Display statistics about the database and the data")

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

    def delete_database(self, db_name):
        try:
            os.remove(db_name)
            print(f"Deleted database: {db_name}")
        except FileNotFoundError:
            print(f"Database not found: {db_name}")

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
        elif args.subcommand == "delete":
            print("Action: Delete database")
            self.delete_database(args.db_name)
        else:
            # No subcommand specified, try to import using default settings
            print("Action: Import using default settings")
            self.import_data(self.DEFAULT_DB_NAME, None)

    def get_table_names(self, cursor):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in cursor.fetchall()]

    def get_table_count(self, cursor, table_name):
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        return cursor.fetchone()[0]

if __name__ == "__main__":
    tool = ChatGPTTool()
    tool.run()
