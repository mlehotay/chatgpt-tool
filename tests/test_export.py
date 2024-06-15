import unittest
import os
import json
import sqlite3
from tempfile import TemporaryDirectory
from src.chatgpt_tool import ChatGPTTool  # Adjust the import based on your module structure

class TestChatGPTToolExport(unittest.TestCase):

    def setUp(self):
        self.test_dir = TemporaryDirectory()
        self.db_path = ":memory:"
        self.tool = ChatGPTTool(db_path=self.db_path)
        self.conn = sqlite3.connect(self.tool.db_path)
        self.setup_database()

    def tearDown(self):
        self.conn.close()
        self.test_dir.cleanup()

    def setup_database(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE conversations_v5 (
                id TEXT,
                title TEXT,
                create_time REAL,
                messages TEXT
            )
        ''')
        self.mock_conversation = {
            'id': '12345',
            'title': 'Test Conversation',
            'create_time': 1687066941.60843,
            'messages': json.dumps([
                {'role': 'user', 'content': 'Hello'},
                {'role': 'assistant', 'content': 'Hi there!'}
            ])
        }
        cursor.execute('''
            INSERT INTO conversations_v5 (id, title, create_time, messages)
            VALUES (?, ?, ?, ?)
        ''', (self.mock_conversation['id'], self.mock_conversation['title'],
              self.mock_conversation['create_time'], self.mock_conversation['messages']))
        self.conn.commit()

    def test_export_conversation_as_text(self):
        output_dir = self.test_dir.name
        self.tool.export_conversations(self.tool.db_path, output_dir, export_format='text', prefixes=['123'])

        output_file = os.path.join(output_dir, '12345.txt')
        self.assertTrue(os.path.exists(output_file))

        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("Conversation ID: 12345", content)
            self.assertIn("Title: Test Conversation", content)
            self.assertIn("user: Hello", content)
            self.assertIn("assistant: Hi there!", content)

    def test_export_conversation_as_json(self):
        output_dir = self.test_dir.name
        self.tool.export_conversations(self.tool.db_path, output_dir, export_format='json', prefixes=['123'])

        output_file = os.path.join(output_dir, '12345.json')
        self.assertTrue(os.path.exists(output_file))

        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data['id'], '12345')
            self.assertEqual(data['title'], 'Test Conversation')
            self.assertEqual(len(data['messages']), 2)
            self.assertEqual(data['messages'][0]['content'], 'Hello')

    def test_export_conversation_as_html(self):
        output_dir = self.test_dir.name
        self.tool.export_conversations(self.tool.db_path, output_dir, export_format='html', prefixes=['123'])

        output_file = os.path.join(output_dir, '12345.html')
        self.assertTrue(os.path.exists(output_file))

        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("<html><body><pre>", content)
            self.assertIn("Conversation ID: 12345", content)
            self.assertIn("Title: Test Conversation", content)
            self.assertIn("user: Hello", content)
            self.assertIn("assistant: Hi there!", content)
            self.assertIn("</pre></body></html>", content)

if __name__ == '__main__':
    unittest.main()
