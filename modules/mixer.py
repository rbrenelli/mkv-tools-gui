import customtkinter as ctk
from tkinter import messagebox
from utils import file_dialogs
import os
import shutil
import tempfile
import subprocess
from tkinter import PanedWindow
from modules.widgets import TrackListFrame, FileListFrame

class MixerFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=10)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Ensure PanedWindow expands!

        # Header
        self.header = ctk.CTkLabel(self, text="Add Subtitles (Batch)", 
                                    font=ctk.CTkFont(size=24, weight="bold"))
        self.header.grid(row=0, column=0, padx=10, pady=(10, 15), sticky="w")

        # Standard File Selection
        self.mkv_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.mkv_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.mkv_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.mkv_frame, text="Source MKV:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(0, 10))
        self.mkv_entry = ctk.CTkEntry(self.mkv_frame, height=40)
        self.mkv_entry.grid(row=0, column=1, padx=0, sticky="ew")
        ctk.CTkButton(self.mkv_frame, text="Browse", command=self.browse_mkv, width=100, height=40).grid(row=0, column=2, padx=(10, 0))
 
        # Main content area with PanedWindow for resizability
        self.pane = ctk.CTkFrame(self, fg_color="transparent")
        self.pane.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.pane.grid_columnconfigure(0, weight=1)
        self.pane.grid_rowconfigure(0, weight=1)

        # Style the PanedWindow sash and background
        sash_color = "#3b82f6" # Accent blue for visibility
        
        from tkinter import PanedWindow, Frame
        self.paned_window = PanedWindow(self.pane, orient="vertical", 
                                         sashwidth=6, bg=sash_color, 
                                         sashpad=0, bd=0, opaqueresize=True)
        self.paned_window.grid(row=0, column=0, sticky="nsew")

        # Top Section Wrapper (Dynamic ctk.CTkFrame)
        # We use a tuple color to ensure it switches automatically between light/dark
        self.top_wrapper = ctk.CTkFrame(self.paned_window, fg_color=("#f9fafb", "#111827"), corner_radius=0)
        self.paned_window.add(self.top_wrapper, minsize=100)
        
        # Top Section: Base MKV Tracks
        self.base_tracks_title = ctk.CTkLabel(self.top_wrapper, text="Original MKV Tracks", font=ctk.CTkFont(weight="bold"))
        self.base_tracks_title.pack(padx=10, pady=(5, 5), anchor="w")
        
        self.base_track_list = TrackListFrame(self.top_wrapper)
        self.base_track_list.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        # Bottom Section Wrapper (Dynamic ctk.CTkFrame)
        self.bottom_wrapper = ctk.CTkFrame(self.paned_window, fg_color=("#f9fafb", "#111827"), corner_radius=0)
        self.paned_window.add(self.bottom_wrapper, minsize=150)

        # Bottom Section Content
        self.sub_container = ctk.CTkFrame(self.bottom_wrapper, fg_color="transparent")
        self.sub_container.pack(fill="both", expand=True)
        self.sub_container.grid_columnconfigure(0, weight=1)
        self.sub_container.grid_rowconfigure(2, weight=1)

        # Subtitle Controls
        self.sub_controls = ctk.CTkFrame(self.sub_container, fg_color="transparent")
        self.sub_controls.grid(row=0, column=0, pady=(10, 5), sticky="ew", padx=10)
        
        ctk.CTkButton(self.sub_controls, text="Add Subtitle Files", command=self.add_subs, height=35).pack(side="left", padx=(0, 10))
        ctk.CTkButton(self.sub_controls, text="Clear List", command=self.clear_subs,
                      fg_color="transparent", border_width=1, hover_color=["#fee2e2", "#450a0a"], 
                      text_color=["#ef4444", "#f87171"], height=35).pack(side="left")

        # Subtitle Title
        self.sub_title = ctk.CTkLabel(self.sub_container, text="Subtitles to Add", font=ctk.CTkFont(weight="bold"))
        self.sub_title.grid(row=1, column=0, padx=10, pady=(5, 5), sticky="w")

        # Subtitle List
        self.sub_list_frame = FileListFrame(self.sub_container)
        self.sub_list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Action Buttons
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=6, column=0, padx=10, pady=(10, 20), sticky="ew")
        
        self.process_btn = ctk.CTkButton(self.action_frame, text="Process & Save", command=self.process, 
                                          state="disabled", height=45, font=ctk.CTkFont(size=14, weight="bold"))
        self.process_btn.pack(side="right")

        self.mkv_path = None
        self.sub_files = [] # List of dicts: {path, lang_var, name_var}
        
        self.languages = [
            "eng (English)", "spa (Spanish)", "por (Portuguese)", "fra (French)", 
            "deu (German)", "ita (Italian)", "jpn (Japanese)", "chi (Chinese)", 
            "rus (Russian)", "kor (Korean)", "ara (Arabic)", "hin (Hindi)"
        ]

        self.LANG_MAP = {
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

    def browse_mkv(self):
        file_path = file_dialogs.select_file("Select MKV File", filetypes=[("MKV Files", "*.mkv")])
        if file_path:
            self.mkv_path = file_path
            self.mkv_entry.delete(0, "end")
            self.mkv_entry.insert(0, file_path)
            self.base_track_list.load_tracks(file_path)
            self.check_ready()

    def add_subs(self):
        file_paths = file_dialogs.select_files("Select Subtitle Files", filetypes=[("Subtitle Files", "*.srt *.ass *.ssa *.sub")])
        if file_paths:
            for p in file_paths:
                self.add_sub_row(p)
            self.check_ready()

    def detect_language(self, filename):
        import re
        basename = os.path.splitext(os.path.basename(filename))[0]
        parts = re.split(r'[._\-\s]+', basename)
        
        for part in reversed(parts):
            lower_part = part.lower()
            if lower_part in self.LANG_MAP:
                target_code = self.LANG_MAP[lower_part]
                for lang_str in self.languages:
                    if lang_str.startswith(target_code + " "):
                        return lang_str
        return None

    def add_sub_row(self, path):
        def on_default_click(var):
            if var.get():
                for s in self.sub_files:
                     if s["default_var"] != var:
                         s["default_var"].set(False)

        row_data = self.sub_list_frame.add_file_row(path, on_default_click)
        
        # Auto-fill logic (preserving existing behavior)
        detected_lang = self.detect_language(path)
        initial_lang = detected_lang if detected_lang else self.languages[0]
        row_data["lang_var"].set(initial_lang)
        
        default_name = initial_lang.split("(")[1].replace(")", "")
        row_data["name_var"].set(default_name)
        
        is_default = (initial_lang.split(" ")[0] == "eng")
        row_data["default_var"].set(is_default)
        
        # Add callback for language change updating name
        def update_name(choice):
            lang_name = choice.split("(")[1].replace(")", "")
            row_data["name_var"].set(lang_name)
        row_data["lang_menu"].configure(command=update_name)
        
        self.sub_files.append(row_data)

    def clear_subs(self):
        self.sub_list_frame.clear()
        self.sub_files = []
        self.check_ready()

    def check_ready(self):
        if self.mkv_path and self.sub_files:
            self.process_btn.configure(state="normal")
        else:
            self.process_btn.configure(state="disabled")

    def process(self):
        if not self.mkv_path or not self.sub_files:
            return

        output_path = file_dialogs.save_file(
            title="Save Muxed MKV",
            defaultextension=".mkv", 
            filetypes=[("MKV Files", "*.mkv")],
            initialfile=os.path.splitext(os.path.basename(self.mkv_path))[0] + "_muxed.mkv"
        )
        if not output_path:
            return

        mkvmerge = shutil.which("mkvmerge")
        if not mkvmerge:
            messagebox.showerror("Error", "mkvmerge not found.")
            return

        cmd = [mkvmerge, "-o", output_path]
        
        # Base MKV options from TrackListFrame
        keep_map, track_opts = self.base_track_list.get_options()
        
        if keep_map['video']:
            cmd.extend(["--video-tracks", ",".join(keep_map['video'])])
        else:
            cmd.append("--no-video")
            
        if keep_map['audio']:
            cmd.extend(["--audio-tracks", ",".join(keep_map['audio'])])
        else:
            cmd.append("--no-audio")
            
        if keep_map['subtitles']:
            cmd.extend(["--subtitle-tracks", ",".join(keep_map['subtitles'])])
        else:
            cmd.append("--no-subtitles")
        
        cmd.extend(track_opts)
        cmd.append(self.mkv_path)
        
        for item in self.sub_files:
            lang_code = item["lang_var"].get().split(" ")[0]
            track_name = item["name_var"].get()
            sub_path = item["path"]
            
            # Add options for the NEXT file (the subtitle file)
            is_def = "1" if item["default_var"].get() else "0"
            cmd.extend(["--language", f"0:{lang_code}"])
            if track_name:
                cmd.extend(["--track-name", f"0:{track_name}"])
            cmd.extend(["--default-track-flag", f"0:{is_def}"])
            cmd.extend(["--forced-display-flag", "0:0"])
            
            cmd.append(sub_path)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode <= 1:
                if result.returncode == 1:
                    warn_msg = f"File saved successfully at:\n{output_path}\n\n"
                    warn_msg += "mkvmerge reported warnings about your input files:\n\n"
                    warn_msg += result.stdout
                    messagebox.showwarning("Success with Warnings", warn_msg)
                else:
                    messagebox.showinfo("Success", f"File saved to:\n{output_path}")
            else:
                err_msg = f"Stderr:\n{result.stderr}\n\nStdout:\n{result.stdout}"
                messagebox.showerror("Error", f"mkvmerge failed:\n{err_msg}")
        except Exception as e:
            messagebox.showerror("Error", f"Exception: {e}")
