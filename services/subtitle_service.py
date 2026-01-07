
import os
import re
from typing import Optional
from modules.models.data_models import SubtitleFile

class SubtitleService:
    # Mapping commonly used codes to full names could be extensive.
    # Using a small subset for now or relying on external libraries if available.
    # Since we can't install new deps easily without user permission, we'll build a simple map.

    LANG_MAP = {
        "en": "English", "eng": "English",
        "pt": "Portuguese", "por": "Portuguese",
        "br": "Portuguese (Brazil)", "pt-br": "Portuguese (Brazil)", "pt_br": "Portuguese (Brazil)",
        "es": "Spanish", "spa": "Spanish",
        "fr": "French", "fre": "French", "fra": "French",
        "de": "German", "ger": "German", "deu": "German",
        "it": "Italian", "ita": "Italian",
        "ja": "Japanese", "jpn": "Japanese",
        "ko": "Korean", "kor": "Korean",
        "zh": "Chinese", "chi": "Chinese", "zho": "Chinese",
        "ru": "Russian", "rus": "Russian"
    }

    def parse_filename(self, filepath: str) -> SubtitleFile:
        """
        Parses a subtitle filename to extract language and flags.
        Ex: movie.pt-br.forced.srt
        """
        filename = os.path.basename(filepath)
        lower_name = filename.lower()

        # Detection logic
        is_forced = "forced" in lower_name
        is_sdh = "sdh" in lower_name

        # Try to find language code
        # Split by dots or dashes
        parts = re.split(r'[.\-_]', lower_name)

        lang_code = "und"
        lang_name = "Undetermined"

        for part in parts:
            if part in self.LANG_MAP:
                lang_code = part
                lang_name = self.LANG_MAP[part]
                break

        # Special case for 'pt-br' etc if split didn't catch composite
        if "pt-br" in lower_name or "pt_br" in lower_name:
             lang_code = "pt-br"
             lang_name = "Portuguese (Brazil)"

        return SubtitleFile(
            filepath=filepath,
            language_code=lang_code,
            language_name=lang_name,
            track_name=lang_name, # Default track name
            is_forced=is_forced,
            is_sdh=is_sdh
        )

    def normalize_language(self, code: str) -> str:
        return self.LANG_MAP.get(code.lower(), code)
