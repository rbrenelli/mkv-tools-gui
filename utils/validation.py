import os

def is_safe_filename(filename: str) -> bool:
    """
    Validates if a filename is safe to use.
    Returns False if the filename contains path separators, is empty,
    or contains null bytes.
    """
    if not filename:
        return False

    # Check for path separators
    # We explicitly check for both forward and backward slashes to ensure cross-platform safety
    if os.path.sep in filename or (os.path.altsep and os.path.altsep in filename) or '/' in filename or '\\' in filename:
        return False

    # Check for null bytes
    if '\0' in filename:
        return False

    # Check for relative path traversal components explicitly
    if filename == '..' or filename == '.':
        return False

    if '..' in filename:
        # Strict check: disallow '..' entirely to be safe, though technically ".." could be a filename
        # But for this app, it's safer to disallow it.
        # Actually, if we block separators, ".." can only be the exact filename or part of a name like "video..mkv".
        # "video..mkv" is safe. ".." alone is a directory reference.
        pass

    return True
