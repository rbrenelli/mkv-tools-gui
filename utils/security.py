import os
import re

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a filename to prevent path traversal and ensure it's safe for the filesystem.

    1. Removes directory separators (path traversal prevention).
    2. Allows only alphanumeric characters, spaces, dots, dashes, and underscores.
    3. Strips leading/trailing whitespace.
    4. Ensures the filename is not empty.

    Args:
        filename (str): The candidate filename provided by user input.

    Returns:
        str: A sanitized version of the filename safe to use.
    """
    if not filename:
        return "unnamed_file"

    # Prevent path traversal by using basename
    # This turns "foo/bar" -> "bar" and "../../bar" -> "bar"
    name = os.path.basename(filename)

    # Allow only safe characters (alphanumeric, space, dot, underscore, dash)
    # This prevents potentially dangerous shell chars or control characters
    safe_name = re.sub(r'[^a-zA-Z0-9 \._-]', '', name)

    safe_name = safe_name.strip()

    # Fallback if result is empty or just dots/spaces
    if not safe_name or safe_name.replace('.', '') == '':
        safe_name = "unnamed_file"

    return safe_name
