import unittest
from utils.security import sanitize_filename

class TestSecurity(unittest.TestCase):
    def test_sanitize_filename_basic(self):
        self.assertEqual(sanitize_filename("test.mkv"), "test.mkv")
        self.assertEqual(sanitize_filename("my_video-1.mp4"), "my_video-1.mp4")

    def test_sanitize_filename_path_traversal(self):
        self.assertEqual(sanitize_filename("../test.mkv"), "test.mkv")
        self.assertEqual(sanitize_filename("../../etc/passwd"), "passwd")
        self.assertEqual(sanitize_filename("subdir/test.mkv"), "test.mkv")

    def test_sanitize_filename_unsafe_chars(self):
        # : is replaced by _
        self.assertEqual(sanitize_filename("test:file.mkv"), "test_file.mkv")
        # * and ? are replaced by _
        self.assertEqual(sanitize_filename("test*file?.mkv"), "test_file_.mkv")
        # $ is replaced by _
        self.assertEqual(sanitize_filename("test$file.mkv"), "test_file.mkv")

    def test_sanitize_filename_empty(self):
        self.assertEqual(sanitize_filename(""), "unnamed_file")
        self.assertEqual(sanitize_filename("   "), "unnamed_file")
        self.assertEqual(sanitize_filename(None), "unnamed_file")
        self.assertEqual(sanitize_filename(123), "unnamed_file")

    def test_sanitize_filename_spaces(self):
        self.assertEqual(sanitize_filename("my file.mkv"), "my file.mkv")
        self.assertEqual(sanitize_filename("  my file.mkv  "), "my file.mkv")

if __name__ == '__main__':
    unittest.main()
