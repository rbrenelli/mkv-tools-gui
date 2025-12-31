import re
import os

languages = [
    "eng (English)", "spa (Spanish)", "por (Portuguese)", "fra (French)", 
    "deu (German)", "ita (Italian)", "jpn (Japanese)", "chi (Chinese)", 
    "rus (Russian)", "kor (Korean)", "ara (Arabic)", "hin (Hindi)"
]

# Map common codes to our list keys
LANG_MAP = {
    'en': 'eng', 'eng': 'eng', 'english': 'eng', 'en-us': 'eng', 'en-gb': 'eng',
    'pt': 'por', 'por': 'por', 'portuguese': 'por', 'pt-br': 'por', 'pob': 'por',
    'es': 'spa', 'spa': 'spa', 'spanish': 'spa', 'esp': 'spa',
    'fr': 'fra', 'fra': 'fra', 'french': 'fra',
    'de': 'deu', 'deu': 'deu', 'german': 'deu', 'ger': 'deu',
    'it': 'ita', 'ita': 'ita', 'italian': 'ita',
    'ja': 'jpn', 'jpn': 'jpn', 'japanese': 'jpn', 'jp': 'jpn',
    'zh': 'chi', 'chi': 'chi', 'chinese': 'chi', 'chn': 'chi', 'zho': 'chi',
    'ru': 'rus', 'rus': 'rus', 'russian': 'rus',
    'ko': 'kor', 'kor': 'kor', 'korean': 'kor',
    'ar': 'ara', 'ara': 'ara', 'arabic': 'ara',
    'hi': 'hin', 'hin': 'hin', 'hindi': 'hin'
}

def detect_language(filename):
    # Remove extension first (.srt, .ass, etc)
    basename = os.path.splitext(filename)[0]
    
    # Strategy 1: Look for language code at the end of the filename (e.g. movie.en, movie.pt-br)
    # We split by '.' or '_' or '-' or ' '
    parts = re.split(r'[._\-\s]+', basename)
    
    # Iterate backwards through parts to find a match
    for part in reversed(parts):
        lower_part = part.lower()
        if lower_part in LANG_MAP:
            target_code = LANG_MAP[lower_part]
            # Find the full string in languages list
            for lang_str in languages:
                if lang_str.startswith(target_code + " "):
                    return lang_str
    
    return None

# Test cases
test_files = [
    "subtitle.zh.srt",
    "subtitlename.pt.srt",
    "movie.pob.srt",
    "film.pt-BR.srt",
    "show.en-us.srt",
    "episode.ara.srt",
    "title.hin.ass",
    "random_movie_spa.sub",
    "mixed.case.CHI.srt",
    "delimited_by_underscore_eng.srt",
    "no_lang.srt"
]

print(f"{'Filename':<30} | {'Detected':<20}")
print("-" * 55)
for f in test_files:
    res = detect_language(f)
    print(f"{f:<30} | {res if res else 'None'}")
