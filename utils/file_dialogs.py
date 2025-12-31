import os
import tkinter as tk
from tkinter import filedialog
from contextlib import contextmanager

VIDEO_FILE_TYPES = [
    ("Video Files", "*.mkv *.mp4 *.avi *.mov *.m4v"),
    ("All Files", "*.*")
]

@contextmanager
def _tk_context():
    """
    Context manager to handle Tkinter root window.
    Ensures a root window exists and is hidden, preventing empty windows.
    """
    root = None
    created = False

    # Check if a root already exists (e.g., from the main app)
    if tk._default_root:
        yield tk._default_root
    else:
        try:
            root = tk.Tk()
            root.withdraw()  # Hide the window
            created = True
            yield root
        finally:
            if created and root:
                root.destroy()

def select_file(title="Select File", filetypes=None):
    """
    Open single file selection dialog.
    Returns absolute path string or None.
    """
    with _tk_context():
        kwargs = {"title": title}
        if filetypes:
            kwargs["filetypes"] = filetypes

        file_path = filedialog.askopenfilename(**kwargs)
        if file_path:
            return os.path.abspath(file_path)
        return None

def select_files(title="Select Files", filetypes=None):
    """
    Open multiple file selection dialog.
    Returns list of strings or empty list.
    """
    with _tk_context():
        kwargs = {"title": title}
        if filetypes:
            kwargs["filetypes"] = filetypes

        files = filedialog.askopenfilenames(**kwargs)
        # files is a tuple of strings
        if files:
            return [os.path.abspath(f) for f in files]
        return []

def save_file(title="Save As", initialfile=None, filetypes=None, defaultextension=None):
    """
    Open save file dialog.
    Returns absolute path string or None.
    """
    with _tk_context():
        kwargs = {"title": title, "confirmoverwrite": True}
        if initialfile:
            kwargs["initialfile"] = initialfile
        if filetypes:
            kwargs["filetypes"] = filetypes
        if defaultextension:
            kwargs["defaultextension"] = defaultextension

        file_path = filedialog.asksaveasfilename(**kwargs)
        if file_path:
            return os.path.abspath(file_path)
        return None

def select_directory(title="Select Directory"):
    """
    Open directory selection dialog.
    Returns absolute path string or None.
    """
    with _tk_context():
        directory = filedialog.askdirectory(title=title)
        if directory:
            return os.path.abspath(directory)
        return None
