import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog
from contextlib import contextmanager

VIDEO_FILE_TYPES = [
    ("Video Files", "*.mkv *.mp4 *.avi *.mov *.m4v"),
    ("All Files", "*.*")
]

# Detect Linux Tools
_ZENITY_PATH = shutil.which("zenity")
_KDIALOG_PATH = shutil.which("kdialog")

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

class FallbackRequired(Exception):
    pass

def _run_linux_cmd(cmd):
    """
    Runs a linux command.
    Returns:
        stdout string if success (returncode 0)
        None if cancelled (returncode 1)
    Raises:
        FallbackRequired if returncode is neither 0 nor 1, or execution fails.
    """
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        elif result.returncode == 1:
            return None # User cancelled
        else:
            # Something went wrong (e.g. invalid args, crash)
            print(f"Linux dialog tool failed with code {result.returncode}: {result.stderr}")
            raise FallbackRequired()
    except Exception as e:
        print(f"Linux dialog tool execution error: {e}")
        raise FallbackRequired()

def select_file(title="Select File", filetypes=None):
    """
    Open single file selection dialog.
    Returns absolute path string or None.
    """
    if sys.platform.startswith("linux"):
        try:
            if _ZENITY_PATH:
                cmd = [_ZENITY_PATH, "--file-selection", f"--title={title}"]
                if filetypes:
                    for name, pattern in filetypes:
                        # Zenity 4.x format: "Name | Pattern1 Pattern2"
                        cmd.append(f"--file-filter={name} | {pattern}")

                path = _run_linux_cmd(cmd)
                if path: return os.path.abspath(path)
                if path is None: return None # Cancelled

            elif _KDIALOG_PATH:
                cmd = [_KDIALOG_PATH, "--getopenfilename", os.getcwd()]
                if filetypes:
                    # KDialog filter: "*.mkv *.mp4|Video Files"
                    filters = []
                    for name, pattern in filetypes:
                        filters.append(f"{pattern}|{name}")
                    cmd.append("\n".join(filters))

                path = _run_linux_cmd(cmd)
                if path: return os.path.abspath(path)
                if path is None: return None

        except FallbackRequired:
            print("DEBUG: Zenity/KDialog failed, falling back to Tkinter file dialog")

    # Fallback
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
    if sys.platform.startswith("linux"):
        try:
            if _ZENITY_PATH:
                # Zenity multiple returns paths separated by | by default
                cmd = [_ZENITY_PATH, "--file-selection", "--multiple", f"--title={title}"]
                if filetypes:
                    for name, pattern in filetypes:
                        # Zenity 4.x format: "Name | Pattern1 Pattern2"
                        cmd.append(f"--file-filter={name} | {pattern}")

                out = _run_linux_cmd(cmd)
                if out:
                    # Parse output
                    paths = out.split('|')
                    return [os.path.abspath(p) for p in paths if p]
                if out is None: return [] # Cancelled

            elif _KDIALOG_PATH:
                # KDialog multiple
                cmd = [_KDIALOG_PATH, "--getopenfilename", os.getcwd(), "--multiple", "--separate-output"]
                if filetypes:
                    filters = []
                    for name, pattern in filetypes:
                        filters.append(f"{pattern}|{name}")
                    cmd.append("\n".join(filters))

                out = _run_linux_cmd(cmd)
                if out:
                    paths = out.strip().split('\n')
                    return [os.path.abspath(p) for p in paths if p]
                if out is None: return []

        except FallbackRequired:
            print("DEBUG: Zenity/KDialog failed, falling back to Tkinter file dialog")

    with _tk_context():
        kwargs = {"title": title}
        if filetypes:
            kwargs["filetypes"] = filetypes

        files = filedialog.askopenfilenames(**kwargs)
        if files:
            return [os.path.abspath(f) for f in files]
        return []

def save_file(title="Save As", initialfile=None, filetypes=None, defaultextension=None):
    """
    Open save file dialog.
    Returns absolute path string or None.
    """
    if sys.platform.startswith("linux"):
        try:
            if _ZENITY_PATH:
                # Note: --confirm-overwrite is deprecated in zenity 4.x but harmless
                cmd = [_ZENITY_PATH, "--file-selection", "--save", f"--title={title}"]
                if initialfile:
                    cmd.append(f"--filename={initialfile}")
                if filetypes:
                    for name, pattern in filetypes:
                        # Zenity 4.x format: "Name | Pattern1 Pattern2"
                        cmd.append(f"--file-filter={name} | {pattern}")

                path = _run_linux_cmd(cmd)
                if path: return os.path.abspath(path)
                if path is None: return None

            elif _KDIALOG_PATH:
                cmd = [_KDIALOG_PATH, "--getsavefilename", os.getcwd()]
                if filetypes:
                     filters = []
                     for name, pattern in filetypes:
                         filters.append(f"{pattern}|{name}")
                     cmd.append("\n".join(filters))

                path = _run_linux_cmd(cmd)
                if path:
                    return os.path.abspath(path)
                if path is None: return None

        except FallbackRequired:
            print("DEBUG: Zenity/KDialog failed, falling back to Tkinter file dialog")

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
    if sys.platform.startswith("linux"):
        try:
            if _ZENITY_PATH:
                cmd = [_ZENITY_PATH, "--file-selection", "--directory", f"--title={title}"]
                path = _run_linux_cmd(cmd)
                if path: return os.path.abspath(path)
                if path is None: return None

            elif _KDIALOG_PATH:
                cmd = [_KDIALOG_PATH, "--getexistingdirectory", os.getcwd()]
                path = _run_linux_cmd(cmd)
                if path: return os.path.abspath(path)
                if path is None: return None

        except FallbackRequired:
            print("DEBUG: Zenity/KDialog failed, falling back to Tkinter file dialog")

    with _tk_context():
        directory = filedialog.askdirectory(title=title)
        if directory:
            return os.path.abspath(directory)
        return None
