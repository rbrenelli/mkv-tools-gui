
import subprocess
import shutil
import tkinter.filedialog
import os

class LinuxDialogs:
    @staticmethod
    def askdirectory(title="Select Directory"):
        # Try Zenity
        zenity = shutil.which("zenity")
        if zenity:
            try:
                cmd = [zenity, "--file-selection", "--directory", f"--title={title}"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    path = result.stdout.strip()
                    if path: return path
                # Exit code 1 means Cancel/Closed, do not fallback
                if result.returncode == 1:
                    return ""
            except:
                pass

        # Try KDialog
        kdialog = shutil.which("kdialog")
        if kdialog:
            try:
                cmd = [kdialog, "--getexistingdirectory", os.getcwd(), title]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    path = result.stdout.strip()
                    if path: return path
                # Exit code 1 means Cancel
                if result.returncode == 1:
                    return ""
            except:
                pass

        # Fallback
        return tkinter.filedialog.askdirectory(title=title)

    @staticmethod
    def askopenfilename(title="Select File", filetypes=None):
        # filetypes: list of (name, pattern) e.g. [("Video", "*.mkv *.mp4")]

        # Zenity Filter Format: --file-filter="Name | *.ext *.ext2"
        # KDialog Filter Format: "Name (*.ext *.ext2)"

        zenity = shutil.which("zenity")
        if zenity:
            try:
                cmd = [zenity, "--file-selection", f"--title={title}"]
                if filetypes:
                    for name, pattern in filetypes:
                        # Convert pattern "*.mkv *.mp4" to standard regex-ish or simple
                        # Zenity expects "Name | *.ext *.ext"
                        cmd.append(f"--file-filter={name} | {pattern}")

                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    path = result.stdout.strip()
                    if path: return path
                if result.returncode == 1:
                    return ""
            except:
                pass

        kdialog = shutil.which("kdialog")
        if kdialog:
            try:
                # kdialog --getopenfilename [startDir] [filter]
                # filter: "Video files (*.mkv *.mp4)"
                filter_str = ""
                if filetypes:
                    # simplistic: take first or join
                    # KDialog usually expects one string separated by newlines or just one argument
                    parts = []
                    for name, pattern in filetypes:
                        parts.append(f"{name} ({pattern})")
                    filter_str = " | ".join(parts)

                cmd = [kdialog, "--getopenfilename", os.getcwd(), filter_str] if filter_str else [kdialog, "--getopenfilename", os.getcwd()]

                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    path = result.stdout.strip()
                    if path: return path
                if result.returncode == 1:
                    return ""
            except:
                pass

        return tkinter.filedialog.askopenfilename(title=title, filetypes=filetypes)

    @staticmethod
    def asksaveasfilename(title="Save As", defaultextension=""):
        zenity = shutil.which("zenity")
        if zenity:
            try:
                cmd = [zenity, "--file-selection", "--save", "--confirm-overwrite", f"--title={title}"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    path = result.stdout.strip()
                    if path:
                        if defaultextension and not os.path.splitext(path)[1]:
                            path += defaultextension
                        return path
                if result.returncode == 1:
                    return ""
            except:
                pass

        # KDialog
        kdialog = shutil.which("kdialog")
        if kdialog:
             try:
                cmd = [kdialog, "--getsavefilename", os.getcwd()]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    path = result.stdout.strip()
                    if path:
                        if defaultextension and not os.path.splitext(path)[1]:
                            path += defaultextension
                        return path
                if result.returncode == 1:
                    return ""
             except:
                 pass

        return tkinter.filedialog.asksaveasfilename(title=title, defaultextension=defaultextension)
