import subprocess
import json
import shutil
import os
from utils.dependency_manager import DependencyManager

def check_ffmpeg():
    """
    Returns True if ffmpeg and ffprobe are available in the system PATH.
    """
    dm = DependencyManager()
    ffmpeg_path = dm.get_binary_path("ffmpeg")
    ffprobe_path = dm.get_binary_path("ffprobe")
    return bool(ffmpeg_path and ffprobe_path)

def get_ffmpeg_info(file_path):
    """
    Use ffprobe to get info about a video file and return it in a format
    compatible with the app's existing MKV structure.
    """
    ffprobe_exe = DependencyManager().get_binary_path("ffprobe")
    if not ffprobe_exe:
        raise FileNotFoundError("ffprobe not found")

    cmd = [
        ffprobe_exe,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        file_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"Error running ffprobe: {result.stderr}")
            return None

        data = json.loads(result.stdout)

        # Transform ffprobe JSON to expected app structure
        # Expected structure:
        # {
        #    "tracks": [
        #        {
        #            "id": <int>,
        #            "type": <str> ("video", "audio", "subtitles"),
        #            "properties": {
        #                "codec_id": <str>,
        #                "language": <str>,
        #                "track_name": <str>
        #            }
        #        },
        #        ...
        #    ]
        # }

        tracks = []
        if "streams" in data:
            for stream in data["streams"]:
                codec_type = stream.get("codec_type")

                # Map codec_type to expected type
                if codec_type == "video":
                    track_type = "video"
                elif codec_type == "audio":
                    track_type = "audio"
                elif codec_type == "subtitle":
                    track_type = "subtitles"
                else:
                    # Skip unknown types (like data or attachments if any, unless we want to support them)
                    # The prompt only mentions video, audio, subtitles.
                    continue

                # Extract properties
                codec_name = stream.get("codec_name", "unknown")
                tags = stream.get("tags", {})
                language = tags.get("language", "und")
                track_name = tags.get("title", "Unknown") # Prompt says "Unknown" as default

                track_entry = {
                    "id": stream["index"], # Prompt says map index to id
                    "type": track_type,
                    "properties": {
                        "codec_id": codec_name,
                        "language": language,
                        "track_name": track_name
                    }
                }
                tracks.append(track_entry)

        return {"tracks": tracks}

    except Exception as e:
        print(f"Exception running ffprobe: {e}")
        return None

def extract_stream_cmd(input_path, track_id, output_path):
    """
    Return a list of strings for the subprocess command to extract a specific track.
    Logic: ffmpeg -i input_path -map 0:<track_id> -c copy output_path
    """
    ffmpeg_exe = DependencyManager().get_binary_path("ffmpeg")
    if not ffmpeg_exe:
        raise FileNotFoundError("ffmpeg not found")

    return [
        ffmpeg_exe,
        "-i", input_path,
        "-map", f"0:{track_id}",
        "-c", "copy",
        output_path
    ]
