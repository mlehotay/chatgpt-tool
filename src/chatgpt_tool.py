import argparse
import json
import os
import sqlite3
import zipfile
import shutil
import tempfile
import string
import hashlib
from gazpacho import Soup

"""
ChatGPT Tool

ChatGPT Tool is a command-line utility for importing ChatGPT conversations from JSON and managing them in a SQLite database.

"""

class ChatGPTTool:
    DB_NAME = "chatgpt.db"
    DATA_PATH = "data"
    EXPORT_PATH = "export"
    SCHEMA_TABLE = "schema"
    CHAT_TABLE = "conversations"

    TABLE_MAPPING = {
        "chat": CHAT_TABLE,
        # Add more mappings if needed
    }

    # init
    ###########################################################################
    # This section contains the setup for the command-line interface (CLI) and
    # subcommands with their respective arguments and descriptions.
    ###########################################################################

    def __init__(self, db_path=None):
        self.db_path = db_path or self.DB_NAME
        self.parser = argparse.ArgumentParser(prog="chatgpt_tool", description="ChatGPT Tool")

        subparsers = self.parser.add_subparsers(title="subcommands", dest="subcommand")

        # Subcommand: import
        import_parser = subparsers.add_parser("import", help="Import JSON data into the SQLite database")
        import_parser.add_argument("path", help="Filepath or directory for import")
        import_parser.add_argument("-db", "--db-name", dest="db_name", default=self.DB_NAME, help="Name of the SQLite database (default: chatgpt.db)")

        # Subcommand: show
        show_parser = subparsers.add_parser("show", help="Display database tables")
        show_parser.add_argument("-db", "--db-name", dest="db_name", default=self.DB_NAME, help="Name of the SQLite database (default: chatgpt.db)")

        # Subcommand: info
        info_parser = subparsers.add_parser("info", help="Display database information")
        info_parser.add_argument("-db", "--db-name", dest="db_name", default=self.DB_NAME, help="Name of the SQLite database (default: chatgpt.db)")

        # Subcommand: export
        export_parser = subparsers.add_parser("export", help="Export conversations from the SQLite database")
        export_parser.add_argument("path", help="Output directory for export")
        export_parser.add_argument("-db", "--db-name", dest="db_name", default=self.DB_NAME, help="Name of the SQLite database (default: chatgpt.db)")
        export_parser.add_argument("-html", action="store_true", help="Export conversations as HTML files")
        export_parser.add_argument("-text", action="store_true", help="Export conversations as plain text files")
        export_parser.add_argument("-json", action="store_true", help="Export conversations as JSON files (default)")
        export_parser.add_argument("-prefix", dest="prefix", help="Export conversations with IDs starting with the specified prefix")

        # Subcommand: print
        print_parser = subparsers.add_parser("print", help="Print conversation")
        print_parser.add_argument("prefix", help="Conversation ID prefix to find and print.")
        print_parser.add_argument("-db", "--db-name", dest="db_name", default=self.DB_NAME, help="Name of the SQLite database (default: chatgpt.db)")

        # Subcommand: inspect
        inspect_parser = subparsers.add_parser("inspect", help="Inspect data files")
        inspect_parser.add_argument("path", nargs="?", default=self.DATA_PATH, help="Data directory for inspection")

    # import
    ###########################################################################
    # Place functions related to importing data into the database here. This
    # includes functions like `import_data`, `traverse_files`, `process_file`,
    # and other related helper functions.
    ###########################################################################

    def import_data(self, db_name, data_path):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        self.create_schema_table(cursor)  # Create the schema table if it doesn't exist
        self.traverse_files(data_path, self.import_json_data_to_sqlite, cursor)

        conn.commit()
        conn.close()

    def traverse_files(self, path, process_function, *args):
        if os.path.isdir(path):
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    self.traverse_files(file_path, process_function, *args)
        elif path.endswith(".zip"):
            # print(f"Importing zip file '{path}'")
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(path, "r") as zip_file:
                    for name in zip_file.namelist():
                        extracted_file_path = zip_file.extract(name, path=temp_dir)
                        self.traverse_files(extracted_file_path, process_function, *args)
        else:
            _, file_extension = os.path.splitext(path)
            if file_extension.lower() in (".json", ".html"):
                self.process_file(path, process_function, *args)

    def process_file(self, path, process_function, *args):
        _, file_extension = os.path.splitext(path)
        table_name = None

        try:
            if os.path.getsize(path) == 0:
                print(f"Warning: Skipping empty file '{path}'")
            elif file_extension.lower() == ".json":
                # print(f"Importing JSON file '{path}'")
                with open(path) as file:
                    json_data = json.load(file)
                    table_name = self.get_table_name(path)
                    process_function(*args, json_data, table_name)
            elif file_extension.lower() == ".html":
                # print(f"Importing HTML file '{path}'")
                with open(path) as file:
                    html_content = file.read()
                    json_data = self.extract_json_from_html(html_content)
                    if json_data:
                        html_basename = self.get_table_name(path)
                        table_name = self.TABLE_MAPPING.get(html_basename, html_basename)
                        process_function(*args, json_data, table_name)
                    else:
                        print("Warning: No JSON data found in the HTML file.")
            else:
                print("Warning: Unexpected file format.")
        except Exception as e:
            print(f"Error processing file '{path}': {e}")

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

    def import_json_data_to_sqlite(self, cursor, json_data, table_name):
        if not json_data: # Check if the JSON data is empty (in list format)
            print(f"Skipping import for table: {table_name} (empty JSON data)")
            return

        id_field_name, column_names = self.get_id_and_column_names(json_data)
        if not id_field_name:
            print(f"Skipping import for table: {table_name} (no 'id' field found)")
            return

        elif isinstance(json_data, list):
            if json_data and isinstance(json_data[0], dict): # Check if it's a list of dictionaries
                existing_table_name = self.get_existing_table_name(cursor, table_name)
                if existing_table_name:
                    existing_column_names = self.get_column_names(cursor, existing_table_name)
                    new_column_names = sorted(json_data[0].keys())

                    if existing_column_names == new_column_names:
                        # Same schema and column names, use existing table
                        table_name = existing_table_name
                    else:
                        # Schema changed, create a new table
                        self.create_table(cursor, table_name, new_column_names)
                else:
                    # No table with the same name, create a new table
                    self.create_table(cursor, table_name, sorted(json_data[0].keys()))
            else:
                print(f"Skipping import for table: {table_name} (invalid JSON data)")
                return
        elif not isinstance(json_data, dict): # Check if the JSON data is not in valid dictionary format
            print(f"Skipping import for table: {table_name} (invalid JSON data)")
            return
        elif isinstance(json_data, str): # If the JSON data is a string, try to parse it into a dictionary
            try:
                json_data = json.loads(json_data)
            except json.JSONDecodeError:
                print(f"Skipping import for table: {table_name} (invalid JSON data)")
                return

        # Record schema changes
        self.record_schema_change(cursor, table_name, existing_column_names, new_column_names)

        # Insert data into the table
        if isinstance(json_data, list):
            self.insert_data_list(cursor, table_name, json_data)
        else:
            self.insert_data_single(cursor, table_name, json_data)

    def get_id_and_column_names(self, json_data):
        if isinstance(json_data, list):
            first_object = json_data[0]
        else:
            first_object = json_data

        id_field_name = next((key for key in first_object.keys() if key.lower() == "id"), None)
        if not id_field_name:
            return None, None

        column_names = first_object.keys()
        return id_field_name, column_names

    def get_column_names(self, cursor, table_name):
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns_info = cursor.fetchall()
        return [column_info[1] for column_info in columns_info]

    def create_table(self, cursor, table_name, column_names):
        id_field_name, _ = self.get_id_and_column_names(column_names)
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({id_field_name} TEXT PRIMARY KEY,"
        for column_name in column_names:
            if column_name.lower() != id_field_name.lower():
                create_table_query += f"{column_name} TEXT,"
        create_table_query = create_table_query.rstrip(',')
        create_table_query += ")"
        cursor.execute(create_table_query)

    def insert_data_list(self, cursor, table_name, json_data_list):
        for item in json_data_list:
            if item:
                inferred_id_field_name = self.infer_id_field_name(cursor, table_name)
                values = tuple(str(value) for value in item.values())
                self.insert_data(cursor, table_name, item.keys(), values, inferred_id_field_name)

    def insert_data_single(self, cursor, table_name, json_data):
        values = tuple(str(value) for value in json_data.values())
        self.insert_data(cursor, table_name, json_data.keys(), values)

    def insert_data(self, cursor, table_name, column_names, values):
        insert_query = f"INSERT OR IGNORE INTO {table_name} ({','.join(column_names)}) VALUES ({','.join(['?'] * len(values))})"
        cursor.execute(insert_query, values)

    # print
    ###########################################################################
    # Functions that handle printing and displaying information from the
    # database or conversations belong in this section. Include functions like
    # `print_tables`, `print_single_conversation`, and others.
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

    def print_conversation(self, db_name, prefix):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        conversation_ids = self.get_matching_conversation_ids(cursor, prefix)

        if conversation_ids:
            for conversation_id in conversation_ids:
                self.print_single_conversation(cursor, conversation_id)
        else:
            print(f"No conversations found with prefix: {prefix}")

        conn.close()

    def print_single_conversation(self, cursor, conversation_id):
        cursor.execute(f"SELECT * FROM {self.CHAT_TABLE} WHERE id = ?", (conversation_id,))
        row = cursor.fetchone()

        if row:
            column_names = [column[0] for column in cursor.description]
            conversation = dict(zip(column_names, row))

            print(f"Conversation ID: {conversation_id}")
            messages = self.get_conversation_messages(conversation)
            for message in messages:
                print(f"{message['author']}: {message['text']}")
            print()
        else:
            print(f"Conversation not found: {conversation_id}")

    def get_matching_conversation_ids(self, cursor, prefix):
        cursor.execute(f"SELECT id FROM {self.CHAT_TABLE} WHERE id LIKE ?", (f"{prefix}%",))
        return [row[0] for row in cursor.fetchall()]

    def get_conversation_messages(self, conversation):
        messages = []
        current_node = conversation["current_node"]
        mapping = conversation["mapping"]

        while current_node is not None:
            node = mapping[current_node]
            if (
                "message" in node
                and node["message"]
                and "content" in node["message"]
                and node["message"]["content"]["content_type"] == "text"
                and "parts" in node["message"]["content"]
                and node["message"]["content"]["parts"]
                and len(node["message"]["content"]["parts"][0]) > 0
                and node["message"]["author"]["role"] != "system"
            ):
                author = node["message"]["author"]["role"]
                if author == "assistant":
                    author = "ChatGPT"
                messages.append({"author": author, "text": node["message"]["content"]["parts"][0]})
            current_node = node["parent"]

        return messages[::-1]

    def truncate_string(self, string, max_length):
        if len(string) <= max_length:
            return string
        return string[:max_length-3] + "..."

    def get_truncation_length(self):
        terminal_size = shutil.get_terminal_size(fallback=(80, 24))
        return terminal_size.columns - 3  # Subtract 3 to account for ellipsis

    # info
    ###########################################################################
    # Include functions that provide information about the database, such as
    # `info`, `get_table_names`, `get_table_count`, and others.
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

    def get_existing_table_name(self, cursor, table_name):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        existing_table = cursor.fetchone()
        return existing_table[0] if existing_table else None

    def query_table(self, table_name, condition_field, condition_value):
        conn = sqlite3.connect(self.DB_NAME)
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

    def print_table_schemas(self, conn, print_types=False):
        cursor = conn.cursor()

        # Get a list of all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = cursor.fetchall()

        # Print the schema for each table
        for table_name in table_names:
            self.print_single_table_schema(cursor, table_name[0], print_types)

        cursor.close()

    def print_single_table_schema(self, cursor, table_name, print_types=False):
        # Get the columns and data types for the table
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns_info = cursor.fetchall()

        print(f"Schema for table '{table_name}':")
        for column_info in columns_info:
            if print_types:
                print(f"  {column_info[1]} ({column_info[2]})")
            else:
                print(f"  {column_info[1]}")

        print()

    # export
    ###########################################################################
    # Functions related to exporting conversations and data should be grouped
    # here. Functions like `export_conversations`, `export_conversation`,
    # `export_conversation_plain_text`, and others fit in this section.
    ###########################################################################

    def export_conversations(self, db_name, output_directory=None, export_format="html", prefix=None):
        output_directory = output_directory or self.EXPORT_PATH

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        tables = self.get_table_names(cursor)

        for table in tables:
            json_data = self.export_table_as_json(cursor, table)

            if json_data:
                if prefix is None or table.startswith(prefix):
                    if export_format == "html":
                        self.export_conversations_as_html(table, json_data, output_directory)
                    elif export_format == "json":
                        self.export_conversations_as_json(table, json_data, output_directory)
                    else:
                        print(f"Unknown export format: {export_format}")

        conn.close()

    def export_conversation(self, db_name, conversation_id, output_directory=None, export_format="html"):
        output_directory = output_directory or self.EXPORT_PATH

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        conversation = self.query_table(self.CHAT_TABLE, "id", conversation_id)

        if conversation:
            table_name = conversation["table_name"]
            if export_format == "html":
                self.export_conversation_as_html(conversation_id, conversation, output_directory)
            elif export_format == "json":
                self.export_conversation_as_json(conversation_id, conversation, output_directory)
            else:
                print(f"Unknown export format: {export_format}")
        else:
            print(f"Conversation not found: {conversation_id}")

        conn.close()

    def export_conversation_as_html(self, conversation_id, conversation, output_directory):
        output_file = os.path.join(output_directory, f"{conversation_id}.html")
        template = self.load_template("conversation_template.html")
        conversation_json = json.dumps(conversation, indent=4)
        html_content = template.replace("<!-- insert conversations here -->", conversation_json)
        with open(output_file, "w") as file:
            file.write(html_content)
        print(f"Exported conversation {conversation_id} as HTML to {output_file}")

    def export_conversation_as_json(self, conversation_id, conversation, output_directory):
        output_file = os.path.join(output_directory, f"{conversation_id}.json")
        with open(output_file, "w") as file:
            json.dump(conversation, file, indent=4)
        print(f"Exported conversation {conversation_id} as JSON to {output_file}")

    def export_conversation_plain_text(self, db_name, conversation_ids, output_directory=None):
        output_directory = output_directory or self.EXPORT_PATH

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        conversations = self.get_conversations_by_ids(cursor, conversation_ids)

        if conversations:
            for conversation in conversations:
                conversation_id = conversation["id"]
                self.export_conversation_as_plain_text(conversation_id, conversation, output_directory)
        else:
            print("No conversations found.")

        conn.close()

    def export_conversation_as_plain_text(self, conversation_id, conversation, output_directory):
        output_file = os.path.join(output_directory, f"{conversation_id}.txt")

        with open(output_file, "w") as file:
            file.write(f"Conversation ID: {conversation_id}\n")
            for key, value in conversation.items():
                file.write(f"{key}: {value}\n")

        print(f"Exported conversation {conversation_id} as plain text to {output_file}")

    def export_table_as_json(self, cursor, table_name):
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        column_names = [column[0] for column in cursor.description]
        json_data = []

        for row in rows:
            conversation = dict(zip(column_names, row))
            json_data.append(conversation)

        return json_data

    def export_database_as_json(self, db_name, output_directory=None):
        output_directory = output_directory or self.EXPORT_PATH

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

                print(f"Exported {table} table as JSON to: {output_file}")

        conn.close()

    # inspect
    ###########################################################################
    # Functions for inspecting data and JSON formats should be placed here.
    # Include functions like `inspect_data` and `inspect_json_data`.
    ###########################################################################

    def inspect_data(self, data_path=None):
        data_path = data_path or self.DATA_PATH

        if not os.path.exists(data_path):
            print(f"Error: Data directory not found: {data_path}")
            return

        self.traverse_files(data_path, self.inspect_json_data)

    def inspect_json_data(self, json_data, table_name=None):
        if not json_data:
            print("Warning: JSON data is empty.")
            return

        if not isinstance(json_data, list) or not all(isinstance(item, dict) for item in json_data):
            print("Warning: Invalid JSON data format. Expected a list of dictionaries.")
            return

        if table_name:
            print(f"Table Name: {table_name}")

        if json_data:
            print(f"Schema: {list(json_data[0].keys())}")
            print(f"Number of Records: {len(json_data)}")
            # ... (other inspection logic)

    # schema
    ###########################################################################
    # This section includes functions related to schema management and changes.
    # Functions like `create_schema_table`, `record_schema_change`,
    # `infer_id_field_name`, and others should be in this section.
    ###########################################################################

    def create_schema_table(self, cursor):
        create_table_query = f"CREATE TABLE IF NOT EXISTS {self.SCHEMA_TABLE} ("
        create_table_query += "change_id INTEGER PRIMARY KEY AUTOINCREMENT,"
        create_table_query += "table_name TEXT,"
        create_table_query += "old_column_names TEXT,"
        create_table_query += "new_column_names TEXT)"
        cursor.execute(create_table_query)

    def record_schema_change(self, cursor, table_name, old_column_names, new_column_names):
        # Insert schema change record into the schema_changes table
        cursor.execute(f"INSERT INTO {self.SCHEMA_CHANGES_TABLE} (table_name, old_column_names, new_column_names) VALUES (?, ?, ?)", (table_name, ",".join(old_column_names), ",".join(new_column_names)))

    def infer_id_field_name(self, cursor, table_name):
        select_query = f"SELECT new_column_name FROM {self.SCHEMA_TABLE} WHERE table_name = ?"
        cursor.execute(select_query, (table_name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        return "id"  # Default to "id" if no historical change is recorded

    def is_old_column_name(self, column_name, table_name):
        # Logic to check if the column name is in old format, e.g., "id" or "conversations_id"
        return column_name.lower() == "id" or f"{table_name}s_id" in column_name.lower()

    def build_new_column_name(self, old_column_name, table_name):
        # Logic to build the new column name from the old column name, considering pluralization
        # For example, you can remove "_id" and pluralize the table name
        new_column_name = old_column_name.replace(f"{table_name}s_id", "")
        new_column_name = new_column_name + "_id"
        return new_column_name

    def rename_columns_based_on_schema_changes(self, conn):
        cursor = conn.cursor()

        select_query = f"SELECT table_name, old_column_name, new_column_name FROM {self.SCHEMA_VERSION_TABLE}"
        cursor.execute(select_query)
        schema_changes = cursor.fetchall()

        for change in schema_changes:
            self.rename_column(conn, change[0], change[1], change[2])

        cursor.close()

    def rename_column(self, conn, table_name, old_column_name, new_column_name):
        cursor = conn.cursor()

        alter_query = f"ALTER TABLE {table_name} RENAME COLUMN {old_column_name} TO {new_column_name}"
        try:
            cursor.execute(alter_query)
            print(f"Renamed column '{old_column_name}' to '{new_column_name}' in table '{table_name}'")
        except Exception as e:
            print(f"Error renaming column: {e}")

        cursor.close()

    def calculate_file_hash(self, json_data, table_name):
        # Calculate a hash of the JSON data and table name (use a suitable hash function)
        hash_data = {
            "json_data": json_data,
            "table_name": table_name
        }
        return hashlib.md5(json.dumps(hash_data, sort_keys=True).encode()).hexdigest()

    def calculate_column_names_hash(self, json_data):
        # Calculate a hash of the column names (use a suitable hash function)
        column_names = sorted(json_data[0].keys()) if json_data else []
        return hashlib.md5("".join(column_names).encode()).hexdigest()

    def get_existing_table_name(self, cursor, column_names_hash):
        # Check if a table with the given hash exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?;", (column_names_hash,))
        result = cursor.fetchone()
        if result:
            return result[0]
        return None

    # run
    ###########################################################################
    # This section contains the `run` method, which is responsible for
    # executing the appropriate subcommand based on user input.
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
            if args.text:
                print("Action: Export conversations as plain text")
                self.export_conversations_as_text(args.db_name, args.path, args.prefix)
            elif args.html:
                print("Action: Export conversations as HTML")
                self.export_conversations_as_html(args.db_name, args.path, args.prefix)
            else:
                print("Action: Export entire database as JSON")
                self.export_database_as_json(args.db_name, args.path)
        elif args.subcommand == "print":
            print("Action: Print conversation")
            if args.prefix:
                self.print_conversation(args.db_name, args.prefix)
            else:
                print("Error: 'print' subcommand requires the 'prefix' argument.")
        elif args.subcommand == "inspect":
            print("Action: Inspect data files")
            self.inspect_data(args.path)
        else:
            self.parser.print_help()

# main
###############################################################################
# This is where the main execution of the script occurs using the
# `if __name__ == "__main__":` block. Create an instance of your class and run
# the tool using the `run` method.
###############################################################################

if __name__ == "__main__":
    tool = ChatGPTTool()
    tool.run()
