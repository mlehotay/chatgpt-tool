import unittest
import random
import string
from datetime import datetime, timedelta

class DataGenerator:

    # Data type generators
    ###########################################################################

    @classmethod
    def generate_user(cls, hashcode=None):
        if hashcode is None or hashcode == 'a1dd9e6ff9fb7b63ed62cde37a101145':
            user = {
                "id": cls.random_user_id(),
                "email": cls.random_email(),
                "chatgpt_plus_user": cls.random_boolean(),
                "phone_number": cls.random_phone()
            }
        else:
            schema = cls.get_schema_by_hashcode(hashcode)
            if schema:
                user = {}
                for column_name in schema["column_names"]:
                    user[column_name] = cls.random_value_for_column(column_name)
            else:
                raise ValueError("Invalid schema hashcode")
        return user

    @classmethod
    def random_value_for_column(cls, column_name):
        if column_name == "id":
            return cls.random_user_id()
        elif column_name == "email":
            return cls.random_email()
        elif column_name == "chatgpt_plus_user":
            return cls.random_boolean()
        elif column_name == "phone_number":
            return cls.random_phone()
        else:
            return cls.random_string()  # Add handling for other fields

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
            "id": cls.random_uuid(),
            "conversation_id": cls.random_uuid(),
            "title": cls.random_title(),
            "is_anonymous": cls.random_boolean()
        }
        return shared_conversation

    @classmethod
    def generate_chat(cls):
        pass

    # Random value generators
    ###########################################################################

    corpus = """Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua
    Ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat
    Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur
    Excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum"""

    @staticmethod
    def random_email():
        username = DataGenerator.random_string()
        domain = random.choice(["gmail.com", "example.com", "yahoo.com"])
        return f"{username}@{domain}"

    @staticmethod
    def random_uuid():
        return f"{DataGenerator.random_hex(8)}-{DataGenerator.random_hex(4)}-{DataGenerator.random_hex(4)}-{DataGenerator.random_hex(4)}-{DataGenerator.random_hex(12)}"

    @staticmethod
    def random_string(length=10):
        return ''.join(random.choice(string.ascii_letters) for _ in range(length))

    @staticmethod
    def random_title():
        words = [DataGenerator.random_string().capitalize() for _ in range(random.randint(2, 5))]
        return ''.join(words)

    @staticmethod
    def random_sentence():
        phrases = [DataGenerator.random_phrase() for _ in range(random.randint(2, 5))]
        sentence = ' '.join(phrases).capitalize()
        sentence += random.choice(['.', '!', '?'])
        return sentence

    @staticmethod
    def random_phrase():
        num_words = random.randint(3, 10)
        words = random.sample(DataGenerator.corpus.split(), num_words)
        return ' '.join(words)

    @staticmethod
    def random_hex(length):
        return ''.join(random.choice(string.hexdigits) for _ in range(length))

    @staticmethod
    def random_boolean():
        return random.choice([True, False])

    @staticmethod
    def random_phone():
        country_code = "+1"  # Replace with the appropriate country code
        number = "".join(str(random.randint(0, 9)) for _ in range(10))
        return country_code + number

    @staticmethod
    def random_user_id():
        characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        random_part = ''.join(random.choice(characters) for _ in range(24))
        return f"user-{random_part}"

# Unit tests
###############################################################################

class TestDataGenerator(unittest.TestCase):
    def test_random_email(self):
        email = DataGenerator.random_email()
        self.assertTrue('@' in email)

    def test_random_uuid(self):
        uuid = DataGenerator.random_uuid()
        self.assertEqual(len(uuid), 36)

    def test_random_title(self):
        title = DataGenerator.random_title()
        self.assertTrue(title.isalpha())

    def test_random_sentence(self):
        sentence = DataGenerator.random_sentence()
        self.assertTrue(sentence.isalpha())

    def test_random_phrase(self):
        phrase = DataGenerator.random_phrase()
        self.assertTrue(phrase in DataGenerator.corpus)

if __name__ == '__main__':
    unittest.main()
