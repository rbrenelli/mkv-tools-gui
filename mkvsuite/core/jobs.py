"""Interpreting what the MKVToolNix tools print and return."""
import re
from dataclasses import dataclass

_PROGRESS = re.compile(r"^#GUI#progress (\d+)%")
_MESSAGE = re.compile(r"^#GUI#(warning|error)\s*(.*)")


@dataclass
class Outcome:
    ok: bool
    warnings: str = ""
    error: str = ""


def progress_from_line(line):
    """Percent (0-100) from a `--gui-mode` progress line, else None."""
    m = _PROGRESS.match(line.strip())
    return int(m.group(1)) if m else None


_FF_KEYS = re.compile(r"^(frame|fps|bitrate|total_size|out_time_us|out_time_ms|out_time|dup_frames|drop_frames|"
                      r"speed|progress|stream_\d+_\d+_q)=")
_FF_TIME = re.compile(r"^out_time_us=(\d+)")


def is_noise(line):
    """Control chatter that does not belong in the log (--gui-mode lines, ffmpeg -progress key=value lines)."""
    return (line.startswith("#GUI#begin_scanning_playlists") or line.startswith("#GUI#end_scanning_playlists")
            or bool(_FF_KEYS.match(line)))


def ffmpeg_progress(line, duration_ns):
    """Percent from an `-progress pipe:1` line (out_time_us=...), given the file duration."""
    m = _FF_TIME.match(line.strip())
    if not m or not duration_ns:
        return None
    return max(0, min(99, int(int(m.group(1)) * 1000 / duration_ns * 100)))


def interpret_ffmpeg(exit_code, output):
    """ffmpeg: 0 = ok, anything else is an error (shows the last lines it printed)."""
    if exit_code == 0:
        return Outcome(True)
    lines = [l for l in output.splitlines() if l.strip() and not is_noise(l)]
    return Outcome(False, error="\n".join(lines[-12:]) or f"ffmpeg exited with code {exit_code}")


def interpret(exit_code, output):
    """
    mkvmerge, mkvextract and mkvpropedit all use: 0 = ok, 1 = finished with warnings, 2 = error.
    """
    lines = [l for l in output.splitlines() if l.strip() and not is_noise(l) and progress_from_line(l) is None]
    if exit_code == 0:
        return Outcome(True)
    if exit_code == 1:
        warn = [m.group(2) for l in lines if (m := _MESSAGE.match(l)) and m.group(1) == "warning"]
        return Outcome(True, warnings="\n".join(warn) or "\n".join(lines))
    err = [m.group(2) for l in lines if (m := _MESSAGE.match(l)) and m.group(1) == "error"]
    return Outcome(False, error="\n".join(err) or "\n".join(lines[-15:]) or f"exited with code {exit_code}")
