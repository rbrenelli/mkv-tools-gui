import unittest
import sys
import os

# Add the repository root to sys.path so we can import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.validation import is_safe_filename

class TestValidation(unittest.TestCase):
    def test_safe_filenames(self):
        self.assertTrue(is_safe_filename("valid_file.mkv"))
        self.assertTrue(is_safe_filename("file with spaces.mp4"))
        self.assertTrue(is_safe_filename("file-with-dashes.srt"))
        self.assertTrue(is_safe_filename("file_with_underscores.ass"))
        self.assertTrue(is_safe_filename("mixedCaseFile.txt"))
        self.assertTrue(is_safe_filename("file..name.txt")) # This is valid now

    def test_unsafe_filenames(self):
        # Path traversal
        self.assertFalse(is_safe_filename("folder/file.mkv"))
        self.assertFalse(is_safe_filename("folder\\file.mkv"))
        self.assertFalse(is_safe_filename("/absolute/path/file.mkv"))

        # Reserved names acting as traversal
        self.assertFalse(is_safe_filename(".."))
        self.assertFalse(is_safe_filename("."))

    def test_empty(self):
        self.assertFalse(is_safe_filename(""))
        self.assertFalse(is_safe_filename(None))

if __name__ == '__main__':
    unittest.main()
