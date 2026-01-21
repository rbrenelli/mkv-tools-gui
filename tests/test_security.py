import unittest
from utils.security import sanitize_filename

class TestSecurity(unittest.TestCase):
    def test_sanitize_filename_basic(self):
        self.assertEqual(sanitize_filename("valid_file.mp4"), "valid_file.mp4")
        self.assertEqual(sanitize_filename("My Video.mkv"), "My Video.mkv")

    def test_sanitize_filename_traversal(self):
        self.assertEqual(sanitize_filename("../../etc/passwd"), "passwd")
        # On Linux, \ is not a path separator, so it gets replaced by sanitize_filename
        # effectively neutralizing the traversal attempt.
        self.assertEqual(sanitize_filename("..\\windows\\system32"), "_windows_system32")

    def test_sanitize_filename_special_chars(self):
        self.assertEqual(sanitize_filename("cool|movie?.mp4"), "cool_movie_.mp4")
        self.assertEqual(sanitize_filename("file*name.txt"), "file_name.txt")
        # Spaces are allowed
        self.assertEqual(sanitize_filename("$(rm -rf).sh"), "__rm -rf_.sh")

    def test_sanitize_filename_empty(self):
        self.assertEqual(sanitize_filename(""), "unnamed_file")
        self.assertEqual(sanitize_filename("   "), "unnamed_file")
        self.assertEqual(sanitize_filename("."), "unnamed_file")
        self.assertEqual(sanitize_filename(".."), "unnamed_file")

    def test_sanitize_filename_reserved(self):
        # On Linux/Python basename, / is separator.
        self.assertEqual(sanitize_filename("/root/secret"), "secret")

if __name__ == "__main__":
    unittest.main()
