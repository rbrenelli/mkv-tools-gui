
import json
import os
from typing import List, Optional
from modules.models.data_models import MediaFile, Track
from utils.command_runner import CommandRunner
from services.dependency_service import DependencyService

class MediaService:
    def __init__(self, dependency_service: DependencyService):
        self.deps = dependency_service
        self.runner = CommandRunner()

    def inspect_file(self, filepath: str) -> MediaFile:
        """
        Inspects a media file using mkvmerge (for MKV) or ffprobe (for others).
        Returns a MediaFile object.
        """
        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".mkv":
            return self._inspect_mkv(filepath)
        else:
            return self._inspect_ffmpeg(filepath)

    def _inspect_mkv(self, filepath: str) -> MediaFile:
        mkvmerge = self.deps.get_tool_path("mkvmerge")
        if not mkvmerge:
             raise RuntimeError("mkvmerge not found")

        cmd = [mkvmerge, "-J", filepath]
        rc, output = self.runner.run_command_sync(cmd)

        if rc != 0:
            raise RuntimeError(f"Failed to inspect MKV: {output}")

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            raise RuntimeError("Failed to parse mkvmerge output")

        tracks = []
        for t in data.get("tracks", []):
            tracks.append(Track(
                id=t["id"],
                type=t["type"],
                codec=t["codec"],
                language=t.get("properties", {}).get("language", "und"),
                name=t.get("properties", {}).get("track_name"),
                properties=t.get("properties", {})
            ))

        # mkvmerge duration is in nanoseconds usually, or requires calculation
        # It's in container properties usually
        duration_ns = data.get("container", {}).get("properties", {}).get("duration")
        duration = float(duration_ns) / 1_000_000_000 if duration_ns else 0

        return MediaFile(
            filepath=filepath,
            format="mkv",
            tracks=tracks,
            duration=duration
        )

    def _inspect_ffmpeg(self, filepath: str) -> MediaFile:
        ffprobe = self.deps.get_tool_path("ffprobe")
        if not ffprobe:
             raise RuntimeError("ffprobe not found")

        cmd = [
            ffprobe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            filepath
        ]
        rc, output = self.runner.run_command_sync(cmd)

        if rc != 0:
            raise RuntimeError(f"Failed to inspect file with ffprobe: {output}")

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            raise RuntimeError("Failed to parse ffprobe output")

        tracks = []
        # ffprobe streams index is 0-based.
        # However, for extraction/manipulation later, we need to map this carefully.
        # mkvmerge uses its own IDs. ffmpeg uses stream indices.

        for i, stream in enumerate(data.get("streams", [])):
            codec_type = stream.get("codec_type")
            # Map ffmpeg types to mkvmerge types for consistency in UI
            t_type = codec_type # 'video', 'audio', 'subtitle' -> 'subtitles'
            if t_type == 'subtitle':
                t_type = 'subtitles'

            tracks.append(Track(
                id=i, # FFmpeg stream index
                type=t_type,
                codec=stream.get("codec_name", "unknown"),
                language=stream.get("tags", {}).get("language", "und"),
                name=stream.get("tags", {}).get("title"),
                properties=stream
            ))

        duration = float(data.get("format", {}).get("duration", 0))

        return MediaFile(
            filepath=filepath,
            format="ffmpeg_supported", # generic bucket
            tracks=tracks,
            duration=duration
        )
