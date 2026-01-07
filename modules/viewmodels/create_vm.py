
from typing import List, Callable, Optional, Dict, Any
from services.export_service import ExportService
from services.error_service import ErrorService

class CreateViewModel:
    def __init__(self, export_service: ExportService):
        self.export_service = export_service
        self.inputs: List[Dict[str, Any]] = [] # list of {path: str, type: str}
        self.output_format = "mkv"

        self.on_list_updated: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_progress: Optional[Callable[[str], None]] = None
        self.on_complete: Optional[Callable[[str], None]] = None

    def add_input(self, filepath: str):
        # We could inspect file type here, but for now just add it
        self.inputs.append({"path": filepath})
        if self.on_list_updated:
            self.on_list_updated()

    def remove_input(self, index: int):
        if 0 <= index < len(self.inputs):
            self.inputs.pop(index)
            if self.on_list_updated:
                self.on_list_updated()

    def set_output_format(self, fmt: str):
        self.output_format = fmt

    def create_video(self, output_path: str):
        if not self.inputs:
            if self.on_error: self.on_error("No input files selected.")
            return

        def on_complete(rc, output):
            if rc == 0:
                if self.on_complete: self.on_complete("Creation successful!")
            else:
                if self.on_error: self.on_error(f"Error: {output}")

        self.export_service.create_video(
            self.inputs,
            self.output_format,
            output_path,
            lambda line: self.on_progress(line) if self.on_progress else None,
            on_complete
        )
