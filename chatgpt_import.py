import json
import sqlite3

"""
This is a ChatGPT export importer.
It imports conversations that have been exported from ChatGPT.
"""

DB_NAME = 'chatgpt.db'
USER_FILE = 'user.json'

# Read the JSON data from the file
with open(USER_FILE) as file:
    json_data =  json.load(file)

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Create a table for the JSON data
create_table_query = "CREATE TABLE IF NOT EXISTS users (id TEXT, email TEXT, chatgpt_plus_user TEXT, phone_number TEXT)"
cursor.execute(create_table_query)

# Extract the values from the JSON object
values = tuple(json_data.values())

# Insert data into the table
insert_query = "INSERT INTO users VALUES (?, ?, ?, ?)"
cursor.execute(insert_query, values)

conn.commit()
conn.close()
