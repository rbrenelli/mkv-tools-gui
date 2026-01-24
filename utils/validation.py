import os

def is_safe_filename(filename):
    """
    Checks if the filename is safe (no path traversal).
    Returns True if safe, False otherwise.
    """
    if not filename or not isinstance(filename, str):
        return False

    # Must be a pure filename, no directory components
    # os.path.dirname returns non-empty string if there are path separators
    if os.path.dirname(filename):
        return False

    # Double check that basename matches input (canonical way to ensure no path info)
    if os.path.basename(filename) != filename:
        return False

    # Block special directory names
    if filename in ('.', '..'):
        return False

    # Block empty or whitespace only
    if not filename.strip():
        return False

    return True
