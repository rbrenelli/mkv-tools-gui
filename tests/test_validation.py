import unittest
import os
from utils.validation import is_safe_filename

class TestValidation(unittest.TestCase):
    def test_safe_filenames(self):
        self.assertTrue(is_safe_filename("test.mkv"))
        self.assertTrue(is_safe_filename("video_1.mp4"))
        self.assertTrue(is_safe_filename("my file.txt"))
        self.assertTrue(is_safe_filename("valid-name"))

    def test_unsafe_filenames_traversal(self):
        self.assertFalse(is_safe_filename("../test.mkv"))
        self.assertFalse(is_safe_filename(".."))
        self.assertFalse(is_safe_filename("."))
        self.assertFalse(is_safe_filename("/tmp/test.mkv"))
        self.assertFalse(is_safe_filename("dir/file.mkv"))
        # Test platform specific separator
        self.assertFalse(is_safe_filename(f"dir{os.sep}file.mkv"))

    def test_empty_or_whitespace(self):
        self.assertFalse(is_safe_filename(""))
        self.assertFalse(is_safe_filename("   "))
        self.assertFalse(is_safe_filename(None))
        self.assertFalse(is_safe_filename(123))

if __name__ == '__main__':
    unittest.main()
