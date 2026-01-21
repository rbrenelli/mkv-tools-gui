import os
import re

def sanitize_filename(filename, replacement="_"):
    """
    Sanitize a filename to prevent path traversal and shell injection.

    Args:
        filename (str): The filename to sanitize.
        replacement (str): The character to replace invalid characters with.

    Returns:
        str: The sanitized filename.
    """
    if not filename:
        return "unnamed_file"

    # Remove directory separators and path traversal attempts by taking only the basename
    # This effectively strips 'folder/', '../', etc.
    filename = os.path.basename(filename)

    # Whitelist alphanumeric, dot, dash, underscore, space
    # Everything else gets replaced
    clean_name = re.sub(r'[^a-zA-Z0-9._\- ]', replacement, filename)

    # Remove leading/trailing dots/spaces to avoid issues on Windows/Linux
    clean_name = clean_name.strip(" .")

    if not clean_name:
        return "unnamed_file"

    return clean_name
