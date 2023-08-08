import unittest
import os
import sys

def create_test_suite(test_dir):
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern='test_*.py')
    return suite

def run_tests(test_dirs):
    test_root = os.path.dirname(os.path.abspath(__file__))

    for function_name in test_dirs:
        test_dir = os.path.join(test_root, function_name)
        if not os.path.isdir(test_dir):
            print(f"Error: Test directory '{function_name}' not found.")
            sys.exit(1)

        suite = create_test_suite(test_dir)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_runner.py [--all | dir_name1 [dir_name2 ...]]")
        sys.exit(1)

    if sys.argv[1] == '--all':
        test_dirs = [
            d for d in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__))))
            if os.path.isdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), d))
        ]
    else:
        test_dirs = sys.argv[1:]

    run_tests(test_dirs)
