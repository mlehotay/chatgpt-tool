# src/chatgpt_tool.py
import argparse
import ast
import hashlib
import json
import os
import shutil
import sqlite3
import string
import sys
import tempfile
import zipfile
from datetime import datetime

try:
    from gazpacho import Soup
    process_html = True
except ImportError:
    process_html = False

"""
ChatGPT Tool

ChatGPT Tool is a command-line utility for importing ChatGPT conversations from JSON and managing them in a SQLite database.

"""

class Conversation:
    DISPLAY_STYLES = {
        'default': {'divider': '', 'blank': True},
        'irc': {'divider': '--', 'blank': False},
        'full': {'divider': '-' * 79, 'blank': True},
        'raw': {'divider': None, 'blank': True}
    }

    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, table, id, create_time, title):
        self.table = table
        self.id = id
        self.create_time = create_time
        self.title = title

    def __repr__(self):
        formatted_create_time = datetime.fromtimestamp(self.create_time).strftime(self.TIME_FORMAT)
        return f"Conversation(id='{self.id}', create_time='{formatted_create_time}', title='{self.title}')"

    def __str__(self):
        return f"{self.title}"

    def __lt__(self, other):
        return self.create_time < other.create_time

class ChatGPTTool:
    DB_NAME = "chatgpt.db"
    DATA_PATH = "data"
    EXPORT_PATH = "export"
    SCHEMA_TABLE = "schema"
    CHAT_TABLE = "conversations"
    USER_TABLE = "user"

    TABLE_MAPPING = {
        "chat": CHAT_TABLE, # ConversationIdentifier
        "user": USER_TABLE,
        # "raw": OTHER_TABLE,
        # Add more mappings if needed
    }

    EXIT_SUCCESS = 0
    EXIT_ERROR = 1
    EXIT_USAGE_ERROR = 2

    # init
    ###########################################################################
    # This section contains the setup for the command-line interface (CLI) and
    # subcommands with their respective arguments and descriptions.
    ###########################################################################

    def __init__(self, db_path=None):
        """
        Initialize the ChatGPTTool with command-line arguments and database path.
        """
        self.verbose = False
        self.db_path = db_path or self.DB_NAME
        self.schema_cache = {}  # Initialize the cache dictionary
        self.args = None  # will be assigned after parsing

        # Create the top-level parser
        self.parser = argparse.ArgumentParser(prog="chatgpt_tool", description="ChatGPT Tool")
        self.parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode')
        self.parser.add_argument("-db", "--db-name", dest="db_name", default=self.db_path, help="Name of the SQLite database (default: chatgpt.db)")

        # Create subparsers
        subparsers = self.parser.add_subparsers(title="subcommands", dest="subcommand")

        # Subcommand: import
        import_parser = subparsers.add_parser("import", help="Import JSON data into the SQLite database")
        import_parser.add_argument("path", help="Filepath or directory for import")

        # Subcommand: show
        show_parser = subparsers.add_parser("show", help="Display database tables")

        # Subcommand: info
        info_parser = subparsers.add_parser("info", help="Display database information")

        # Subcommand: export
        export_parser = subparsers.add_parser("export", help="Export conversations from the SQLite database")
        export_parser.add_argument("prefixes", nargs="*", help="Export conversations with IDs starting with the specified prefix")
        export_parser.add_argument("--format", choices=['text', 'html', 'json'], default='text', help="Choose an output format")

        # Subcommand: print
        print_parser = subparsers.add_parser('print', help='Print data from the database')
        print_parser.add_argument('prefixes', nargs='+', type=str, help='Prefixes of conversation IDs or user IDs to print')
        print_parser.add_argument("--style", choices=Conversation.DISPLAY_STYLES.keys(), default='default', help="Choose a display style (default, irc, full, raw)")

        # Subcommand: inspect
        inspect_parser = subparsers.add_parser("inspect", help="Inspect data files")
        inspect_parser.add_argument("path", nargs="?", default=self.DATA_PATH, help="Data directory for inspection")

        self.args = self.parser.parse_args()
        self.verbose = self.args.verbose
        self.db_path = self.args.db_name  # Update self.db_path with parsed value


    # import
    ###########################################################################
    # Place functions related to importing data into the database here. This
    # includes functions like `import_data`, `traverse_files`, `process_file`,
    # and other related helper functions.
    ###########################################################################

    def import_data(self, db_name, data_path):
        """
        Import data from JSON files into the SQLite database.
        """
        with sqlite3.connect(db_name) as conn:
            self.create_schema_table(conn.cursor())  # Create schema table
            self.traverse_files(data_path, self.import_json_data_to_sqlite, conn)

    def traverse_files(self, path, process_function, *args):
        """
        Traverse files in the specified directory and process them.
        """
        if os.path.isdir(path):
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    self.traverse_files(file_path, process_function, *args)
        elif path.endswith(".zip"):
            if self.verbose:
                print(f"Reading archive '{path}'")
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(path, "r") as zip_file:
                    for name in zip_file.namelist():
                        extracted_file_path = zip_file.extract(name, path=temp_dir)
                        self.traverse_files(extracted_file_path, process_function, *args)
        else:
            self.process_file(path, process_function, *args)

    def process_file(self, path, process_function, *args):
        """
        Process individual files based on their extension.
        """
        _, file_extension = os.path.splitext(path)

        if self.verbose:
            print(f"Reading file '{path}'")

        if os.path.getsize(path) == 0:
            print(f"Warning: Skipping empty file '{path}'")
        elif file_extension.lower() == ".json":
            with open(path) as file:
                json_data = json.load(file)
                process_function(*args, json_data, path)
        elif file_extension.lower() == ".html":
            with open(path) as file:
                html_content = file.read()
                json_data = self.extract_json_from_html(html_content)
                if json_data:
                    process_function(*args, json_data, path)
                else:
                    print("Warning: No JSON data found in the HTML file.")
        else:
            print(f"Warning: Unexpected file format '{path}'")

    def get_table_name(self, file_path):
        """
        Generate a valid SQLite table name based on the file path.
        """
        base_filename = os.path.basename(file_path)
        suggested_name = os.path.splitext(base_filename)[0]

        # Generate a valid sqlite table name
        valid_chars = set(string.ascii_letters + string.digits + "_")
        table_name = ''.join(c if c in valid_chars else "_" for c in suggested_name)
        table_name = table_name.strip("_")

        # Use the mapping if available, or the generated name
        return self.TABLE_MAPPING.get(table_name, table_name)

    def get_versioned_table_name(self, cursor, table_name, column_names):
        """
        Get a versioned table name if there are schema changes.
        """
        versioned_table_name = table_name
        version = 1
        hash_value = self.calculate_column_names_hash(column_names)

        while self.table_exists(cursor, versioned_table_name):
            if versioned_table_name in self.schema_cache and self.schema_cache[versioned_table_name] == hash_value:
                break
            hash2 = self.query_single_value("schema", "table_name", versioned_table_name, "hash_value")
            if hash_value == hash2:
                self.schema_cache[versioned_table_name] = hash_value
                break
            version += 1
            versioned_table_name = f"{table_name}_v{version}"

        return versioned_table_name, hash_value

    # https://docs.python.org/3/library/json.html
    # https://docs.python.org/3/library/json.html#module-json.tool

    # class json.JSONDecoder(*, object_hook=None, parse_float=None, parse_int=None, parse_constant=None, strict=True, object_pairs_hook=None)

    # If strict is false (True is the default), then control characters will be
    # allowed inside strings. Control characters in this context are those with
    # character codes in the 0–31 range, including '\t' (tab), '\n', '\r' and
    # '\0'.

    # raw_decode(s)

    # Decode a JSON document from s (a str beginning with a JSON document) and
    # return a 2-tuple of the Python representation and the index in s where the
    # document ended.

    # This can be used to decode a JSON document from a string that may have
    # extraneous data at the end.

    def extract_json_from_html(self, html_content):
        """
        Extract JSON data from HTML content if present.
        """
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
                except (json.JSONDecodeError, ValueError, IndexError) as e:
                    print("Warning: Unable to extract JSON objects from jsonData variable.")
                    print("Error:", e)
                    print(self.truncate_string(json_string, self.get_truncation_length()))
                    return None

        if json_data is not None:
            return json_data

        print("Warning: No <script> tag containing jsonData variable found.")
        return []

    def extract_json_from_html_re(self, html_content):
        # Use regular expression to find all <script> tags
        script_tags = re.findall(r'<script[^>]*>(.*?)</script>', html_content, re.DOTALL)

        # List to store extracted JSON data
        json_data_list = []

        # Search for <script> tags containing jsonData variable assignment
        for script_tag in script_tags:
            # Use regular expressions to extract JSON content
            json_matches = re.findall(r'jsonData\s*=\s*\[.*?\];', script_tag, re.DOTALL)
            for json_match in json_matches:
                try:
                    # Extract JSON-like content
                    json_string = json_match.split('=')[1].strip()
                    # Clean the content by removing JavaScript code
                    json_string = re.sub(r'(function[^}]+})', '', json_string)
                    # Attempt to parse the cleaned JSON-like content
                    json_data = ast.literal_eval(json_string)
                    json_data_list.append(json_data)
                except (ValueError, SyntaxError) as e:
                    print("Warning: Unable to extract JSON objects from HTML file.")
                    print("Error:", e)
                    print("Problematic Content:")
                    print(json_match)  # Print the problematic content

        if json_data_list:
            return json_data_list

        print("Warning: No <script> tag containing jsonData variable found.")
        return []

    def import_json_data_to_sqlite(self, conn, json_data, path):
        """
        Import JSON data into SQLite database.
        """
        if not json_data:
            if self.verbose:
                print(f"Skipping import for file: {path} (empty JSON data)")
            return
        elif not isinstance(json_data, list):
            json_data = [json_data]  # Convert single object to a list with a single element

        cursor = conn.cursor()
        table_name = self.get_table_name(path)

        for json_object in json_data:
            self.import_single_json_object(cursor, table_name, json_object)

        conn.commit()  # Commit the transaction
        cursor.close()  # Close the cursor

    def import_single_json_object(self, cursor, table_name, json_object):
        """
        Import a single JSON object into the SQLite database.
        """
        id_field_name, column_names = self.get_id_and_column_names(json_object)
        try:
            cursor.execute("BEGIN")
            table_name, hash_value = self.get_versioned_table_name(cursor, table_name, column_names)
            # Create the table if necessary
            if not self.table_exists(cursor, table_name):
                self.create_table(cursor, table_name, id_field_name, column_names)
                self.record_schema_change(cursor, hash_value, table_name, column_names)
            # Insert data into the table
            self.insert_data_single(cursor, table_name, json_object)
            cursor.execute("COMMIT")
        except Exception as e:
            cursor.execute("ROLLBACK")
            print(f"Error importing data: {e}")

    def get_id_and_column_names(self, json_data):
        if isinstance(json_data, list):
            first_object = json_data[0] if json_data else {}
        else:
            first_object = json_data

        id_field_name = next((key for key in first_object.keys() if key.lower() == "id"), None)
        column_names = list(first_object.keys())
        return id_field_name, column_names

    def create_table(self, cursor, table_name, id_field_name, column_names):
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ("

        if id_field_name:
            create_table_query += f"{id_field_name} TEXT PRIMARY KEY,"

        for column_name in column_names:
            if not id_field_name or id_field_name and id_field_name.lower() != column_name.lower():
                create_table_query += f"{column_name} TEXT,"

        if not id_field_name:
            # Define a compound primary key if there's no id field
            create_table_query += f"PRIMARY KEY ({','.join(column_names)})"

        create_table_query = create_table_query.rstrip(',')
        create_table_query += ")"

        if self.verbose:
            print(f"Creating table '{table_name}': {id_field_name}, {column_names}")
        cursor.execute(create_table_query)

    def insert_data_list(self, cursor, table_name, json_data_list):
        for item in json_data_list:
            if item:
                values = self.convert_values(item)
                self.insert_data(cursor, table_name, item.keys(), values)

    def insert_data_single(self, cursor, table_name, json_data):
        values = self.convert_values(json_data)
        self.insert_data(cursor, table_name, json_data.keys(), values)

    def insert_data(self, cursor, table_name, column_names, values):
        insert_query = f"INSERT OR IGNORE INTO {table_name} ({','.join(column_names)}) VALUES ({','.join(['?'] * len(values))})"
        cursor.execute(insert_query, values)

    def convert_values(self, json_data):
        converted_values = []
        for key, value in json_data.items():
            # value_type = type(value).__name__
            # print(f"Value for key '{key}' has type: {value_type}")
            if isinstance(value, (str, int, float, bool)):
                converted_values.append(value)
            elif isinstance(value, datetime):
                converted_values.append(value.strftime('%Y-%m-%d %H:%M:%S'))
            else:
                # Handle other data types here, or convert them to strings
                converted_values.append(str(value))
        return converted_values

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
            column_names = self.get_column_names(cursor, table)
            table_stats.append((table, column_names, self.get_table_count(cursor, table)))

        # Display the statistics
        print("Database Information:")
        print(f"Database Name: {db_name}")
        print(f"Number of Tables: {len(tables)}")
        print()

        print("Table Statistics:")
        for table, columns, count in table_stats:
            print(f"Table Name: {table}")
            print(f"Column Names: {', '.join(columns)}")
            print(f"Number of Rows: {count}")
            print()

        # print("Table Schemas:")
        # self.print_table_schemas(conn, print_types=True)

        # Close the database connection
        conn.close()

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

    def get_table_names(self, cursor, filter_prefix=None):
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        if filter_prefix:
            query += f" AND name LIKE '{filter_prefix}%'"
        cursor.execute(query)
        return [row[0] for row in cursor.fetchall()]

    def get_column_names(self, cursor, table_name):
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns_info = cursor.fetchall()
        return [column_info[1] for column_info in columns_info]

    def get_table_count(self, cursor, table_name):
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        return cursor.fetchone()[0]

    def table_exists(self, cursor, table_name):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        existing_table = cursor.fetchone()
        return existing_table is not None

    def query_table(self, table_name, condition_field=None, condition_value=None, fetch_one=False):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if condition_field and condition_value:
                query = f"SELECT * FROM {table_name} WHERE {condition_field} = ?"
                cursor.execute(query, (condition_value,))
            else:
                query = f"SELECT * FROM {table_name}"
                cursor.execute(query)

            if fetch_one:
                row = cursor.fetchone()
                if row:
                    column_names = [column[0] for column in cursor.description]
                    result = dict(zip(column_names, row))
                else:
                    result = None
            else:
                rows = cursor.fetchall()
                column_names = [column[0] for column in cursor.description]
                result = [dict(zip(column_names, row)) for row in rows]

        except sqlite3.Error as e:
            print(f"Error querying table '{table_name}': {e}")
            result = None
            # Raise a custom exception or re-raise the exception here if needed
        finally:
            conn.close()

        return result

    def query_single_value(self, table_name, condition_field, condition_value, value_field):
        result = self.query_table(table_name, condition_field, condition_value, fetch_one=True)
        if result:
            return result.get(value_field, None)
        else:
            return None

    def check_row_in_table(self, table_name, condition_field, condition_value):
        result = self.query_table(table_name, condition_field, condition_value, fetch_one=True)
        return result is not None

    # schema
    ###########################################################################
    # This section includes functions related to schema management and changes.
    # Functions like `create_schema_table`, `record_schema_change`,
    # `infer_id_field_name`, and others should be in this section.
    ###########################################################################

    def create_schema_table(self, cursor):
        create_table_query = f"CREATE TABLE IF NOT EXISTS {self.SCHEMA_TABLE} ("
        create_table_query += "hash_value TEXT,"
        create_table_query += "table_name TEXT,"
        create_table_query += "column_names TEXT)"
        cursor.execute(create_table_query)

    def record_schema_change(self, cursor, hash_value, table_name, column_names):
        cursor.execute(f"INSERT OR IGNORE INTO {self.SCHEMA_TABLE} (hash_value, table_name, column_names) VALUES (?, ?, ?)", (hash_value, table_name, ",".join(column_names)))

    def calculate_column_names_hash(self, column_names):
        # Calculate a hash of the column names
        column_names = sorted(column_names) if column_names else []
        return hashlib.md5("".join(column_names).encode()).hexdigest()

    def get_schema_by_hash_value(self, hash_value):
        result = self.query_table("schema", "hash_value", hash_value)

        if result:
            schema = {
                "table_name": result[0]["table_name"],
                "column_names": result[0]["column_names"].split(","),
                "hash_value": result[0]["hash_value"]
            }
        else:
            schema = None

        return schema

    def get_existing_table_name(self, cursor, column_names_hash):
        # Check if a table with the given hash exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?;", (column_names_hash,))
        result = cursor.fetchone()
        if result:
            return result[0]
        return None

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

    # print
    ###########################################################################
    # Functions that handle printing and displaying information from the
    # database or conversations belong in this section. Include functions like
    # `print_tables`, `print_single_conversation`, and others.
    ###########################################################################

    def print_tables(self, db_name, file_handle=sys.stdout):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        truncation_length = self.get_truncation_length()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            print(f"Table: {table_name}", file=file_handle)
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            print(self.truncate_string(str(column_names), truncation_length), file=file_handle)
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            for row in rows:
                print(self.truncate_string(str(row), truncation_length), file=file_handle)
            print(file_handle)

        conn.close()

    def truncate_string(self, string, max_length):
        if len(string) <= max_length:
            return string
        return string[:max_length-3] + "..."

    def get_truncation_length(self):
        terminal_size = shutil.get_terminal_size(fallback=(80, 24))
        return terminal_size.columns - 3  # Subtract 3 to account for ellipsis

    def print_conversations(self, db_name, prefixes, style, file_handle=sys.stdout):
        """
        Prints conversations from the SQLite database filtered by prefixes and style.
        """
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        all_conversations = self.get_matching_conversations(cursor, prefixes)

        divider = Conversation.DISPLAY_STYLES.get(style, {}).get('divider', '')

        if all_conversations:
            for i, conversation in enumerate(all_conversations):
                self.print_single_conversation(cursor, conversation, style, file_handle)
                if i < len(all_conversations) - 1 and divider:
                    print(divider, file=file_handle)
        else:
            print(f"No conversations found with prefixes: {', '.join(prefixes)}", file=file_handle)

        conn.close()

    def get_matching_conversations(self, cursor, prefixes=None):
        """
        Retrieves conversation objects matching the given prefixes, removes duplicates, and sorts them by create_time.
        """
        # Ensure prefixes is a list
        if prefixes is None:
            prefixes = []

        tables = self.get_table_names(cursor, filter_prefix=self.CHAT_TABLE)
        matching_conversations = []
        unique_ids = set()

        if prefixes:
            for prefix in prefixes:
                for table in tables:
                    cursor.execute(f"SELECT id, create_time, title FROM {table} WHERE id LIKE ?", (f"{prefix}%",))
                    for row in cursor.fetchall():
                        if row[0] not in unique_ids:
                            unique_ids.add(row[0])
                            matching_conversations.append(Conversation(table, row[0], float(row[1]), row[2]))
        else:
            for table in tables:
                cursor.execute(f"SELECT id, create_time, title FROM {table}")
                for row in cursor.fetchall():
                    if row[0] not in unique_ids:
                        unique_ids.add(row[0])
                        matching_conversations.append(Conversation(table, row[0], float(row[1]), row[2]))

        matching_conversations.sort(key=lambda conv: conv.create_time)  # Sort by create_time
        return matching_conversations

    def fetch_conversation(self, cursor, conversation):
        """
        Fetches a single conversation from the database.
        """
        cursor.execute(f"SELECT * FROM {conversation.table} WHERE id = ?", (conversation.id,))
        row = cursor.fetchone()
        if row:
            column_names = [column[0] for column in cursor.description]
            return dict(zip(column_names, row))
        return None


    def print_single_conversation(self, cursor, conversation, style, file_handle=None):
        """
        Prints a single conversation.
        """
        conversation_data = self.fetch_conversation(cursor, conversation)
        if conversation_data:
            self.print_header(conversation_data, style, file_handle)
            self.print_messages(conversation_data, style, file_handle)
        else:
            output = f"Conversation not found: {conversation.id} in {conversation.table}"
            if file_handle:
                file_handle.write(output + "\n")
            else:
                print(output)

    def print_header(self, conversation_data, style, file_handle=None):
        """
        Prints the header information of a conversation.
        """
        divider = Conversation.DISPLAY_STYLES[style]['divider']
        blank = Conversation.DISPLAY_STYLES[style]['blank']
        output = ""
        if style == 'raw':
            for key, value in conversation_data.items():
                if key != 'mapping':
                    output += f"{key}: {value}\n"
        else:
            output += f"Title: {conversation_data['title']}\n"
            output += f"ID: {conversation_data['id']}\n"
            if style != 'default':
                output += f"Create time: {datetime.fromtimestamp(float(conversation_data['create_time'])).strftime(Conversation.TIME_FORMAT)}\n"
                output += f"Update time: {datetime.fromtimestamp(float(conversation_data['update_time'])).strftime(Conversation.TIME_FORMAT)}\n"
            if style == 'full':
                output += f"Current node: {conversation_data['current_node']}\n"
                output += f"Moderation results: {conversation_data['moderation_results']}\n"
                output += f"Plugin IDs: {conversation_data['plugin_ids']}\n"
                if "conversation_id" in conversation_data:
                    output += f"Conversation ID: {conversation_data['conversation_id']}\n"
                if "conversation_template_id" in conversation_data:
                    output += f"Conversation Template ID: {conversation_data['conversation_template_id']}\n"
        if divider or blank:
            output += "\n"

        if file_handle:
            file_handle.write(output)
        else:
            print(output)

    def print_messages(self, conversation_data, style, file_handle=None):
        """
        Prints the messages of a conversation.
        """
        blank = Conversation.DISPLAY_STYLES[style]['blank']
        messages = self.get_conversation_messages(conversation_data)
        output = ""
        if style == 'raw':
            mapping = ast.literal_eval(conversation_data['mapping'])

        if messages:
            for message in messages:
                author = str(message['author'])
                text = message['text']
                if style == 'raw':
                    id = message['id']
                    node = mapping[id]
                    output += f"node: {node}\n"
                elif style == 'irc' or style == 'full':
                    timestamp = message['timestamp'] or 0
                    timestamp = datetime.fromtimestamp(float(timestamp)).strftime(Conversation.TIME_FORMAT)
                    output += f"{timestamp} <{author}> {text}\n"
                else:  # default style
                    if author == "system":
                        continue
                    elif author == "assistant":
                        author = "ChatGPT"
                    output += f"{author}: {text}\n"
                if blank:
                    output += "\n"

        if file_handle:
            file_handle.write(output)
        else:
            print(output)

    def get_conversation_messages(self, conversation_data):
        """
        Retrieves the messages from a conversation.
        """
        if 'mapping' not in conversation_data or not conversation_data['mapping']:
            print(f"Warning: 'mapping' field is missing or empty in conversation ID: {conversation_data['id']}")
            return []

        try:
            # mapping = json.loads(conversation['mapping'])
            mapping = ast.literal_eval(conversation_data['mapping'])
        except json.JSONDecodeError as e:
            print(f"Error decoding 'mapping' field for conversation ID: {conversation_data['id']}")
            print(f"JSON Decode Error: {e}")
            print(f"Mapping string: {conversation_data['mapping']}")
            return []

        messages = []
        current_node = conversation_data['current_node']
        while current_node is not None:
            node = mapping.get(current_node)
            if node and "message" in node and node["message"]:
                message = node["message"]
                if "author" in message and "content" in message:
                    author = message["author"]["role"]
                    timestamp = message.get("create_time", 0)
                    content = message["content"]
                    if "content_type" in content and content["content_type"] == "text" and "parts" in content:
                        text = content["parts"][0]
                        messages.append({"id": current_node, "author": author, "timestamp": timestamp, "text": text})
            current_node = node.get("parent")

        return messages[::-1]

    # export
    ###########################################################################
    # Functions related to exporting conversations and data should be grouped
    # here. Functions like `export_conversations`, `export_conversation`,
    # `export_conversation_plain_text`, and others fit in this section.
    ###########################################################################

    def export_conversations(self, db_name, prefixes=None, export_format="text"):
        """
        Export conversations from the SQLite database based on specified prefixes and export format.
        """
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        all_conversations = self.get_matching_conversations(cursor, prefixes)

        print(f"Prefixes: {prefixes}")
        print(f"Total conversations to export: {len(all_conversations)}")

        if not os.path.exists(self.EXPORT_PATH):
            os.makedirs(self.EXPORT_PATH)

        if export_format == "json":
            self.export_conversations_as_json(cursor, all_conversations)
        elif export_format == "html":
            self.export_conversations_as_html(cursor, all_conversations)
        elif export_format == "text":
            self.export_conversations_as_plain_text(cursor, all_conversations)
        else:
            print(f"Unknown export format: {export_format}")

        conn.close()

    def export_conversations_as_json(self, cursor, all_conversations):
        for conversation in all_conversations:
            output_file = os.path.join(self.EXPORT_PATH, f"{conversation.id}.json")
            if self.verbose:
                print(f"Exporting {conversation} to {output_file}")
            with open(output_file, 'w', encoding='utf-8') as file_handle:
                self.print_single_conversation(cursor, conversation, 'json', file_handle)

    def export_conversations_as_html(self, cursor, all_conversations):
        """
        Exports the given conversations to separate HTML files.
        """
        for conversation in all_conversations:
            self.export_single_conversation_as_html(cursor, conversation)

    def export_single_conversation_as_html(self, cursor, conversation):
        """
        Exports a single conversation to an HTML file.
        """

        # Read template HTML, styles, & script
        with open('templates/chat.html', 'r') as file:
            html_template = file.read()
        with open('assets/styles.css', 'r') as file:
            styles = file.read()
        with open('assets/script.js', 'r') as file:
            script = file.read()

        # Prepare the conversation data
        full_conv = self.fetch_conversation(cursor, conversation)
        if full_conv:
            conv_dict = {
                "title": conversation.title,
                "current_node": full_conv["current_node"],
                "mapping": ast.literal_eval(full_conv["mapping"])  # Use ast.literal_eval for safety
            }
            conversations_data = [conv_dict]

            # Inject title, JSON data, styles, and script into the template
            html_content = html_template.replace('<!-- insert title here -->', conversation.title)
            html_content = html_content.replace('<!-- insert styles.css here -->', styles)
            html_content = html_content.replace('<!-- insert [json] here -->', json.dumps(conversations_data))
            html_content = html_content.replace('<!-- insert script.js here -->', script)

            # Write the final HTML to a file
            file_name = os.path.join(self.EXPORT_PATH, f'{conversation.id}.html')
            with open(file_name, 'w') as file:
                file.write(html_content)

            print(f'HTML file for conversation "{conversation.id}" generated successfully.')

    def export_conversations_as_plain_text(self, cursor, all_conversations):
        for conversation in all_conversations:
            output_file = os.path.join(self.EXPORT_PATH, f"{conversation.id}.txt")
            if self.verbose:
                print(f"Exporting {conversation} to {output_file}")
            with open(output_file, 'w', encoding='utf-8') as file_handle:
                self.print_single_conversation(cursor, conversation, 'full', file_handle)

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

    # run
    ###########################################################################
    # This section contains the `run` method, which is responsible for
    # executing the appropriate subcommand based on user input.
    ###########################################################################

    def run(self):
        """
        Execute the appropriate subcommand based on user input.
        """
        if self.verbose:
            print(f"Subcommand: {self.args.subcommand}")
            print("Parsed Arguments:")
            for arg, value in vars(self.args).items():
                print(f"  {arg}: {value}")

        exit_code = self.EXIT_SUCCESS  # Initialize with success

        if self.args.subcommand == "import":
            exit_code = self.import_data(self.args.db_name, self.args.path)
        elif self.args.subcommand == "show":
            exit_code = self.print_tables(self.args.db_name)
        elif self.args.subcommand == "info":
            exit_code = self.info(self.args.db_name)
        elif self.args.subcommand == "export":
            exit_code = self.export_conversations(self.args.db_name, self.args.prefixes, self.args.format)
        elif self.args.subcommand == "print":
            exit_code = self.print_conversations(self.args.db_name, self.args.prefixes, self.args.style)
        elif self.args.subcommand == "inspect":
            exit_code = self.inspect_data(self.args.path)

        # to do:
        #     - add text search for conversations and messages
        #     - filename globbing for CLI arguments

        else:
            self.parser.print_help()
            exit_code = self.EXIT_USAGE_ERROR  # Set exit code to indicate a usage error

        if self.verbose:
            print("Exit Code:", exit_code)

        sys.exit(exit_code)  # Exit the script with the determined exit code

# main
###############################################################################
# This is where the main execution of the script occurs using the
# `if __name__ == "__main__":` block. Create an instance of your class and run
# the tool using the `run` method.
###############################################################################

if __name__ == "__main__":
    tool = ChatGPTTool()
    tool.run()
