"""One entry point for reading any supported video file."""
import os

from .model import MkvError, read_info
from .tools import FFMPEG_HINT, missing_ffmpeg

MATROSKA_EXTS = {".mkv", ".mka", ".mks", ".webm"}


def is_matroska(path):
    return os.path.splitext(path)[1].lower() in MATROSKA_EXTS


def read_media(path):
    """MKV/WebM through mkvmerge; MP4/AVI/MOV and others through ffprobe. Raises MkvError."""
    if is_matroska(path):
        return read_info(path)
    if missing_ffmpeg():
        raise MkvError(f"MP4 and other formats need ffmpeg.\nInstall it with:  {FFMPEG_HINT}")
    from .ffmpeg import read_probe
    return read_probe(path)
