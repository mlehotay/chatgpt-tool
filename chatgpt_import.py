import json
import sqlite3
import argparse
import shutil


def truncate_string(string, max_length):
    if len(string) <= max_length:
        return string
    return string[:max_length-3] + "..."


def get_truncation_length():
    terminal_size = shutil.get_terminal_size(fallback=(80, 24))
    return terminal_size.columns - 3  # Subtract 3 to account for ellipsis


def import_json_data_to_sqlite(db_name, data_files):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    for table_name, file_path in data_files.items():
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
            insert_query = f"INSERT INTO {table_name} VALUES ({','.join(['?'] * len(values))})"
            cursor.execute(insert_query, values)

    conn.commit()
    conn.close()


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
    parser = argparse.ArgumentParser(description="ChatGPT Export Importer")
    parser.add_argument("db_name", type=str, nargs="?", default=None, help="SQLite database name")
    parser.add_argument("data_files", type=str, nargs="*", default=[], help="Data files to import (JSON format)")
    parser.add_argument("-p", "--print-tables", action="store_true", help="Print the content of the tables")

    args = parser.parse_args()

    if args.db_name is not None and args.data_files:
        import_json_data_to_sqlite(args.db_name, {f"data_{i}": file_path for i, file_path in enumerate(args.data_files)})
    elif args.print_tables and args.db_name is not None:
        print_tables(args.db_name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
