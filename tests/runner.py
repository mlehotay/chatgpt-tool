import unittest
import importlib
import os
import string

from unittest import TestLoader, TextTestRunner, TestSuite

def list_test_functions(test_directory):
    test_functions = []
    for file in os.listdir(test_directory):
        if file.startswith("test_") and file.endswith(".py"):
            module_name = f"tests.{os.path.splitext(file)[0]}"
            module = importlib.import_module(module_name)
            test_functions.extend(get_test_methods(module))
    return test_functions

def get_test_methods(module):
    test_methods = []
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, type) and issubclass(attr, unittest.TestCase):
            test_methods.extend([getattr(attr, method) for method in dir(attr) if method.startswith("test_")])
    return test_methods

def print_test_result_summary(result):
    print("\nTest Result Summary:")
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Total Passed: {result.testsRun - len(result.errors) - len(result.failures)}")
    print(f"Total Failed: {len(result.errors) + len(result.failures)}")
    print(f"Total Skipped: {len(result.skipped)}")

def main():
    test_directory = os.path.dirname(os.path.abspath(__file__))

    test_functions = list_test_functions(test_directory)

    # Create a TestSuite containing all the test functions
    all_test_suite = TestSuite(unittest.defaultTestLoader.loadTestsFromName(func.__module__ + '.' + func.__name__) for func in test_functions)

    # Run the complete suite and get the result
    result = TextTestRunner(verbosity=2).run(all_test_suite)

    # Print the test result summary
    print_test_result_summary(result)

if __name__ == "__main__":
    main()
