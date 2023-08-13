import argparse
import json
import os
import sqlite3
import zipfile
import shutil
import tempfile
import string

from gazpacho import Soup

"""
ChatGPT Tool

ChatGPT Tool is a command-line utility for importing ChatGPT conversations from JSON and managing them in a SQLite database.

"""

html_to_json_mapping = {
    "chat": "conversations",
    # Add more mappings if needed
}

class ChatGPTTool:
    DEFAULT_DB_NAME = "chatgpt.db"
    DEFAULT_DATA_PATH = "data"
    CHAT_TABLE = "conversations"

    # init
    ###########################################################################

    def __init__(self):
        self.parser = argparse.ArgumentParser(prog="chatgpt_tool", description="ChatGPT Tool")

        subparsers = self.parser.add_subparsers(title="subcommands", dest="subcommand")

        # Subcommand: import
        import_parser = subparsers.add_parser("import", help="Import JSON data into the SQLite database")
        import_parser.add_argument("path", help="Filepath or directory for import")
        import_parser.add_argument("-db", "--db-name", dest="db_name", default=self.DEFAULT_DB_NAME, help="Name of the SQLite database (default: chatgpt.db)")

        # Subcommand: show
        show_parser = subparsers.add_parser("show", help="Display database tables")
        show_parser.add_argument("-db", "--db-name", dest="db_name", default=self.DEFAULT_DB_NAME, help="Name of the SQLite database (default: chatgpt.db)")

        # Subcommand: info
        info_parser = subparsers.add_parser("info", help="Display database information")
        info_parser.add_argument("-db", "--db-name", dest="db_name", default=self.DEFAULT_DB_NAME, help="Name of the SQLite database (default: chatgpt.db)")

        # Subcommand: export
        export_parser = subparsers.add_parser("export", help="Export conversations from the SQLite database")
        export_parser.add_argument("path", help="Output directory for export")
        export_parser.add_argument("-db", "--db-name", dest="db_name", default=self.DEFAULT_DB_NAME, help="Name of the SQLite database (default: chatgpt.db)")

        # Subcommand: print
        print_parser = subparsers.add_parser("print", help="Print conversation")
        print_parser.add_argument("id_prefix", help="Conversation ID prefix to find and print.")
        print_parser.add_argument("-db", "--db-name", dest="db_name", default=self.DEFAULT_DB_NAME, help="Name of the SQLite database (default: chatgpt.db)")

        # Subcommand: inspect
        inspect_parser = subparsers.add_parser("inspect", help="Inspect data files")
        inspect_parser.add_argument("path", nargs="?", default=self.DEFAULT_DATA_PATH, help="Data directory for inspection")

    # import
    ###########################################################################

    def import_data(self, db_name, data_path):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        self.traverse_files(data_path, self.import_file, cursor)

        conn.commit()
        conn.close()

    def traverse_files(self, path, process_function, *args):
        if os.path.isdir(path):
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    self.traverse_files(file_path, process_function, *args)
        elif path.endswith(".zip"):
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(path, "r") as zip_file:
                    for name in zip_file.namelist():
                        extracted_file_path = zip_file.extract(name, path=temp_dir)
                        self.traverse_files(extracted_file_path, process_function, *args)
        else:
            process_function(*args, path)

    def import_file(self, cursor, file_path):
        print(f"Importing data from: {file_path}")
        if file_path.endswith(".json"):
            with open(file_path) as file:
                json_data = json.load(file)
                table_name = self.get_table_name(file_path)
                self.import_json_data_to_sqlite(cursor, table_name, json_data)
        elif file_path.endswith(".html"):
            with open(file_path) as file:
                html_basename = self.get_table_name(file_path)
                html_content = file.read()
                json_data = self.extract_json_from_html(html_content)
                if json_data:
                    table_name = html_to_json_mapping.get(html_basename, html_basename)
                    self.import_json_data_to_sqlite(cursor, table_name, json_data)
                else:
                    print(f"Warning: No JSON data found in the HTML file: {file_path}")
        else:
            print(f"Warning: Unexpected file format: {file_path}")

    def get_table_name(self, file_path):
        base_filename = os.path.basename(file_path)
        table_name = os.path.splitext(base_filename)[0]

        # Create a set of valid characters for the table name
        valid_chars = set(string.ascii_letters + string.digits + "_")

        # Generate the table name using only valid characters
        table_name = ''.join(c if c in valid_chars else "_" for c in table_name)

        return table_name

    def extract_json_from_html(self, html_content):
        # Parse the HTML content using Gazpacho
        soup = Soup(html_content)

        # Find the <script> tags in the HTML
        script_tags = soup.find('script', mode='all', partial=False)

        # Search for the <script> tag containing the jsonData variable assignment
        json_data = None
        for script_tag in script_tags:
            if 'jsonData =' in script_tag.text:
                lines = script_tag.text.split('\n')
                line_with_json = next(line for line in lines if 'jsonData =' in line)
                try:
                    json_start = line_with_json.index("[")
                    json_end = line_with_json.rindex("]") + 1
                    json_string = line_with_json[json_start:json_end]

                    # Convert JSON string to Python object (list of dicts)
                    json_data = json.loads(json_string)
                    break
                except (json.JSONDecodeError, ValueError, IndexError):
                    print("Warning: Unable to extract JSON objects from jsonData variable.")
                    return None

        if json_data is not None:
            return json_data

        print("Warning: No <script> tag containing jsonData variable found.")
        return []

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
        # print(f"table: {table_name}; columns: {column_names}")

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

    def truncate_string(self, string, max_length):
        if len(string) <= max_length:
            return string
        return string[:max_length-3] + "..."

    def get_truncation_length(self):
        terminal_size = shutil.get_terminal_size(fallback=(80, 24))
        return terminal_size.columns - 3  # Subtract 3 to account for ellipsis

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

    def get_table_names(self, cursor):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in cursor.fetchall()]

    def get_table_count(self, cursor, table_name):
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        return cursor.fetchone()[0]

    def query_table(self, table_name, condition_field, condition_value):
        conn = sqlite3.connect(self.DEFAULT_DB_NAME)
        cursor = conn.cursor()

        query = f"SELECT * FROM {table_name} WHERE {condition_field} = ?"
        cursor.execute(query, (condition_value,))
        row = cursor.fetchone()

        if row:
            column_names = [column[0] for column in cursor.description]
            result = dict(zip(column_names, row))
        else:
            result = None

        conn.close()
        return result

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

    # print
    ###########################################################################

    def print_conversation(self, db_name, conversation_id):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM {self.CHAT_TABLE} WHERE id = ?", (conversation_id,))
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

        self.traverse_files(data_path, self.inspect_file)

    def inspect_file(self, file_path):
        print(f"Inspecting data from: {file_path}")
        if file_path.endswith(".json"):
            with open(file_path) as file:
                json_data = json.load(file)
                self.inspect_json_data(json_data)
        elif file_path.endswith(".html"):
            with open(file_path) as file:
                html_content = file.read()
                json_data = self.extract_json_from_html(html_content)
                if json_data:
                    self.inspect_json_data(json_data)
                else:
                    print("Warning: No JSON data found in the HTML file.")
        else:
            print("Warning: Unexpected file format.")

    def inspect_json_data(self, json_data):
        if not json_data:
            print("Warning: JSON data is empty.")
            return

        if not isinstance(json_data, list) or not all(isinstance(item, dict) for item in json_data):
            print("Warning: Invalid JSON data format. Expected a list of dictionaries.")
            return

        if json_data:
            print(f"Schema: {list(json_data[0].keys())}")
            print(f"Number of Records: {len(json_data)}")
            # ... (other inspection logic)

    # run
    ###########################################################################

    def run(self):
        args = self.parser.parse_args()

        if args.subcommand == "import":
            print("Action: Import")
            self.import_data(args.db_name, args.path)
        elif args.subcommand == "show":
            print("Action: Display database tables")
            self.print_tables(args.db_name)
        elif args.subcommand == "info":
            print("Action: Display database information")
            self.info(args.db_name)
        elif args.subcommand == "export":
            print("Action: Export conversations")
            self.export_conversations(args.db_name, args.path)
        elif args.subcommand == "print":
            print("Action: Print conversation")
            if args.id_prefix:
                self.print_conversation(args.db_name, args.id_prefix)
            else:
                print("Error: 'print' subcommand requires the 'id_prefix' argument.")
        elif args.subcommand == "inspect":
            print("Action: Inspect data files")
            self.inspect_data(args.path)
        else:
            self.parser.print_help()

# main
###############################################################################

if __name__ == "__main__":
    tool = ChatGPTTool()
    tool.run()
