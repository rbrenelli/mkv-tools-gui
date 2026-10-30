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

# ffprobe codec names (codec_id is stored as "ffmpeg:<name>" for non-MKV files)
FFMPEG_EXTENSIONS = {
    "subrip": ".srt", "srt": ".srt", "mov_text": ".srt", "text": ".srt", "ass": ".ass", "ssa": ".ass",
    "webvtt": ".vtt", "hdmv_pgs_subtitle": ".sup", "dvd_subtitle": ".mks",
    "aac": ".aac", "ac3": ".ac3", "eac3": ".eac3", "dts": ".dts", "flac": ".flac", "opus": ".opus",
    "vorbis": ".ogg", "mp3": ".mp3", "mp2": ".mp2", "truehd": ".thd",
    "h264": ".h264", "hevc": ".h265", "vp9": ".ivf", "vp8": ".ivf", "av1": ".obu", "mpeg2video": ".m2v",
}

_BAD = re.compile(r"[^\w .\-\[\]()]", re.UNICODE)


def extension_for(codec_id):
    cid = codec_id or ""
    if cid.startswith("ffmpeg:"):
        name = cid[7:]
        if name.startswith("pcm_"):
            return ".wav"
        return FFMPEG_EXTENSIONS.get(name, ".mkv" if name else ".bin")
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
