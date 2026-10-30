"""Language handling: full ISO 639-2 list from `mkvmerge --list-languages`, plus filename detection."""
import os
import re
import subprocess
from dataclasses import dataclass

from .tools import clean_env, find_tool


@dataclass(frozen=True)
class Language:
    code: str      # ISO 639-2, what mkvmerge/mkvpropedit expect
    name: str
    iso1: str = ""

    @property
    def label(self):
        return f"{self.name} ({self.code})"


# Shown first in pickers
COMMON_CODES = ["eng", "por", "spa", "fra", "deu", "ita", "jpn", "chi", "rus", "kor", "ara", "hin", "und"]

FALLBACK = [
    Language("eng", "English", "en"), Language("por", "Portuguese", "pt"), Language("spa", "Spanish", "es"),
    Language("fra", "French", "fr"), Language("deu", "German", "de"), Language("ita", "Italian", "it"),
    Language("jpn", "Japanese", "ja"), Language("chi", "Chinese", "zh"), Language("rus", "Russian", "ru"),
    Language("kor", "Korean", "ko"), Language("ara", "Arabic", "ar"), Language("hin", "Hindi", "hi"),
    Language("und", "Undetermined"),
]

# Extra aliases people put in file names that are not ISO codes/names
ALIASES = {"pob": "por", "ptbr": "por", "br": "por", "esp": "spa", "ger": "deu", "fre": "fra",
           "jp": "jpn", "chn": "chi", "zho": "chi", "cn": "chi"}


def parse_language_table(text):
    """Parse the table printed by `mkvmerge --list-languages`; keep rows that have an ISO 639-2 code."""
    langs, seen = [], set()
    for line in text.splitlines():
        cols = [c.strip() for c in line.split("|")]
        if len(cols) != 4 or cols[2] in ("", "ISO 639-2 code") or set(cols[0]) == {"-"}:
            continue
        name, _iso3, iso2, iso1 = cols
        if iso2 in seen:
            continue
        seen.add(iso2)
        langs.append(Language(iso2, name.split(";")[0].strip(), iso1))
    return langs


def load_languages():
    """All languages known to the installed mkvmerge, common ones first; falls back to a short list."""
    exe = find_tool("mkvmerge")
    langs = []
    if exe:
        try:
            r = subprocess.run([exe, "--list-languages"], capture_output=True, text=True,
                               env=clean_env(), check=False, timeout=15)
            langs = parse_language_table(r.stdout)
        except (OSError, subprocess.SubprocessError):
            langs = []
    if not langs:
        return list(FALLBACK)
    by_code = {l.code: l for l in langs}
    for l in FALLBACK:  # make sure the common ones exist (e.g. 'und')
        by_code.setdefault(l.code, l)
    common = [by_code[c] for c in COMMON_CODES if c in by_code]
    rest = sorted((l for c, l in by_code.items() if c not in COMMON_CODES), key=lambda l: l.name.lower())
    return common + rest


def detect_language(filename, languages):
    """
    Guess the language from a file name like 'Movie.pt-BR.srt' or 'Movie_English.srt'.
    Only the last three name parts are considered (so 'It.Follows.srt' is not 'Italian').
    Returns a language code or None.
    """
    stem = os.path.splitext(os.path.basename(filename))[0]
    parts = [p for p in re.split(r"[.\-_\s]+", stem) if p]
    table = {}
    for l in languages:
        table[l.code] = l.code
        if l.iso1:
            table[l.iso1] = l.code
        table[l.name.lower()] = l.code
    table.update(ALIASES)
    if len(parts) == 1:   # a bare 'pt.srt' / 'eng.srt' is a language; a bare title like 'It.srt' is too risky
        l = parts[0].lower()
        return table.get(l) if len(l) in (2, 3) and l in table and l != "und" else None
    # 'pt-BR' splits into ['pt', 'BR']; the alias 'br' maps to Portuguese, so check from the end
    for part in reversed(parts[1:][-3:]):
        code = table.get(part.lower())
        if code and code != "und":
            return code
    return None
