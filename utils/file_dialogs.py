import subprocess
import os
import platform
import shutil
import tkinter as tk
from tkinter import filedialog
from contextlib import contextmanager

VIDEO_FILE_TYPES = [
    ("Video Files", "*.mkv *.mp4 *.avi *.mov *.m4v"),
    ("All Files", "*.*")
]

def _convert_filters(filetypes):
    """
    Convert list of tuples [("Name", "*.ext *.ext2")] 
    to cmd list ["--file-filter=Name | *.ext *.ext2"]
    """
    filters = []
    if not filetypes:
        return filters
        
    for name, pattern in filetypes:
        if pattern == "*.*":
            filters.append(f"--file-filter={name} | *")
        else:
            # Zenity likes "*.mkv *.mp4", which matches our input tuple usually
            filters.append(f"--file-filter={name} | {pattern}")
    return filters

def _use_zenity():
    """Check if we are on Linux and zenity is available."""
    return platform.system() == 'Linux' and shutil.which('zenity') is not None

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
    if _use_zenity():
        cmd = ["zenity", "--file-selection", f"--title={title}"]
        
        if filetypes:
            cmd.extend(_convert_filters(filetypes))

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except FileNotFoundError:
            pass

    # Fallback to tkinter
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
    if _use_zenity():
        cmd = ["zenity", "--file-selection", "--multiple", "--separator=|", f"--title={title}"]
        
        if filetypes:
            cmd.extend(_convert_filters(filetypes))

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # Zenity returns "path1|path2|path3"
                return result.stdout.strip().split("|")
            return []
        except Exception as e:
            print(f"Error invoking zenity: {e}")
            return []

    # Fallback to tkinter
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
    if _use_zenity():
        cmd = ["zenity", "--file-selection", "--save", "--confirm-overwrite", f"--title={title}"]
        
        if initialfile:
            # Zenity uses --filename to set the initial name/path
            cmd.append(f"--filename={initialfile}")
        
        if filetypes:
            cmd.extend(_convert_filters(filetypes))

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            path = result.stdout.strip()

            if result.returncode == 0 and path:
                # If defaultextension is provided and path has no extension, append it
                if defaultextension and not os.path.splitext(path)[1]:
                    path += defaultextension
                return path
            return None
        except Exception as e:
            print(f"Error invoking zenity: {e}")
            return None

    # Fallback to tkinter
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
    if _use_zenity():
        cmd = ["zenity", "--file-selection", "--directory", f"--title={title}"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            print(f"Error invoking zenity: {e}")
            return None

    # Fallback to tkinter
    with _tk_context():
        directory = filedialog.askdirectory(title=title)
        if directory:
            return os.path.abspath(directory)
        return None
