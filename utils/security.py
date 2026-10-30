import os


def safe_output_path(out_dir, name):
    """
    Join a user-typed file name onto out_dir, keeping the result inside out_dir.
    Only the final path component of `name` is used. Returns None if nothing
    usable is left (empty, ".", "..").
    """
    base = os.path.basename(name.replace("\\", "/")).strip()
    if base in ("", ".", ".."):
        return None
    return os.path.join(out_dir, base)
