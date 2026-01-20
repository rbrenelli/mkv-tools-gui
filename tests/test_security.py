import unittest
import sys
import os

# Add repo root to path so we can import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.security import sanitize_filename

class TestSecurity(unittest.TestCase):
    def test_basic_filename(self):
        self.assertEqual(sanitize_filename("video.mkv"), "video.mkv")

    def test_path_traversal(self):
        self.assertEqual(sanitize_filename("../../etc/passwd"), "passwd")
        self.assertEqual(sanitize_filename("/var/log/syslog"), "syslog")

        # On Linux, backslash is a valid char, so basename doesn't split it.
        # Our regex removes backslashes, so it effectively sanitizes it by merging.
        # "..\..\windows\system32" -> "....windowssystem32"
        # This is safe (no traversal).
        self.assertEqual(sanitize_filename("..\\..\\windows\\system32"), "....windowssystem32")

        # Test explicit traversal removal + regex cleaning
        self.assertEqual(sanitize_filename("../evil.sh"), "evil.sh")

    def test_special_chars(self):
        # Allow dots, dashes, underscores
        self.assertEqual(sanitize_filename("my-video_final.v2.mkv"), "my-video_final.v2.mkv")

        # Remove unsafe chars
        # Note: basename("video; rm -rf /") returns "" because of trailing slash
        self.assertEqual(sanitize_filename("video; rm -rf /"), "unnamed_file")

        # Test without trailing slash
        # Spaces are allowed
        self.assertEqual(sanitize_filename("video; rm -rf"), "video rm -rf")

        self.assertEqual(sanitize_filename("file$(whoami).mkv"), "filewhoami.mkv")

    def test_empty_input(self):
        self.assertEqual(sanitize_filename(""), "unnamed_file")
        self.assertEqual(sanitize_filename("   "), "unnamed_file")

    def test_only_unsafe(self):
        self.assertEqual(sanitize_filename("///"), "unnamed_file")
        self.assertEqual(sanitize_filename("..."), "unnamed_file")

if __name__ == '__main__':
    unittest.main()
