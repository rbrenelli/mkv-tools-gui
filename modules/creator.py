import customtkinter as ctk
from tkinter import messagebox, PanedWindow
from utils import file_dialogs
import os
import shutil
import subprocess
from modules.widgets import TrackListFrame, FileListFrame
from utils import theme

class CreatorFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=10)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Ensure PanedWindow expands!
        
        # Header
        self.header = ctk.CTkLabel(self, text="Create MKV from Video + Subs", 
                                    font=ctk.CTkFont(size=24, weight="bold"))
        self.header.grid(row=0, column=0, padx=10, pady=(10, 15), sticky="w")
 
        # Standard File Selection
        self.video_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.video_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.video_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.video_frame, text="Video File:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(0, 10))
        self.video_entry = ctk.CTkEntry(self.video_frame, height=40)
        self.video_entry.grid(row=0, column=1, padx=0, sticky="ew")
        ctk.CTkButton(self.video_frame, text="Browse", command=self.browse_video, width=100, height=40).grid(row=0, column=2, padx=(10, 0))
 
        # Main content area with PanedWindow for resizability
        self.pane = ctk.CTkFrame(self, fg_color="transparent")
        self.pane.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.pane.grid_columnconfigure(0, weight=1)
        self.pane.grid_rowconfigure(0, weight=1)

        # Style the PanedWindow sash and background
        # Style the PanedWindow sash and background
        
        from tkinter import PanedWindow, Frame
        self.paned_window = PanedWindow(self.pane, orient="vertical", 
                                         sashwidth=6, bg=theme.COLOR_SASH,
                                         sashpad=0, bd=0, opaqueresize=True)
        self.paned_window.grid(row=0, column=0, sticky="nsew")

        # Top Section Wrapper (Dynamic ctk.CTkFrame)
        self.top_wrapper = ctk.CTkFrame(self.paned_window, fg_color=theme.COLOR_BG_MAIN, corner_radius=0)
        self.paned_window.add(self.top_wrapper, minsize=100)

        # Video Tracks Title
        self.video_tracks_title = ctk.CTkLabel(self.top_wrapper, text="Video File Tracks", font=ctk.CTkFont(weight="bold"))
        self.video_tracks_title.pack(padx=10, pady=(5, 5), anchor="w")

        # Top Section: Video Tracks
        self.video_track_list = TrackListFrame(self.top_wrapper)
        self.video_track_list.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        # Bottom Section Wrapper (Dynamic ctk.CTkFrame)
        self.bottom_wrapper = ctk.CTkFrame(self.paned_window, fg_color=theme.COLOR_BG_MAIN, corner_radius=0)
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
                      fg_color="transparent", border_width=1, hover_color=theme.COLOR_BTN_CLEAR_HOVER,
                      text_color=theme.COLOR_BTN_CLEAR_TEXT, height=35).pack(side="left")

        # Subtitle Title
        self.sub_title = ctk.CTkLabel(self.sub_container, text="Subtitles to Add", font=ctk.CTkFont(weight="bold"))
        self.sub_title.grid(row=1, column=0, padx=10, pady=(5, 5), sticky="w")

        # Subtitle List
        self.sub_list_frame = FileListFrame(self.sub_container)
        self.sub_list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Action Buttons
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=6, column=0, padx=10, pady=(10, 20), sticky="ew")
        
        self.create_btn = ctk.CTkButton(self.action_frame, text="Create MKV", command=self.create_mkv, 
                                         state="disabled", height=45, font=ctk.CTkFont(size=14, weight="bold"))
        self.create_btn.pack(side="right")

        self.video_path = None
        self.sub_files = []
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

    def browse_video(self):
        file_path = file_dialogs.select_file("Select Video File", filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv"), ("All Files", "*.*")])
        if file_path:
            self.video_path = file_path
            self.video_entry.delete(0, "end")
            self.video_entry.insert(0, file_path)
            self.video_track_list.load_tracks(file_path)
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
        
        # Auto-fill logic
        detected_lang = self.detect_language(path)
        initial_lang = detected_lang if detected_lang else self.languages[0]
        row_data["lang_var"].set(initial_lang)
        
        default_name = initial_lang.split("(")[1].replace(")", "")
        row_data["name_var"].set(default_name)
        
        is_default = (initial_lang.split(" ")[0] == "eng")
        row_data["default_var"].set(is_default)
        
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
        if self.video_path:
            self.create_btn.configure(state="normal")
        else:
            self.create_btn.configure(state="disabled")

    def create_mkv(self):
        if not self.video_path:
            return

        output_path = file_dialogs.save_file(
            title="Save New MKV",
            defaultextension=".mkv", 
            filetypes=[("MKV Files", "*.mkv")],
            initialfile=os.path.splitext(os.path.basename(self.video_path))[0] + ".mkv"
        )
        if not output_path:
            return

        mkvmerge = shutil.which("mkvmerge")
        if not mkvmerge:
            messagebox.showerror("Error", "mkvmerge not found.")
            return

        cmd = [mkvmerge, "-o", output_path]
        
        # Video File Options
        keep_map, track_opts = self.video_track_list.get_options()
        
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
        cmd.append(self.video_path)
        
        # External Subs
        for item in self.sub_files:
            lang_code = item["lang_var"].get().split(" ")[0]
            track_name = item["name_var"].get()
            sub_path = item["path"]
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
                    # Success but with warnings - show them to the user
                    # These are typically from file content issues (e.g., subtitle timestamps)
                    warn_msg = f"MKV created successfully at:\n{output_path}\n\n"
                    warn_msg += "mkvmerge reported warnings about your input files:\n\n"
                    warn_msg += result.stdout
                    messagebox.showwarning("Success with Warnings", warn_msg)
                else:
                    messagebox.showinfo("Success", f"MKV created successfully:\n{output_path}")
            else:
                # mkvmerge may output to stdout even on error, or just be useful context
                err_msg = f"Stderr:\n{result.stderr}\n\nStdout:\n{result.stdout}"
                messagebox.showerror("Error", f"mkvmerge failed:\n{err_msg}")
        except Exception as e:
            messagebox.showerror("Error", f"Exception: {e}")
