import argparse
from chatgpt_importer import ChatGPTImporter
from chatgpt_printer import ChatGPTPrinter

"""
ChatGPT Tool

Features:
- Command-line interface:
    - Accept command-line arguments for importing or printing
    - Accept command-line arguments for the database name and data files to import
    - Make all command-line arguments optional
- Default behavior:
    - If no command-line arguments are provided, it tries to import data using the default settings
- Entry point:
    - Invokes importing or printing functionality based on the command-line arguments

To Do:
- Help text and usage information:
    - Provide a help message that explains the available command-line arguments and their usage
- Error handling:
    - Handle errors related to command-line arguments, SQLite operations, etc
"""

def main():
    parser = argparse.ArgumentParser(description="ChatGPT Tool")
    parser.add_argument("db_name", type=str, nargs="?", default="chatgpt.db", help="SQLite database name")
    parser.add_argument("data_files", type=str, nargs="*", default=None, help="Data files to import (JSON format)")
    parser.add_argument("-p", "--print-tables", action="store_true", help="Print the content of the tables")

    args = parser.parse_args()

    if args.print_tables:
        print("Action: Print tables")
        printer = ChatGPTPrinter(args.db_name)
        printer.print_tables()
    else:
        if args.data_files is None:
            print("Action: Import using default settings")
            default_data_directory = ChatGPTImporter.DEFAULT_DATA_DIRECTORY
            data_files = [
                os.path.join(default_data_directory, file)
                for file in os.listdir(default_data_directory)
                if file.endswith(".json")
            ]
        else:
            print("Action: Import")
            data_files = args.data_files

        importer = ChatGPTImporter(args.db_name, data_files)
        importer.import_data()

if __name__ == "__main__":
    main()
