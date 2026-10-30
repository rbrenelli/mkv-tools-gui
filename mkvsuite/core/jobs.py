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


def is_noise(line):
    """--gui-mode lines that are control chatter, not for the log."""
    return line.startswith("#GUI#begin_scanning_playlists") or line.startswith("#GUI#end_scanning_playlists")


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
