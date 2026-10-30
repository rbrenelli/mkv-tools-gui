import os
import unittest

from utils.security import safe_output_path


class SafeOutputPathTests(unittest.TestCase):
    def test_plain_name(self):
        self.assertEqual(safe_output_path("/out", "a.srt"), os.path.join("/out", "a.srt"))

    def test_keeps_unicode_and_brackets(self):
        self.assertEqual(safe_output_path("/out", "Filme [1080p] ção.mkv"),
                         os.path.join("/out", "Filme [1080p] ção.mkv"))

    def test_traversal_is_stripped(self):
        self.assertEqual(safe_output_path("/out", "../../etc/passwd"), os.path.join("/out", "passwd"))

    def test_absolute_path_is_stripped(self):
        self.assertEqual(safe_output_path("/out", "/etc/cron.d/x"), os.path.join("/out", "x"))

    def test_backslash_traversal_is_stripped(self):
        self.assertEqual(safe_output_path("/out", "..\\..\\x.srt"), os.path.join("/out", "x.srt"))

    def test_unusable_names(self):
        for bad in ("", "   ", ".", "..", "a/..", "/"):
            self.assertIsNone(safe_output_path("/out", bad), bad)


if __name__ == "__main__":
    unittest.main()
