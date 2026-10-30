import os


def safe_output_path(out_dir, name):
    """
    Join a user-typed file name onto out_dir, keeping the result inside out_dir.
    Only the final path component of `name` is used. Returns None if nothing usable is left.
    """
    base = os.path.basename(name.replace("\\", "/")).strip()
    if base in ("", ".", ".."):
        return None
    return os.path.join(out_dir, base)


def unique_path(path):
    """Return `path`, or `path` with _1, _2, ... before the extension if it already exists."""
    if not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(path)
    n = 1
    while os.path.exists(f"{stem}_{n}{ext}"):
        n += 1
    return f"{stem}_{n}{ext}"
