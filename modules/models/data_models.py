
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class Track:
    id: int
    type: str # 'video', 'audio', 'subtitles'
    codec: str
    language: str
    name: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)

    # UI State
    selected: bool = False
    output_filename: Optional[str] = None # For extraction

@dataclass
class MediaFile:
    filepath: str
    format: str # 'mkv', 'mp4', etc.
    tracks: list[Track] = field(default_factory=list)
    duration: Optional[float] = None

    @property
    def filename(self):
        import os
        return os.path.basename(self.filepath)

@dataclass
class SubtitleFile:
    filepath: str
    language_code: str # 'eng', 'por', etc.
    language_name: str # 'English', 'Portuguese (Brazil)'
    track_name: str = ""
    is_forced: bool = False
    is_sdh: bool = False

    @property
    def filename(self):
        import os
        return os.path.basename(self.filepath)
