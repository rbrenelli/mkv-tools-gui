"""MP4/AVI/MOV support through ffprobe/ffmpeg (MKV files use MKVToolNix instead)."""
import json
import os
import subprocess

from . import naming
from .model import MediaInfo, MkvError, Track
from .tools import clean_env, find_tool

TEXT_CODECS = {"subrip", "srt", "ass", "ssa", "webvtt", "mov_text", "text"}
MP4_EXTS = {".mp4", ".m4v", ".mov"}
_TYPE_LETTER = {"video": "v", "audio": "a", "subtitles": "s"}
_TEXT_FOR_EXT = {".srt": "srt", ".vtt": "webvtt", ".ass": "ass", ".ssa": "ass"}


class UnsupportedError(ValueError):
    """The requested combination cannot be done (for example PGS subtitles into MP4)."""


PRETTY = {"h264": "H.264", "hevc": "HEVC (H.265)", "mpeg4": "MPEG-4", "mpeg2video": "MPEG-2", "vp9": "VP9", "vp8": "VP8",
          "av1": "AV1", "aac": "AAC", "ac3": "AC-3", "eac3": "E-AC-3", "dts": "DTS", "mp3": "MP3", "opus": "Opus",
          "vorbis": "Vorbis", "flac": "FLAC", "truehd": "TrueHD", "subrip": "SubRip (SRT)", "mov_text": "MOV text",
          "ass": "ASS", "ssa": "SSA", "webvtt": "WebVTT", "hdmv_pgs_subtitle": "PGS", "dvd_subtitle": "VobSub"}


def parse_probe(data, path=""):
    tracks = []
    for s in data.get("streams", []):
        ctype = {"video": "video", "audio": "audio", "subtitle": "subtitles"}.get(s.get("codec_type"))
        if not ctype:
            continue
        # cover art in MP3/M4A shows up as a "video" stream
        if ctype == "video" and s.get("disposition", {}).get("attached_pic"):
            continue
        tags = {k.lower(): v for k, v in (s.get("tags") or {}).items()}
        disp = s.get("disposition") or {}
        name = s.get("codec_name", "unknown")
        tracks.append(Track(
            id=int(s["index"]), type=ctype, codec=PRETTY.get(name, name.upper()), codec_id=f"ffmpeg:{name}",
            language=tags.get("language") or "und", name=tags.get("title", "") or "",
            default=bool(disp.get("default")), forced=bool(disp.get("forced")), enabled=True, uid=0,
            text_subtitles=ctype == "subtitles" and name in TEXT_CODECS))
    fmt = data.get("format", {})
    try:
        dur = int(float(fmt.get("duration", 0)) * 1e9)
    except (TypeError, ValueError):
        dur = 0
    return MediaInfo(path=path, container=fmt.get("format_name", ""), duration_ns=dur, tracks=tracks, backend="ffmpeg")


def read_probe(path):
    exe = find_tool("ffprobe")
    if not exe:
        raise MkvError("ffprobe not found")
    r = subprocess.run([exe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams",
                        os.path.abspath(path)], capture_output=True, text=True, env=clean_env(), check=False)
    if r.returncode != 0 or not r.stdout.strip():
        raise MkvError(r.stderr.strip() or "Could not read this file")
    try:
        return parse_probe(json.loads(r.stdout), path)
    except json.JSONDecodeError as e:
        raise MkvError(f"Could not parse ffprobe output: {e}") from e


def _wanted(info, keep_ids):
    return [t for t in info.tracks if t.type in _TYPE_LETTER and (keep_ids is None or t.id in keep_ids)]


def build_extract(ffmpeg, info, mapping):
    """One ffmpeg process writing every selected track to its own file. mapping: {stream_index: out_path}."""
    cmd = [ffmpeg, "-nostdin", "-y", "-v", "error", "-progress", "pipe:1", "-nostats", "-i", os.path.abspath(info.path)]
    by_id = {t.id: t for t in info.tracks}
    for idx, out in mapping.items():
        t = by_id[idx]
        ext = os.path.splitext(out)[1].lower()
        cmd += ["-map", f"0:{idx}"]
        if t.type == "subtitles" and ext in _TEXT_FOR_EXT and t.text_subtitles:
            cmd += ["-c:s", _TEXT_FOR_EXT[ext]]
        else:
            cmd += ["-c", "copy"]
        cmd.append(out)
    return cmd


def _flags(default, forced):
    parts = (["default"] if default else []) + (["forced"] if forced else [])
    return "+".join(parts) or "0"


def build_mux(ffmpeg, output, info, keep_ids=None, edits=None, subs=()):
    """
    Remux to MP4 (mov_text subtitles) or MKV (text subtitles kept as SRT/ASS) with ffmpeg: drop tracks,
    change language/name/default/forced, and append external subtitle files. Raises UnsupportedError for
    combinations MP4 cannot hold (PGS/VobSub, picture subtitles).
    """
    edits = edits or {}
    mp4 = os.path.splitext(output)[1].lower() in MP4_EXTS
    kept = _wanted(info, keep_ids)
    cmd = [ffmpeg, "-nostdin", "-y", "-v", "error", "-progress", "pipe:1", "-nostats", "-i", os.path.abspath(info.path)]
    for s in subs:
        cmd += ["-i", os.path.abspath(s.path)]
    for t in kept:
        cmd += ["-map", f"0:{t.id}"]
    for i in range(len(subs)):
        cmd += ["-map", f"{i + 1}:0"]
    cmd += ["-c", "copy"]

    counters = {"v": 0, "a": 0, "s": 0}

    def meta(letter, n, language=None, name=None, flags=None):
        out = []
        if language is not None:
            out += [f"-metadata:s:{letter}:{n}", f"language={language}"]
        if name is not None:
            out += [f"-metadata:s:{letter}:{n}", f"title={name}"]
            if mp4:
                out += [f"-metadata:s:{letter}:{n}", f"handler_name={name}"]
        if flags is not None:
            out += [f"-disposition:{letter}:{n}", flags]
        return out

    for t in kept:
        letter = _TYPE_LETTER[t.type]
        n = counters[letter]
        counters[letter] += 1
        name = t.codec_id[7:] if t.codec_id.startswith("ffmpeg:") else ""
        if t.type == "subtitles":
            if mp4 and not t.text_subtitles:
                raise UnsupportedError(f"MP4 can't hold “{t.codec}” subtitles ({t.short}). "
                                       "Untick that track, or save as MKV.")
            if mp4 and name != "mov_text":
                cmd += [f"-c:s:{n}", "mov_text"]
            elif not mp4 and name == "mov_text":
                cmd += [f"-c:s:{n}", "srt"]
        e = edits.get(t.id)
        if e:
            flags = None
            if e.default is not None or e.forced is not None:
                flags = _flags(t.default if e.default is None else e.default, t.forced if e.forced is None else e.forced)
            cmd += meta(letter, n, e.language, e.name, flags)

    for s in subs:
        n = counters["s"]
        counters["s"] += 1
        ext = os.path.splitext(s.path)[1].lower()
        if ext not in _TEXT_FOR_EXT:
            if mp4:
                raise UnsupportedError(f"“{os.path.basename(s.path)}” is a picture-based subtitle; MP4 can't hold it. Save as MKV.")
        else:
            cmd += [f"-c:s:{n}", "mov_text" if mp4 else _TEXT_FOR_EXT[ext]]
        cmd += meta("s", n, s.language or "und", s.name or None, _flags(s.default, s.forced))
    cmd.append(output)
    return cmd
