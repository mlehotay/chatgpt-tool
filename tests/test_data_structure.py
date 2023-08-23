import unittest
import json
import shutil
import os
import random
from datetime import datetime, timedelta
from .data_generator import DataGenerator


class TestDataGenerationAndImport(unittest.TestCase):

    # setUp & tearDown
    ###########################################################################

    @classmethod
    def setUpClass(cls):
        cls.test_data_dir = "test_data"
        os.makedirs(cls.test_data_dir, exist_ok=True)

        cls.conversations_file = os.path.join(cls.test_data_dir, "conversations.json")
        cls.user_file = os.path.join(cls.test_data_dir, "user.json")
        cls.message_feedback_file = os.path.join(cls.test_data_dir, "message_feedback.json")
        cls.model_comparisons_file = os.path.join(cls.test_data_dir, "model_comparisons.json")
        cls.shared_conversations_file = os.path.join(cls.test_data_dir, "shared_conversations.json")
        cls.chat_file = os.path.join(cls.test_data_dir, "chat.html")

        cls.generate_test_data()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_data_dir)

    @classmethod
    def generate_test_data(cls):
        conversations_data = [cls.generate_conversation() for _ in range(5)]
        user_data = [cls.generate_user() for _ in range(10)]
        message_feedback_data = [cls.generate_message_feedback() for _ in range(20)]
        model_comparison_data = [cls.generate_model_comparison() for _ in range(10)]
        shared_conversations_data = [cls.generate_shared_conversation() for _ in range(5)]
        chat_data = [cls.generate_chat() for _ in range(5)]

        with open(cls.conversations_file, 'w') as f:
            json.dump(conversations_data, f, indent=2)

        with open(cls.user_file, 'w') as f:
            json.dump(user_data, f, indent=2)

        with open(cls.message_feedback_file, 'w') as f:
            json.dump(message_feedback_data, f, indent=2)

        with open(cls.model_comparisons_file, 'w') as f:
            json.dump(model_comparison_data, f, indent=2)

        with open(cls.shared_conversations_file, 'w') as f:
            json.dump(shared_conversations_data, f, indent=2)

        with open(cls.chat_file, 'w') as f:
            # html.dump(chat_data, f, indent=2)
            pass

    # data type generators
    ###########################################################################

    @classmethod
    def generate_user(cls):
        user = {
            "id": DataGenerator.random_user_id(),
            "email": DataGenerator.random_email(),
            "chatgpt_plus_user": DataGenerator.random_boolean(),
            "phone_number": DataGenerator.random_phone()
        }
        return user

    @classmethod
    def generate_message_feedback(cls):
        feedback = {
            "id": str(random.randint(1, 100)),
            "message_id": str(random.randint(1, 100)),
            "feedback_type": random.choice(["positive", "negative", "neutral"]),
            "user_id": str(random.randint(1, 100)),
            "create_time": (datetime.now() - timedelta(days=random.randint(1, 30))).timestamp()
        }
        return feedback

    @classmethod
    def generate_model_comparison(cls):
        comparison = {
            "id": str(random.randint(1, 100)),
            "model_a": "model_" + str(random.randint(1, 5)),
            "model_b": "model_" + str(random.randint(6, 10)),
            "preferred_model": random.choice(["model_a", "model_b"]),
            "create_time": (datetime.now() - timedelta(days=random.randint(1, 7))).timestamp()
        }
        return comparison

    @classmethod
    def generate_conversation(cls, num_messages=5):
        conversation = {
            "title": f"Conversation {random.randint(1, 100)}",
            "create_time": (datetime.now() - timedelta(days=random.randint(1, 365))).timestamp(),
            "update_time": datetime.now().timestamp(),
            "mapping": {},
            "moderation_results": [],
            "current_node": "root",
            "plugin_ids": None,
            "conversation_id": str(random.randint(1, 100)),
            "conversation_template_id": None,
            "id": str(random.randint(1, 100))
        }

        for _ in range(num_messages):
            message_id = str(random.randint(1, 100))
            conversation["mapping"][message_id] = {
                "id": message_id,
                "message": {
                    "id": message_id,
                    "author": "user_" + str(random.randint(1, 100)),
                    "create_time": (datetime.now() - timedelta(days=random.randint(1, 30))).timestamp(),
                    "update_time": datetime.now().timestamp(),
                    "content": f"Message {message_id} content",
                    "status": "active",
                    "end_turn": False,
                    "weight": random.random(),
                    "metadata": {},
                    "recipient": None
                },
                "parent": None,
                "children": []
            }

        return conversation

    @classmethod
    def generate_shared_conversation(cls):
        shared_conversation = {
            "id": DataGenerator.random_uuid(),
            "conversation_id": DataGenerator.random_uuid(),
            "title": DataGenerator.random_title(),
            "is_anonymous": DataGenerator.random_boolean()
        }
        return shared_conversation

    @classmethod
    def generate_chat(cls):
        pass

    # test methods
    ###########################################################################

    def test_import_conversations(self):
        with open(self.conversations_file, 'r') as f:
            conversations_data = json.load(f)
        self.assertIsInstance(conversations_data, list)

    def test_import_user(self):
        with open(self.user_file, 'r') as f:
            user_data = json.load(f)
        print(f"user: {user_data}")
        self.assertIsInstance(user_data, list)

    def test_import_message_feedback(self):
        with open(self.message_feedback_file, 'r') as f:
            message_feedback_data = json.load(f)
        self.assertIsInstance(message_feedback_data, list)

    def test_import_model_comparisons(self):
        with open(self.model_comparisons_file, 'r') as f:
            model_comparison_data = json.load(f)
        self.assertIsInstance(model_comparison_data, list)

    def test_import_shared_conversations(self):
        with open(self.shared_conversations_file, 'r') as f:
            shared_conversations_data = json.load(f)
        self.assertIsInstance(shared_conversations_data, list)

    def test_import_chat(self):
        pass

if __name__ == '__main__':
    unittest.main()
