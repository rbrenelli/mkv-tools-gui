import os

def sanitize_filename(filename):
    """
    Sanitizes a filename to prevent path traversal.
    Returns the basename of the file.
    """
    if not filename:
        return ""
    return os.path.basename(filename)
