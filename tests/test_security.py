import unittest
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.extractor import ExtractorFrame

class TestPathTraversal(unittest.TestCase):
    def test_vulnerability_reproduction(self):
        """
        Demonstrates that os.path.join allows path traversal.
        This confirms the vulnerability exists in the old logic.
        """
        output_dir = os.path.join(os.path.sep, "safe", "output", "dir")

        # Attack 1: Relative traversal
        malicious_filename = "../../etc/passwd"
        result = os.path.join(output_dir, malicious_filename)
        resolved = os.path.normpath(result)

        # We expect this to escape output_dir
        # On windows this might be slightly different but the principle holds
        target = os.path.join(os.path.sep, "etc", "passwd")

        # Note: on Linux /safe/output/dir + ../../etc/passwd -> /etc/passwd
        # On Windows \safe\output\dir + ..\..\etc\passwd -> \etc\passwd

        self.assertTrue(resolved.endswith("passwd"))
        self.assertFalse(resolved.startswith(output_dir))

    def test_sanitization_fix(self):
        """
        Tests the fix using the actual method from ExtractorFrame.
        """
        output_dir = os.path.join(os.path.sep, "safe", "output", "dir")

        # Attack 1: Relative traversal
        malicious_filename = "../../etc/passwd"

        # Call the static method
        result = ExtractorFrame._get_safe_output_path(output_dir, malicious_filename)

        expected = os.path.join(output_dir, "passwd")
        self.assertEqual(result, expected)

        # Attack 2: Absolute path
        malicious_filename_abs = "/etc/shadow"
        # Note: os.path.basename handles forward slashes on Windows somewhat correctly
        # depending on python version/context, but let's assume standard behavior.
        # Actually os.path.basename('/etc/shadow') on Windows might include full path if it doesn't recognize / as sep
        # But we are testing in Linux environment here.
        # To be robust, let's use os.path.join for the input too if we want to simulate platform behavior,
        # but the input here is simulating a malicious string which might use / or \.
        # os.path.basename uses os.path.sep.

        # Let's rely on the method doing its job for the current platform.

        result_abs = ExtractorFrame._get_safe_output_path(output_dir, malicious_filename_abs)

        # On Linux, basename('/etc/shadow') -> 'shadow'
        # On Windows, basename('/etc/shadow') might remain '/etc/shadow' if it expects backslash.
        # But wait, the vulnerability is about what os.path.join does.
        # If I am on Windows and attacker sends "C:\Windows", basename handles it.
        # If attacker sends "/etc/passwd" on Windows, it's just a filename with weird chars, not a traversal usually.

        # For this test, since I am on Linux environment in sandbox:
        if os.name == 'posix':
            expected_abs = os.path.join(output_dir, "shadow")
            self.assertEqual(result_abs, expected_abs)

if __name__ == '__main__':
    unittest.main()
