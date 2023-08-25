import unittest
import json
import shutil
import os
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
        conversations_data = [DataGenerator.generate_conversation() for _ in range(5)]
        user_data = [DataGenerator.generate_user() for _ in range(10)]
        message_feedback_data = [DataGenerator.generate_message_feedback() for _ in range(20)]
        model_comparison_data = [DataGenerator.generate_model_comparison() for _ in range(10)]
        shared_conversations_data = [DataGenerator.generate_shared_conversation() for _ in range(5)]
        chat_data = [DataGenerator.generate_chat() for _ in range(5)]

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

    # test methods
    ###########################################################################

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

    def test_import_chat(self):
        pass

if __name__ == '__main__':
    unittest.main()
