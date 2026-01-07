
import os
import threading
from typing import List, Callable, Optional
from modules.models.data_models import MediaFile, Track, SubtitleFile
from utils.command_runner import CommandRunner
from services.dependency_service import DependencyService

class ExportService:
    def __init__(self, dependency_service: DependencyService):
        self.deps = dependency_service
        self.runner = CommandRunner()

    def extract_tracks(
        self,
        source_file: MediaFile,
        tracks_to_extract: List[Track],
        output_dir: str,
        on_progress: Callable[[str], None],
        on_complete: Callable[[int, str], None]
    ):
        """
        Extracts tracks. Uses mkvextract for MKV, ffmpeg for others.
        """
        if source_file.format == "mkv":
            self._extract_mkv(source_file, tracks_to_extract, output_dir, on_progress, on_complete)
        else:
            self._extract_ffmpeg(source_file, tracks_to_extract, output_dir, on_progress, on_complete)

    def _extract_mkv(self, source, tracks, output_dir, on_progress, on_complete):
        mkvextract = self.deps.get_tool_path("mkvextract")

        # mkvextract tracks input.mkv ID:output ID:output ...
        cmd = [mkvextract, "tracks", source.filepath]

        for track in tracks:
            out_name = track.output_filename
            if not out_name:
                # Fallback if not set
                ext = "dat"
                if track.type == "video": ext = "mkv" # mkvextract raw video is weird, often best to keep in container or raw h264
                if track.type == "audio": ext = "ac3" # Guessing
                if track.type == "subtitles": ext = "srt"
                out_name = f"track_{track.id}.{ext}"

            out_path = os.path.join(output_dir, out_name)
            cmd.append(f"{track.id}:{out_path}")

        self.runner.run_command(cmd, on_output=on_progress, on_complete=on_complete)

    def _extract_ffmpeg(self, source, tracks, output_dir, on_progress, on_complete):
        ffmpeg = self.deps.get_tool_path("ffmpeg")

        # FFmpeg extraction is tricky for multiple files at once.
        # It's often easier to run one command per track or use complex filter_complex/map.
        # For simplicity/robustness, we might map all outputs in one command.

        cmd = [ffmpeg, "-y", "-i", source.filepath]

        for track in tracks:
            out_name = track.output_filename
            if not out_name:
                out_name = f"track_{track.id}.dat"

            out_path = os.path.join(output_dir, out_name)

            # Map stream: -map 0:ID -c copy output
            cmd.extend(["-map", f"0:{track.id}", "-c", "copy", out_path])

        self.runner.run_command(cmd, on_output=on_progress, on_complete=on_complete)

    def mux_subtitles(
        self,
        source_video: str,
        subtitles: List[SubtitleFile],
        output_path: str,
        on_progress: Callable[[str], None],
        on_complete: Callable[[int, str], None]
    ):
        """
        Muxes subtitles into a video file using mkvmerge (creates MKV).
        """
        mkvmerge = self.deps.get_tool_path("mkvmerge")

        cmd = [mkvmerge, "-o", output_path, source_video]

        for sub in subtitles:
            # Language code
            cmd.extend(["--language", f"0:{sub.language_code}"])
            # Track name
            if sub.track_name:
                cmd.extend(["--track-name", f"0:{sub.track_name}"])
            # Flags
            if sub.is_forced:
                cmd.extend(["--forced-track", "0:yes"])
            else:
                cmd.extend(["--forced-track", "0:no"])

            cmd.append(sub.filepath)

        self.runner.run_command(cmd, on_output=on_progress, on_complete=on_complete)

    def create_video(
        self,
        inputs: List[Dict[str, Any]], # List of input files with config
        output_format: str, # 'mkv' or 'mp4'
        output_path: str,
        on_progress: Callable[[str], None],
        on_complete: Callable[[int, str], None]
    ):
        """
        Creates a video from multiple inputs.
        If output is mkv, use mkvmerge.
        If output is mp4, use ffmpeg.
        """
        if output_format == "mkv":
            self._create_mkv(inputs, output_path, on_progress, on_complete)
        else:
            self._create_mp4(inputs, output_path, on_progress, on_complete)

    def _create_mkv(self, inputs, output_path, on_progress, on_complete):
        mkvmerge = self.deps.get_tool_path("mkvmerge")
        cmd = [mkvmerge, "-o", output_path]

        for item in inputs:
            path = item['path']
            # Add specific flags if needed based on item config
            # For now, just append inputs
            cmd.append(path)

        self.runner.run_command(cmd, on_output=on_progress, on_complete=on_complete)

    def _create_mp4(self, inputs, output_path, on_progress, on_complete):
        ffmpeg = self.deps.get_tool_path("ffmpeg")
        # Creating MP4 usually implies re-muxing or transcoding.
        # Simple implementation: map all streams, copy video/audio, convert subs.

        cmd = [ffmpeg, "-y"]

        for item in inputs:
             cmd.extend(["-i", item['path']])

        # Map all streams from all inputs
        # This is a simplification. Real logic might need to be smarter about what to include.
        # For now: map everything.
        # BUT: ffmpeg map syntax depends on input index.

        for i in range(len(inputs)):
            cmd.extend(["-map", str(i)])

        cmd.extend(["-c:v", "copy", "-c:a", "copy"])
        # Subtitles for MP4 must be mov_text
        cmd.extend(["-c:s", "mov_text"])

        # Fail if format not supported for stream (e.g. PGS subs in MP4)
        # We might need -strict unofficial or fallback logic, but let's stick to basics.

        cmd.append(output_path)

        self.runner.run_command(cmd, on_output=on_progress, on_complete=on_complete)
