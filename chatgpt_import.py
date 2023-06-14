import json
import sqlite3

DB_NAME = 'chatgpt.db'
data_files = {
    'users': 'user.json',
    'shared_conversations': 'shared_conversations.json',
    'conversations': 'conversations.json',
    'message_feedback': 'message_feedback.json',
    'model_comparisons': 'model_comparisons.json'
}

conn = sqlite3.connect(DB_NAME)
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

            # Create a table for the current data
            create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            for column_name in column_names:
                create_table_query += f"{column_name} TEXT,"
            create_table_query = create_table_query.rstrip(',')
            create_table_query += ")"
            cursor.execute(create_table_query)

            # Insert data into the table
            for item in json_data:
                values = tuple(str(value) for value in item.values())
                insert_query = f"INSERT INTO {table_name} VALUES ({','.join(['?'] * len(values))})"
                cursor.execute(insert_query, values)
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
        values = tuple(str(value) for value in json_data.values())
        insert_query = f"INSERT INTO {table_name} VALUES ({','.join(['?'] * len(values))})"
        cursor.execute(insert_query, values)

conn.commit()
conn.close()
