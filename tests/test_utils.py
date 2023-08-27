import unittest
import string
from .data_generator import DataGenerator

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
        last_word = sentence[-1]
        self.assertTrue(last_word[:-1] in DataGenerator.corpus)  # Remove the punctuation and check in the corpus
        self.assertTrue(last_word[-1] in string.punctuation)  # Check if the last character is punctuation

    def test_random_phrase(self):
        phrase = DataGenerator.random_phrase()
        for word in phrase:
            self.assertTrue(word in DataGenerator.corpus)

if __name__ == '__main__':
    unittest.main()
