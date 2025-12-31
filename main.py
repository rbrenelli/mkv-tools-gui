import customtkinter as ctk
import os
import sys
import tkinter as tk
import threading
from modules.extractor import ExtractorFrame
from modules.mixer import MixerFrame
from modules.editor import EditorFrame
from modules.creator import CreatorFrame
from utils import theme
from utils.dependency_manager import DependencyManager

class MKVToolSuite(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Detect scaling before drawing widgets
        self.detect_scaling()

        self.title("MKV Tool Suite")
        self.geometry("1100x700")

        # Set appearance and default theme
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Configure root grid for expansion
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.configure(fg_color=theme.COLOR_BG_MAIN)

        # Create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, 
                                           fg_color=theme.COLOR_BG_SIDEBAR, border_width=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="MKV Tool Suite", 
                                        font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(40, 30))

        # Nav Buttons
        btn_opts = {"height": 45, "font": ctk.CTkFont(size=14), "fg_color": "transparent", 
                    "text_color": theme.COLOR_BTN_TEXT, "hover_color": theme.COLOR_BTN_HOVER,
                    "anchor": "w", "corner_radius": 8}

        self.sidebar_button_extractor = ctk.CTkButton(self.sidebar_frame, text="  Extract Tracks", 
                                                       command=self.sidebar_button_event_extractor, **btn_opts)
        self.sidebar_button_extractor.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        self.sidebar_button_mixer = ctk.CTkButton(self.sidebar_frame, text="  Add Subtitles",
                                                   command=self.sidebar_button_event_mixer, **btn_opts)
        self.sidebar_button_mixer.grid(row=2, column=0, padx=15, pady=5, sticky="ew")

        self.sidebar_button_editor = ctk.CTkButton(self.sidebar_frame, text="  Edit Tracks",
                                                    command=self.sidebar_button_event_editor, **btn_opts)
        self.sidebar_button_editor.grid(row=3, column=0, padx=15, pady=5, sticky="ew")

        self.sidebar_button_creator = ctk.CTkButton(self.sidebar_frame, text="  Create MKV",
                                                     command=self.sidebar_button_event_creator, **btn_opts)
        self.sidebar_button_creator.grid(row=4, column=0, padx=15, pady=5, sticky="ew")

        # Appearance Mode
        self.appearance_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.appearance_frame.grid(row=6, column=0, padx=20, pady=(10, 30), sticky="ew")
        
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.appearance_frame, values=["Light", "Dark", "System"],
                                                               command=self.change_appearance_mode_event,
                                                               fg_color=theme.COLOR_APPEARANCE_FG,
                                                               button_color=theme.COLOR_APPEARANCE_BTN,
                                                               button_hover_color=theme.COLOR_APPEARANCE_BTN_HOVER,
                                                               text_color=theme.COLOR_APPEARANCE_TEXT,
                                                               width=180)
        self.appearance_mode_optionemenu.pack(pady=10)
        self.appearance_mode_optionemenu.set(ctk.get_appearance_mode())

        # Create frames for each module
        # Pass background color to modules if needed, but transparent is better
        self.extractor_frame = ExtractorFrame(self)
        self.mixer_frame = MixerFrame(self)
        self.editor_frame = EditorFrame(self)
        self.creator_frame = CreatorFrame(self)

        # Ensure all frames are transparent to show root background
        for frame in [self.extractor_frame, self.mixer_frame, self.editor_frame, self.creator_frame]:
            frame.configure(fg_color="transparent")

        # Select default frame
        self.select_frame_by_name("extractor")

        # Check dependencies
        self.check_dependencies_on_startup()

    def check_dependencies_on_startup(self):
        dm = DependencyManager()
        if dm.check_missing_dependencies():
            # Create a Toplevel window
            self.setup_window = ctk.CTkToplevel(self)
            self.setup_window.title("First Run Setup")
            self.setup_window.geometry("400x150")

            # Center the window
            self.update_idletasks()
            width = self.setup_window.winfo_width()
            height = self.setup_window.winfo_height()
            x = (self.winfo_screenwidth() // 2) - (width // 2)
            y = (self.winfo_screenheight() // 2) - (height // 2)
            self.setup_window.geometry(f"{width}x{height}+{x}+{y}")

            # Make it modal-like
            self.setup_window.transient(self)
            self.setup_window.grab_set()

            self.setup_label = ctk.CTkLabel(self.setup_window, text="Downloading required tools (FFmpeg, MKVToolNix)...", wraplength=350)
            self.setup_label.pack(pady=20)

            self.setup_progress = ctk.CTkProgressBar(self.setup_window, width=300)
            self.setup_progress.pack(pady=10)
            self.setup_progress.set(0)

            def update_ui(current, total, message):
                # Schedule UI update on main thread
                self.after(0, lambda: self._update_progress_ui(current, total, message))

            def download_task():
                dm.download_dependencies(update_ui)
                # Close window when done
                self.after(0, self.setup_window.destroy)

            threading.Thread(target=download_task, daemon=True).start()

    def _update_progress_ui(self, current, total, message):
        if hasattr(self, 'setup_progress') and self.setup_progress.winfo_exists():
            progress = current / total if total > 0 else 0
            self.setup_progress.set(progress)

        if hasattr(self, 'setup_label') and self.setup_label.winfo_exists():
            self.setup_label.configure(text=message)

    def detect_scaling(self):
        try:
            # Create a dummy window to get DPI if needed, but self (ctk.CTk) is already a window
            # 1 inch = 96 pixels typically on standard screen
            # self.winfo_fpixels('1i') returns pixels per inch
            dpi = self.winfo_fpixels('1i')
            scale_factor = dpi / 96.0

            # Ensure scale factor is reasonable
            if scale_factor < 1.0:
                scale_factor = 1.0

            ctk.set_widget_scaling(scale_factor)
            ctk.set_window_scaling(scale_factor)
        except Exception as e:
            # Fallback or just ignore scaling issues on some platforms
            print(f"DPI scaling detection failed: {e}")

    def select_frame_by_name(self, name):
        # set button color for selected button
        for btn, n in [(self.sidebar_button_extractor, "extractor"), 
                      (self.sidebar_button_mixer, "mixer"), 
                      (self.sidebar_button_editor, "editor"), 
                      (self.sidebar_button_creator, "creator")]:
            if n == name:
                btn.configure(fg_color=theme.COLOR_ACCENT, text_color="white", hover_color=theme.COLOR_HOVER)
            else:
                btn.configure(fg_color="transparent", text_color=theme.COLOR_BTN_TEXT, hover_color=theme.COLOR_BTN_HOVER)

        # show selected frame
        frames = {
            "extractor": self.extractor_frame,
            "mixer": self.mixer_frame,
            "editor": self.editor_frame,
            "creator": self.creator_frame
        }
        
        for n, frame in frames.items():
            if n == name:
                frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=(20, 10))
            else:
                frame.grid_forget()

    def sidebar_button_event_extractor(self):
        self.select_frame_by_name("extractor")

    def sidebar_button_event_mixer(self):
        self.select_frame_by_name("mixer")

    def sidebar_button_event_editor(self):
        self.select_frame_by_name("editor")

    def sidebar_button_event_creator(self):
        self.select_frame_by_name("creator")

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

if __name__ == "__main__":
    app = MKVToolSuite()
    app.mainloop()
