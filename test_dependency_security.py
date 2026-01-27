import unittest
import hashlib
import tempfile
import os
from utils.dependency_manager import DependencyManager

class TestDependencySecurity(unittest.TestCase):
    def setUp(self):
        self.dm = DependencyManager()

    def test_urls_have_hashes(self):
        """Verify that all configured URLs have a hash field."""
        urls = self.dm._get_urls()
        for name, info in urls.items():
            self.assertIn('hash', info, f"Package {name} missing hash")
            self.assertIsInstance(info['hash'], str, f"Hash for {name} is not a string")
            self.assertEqual(len(info['hash']), 64, f"Hash for {name} is not SHA256 length")

    def test_verify_file_hash_success(self):
        """Test hash verification with matching hash."""
        content = b"test content"
        expected_hash = hashlib.sha256(content).hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            filepath = f.name

        try:
            # Should not raise exception
            self.assertTrue(self.dm._verify_file_hash(filepath, expected_hash))
        finally:
            os.remove(filepath)

    def test_verify_file_hash_failure(self):
        """Test hash verification with mismatching hash."""
        content = b"test content"
        expected_hash = hashlib.sha256(b"different content").hexdigest()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(content)
            filepath = f.name

        try:
            with self.assertRaises(ValueError):
                self.dm._verify_file_hash(filepath, expected_hash)
        finally:
            os.remove(filepath)

if __name__ == '__main__':
    unittest.main()
