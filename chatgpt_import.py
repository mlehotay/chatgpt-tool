import json
import sqlite3
import argparse
import shutil
import os


"""
ChatGPT Export Importer
-----------------------

This script imports conversations that have been exported from ChatGPT and stores them in a SQLite database. It can also
print the content of the tables in the database.

Features
--------
1. Importing JSON data to SQLite:
   - Read JSON data from specified files.
   - Handle both single objects and lists of objects.
   - Create tables dynamically based on the JSON data.
   - Insert data into the respective tables.

2. Organizing JSON files in a subdirectory:
   - Assume all JSON files are located in a subdirectory for better organization.

3. Command-line interface:
   - Accept command-line arguments for the database name and data files to import.
   - Make all command-line arguments optional.
   - Allow importing data into the SQLite database.

4. Printing table content:
   - Print the content of tables in the SQLite database.
   - Retrieve table names dynamically.
   - Truncate long lines based on terminal width.
   - Display table column names.

5. Handling empty JSON files:
   - Check for empty JSON data and skip table creation and data insertion if the JSON data is empty.

To Do
-----
1. Help text and usage information:
   - Provide a help message that explains the available command-line arguments and their usage.

2. Error handling:
   - Handle errors related to file access, JSON parsing, SQLite operations, etc.
"""

DEFAULT_DB_NAME = "chatgpt.db"
DATA_DIRECTORY = "data"


def truncate_string(string, max_length):
    if len(string) <= max_length:
        return string
    return string[:max_length - 3] + "..."


def get_truncation_length():
    terminal_size = shutil.get_terminal_size(fallback=(80, 24))
    return terminal_size.columns - 3  # Subtract 3 to account for ellipsis


def import_json_data_to_sqlite(db_name, data_files):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    for table_name, file_path in data_files.items():
        print(f"Importing data from: {file_path}")
        # Read the JSON data from the file
        with open(file_path) as file:
            json_data = json.load(file)

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
        create_table_query = create_table_query.rstrip(",")
        create_table_query += ")"
        cursor.execute(create_table_query)

        # Insert data into the table
        if isinstance(json_data, list):
            for item in json_data:
                values = tuple(str(value) for value in item.values())
                if len(column_names) != len(values):
                    print("Error: Number of columns in the table does not match the number of values.")
                    continue
                insert_query = f"INSERT INTO {table_name} VALUES ({','.join(['?'] * len(values))})"
                cursor.execute(insert_query, values)
        else:
            values = tuple(str(value) for value in json_data.values())
            if len(column_names) != len(values):
                print("Error: Number of columns in the table does not match the number of values.")
                continue
            insert_query = f"INSERT INTO {table_name} VALUES ({','.join(['?'] * len(values))})"
            cursor.execute(insert_query, values)

    conn.commit()
    conn.close()
    print("Import completed successfully.")


def print_tables(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    truncation_length = get_truncation_length()

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
        print(truncate_string(str(column_names), truncation_length))
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        for row in rows:
            print(truncate_string(str(row), truncation_length))
        print()

    conn.close()


def main():
    parser = argparse.ArgumentParser(prog="ChatGPT Export Importer", description="Import conversations exported from ChatGPT.")
    parser.add_argument("-v", "--version", action="version", version="ChatGPT Export Importer 1.0")
    parser.add_argument("db_name", type=str, nargs="?", default=DEFAULT_DB_NAME,
                        help=f"SQLite database name (default: {DEFAULT_DB_NAME})")
    parser.add_argument("data_files", type=str, nargs="*", default=[],
                        help="Data files to import (JSON format)")
    parser.add_argument("-p", "--print-tables", action="store_true",
                        help="Print the content of the tables")

    args = parser.parse_args()

    if not args.data_files and not args.print_tables:
        # No command-line arguments provided, look for JSON files in the default directory and import them
        if not os.path.exists(DATA_DIRECTORY):
            print(f"Error: Data directory '{DATA_DIRECTORY}' not found.")
            return

        # Get the data files from the data directory
        data_files = [os.path.join(DATA_DIRECTORY, file) for file in os.listdir(DATA_DIRECTORY) if
                      file.endswith(".json")]
        if not data_files:
            print("Error: No JSON data files found in the data directory.")
            return

        print(f"Importing data files: {data_files}")
        import_json_data_to_sqlite(args.db_name, {f"data_{i}": file_path for i, file_path in enumerate(data_files)})
    elif args.data_files:
        if args.print_tables:
            print("Error: Please specify either data files or print tables, not both.")
            return

        print(f"Importing data files: {args.data_files}")
        import_json_data_to_sqlite(args.db_name,
                                   {f"data_{i}": file_path for i, file_path in enumerate(args.data_files)})
    elif args.print_tables:
        print_tables(args.db_name)


if __name__ == "__main__":
    main()
