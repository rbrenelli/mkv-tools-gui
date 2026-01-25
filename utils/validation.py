import os

def is_safe_filename(filename):
    """
    Checks if a filename is safe to use (no path traversal, no reserved characters).
    Returns True if safe, False otherwise.
    """
    if not filename:
        return False

    # Check for path separators
    if "/" in filename or "\\" in filename:
        return False

    # Check for traversal components explicitly
    if filename == "." or filename == "..":
        return False

    return True
