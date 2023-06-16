# ChatGPT Tool

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

- Testing
    - https://docs.python.org/3/library/doctest.html
    - https://docs.python.org/3/library/unittest.html
    - python3 -m unittest discover tests

## Usage

The ChatGPT Tool supports the following command-line arguments:

- `import` subcommand:
  - `-d, --db-name`: SQLite database name (default: `chatgpt.db`)
  - `-f, --data-files`: Data files to import (JSON format)

- `print` subcommand:
  - `-d, --db-name`: SQLite database name (default: `chatgpt.db`)

- `delete` subcommand:
  - `-d, --db-name`: SQLite database name (default: `chatgpt.db`)

To import data, use the `import` subcommand with optional arguments. To print the content of the tables, use the `print` subcommand. To delete the database file, use the `delete` subcommand.

## Dependencies

- Python 3.x
- sqlite3
- argparse
- gazpacho (for HTML parsing, optional)


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

Please refer to the code for further details and implementation.
