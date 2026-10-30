"""Track/file model parsed from `mkvmerge -J`."""
import json
import os
import subprocess
from dataclasses import dataclass, field

from .tools import clean_env, find_tool

TYPES = ("video", "audio", "subtitles")


class MkvError(RuntimeError):
    pass


@dataclass(frozen=True)
class Track:
    id: int
    type: str
    codec: str
    codec_id: str
    language: str
    name: str
    default: bool
    forced: bool
    enabled: bool
    uid: int
    text_subtitles: bool = False

    @property
    def short(self):
        return f"{self.type.capitalize()} #{self.id}"

    @property
    def label(self):
        bits = [self.type.capitalize(), f"#{self.id}", self.codec]
        if self.language and self.language != "und":
            bits.append(self.language)
        return " · ".join(bits)


@dataclass
class MediaInfo:
    path: str
    container: str
    duration_ns: int = 0
    tracks: list = field(default_factory=list)
    backend: str = "mkvtoolnix"   # "ffmpeg" for MP4/AVI/MOV: track ids are ffprobe stream indexes

    def of_type(self, type_):
        return [t for t in self.tracks if t.type == type_]


def parse_info(data, path=""):
    """Build a MediaInfo from the dict returned by `mkvmerge -J`."""
    tracks = []
    for t in data.get("tracks", []):
        p = t.get("properties", {})
        tracks.append(Track(
            id=int(t["id"]),
            type=t.get("type", "other"),
            codec=t.get("codec", ""),
            codec_id=p.get("codec_id", ""),
            language=p.get("language", "und") or "und",
            name=p.get("track_name", "") or "",
            default=bool(p.get("default_track", False)),
            forced=bool(p.get("forced_track", False)),
            enabled=bool(p.get("enabled_track", True)),
            uid=int(p.get("uid", 0) or 0),
            text_subtitles=bool(p.get("text_subtitles", False)),
        ))
    container = data.get("container", {})
    return MediaInfo(
        path=path or data.get("file_name", ""),
        container=container.get("type", ""),
        duration_ns=int(container.get("properties", {}).get("duration", 0) or 0),
        tracks=tracks,
    )


def read_info(path):
    """Run mkvmerge -J (blocking: call from a worker thread). Raises MkvError."""
    exe = find_tool("mkvmerge")
    if not exe:
        raise MkvError("mkvmerge not found")
    try:
        r = subprocess.run([exe, "-J", os.path.abspath(path)], capture_output=True, text=True,
                           env=clean_env(), check=False)
    except OSError as e:
        raise MkvError(f"Could not run mkvmerge: {e}") from e
    if r.returncode == 2 or not r.stdout.strip():
        raise MkvError((r.stdout + r.stderr).strip() or f"mkvmerge failed ({r.returncode})")
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        raise MkvError(f"Could not parse mkvmerge output: {e}") from e
    if not data.get("container", {}).get("recognized", True):
        raise MkvError("Unrecognized file format")
    return parse_info(data, path)
