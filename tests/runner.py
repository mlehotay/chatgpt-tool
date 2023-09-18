import datetime
import importlib
import os
import subprocess
import sys
import unittest
from unittest import TestLoader, TextTestRunner, TestSuite

def list_test_classes(test_directory):
    test_classes = []
    for file in os.listdir(test_directory):
        if file.startswith("test_") and file.endswith(".py"):
            module_name = f"tests.{os.path.splitext(file)[0]}"
            module = importlib.import_module(module_name)
            test_classes.extend(get_test_classes(module))
    return test_classes

def get_test_classes(module):
    test_classes = []
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, type) and issubclass(attr, unittest.TestCase):
            test_classes.append(attr)
    return test_classes

def get_git_version():
    version, branch, modified = ("unknown",) * 3
    try:
        version = subprocess.check_output(['git', 'rev-parse', '--short=7', 'HEAD']).decode().strip()[:7]
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()
        status = subprocess.check_output(['git', 'status', '--porcelain']).decode().strip()
        modified = "Yes" if status else "No"
    except:
        pass
    return version, branch, modified

def print_test_result_summary(result):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    version, branch, modified = get_git_version()

    summary = f"\nTest Result Summary"
    summary += f"\n-------------------"
    summary += f"\nDate: {timestamp}"
    summary += f"\nCommit: {version}"
    summary += f"\nBranch: {branch}"
    summary += f"\nModified: {modified}"
    summary += f"\n"
    summary += f"\nTests Passed: {result.testsRun - len(result.errors) - len(result.failures)}"
    summary += f"\nTests Failed: {len(result.errors) + len(result.failures)}"
    summary += f"\nTests Skipped: {len(result.skipped)}"
    summary += f"\nTotal Tests: {result.testsRun}"

    return summary

def main(output_file=None):
    test_directory = os.path.dirname(os.path.abspath(__file__))
    test_classes = list_test_classes(test_directory)

    # Create a TestSuite containing all the test classes
    all_test_suite = TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls) for cls in test_classes)

    if output_file is not None:
        # Redirect both stdout and stderr to the output file
        sys.stdout = sys.stderr = output_file

    # Run the complete suite and print the results
    result = TextTestRunner(verbosity=2).run(all_test_suite)
    print(print_test_result_summary(result))

    # Restore the original stdout and stderr
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

if __name__ == "__main__":
    # To write output to a file, pass the file object as an argument
    # e.g., output_file = open("test_output.log", "w")
    # To print output to the console, pass None as an argument
    # output_file = None
    output_file = open("docs/results.txt", "w")
    main(output_file)
