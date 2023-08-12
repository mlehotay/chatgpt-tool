# ChatGPT Tool

ChatGPT Tool is a versatile command-line utility designed to simplify the import, management, and analysis of ChatGPT conversations. Whether you have conversations stored as JSON files or HTML exports, this tool empowers you to efficiently organize and access your data using an SQLite database.

## Key Features

### Effortless Data Import

ChatGPT Tool streamlines the data import process, allowing you to effortlessly bring in your ChatGPT conversations. Whether your data is in JSON format or extracted from HTML files, the tool automatically handles the import process.

### Dynamic Table Creation

The tool dynamically generates tables within the SQLite database based on filenames. This ensures that your data is organized efficiently, reducing the overhead of manual table creation.

### Seamless JSON-to-HTML Mapping

With a seamless mapping mechanism, you can easily associate HTML files with their corresponding JSON data. This mapping ensures accurate and consistent data insertion.

### Intelligent Duplicate Management

ChatGPT Tool takes care of duplicate data intelligently. It ensures that only new and unique entries are inserted into the database, preserving data integrity.

### Command-line Simplicity

Enjoy the convenience of a command-line interface that offers intuitive commands for data import, display, and more. Say goodbye to complex GUIs and access powerful features with ease.

### User-Friendly Help

The tool provides comprehensive help messages and usage information, making it accessible to users of all experience levels. Whether you're a beginner or an advanced user, you'll find the tool easy to navigate.

## Getting Started

To get started, follow these steps:

1. Install Python 3.x and required dependencies.
2. Clone or download the repository.
3. Run the tool using the command-line interface to import, display, and manage your data.

## Contributions Welcome

ChatGPT Tool is an open-source project, welcoming contributions from the community. If you have ideas to enhance its features or improve usability, feel free to contribute and be a part of its growth.

## Dependencies

- Python 3.x
- sqlite3
- argparse
- json
- os
- unittest (for testing)
- gazpacho (for HTML parsing, optional)

## Documentation

For detailed usage instructions, examples, and additional information, please refer to the code and the user guide available in the repository.

## License

This project is licensed under the [insert name here] License - see the [LICENSE](LICENSE) file for details.
