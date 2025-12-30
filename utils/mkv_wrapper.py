import subprocess
import json
import shutil
import os

def check_dependencies():
    """Check if mkvmerge and mkvextract are available."""
    mkvmerge = shutil.which("mkvmerge")
    mkvextract = shutil.which("mkvextract")
    return mkvmerge, mkvextract

def get_mkv_info(mkv_path):
    """
    Run mkvmerge -J to get JSON info about the file.
    Returns the parsed JSON object or None on failure.
    """
    mkvmerge_exe = shutil.which("mkvmerge")
    if not mkvmerge_exe:
        raise FileNotFoundError("mkvmerge not found")

    cmd = [mkvmerge_exe, "-J", mkv_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"Error running mkvmerge: {result.stderr}")
            return None
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Exception running mkvmerge: {e}")
        return None

def extract_tracks(mkv_path, track_id_path_map):
    """
    Extract tracks using mkvextract.
    track_id_path_map: dict mapping track_id (int) -> output_path (str)
    """
    mkvextract_exe = shutil.which("mkvextract")
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
    input_files: list of input file paths.
    options: list of global options or per-file options (needs careful ordering).
             For simple cases, we might want a more structured argument builder.
    
    For this wrapper, we'll assume 'options' contains the full command list *before* the input files,
    or we construct the command manually in the caller.
    
    Actually, let's make this generic:
    cmd_args: list of arguments to pass to mkvmerge -o output_path [cmd_args]
    """
    mkvmerge_exe = shutil.which("mkvmerge")
    if not mkvmerge_exe:
        raise FileNotFoundError("mkvmerge not found")

    cmd = [mkvmerge_exe, "-o", output_path]
    if options:
        cmd.extend(options)
    
    # If input_files are provided separately, append them. 
    # But often options need to be interleaved with input files.
    # So if options is provided, we assume the caller handled the interleaving if necessary,
    # OR we just append input files at the end (which is fine for simple appends).
    if input_files:
        cmd.extend(input_files)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode == 0, result.stderr or result.stdout
    except Exception as e:
        return False, str(e)
