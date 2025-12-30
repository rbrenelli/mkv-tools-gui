import subprocess
import os

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

def select_file(title="Select File", filetypes=None):
    """
    Open single file selection dialog.
    Returns absolute path string or None.
    """
    cmd = ["zenity", "--file-selection", f"--title={title}"]
    
    if filetypes:
        cmd.extend(_convert_filters(filetypes))
        
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except FileNotFoundError:
        # Fallback logic could go here, but we verified zenity exists
        print("Error: zenity not found")
        return None

def select_files(title="Select Files", filetypes=None):
    """
    Open multiple file selection dialog.
    Returns list of strings or empty list.
    """
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

def save_file(title="Save As", initialfile=None, filetypes=None, defaultextension=None):
    """
    Open save file dialog.
    Returns absolute path string or None.
    """
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

def select_directory(title="Select Directory"):
    """
    Open directory selection dialog.
    Returns absolute path string or None.
    """
    cmd = ["zenity", "--file-selection", "--directory", f"--title={title}"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception as e:
        print(f"Error invoking zenity: {e}")
        return None
