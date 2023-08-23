import unittest
import random
import string
from datetime import datetime, timedelta

class DataGenerator:

    corpus = """Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua
    Ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat
    Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur
    Excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum"""

    @staticmethod
    def random_email():
        #random_username = ''.join(random.choice(string.ascii_letters) for _ in range(8))
        #random_domain = ''.join(random.choice(string.ascii_lowercase) for _ in range(5))
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
        words = random.sample(lorem_ipsum_words, num_words)
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
        self.assertTrue(phrase in lorem_ipsum_words)

if __name__ == '__main__':
    unittest.main()
