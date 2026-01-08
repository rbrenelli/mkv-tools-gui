
from typing import List, Callable, Optional
from modules.models.data_models import MediaFile, Track
from services.media_service import MediaService
from services.export_service import ExportService
from services.error_service import ErrorService

class ExtractViewModel:
    def __init__(self, media_service: MediaService, export_service: ExportService):
        self.media_service = media_service
        self.export_service = export_service

        self.current_file: Optional[MediaFile] = None
        self.is_busy = False

        # Callbacks for UI updates
        self.on_file_loaded: Optional[Callable[[MediaFile], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_progress: Optional[Callable[[float, str], None]] = None
        self.on_complete: Optional[Callable[[str], None]] = None

    def load_file(self, filepath: str):
        try:
            self.current_file = self.media_service.inspect_file(filepath)
            if self.on_file_loaded:
                self.on_file_loaded(self.current_file)
        except Exception as e:
            msg = ErrorService.get_friendly_message(e)
            if self.on_error:
                self.on_error(msg)

    def toggle_track_selection(self, track_id: int, selected: bool):
        if self.current_file:
            for track in self.current_file.tracks:
                if track.id == track_id:
                    track.selected = selected
                    break

    def set_track_output_name(self, track_id: int, name: str):
         if self.current_file:
            for track in self.current_file.tracks:
                if track.id == track_id:
                    track.output_filename = name
                    break

    def extract_selected(self, output_dir: str):
        if not self.current_file:
            return

        selected_tracks = [t for t in self.current_file.tracks if t.selected]
        if not selected_tracks:
            if self.on_error: self.on_error("No tracks selected.")
            return

        self.is_busy = True

        def progress_cb(line):
            # Parse progress if possible, for now just pass line
            # mkvmerge outputs "Progress: 10%"
            if self.on_progress:
                self.on_progress(0, line) # TODO: Parse percentage

        def complete_cb(rc, output):
            self.is_busy = False
            if rc == 0:
                if self.on_complete: self.on_complete("Extraction successful!")
            else:
                if self.on_error: self.on_error(f"Extraction failed: {output}")

        self.export_service.extract_tracks(
            self.current_file,
            selected_tracks,
            output_dir,
            progress_cb,
            complete_cb
        )
