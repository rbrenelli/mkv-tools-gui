import subprocess
import json
import shutil
import os
from utils.dependency_manager import DependencyManager

def check_dependencies():
    """Check if mkvmerge and mkvextract are available."""
    dm = DependencyManager()
    mkvmerge = dm.get_binary_path("mkvmerge")
    mkvextract = dm.get_binary_path("mkvextract")
    return mkvmerge, mkvextract

def get_mkv_info(mkv_path):
    """
    Run mkvmerge -J to get JSON info about the file.
    Returns the parsed JSON object.
    Raises FileNotFoundError if mkvmerge is missing.
    Raises RuntimeError if mkvmerge fails (e.g. invalid file).
    """
    mkvmerge_exe = DependencyManager().get_binary_path("mkvmerge")
    if not mkvmerge_exe:
        raise FileNotFoundError("mkvmerge not found. Please ensure MKVToolNix is installed.")

    cmd = [mkvmerge_exe, "-J", mkv_path]
    try:
        # Check=False allows us to handle the error code manually
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            raise RuntimeError(f"mkvmerge failed (code {result.returncode}): {error_msg}")

        return json.loads(result.stdout)
    except FileNotFoundError:
        # This handles if subprocess fails to find the executable even if we thought we had the path
        raise FileNotFoundError(f"Could not execute mkvmerge at: {mkvmerge_exe}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse mkvmerge output: {e}")
    except Exception as e:
        # Re-raise known exceptions, wrap others
        if isinstance(e, (RuntimeError, FileNotFoundError)):
            raise e
        raise RuntimeError(f"Error analyzing file: {e}")

def extract_tracks(mkv_path, track_id_path_map):
    """
    Extract tracks using mkvextract.
    track_id_path_map: dict mapping track_id (int) -> output_path (str)
    """
    mkvextract_exe = DependencyManager().get_binary_path("mkvextract")
    if not mkvextract_exe:
        raise FileNotFoundError("mkvextract not found")

    cmd = [mkvextract_exe, mkv_path, "tracks"]
    for tid, path in track_id_path_map.items():
        cmd.append(f"{tid}:{path}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode == 0, result.stderr or result.stdout
    except Exception as e:
        return False, str(e)

def mux_mkv(output_path, input_files, options=None):
    """
    Run mkvmerge to create/mux a file.
    """
    mkvmerge_exe = DependencyManager().get_binary_path("mkvmerge")
    if not mkvmerge_exe:
        raise FileNotFoundError("mkvmerge not found")

    cmd = [mkvmerge_exe, "-o", output_path]
    if options:
        cmd.extend(options)
    
    if input_files:
        cmd.extend(input_files)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode == 0, result.stderr or result.stdout
    except Exception as e:
        return False, str(e)
