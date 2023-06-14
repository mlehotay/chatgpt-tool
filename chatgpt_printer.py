import sqlite3
import argparse
import shutil

"""
ChatGPT Printer

Features:
- Printing table content:
    - Print the content of tables in the SQLite database
    - Retrieve table names dynamically
    - Truncate long lines based on terminal width
    - Display table column names

To Do:
- Error handling:
    - Handle errors related to SQLite operations, etc
"""

class ChatGPTPrinter:
    def __init__(self, db_name):
        self.db_name = db_name

    def truncate_string(self, string, max_length):
        if len(string) <= max_length:
            return string
        return string[:max_length-3] + "..."

    def get_truncation_length(self):
        terminal_size = shutil.get_terminal_size(fallback=(80, 24))
        return terminal_size.columns - 3  # Subtract 3 to account for ellipsis

    def print_tables(self):
        conn = sqlite3.connect(self.db_name)
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

def main():
    parser = argparse.ArgumentParser(prog="ChatGPT Printer", description="Print conversations exported from ChatGPT")
    parser.add_argument("db_name", type=str, nargs="?", default="chatgpt.db",
                        help="SQLite database name")

    args = parser.parse_args()

    printer = ChatGPTPrinter(args.db_name)
    printer.print_tables()


if __name__ == "__main__":
    main()
