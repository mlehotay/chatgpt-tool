import unittest
import json
import os

class TestDataGenerationAndImport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_data_dir = "test_data"
        os.makedirs(cls.test_data_dir, exist_ok=True)

        cls.conversations_file = os.path.join(cls.test_data_dir, "conversations.json")
        cls.user_file = os.path.join(cls.test_data_dir, "user.json")
        cls.message_feedback_file = os.path.join(cls.test_data_dir, "message_feedback.json")
        cls.model_comparisons_file = os.path.join(cls.test_data_dir, "model_comparisons.json")
        cls.shared_conversations_file = os.path.join(cls.test_data_dir, "shared_conversations.json")

        cls.generate_test_data()

    @classmethod
    def tearDownClass(cls):
        os.rmdir(cls.test_data_dir)

    @classmethod
    def generate_test_data(cls):
        conversations_data = [generate_conversation() for _ in range(5)]
        user_data = [generate_user() for _ in range(10)]
        message_feedback_data = [generate_message_feedback() for _ in range(20)]
        model_comparison_data = [generate_model_comparison() for _ in range(10)]
        shared_conversations_data = [generate_shared_conversation() for _ in range(5)]

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

    def test_import_conversations(self):
        with open(self.conversations_file, 'r') as f:
            conversations_data = json.load(f)
        self.assertIsInstance(conversations_data, list)

    def test_import_user(self):
        with open(self.user_file, 'r') as f:
            user_data = json.load(f)
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

###############################################################################

    def generate_user():
        user = {
            "id": str(random.randint(1, 100)),
            "username": "user_" + str(random.randint(1, 100)),
            "email": f"user_{random.randint(1, 100)}@example.com",
            "create_time": (datetime.now() - timedelta(days=random.randint(1, 365))).timestamp()
        }
        return user

    def generate_message_feedback():
        feedback = {
            "id": str(random.randint(1, 100)),
            "message_id": str(random.randint(1, 100)),
            "feedback_type": random.choice(["positive", "negative", "neutral"]),
            "user_id": str(random.randint(1, 100)),
            "create_time": (datetime.now() - timedelta(days=random.randint(1, 30))).timestamp()
        }
        return feedback

    def generate_model_comparison():
        comparison = {
            "id": str(random.randint(1, 100)),
            "model_a": "model_" + str(random.randint(1, 5)),
            "model_b": "model_" + str(random.randint(6, 10)),
            "preferred_model": random.choice(["model_a", "model_b"]),
            "create_time": (datetime.now() - timedelta(days=random.randint(1, 7))).timestamp()
        }
        return comparison

    def generate_conversation(num_messages=5):
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

    def generate_shared_conversation():
        shared_conversation = {
            "id": str(random.randint(1, 100)),
            "conversation_id": str(random.randint(1, 100)),
            "shared_with": "user_" + str(random.randint(1, 100)),
            "share_time": (datetime.now() - timedelta(days=random.randint(1, 365))).timestamp()
        }
        return shared_conversation

    # Generate test data and write to JSON files
    def generate_test_data():
        conversations_data = [generate_conversation() for _ in range(5)]
        user_data = [generate_user() for _ in range(10)]
        message_feedback_data = [generate_message_feedback() for _ in range(20)]
        model_comparison_data = [generate_model_comparison() for _ in range(10)]
        shared_conversations_data = [generate_shared_conversation() for _ in range(5)]

        with open('conversations.json', 'w') as f:
            json.dump(conversations_data, f, indent=2)

        with open('user.json', 'w') as f:
            json.dump(user_data, f, indent=2)

        with open('message_feedback.json', 'w') as f:
            json.dump(message_feedback_data, f, indent=2)

        with open('model_comparisons.json', 'w') as f:
            json.dump(model_comparison_data, f, indent=2)

        with open('shared_conversations.json', 'w') as f:
            json.dump(shared_conversations_data, f, indent=2)

if __name__ == '__main__':
    unittest.main()
