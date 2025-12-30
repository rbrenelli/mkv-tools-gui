import customtkinter as ctk
import os
import sys
from modules.extractor import ExtractorFrame
from modules.mixer import MixerFrame
from modules.editor import EditorFrame
from modules.creator import CreatorFrame

class MKVToolSuite(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MKV Tool Suite")
        self.geometry("1100x700")

        # Set appearance and default theme
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Configure root grid for expansion
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Define custom colors for premium look
        self.accent_color = "#3b82f6"
        self.hover_color = "#2563eb"
        self.root_bg = ("#f9fafb", "#111827")
        self.sidebar_bg = ("#ffffff", "#1f2937")

        self.configure(fg_color=self.root_bg)

        # Create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, 
                                           fg_color=self.sidebar_bg, border_width=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="MKV Tool Suite", 
                                        font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(40, 30))

        # Nav Buttons
        btn_opts = {"height": 45, "font": ctk.CTkFont(size=14), "fg_color": "transparent", 
                    "text_color": ("gray10", "gray90"), "hover_color": ("gray85", "gray25"), 
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
                                                               fg_color=("gray90", "gray20"),
                                                               button_color=("gray85", "gray25"),
                                                               button_hover_color=("gray80", "gray30"),
                                                               text_color=("gray10", "gray90"),
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

    def select_frame_by_name(self, name):
        # set button color for selected button
        for btn, n in [(self.sidebar_button_extractor, "extractor"), 
                      (self.sidebar_button_mixer, "mixer"), 
                      (self.sidebar_button_editor, "editor"), 
                      (self.sidebar_button_creator, "creator")]:
            if n == name:
                btn.configure(fg_color=self.accent_color, text_color="white", hover_color=self.hover_color)
            else:
                btn.configure(fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray85", "gray25"))

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
    # Enable high-DPI scaling
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
        
    app = MKVToolSuite()
    app.mainloop()
