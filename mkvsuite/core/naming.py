"""Default output file names for extracted tracks."""
import os
import re

# Matroska codec id -> extension mkvextract writes
EXTENSIONS = {
    "S_TEXT/UTF8": ".srt", "S_TEXT/ASCII": ".srt", "S_TEXT/ASS": ".ass", "S_TEXT/SSA": ".ssa",
    "S_TEXT/WEBVTT": ".vtt", "S_HDMV/PGS": ".sup", "S_VOBSUB": ".idx", "S_TEXT/USF": ".usf",
    "A_AAC": ".aac", "A_AC3": ".ac3", "A_EAC3": ".eac3", "A_DTS": ".dts", "A_FLAC": ".flac",
    "A_OPUS": ".opus", "A_VORBIS": ".ogg", "A_TRUEHD": ".thd", "A_MPEG/L3": ".mp3", "A_MPEG/L2": ".mp2",
    "V_MPEG4/ISO/AVC": ".h264", "V_MPEGH/ISO/HEVC": ".h265", "V_VP8": ".ivf", "V_VP9": ".ivf",
    "V_AV1": ".obu", "V_MPEG2": ".mpg",
}

_BAD = re.compile(r"[^\w .\-\[\]()]", re.UNICODE)


def extension_for(codec_id):
    cid = codec_id or ""
    if cid in EXTENSIONS:
        return EXTENSIONS[cid]
    if cid.startswith("A_AAC"):
        return ".aac"
    if cid.startswith("A_PCM"):
        return ".wav"
    return ".bin"


def clean_part(text):
    """Keep letters (any script), digits, space and . _ - [ ] ( ); drop the rest."""
    return re.sub(r"\s+", " ", _BAD.sub("", text)).strip()


def default_name(stem, track, taken=()):
    """
    '<stem>.<lang>[.<track name>][.forced].<ext>', made unique against `taken` (a set of names).
    """
    parts = [stem]
    if track.language and track.language != "und":
        parts.append(track.language)
    name = clean_part(track.name)
    if name:
        parts.append(name)
    if track.forced:
        parts.append("forced")
    base = ".".join(parts)
    ext = extension_for(track.codec_id)
    out, n = base + ext, 1
    while out in taken:
        out = f"{base}_{n}{ext}"
        n += 1
    return out


def stem_of(path):
    return os.path.splitext(os.path.basename(path))[0]
