
import customtkinter as ctk
import sys
import threading
from modules.views.sidebar import Sidebar
from modules.views.extract_view import ExtractView
from modules.views.subtitle_view import SubtitleView
from modules.views.create_view import CreateView
from modules.views.settings_view import SettingsView
from modules.views.components.modal import ModalDialog

from modules.viewmodels.app_vm import AppViewModel
from modules.viewmodels.extract_vm import ExtractViewModel
from modules.viewmodels.subtitle_vm import SubtitleViewModel
from modules.viewmodels.create_vm import CreateViewModel
from modules.viewmodels.settings_vm import SettingsViewModel

from services.dependency_service import DependencyService
from services.media_service import MediaService
from services.subtitle_service import SubtitleService
from services.export_service import ExportService

from utils.constants import APP_NAME, COLOR_BG_MAIN, COLOR_BG_SIDEBAR

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("1000x700")

        # Scaling for HighDPI (Chromebooks)
        self.setup_scaling()

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Init Services
        self.dep_service = DependencyService()
        self.media_service = MediaService(self.dep_service)
        self.sub_service = SubtitleService()
        self.export_service = ExportService(self.dep_service)

        # Init ViewModels
        self.app_vm = AppViewModel()
        self.extract_vm = ExtractViewModel(self.media_service, self.export_service)
        self.subtitle_vm = SubtitleViewModel(self.sub_service, self.export_service)
        self.create_vm = CreateViewModel(self.export_service)
        self.settings_vm = SettingsViewModel(self.dep_service)

        # Init Views
        self.sidebar = Sidebar(self, on_navigate=self.navigate)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.views = {
            "Extract": ExtractView(self, self.extract_vm),
            "Subtitles": SubtitleView(self, self.subtitle_vm),
            "Create": CreateView(self, self.create_vm),
            "Settings": SettingsView(self, self.settings_vm)
        }

        self.navigate("Extract")

        # Check deps after UI load
        self.after(100, self.check_startup_deps)

    def setup_scaling(self):
        # Primitive detection or fixed for now
        # CTK handles auto-scaling on Windows/macOS often, but Linux can be tricky.
        # "set_widget_scaling"
        try:
             # Basic heuristic for High DPI
             scaling = self._get_window_scaling()
             if scaling > 1.0:
                 ctk.set_widget_scaling(scaling)
        except:
             pass

    def _get_window_scaling(self):
        # On Linux/X11, getting DPI is non-trivial without external libs.
        # We can try to guess from winfo_fpixels('1i'). Standard is 96 (ish).
        # But for now, rely on CTK or user settings.
        # User prompt says: "Ensure the app detects high-DPI screens ... and scales UI elements by 1.25x or 1.5x automatically"
        # Since I can't easily detect reliably in pure python without Xlib, I will rely on `ctk.set_widget_scaling` if I can infer it.
        # Often `tk` scale factor is available.
        try:
            dpi = self.winfo_fpixels('1i')
            if dpi > 110: return 1.5 # ~144dpi
            if dpi > 96: return 1.25 # ~120dpi
        except:
            pass
        return 1.0

    def navigate(self, name):
        self.app_vm.set_view(name)
        self.sidebar.set_active(name)

        # Hide all
        for v in self.views.values():
            v.grid_forget()

        # Show selected
        self.views[name].grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def check_startup_deps(self):
        missing = self.dep_service.get_missing_tools()
        if missing:
             msg = f"Missing tools: {', '.join(missing)}.\n\nPlease install 'mkvtoolnix' and 'ffmpeg' packages via your system package manager.\n\nExample: sudo apt install mkvtoolnix ffmpeg"
             ModalDialog(self, "Missing Dependencies", msg)

if __name__ == "__main__":
    app = App()
    app.mainloop()
