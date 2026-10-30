"""Chooses the right tool (MKVToolNix or ffmpeg) for an operation and builds the command."""
import os
from dataclasses import dataclass

from . import commands, ffmpeg
from .tools import FFMPEG_HINT, INSTALL_HINT, find_tool

MKV_OUT = {".mkv", ".mka", ".webm"}


class ToolMissing(RuntimeError):
    def __init__(self, tool, hint):
        super().__init__(f"{tool} is not installed.\nInstall it with:  {hint}")
        self.tool, self.hint = tool, hint


@dataclass
class Planned:
    argv: list
    kind: str            # "mkvtoolnix" or "ffmpeg" (decides how output/exit codes are read)
    duration_ns: int = 0


def _need(name, hint):
    exe = find_tool(name)
    if not exe:
        raise ToolMissing(name, hint)
    return exe


def extract(info, mapping):
    """mapping: {track_id: output_path}"""
    if info.backend == "ffmpeg":
        return Planned(ffmpeg.build_extract(_need("ffmpeg", FFMPEG_HINT), info, mapping), "ffmpeg", info.duration_ns)
    return Planned(commands.build_extract(_need("mkvextract", INSTALL_HINT), info.path, mapping), "mkvtoolnix")


def mux(info, output, keep_ids=None, edits=None, subs=()):
    """Remux `info` into `output` (container from the extension). Raises ffmpeg.UnsupportedError / ToolMissing."""
    ext = os.path.splitext(output)[1].lower()
    if info.backend == "mkvtoolnix" and ext in MKV_OUT:
        return Planned(commands.build_mux(_need("mkvmerge", INSTALL_HINT), output, info, keep_ids, edits, subs), "mkvtoolnix")
    return Planned(ffmpeg.build_mux(_need("ffmpeg", FFMPEG_HINT), output, info, keep_ids, edits, subs), "ffmpeg", info.duration_ns)


def propedit(info, edits):
    """In-place edits: MKV only."""
    if info.backend != "mkvtoolnix":
        raise ffmpeg.UnsupportedError("Only MKV files can be edited in place.")
    return Planned(commands.build_propedit(_need("mkvpropedit", INSTALL_HINT), info.path, info, edits), "mkvtoolnix")
