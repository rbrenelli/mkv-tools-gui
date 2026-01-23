import os
import re

def sanitize_filename(filename):
    """
    Sanitizes a filename to prevent path traversal and ensure it is safe for the file system.

    Args:
        filename (str): The filename to sanitize.

    Returns:
        str: A sanitized filename.
    """
    if not filename or not isinstance(filename, str):
        return "unnamed_file"

    # Remove path traversal characters and directory components
    filename = os.path.basename(filename)

    # Replace dangerous characters with underscores
    # Allow alphanumeric, space, dot, underscore, hyphen
    # This regex matches anything NOT in the whitelist and replaces it
    filename = re.sub(r'[^a-zA-Z0-9 ._-]', '_', filename)

    # Remove leading/trailing periods or spaces which can be problematic on Windows
    filename = filename.strip(' .')

    # Prevent empty filenames after sanitization
    if not filename:
        return "unnamed_file"

    return filename
