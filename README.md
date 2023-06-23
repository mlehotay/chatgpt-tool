# ChatGPT Tool

ChatGPT Tool is a command-line utility for importing ChatGPT conversations exported as JSON and managing them in a SQLite database. It can also import conversations from HTML files exported from the ChatGPT website. It is written in Python 3 and uses the sqlite3 module for database interaction.

## Table of Contents

- [ChatGPT Tool](#chatgpt-tool)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Usage](#usage)
  - [Dependencies](#dependencies)
  - [To Do](#to-do)

## Usage

The ChatGPT Tool supports the following command-line arguments:

- `import` subcommand:
  - `-db, --database`: SQLite database name (default: `chatgpt.db`)
  - `-d, --directory`: Directory containing data files to import (JSON format) (default: `data`)
  - `-f, --data-files`: Data file to import (JSON format) (default: `conversations.json`)
  - `-v, --verbose`: Display verbose output

- `print` subcommand:
  - `-db, --database`: SQLite database name (default: `chatgpt.db`)
  - `-v, --verbose`: Display verbose output

- `delete` subcommand:
  - `-db, --database`: SQLite database name (default: `chatgpt.db`)
  - `-v, --verbose`: Display verbose output

- `info` subcommand:
  - `-db, --database`: SQLite database name (default: `chatgpt.db`)
  - `-v, --verbose`: Display verbose output

- `help` subcommand:
  - `-v, --verbose`: Display verbose output

- `test` subcommand:
  - `-u, --unit-tests`: Run unit tests
  - `-d, --doctests`: Run doctests
  - `-v, --verbose`: Display verbose output

    Notes:
        - Run test suites by invoking the `test` subcommand with the `-u` or `-d` options
        - To discover new doctests, run `python3 -m doctest -v chatgpt_tool.py`
        - New unit tests can be added to the `tests` directory

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
    - python3 -m doctest -v chatgpt_tool.py

## Dependencies

- Python 3.x
- sqlite3
- argparse
- json
- os
- sys
- unittest (for testing)
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
