import unittest
from utils.validation import is_safe_filename

class TestValidation(unittest.TestCase):
    def test_safe_filenames(self):
        self.assertTrue(is_safe_filename("file.mkv"))
        self.assertTrue(is_safe_filename("my video 2.mp4"))
        self.assertTrue(is_safe_filename("video-final_v1.mkv"))
        self.assertTrue(is_safe_filename("video(1).mkv"))
        # Filenames with dots (double extensions) are generally safe as long as no separators
        self.assertTrue(is_safe_filename("archive.tar.gz"))
        self.assertTrue(is_safe_filename("...strange...name..."))

    def test_unsafe_filenames(self):
        self.assertFalse(is_safe_filename(""))
        self.assertFalse(is_safe_filename(None))
        self.assertFalse(is_safe_filename("../file.mkv"))
        self.assertFalse(is_safe_filename("dir/file.mkv"))
        self.assertFalse(is_safe_filename("/etc/passwd"))
        self.assertFalse(is_safe_filename("file\\name")) # Backslash
        self.assertFalse(is_safe_filename(".."))
        self.assertFalse(is_safe_filename("."))
        self.assertFalse(is_safe_filename("file\0name"))

if __name__ == '__main__':
    unittest.main()
