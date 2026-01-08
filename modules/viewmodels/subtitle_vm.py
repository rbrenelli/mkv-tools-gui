
from typing import List, Callable, Optional
from modules.models.data_models import SubtitleFile
from services.subtitle_service import SubtitleService
from services.export_service import ExportService
from services.error_service import ErrorService

class SubtitleViewModel:
    def __init__(self, subtitle_service: SubtitleService, export_service: ExportService):
        self.sub_service = subtitle_service
        self.export_service = export_service

        self.video_path: Optional[str] = None
        self.subtitles: List[SubtitleFile] = []

        # Callbacks
        self.on_list_updated: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_progress: Optional[Callable[[str], None]] = None
        self.on_complete: Optional[Callable[[str], None]] = None

    def set_video(self, filepath: str):
        self.video_path = filepath
        # Clear subs or keep them? Usually keep them if user is building a list.
        # But maybe reset if different video. Let's keep for now.

    def add_subtitle(self, filepath: str):
        try:
            sub = self.sub_service.parse_filename(filepath)
            self.subtitles.append(sub)
            if self.on_list_updated:
                self.on_list_updated()
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))

    def remove_subtitle(self, index: int):
        if 0 <= index < len(self.subtitles):
            self.subtitles.pop(index)
            if self.on_list_updated:
                self.on_list_updated()

    def save_file(self, output_path: str):
        if not self.video_path:
            if self.on_error: self.on_error("Please select a video file first.")
            return

        if not self.subtitles:
             if self.on_error: self.on_error("Please add at least one subtitle file.")
             return

        def on_complete(rc, output):
            if rc == 0:
                if self.on_complete: self.on_complete("File saved successfully!")
            else:
                if self.on_error: self.on_error(f"Error: {output}")

        self.export_service.mux_subtitles(
            self.video_path,
            self.subtitles,
            output_path,
            lambda line: self.on_progress(line) if self.on_progress else None,
            on_complete
        )
