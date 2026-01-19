import unittest
import os
from utils.security import sanitize_filename

class TestSecurity(unittest.TestCase):
    def test_sanitize_filename_path_traversal(self):
        """Test that directory traversal sequences are stripped."""
        self.assertEqual(sanitize_filename("../../etc/passwd"), "passwd")
        self.assertEqual(sanitize_filename("/absolute/path/to/file"), "file")

    def test_sanitize_filename_normal(self):
        """Test that normal filenames are preserved."""
        self.assertEqual(sanitize_filename("video.mkv"), "video.mkv")
        self.assertEqual(sanitize_filename("my_video 2.mp4"), "my_video 2.mp4")

    def test_sanitize_filename_empty(self):
        """Test empty input."""
        self.assertEqual(sanitize_filename(""), "")
        self.assertEqual(sanitize_filename(None), "")

if __name__ == '__main__':
    unittest.main()
