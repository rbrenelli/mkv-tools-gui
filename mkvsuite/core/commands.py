"""Pure builders for mkvextract / mkvmerge / mkvpropedit command lines (no I/O, no GUI)."""
import os
from dataclasses import dataclass


@dataclass
class TrackEdit:
    """Changes to one existing track. None = leave as is."""
    language: str = None
    name: str = None
    default: bool = None
    forced: bool = None
    enabled: bool = None

    def is_empty(self):
        return all(v is None for v in (self.language, self.name, self.default, self.forced, self.enabled))


@dataclass
class SubInput:
    """An external subtitle file to add."""
    path: str
    language: str = "und"
    name: str = ""
    default: bool = False
    forced: bool = False


def _flag(v):
    return "1" if v else "0"


def build_extract(mkvextract, source, mapping):
    """mapping: {track_id: output_path}. One call extracts all selected tracks."""
    cmd = [mkvextract, "--gui-mode", os.path.abspath(source), "tracks"]
    for tid, out in mapping.items():
        cmd.append(f"{tid}:{out}")
    return cmd


def _track_selection(info, keep_ids):
    """--video-tracks/--no-video etc. Nothing is emitted for a type when all its tracks are kept."""
    args = []
    if keep_ids is None:
        return args
    for type_, all_flag, only_flag in (("video", "--no-video", "--video-tracks"),
                                        ("audio", "--no-audio", "--audio-tracks"),
                                        ("subtitles", "--no-subtitles", "--subtitle-tracks")):
        ids = [t.id for t in info.of_type(type_)]
        kept = [i for i in ids if i in keep_ids]
        if not ids or len(kept) == len(ids):
            continue
        args += [all_flag] if not kept else [only_flag, ",".join(map(str, kept))]
    return args


def _edit_args(tid, e):
    args = []
    if e.language is not None:
        args += ["--language", f"{tid}:{e.language}"]
    if e.name is not None:
        args += ["--track-name", f"{tid}:{e.name}"]
    if e.default is not None:
        args += ["--default-track-flag", f"{tid}:{_flag(e.default)}"]
    if e.forced is not None:
        args += ["--forced-display-flag", f"{tid}:{_flag(e.forced)}"]
    if e.enabled is not None:
        args += ["--track-enabled-flag", f"{tid}:{_flag(e.enabled)}"]
    return args


def build_mux(mkvmerge, output, info, keep_ids=None, edits=None, subs=()):
    """
    Remux `info.path` into `output`, optionally dropping tracks, changing track properties and
    appending external subtitle files. Existing flags are preserved unless listed in `edits`.
    """
    edits = edits or {}
    cmd = [mkvmerge, "--gui-mode", "-o", output]
    cmd += _track_selection(info, keep_ids)
    for tid, e in edits.items():
        if keep_ids is None or tid in keep_ids:
            cmd += _edit_args(tid, e)
    cmd.append(os.path.abspath(info.path))
    for s in subs:
        cmd += _edit_args(0, TrackEdit(language=s.language or "und", name=s.name or None,
                                       default=s.default, forced=s.forced))
        cmd.append(os.path.abspath(s.path))
    return cmd


def build_propedit(mkvpropedit, path, info, edits):
    """In-place property edits (no remux). `info` supplies track UIDs for exact selection."""
    by_id = {t.id: t for t in info.tracks}
    cmd = [mkvpropedit, os.path.abspath(path)]
    for tid, e in edits.items():
        if e.is_empty() or tid not in by_id:
            continue
        cmd += ["--edit", f"track:={by_id[tid].uid}"]
        if e.language is not None:
            cmd += ["--set", f"language={e.language}"]
        if e.name is not None:
            cmd += ["--set", f"name={e.name}"] if e.name else ["--delete", "name"]
        if e.default is not None:
            cmd += ["--set", f"flag-default={_flag(e.default)}"]
        if e.forced is not None:
            cmd += ["--set", f"flag-forced={_flag(e.forced)}"]
        if e.enabled is not None:
            cmd += ["--set", f"flag-enabled={_flag(e.enabled)}"]
    return cmd
