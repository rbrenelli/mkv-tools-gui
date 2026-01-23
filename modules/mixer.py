import customtkinter as ctk
from tkinter import messagebox
from utils import file_dialogs
import os
import shutil
import tempfile
import subprocess
from tkinter import PanedWindow
from modules.widgets import TrackListFrame, FileListFrame
from utils import theme
from utils.dependency_manager import DependencyManager
from utils.security import sanitize_filename

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
        self.video_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.video_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.video_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.video_frame, text="Source Video:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(0, 10))
        self.video_entry = ctk.CTkEntry(self.video_frame, height=40)
        self.video_entry.grid(row=0, column=1, padx=0, sticky="ew")
        ctk.CTkButton(self.video_frame, text="Browse", command=self.browse_video, width=100, height=40).grid(row=0, column=2, padx=(10, 0))
 
        # Main content area with PanedWindow for resizability
        self.pane = ctk.CTkFrame(self, fg_color="transparent")
        self.pane.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.pane.grid_columnconfigure(0, weight=1)
        self.pane.grid_rowconfigure(0, weight=1)

        from tkinter import PanedWindow
        self.paned_window = PanedWindow(self.pane, orient="vertical", 
                                         sashwidth=6, bg=theme.COLOR_SASH,
                                         sashpad=0, bd=0, opaqueresize=True)
        self.paned_window.grid(row=0, column=0, sticky="nsew")

        # Top Section Wrapper
        self.top_wrapper = ctk.CTkFrame(self.paned_window, fg_color=theme.COLOR_BG_MAIN, corner_radius=0)
        self.paned_window.add(self.top_wrapper, minsize=100)
        
        # Top Section: Base MKV Tracks
        self.base_tracks_title = ctk.CTkLabel(self.top_wrapper, text="Original Video Tracks", font=ctk.CTkFont(weight="bold"))
        self.base_tracks_title.pack(padx=10, pady=(5, 5), anchor="w")
        
        self.base_track_list = TrackListFrame(self.top_wrapper, on_open=self.browse_video)
        self.base_track_list.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        # Bottom Section Wrapper
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

        # Output Options Frame (Transparency)
        self.out_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.out_frame.grid(row=6, column=0, padx=10, pady=(5, 0), sticky="ew")

        # Output Format
        ctk.CTkLabel(self.out_frame, text="Format:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 5))
        self.out_fmt_var = ctk.StringVar(value="mkv")

        self.rb_mkv = ctk.CTkRadioButton(self.out_frame, text="MKV", variable=self.out_fmt_var, value="mkv", width=60)
        self.rb_mkv.pack(side="left", padx=5)
        self.rb_mp4 = ctk.CTkRadioButton(self.out_frame, text="MP4", variable=self.out_fmt_var, value="mp4", width=60)
        self.rb_mp4.pack(side="left", padx=5)

        # Output Filename & Dir
        self.out_name_var = ctk.StringVar()
        self.out_dir_var = ctk.StringVar()

        ctk.CTkLabel(self.out_frame, text="Output Name:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(15, 5))
        self.out_name_entry = ctk.CTkEntry(self.out_frame, textvariable=self.out_name_var, width=200)
        self.out_name_entry.pack(side="left", padx=5)

        ctk.CTkButton(self.out_frame, text="Select Output Dir", command=self.select_out_dir, width=120).pack(side="left", padx=10)
        self.out_dir_lbl = ctk.CTkLabel(self.out_frame, textvariable=self.out_dir_var, text_color="gray")
        self.out_dir_lbl.pack(side="left", padx=5)

        # Action Buttons
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=7, column=0, padx=10, pady=(10, 20), sticky="ew")
        
        self.process_btn = ctk.CTkButton(self.action_frame, text="Process & Save", command=self.process, 
                                          state="disabled", height=45, font=ctk.CTkFont(size=14, weight="bold"))
        self.process_btn.pack(side="right")

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
        file_path = file_dialogs.select_file("Select Video File", filetypes=[("Video Files", "*.mkv *.mp4 *.avi"), ("All Files", "*.*")])
        if file_path:
            self.video_path = file_path
            self.video_entry.delete(0, "end")
            self.video_entry.insert(0, file_path)
            self.base_track_list.load_tracks(file_path)

            # Default Output defaults
            dirname = os.path.dirname(file_path)
            basename = os.path.splitext(os.path.basename(file_path))[0]
            self.out_dir_var.set(dirname)
            self.out_name_var.set(basename + "_muxed")

            self.check_ready()

    def select_out_dir(self):
        d = file_dialogs.select_directory("Select Output Directory")
        if d:
            self.out_dir_var.set(d)

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

        def on_remove(row_data):
            if row_data in self.sub_files:
                self.sub_files.remove(row_data)
            self.check_ready()

        row_data = self.sub_list_frame.add_file_row(path, on_default_click, on_remove=on_remove)
        
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
        if self.video_path and self.sub_files:
            self.process_btn.configure(state="normal")
        else:
            self.process_btn.configure(state="disabled")

    def process(self):
        if not self.video_path or not self.sub_files: return

        out_fmt = self.out_fmt_var.get()
        out_name = self.out_name_var.get()
        out_dir = self.out_dir_var.get()

        if not out_name or not out_dir:
            messagebox.showwarning("Warning", "Please specify output directory and filename.")
            return

        if not out_name.lower().endswith(f".{out_fmt}"):
            out_name += f".{out_fmt}"

        out_name = sanitize_filename(out_name)

        output_path = os.path.join(out_dir, out_name)

        if out_fmt == "mkv":
            self._process_mkv(output_path)
        else:
            self._process_mp4(output_path)

    def _process_mkv(self, output_path):
        mkvmerge = shutil.which("mkvmerge")
        if not mkvmerge:
            messagebox.showerror("Error", "mkvmerge not found.")
            return

        cmd = [mkvmerge, "-o", output_path]
        
        keep_map, track_opts = self.base_track_list.get_options()
        
        if keep_map['video']: cmd.extend(["--video-tracks", ",".join(keep_map['video'])])
        else: cmd.append("--no-video")
            
        if keep_map['audio']: cmd.extend(["--audio-tracks", ",".join(keep_map['audio'])])
        else: cmd.append("--no-audio")
            
        if keep_map['subtitles']: cmd.extend(["--subtitle-tracks", ",".join(keep_map['subtitles'])])
        else: cmd.append("--no-subtitles")
        
        cmd.extend(track_opts)
        cmd.append(self.video_path)
        
        for item in self.sub_files:
            lang_code = item["lang_var"].get().split(" ")[0]
            track_name = item["name_var"].get()
            sub_path = item["path"]
            
            is_def = "1" if item["default_var"].get() else "0"
            cmd.extend(["--language", f"0:{lang_code}"])
            if track_name: cmd.extend(["--track-name", f"0:{track_name}"])
            cmd.extend(["--default-track-flag", f"0:{is_def}"])
            cmd.extend(["--forced-display-flag", "0:0"])
            
            cmd.append(sub_path)

        self._run_cmd(cmd, "mkvmerge")

    def _process_mp4(self, output_path):
        ffmpeg = DependencyManager().get_binary_path("ffmpeg")
        if not ffmpeg:
            messagebox.showerror("Error", "ffmpeg not found.")
            return

        cmd = [ffmpeg, "-y", "-i", self.video_path]

        # Add inputs for external subs
        for item in self.sub_files:
            cmd.extend(["-i", item["path"]])

        keep_map, _ = self.base_track_list.get_options()

        # Map kept tracks
        for vid in keep_map['video']: cmd.extend(["-map", f"0:{vid}"])
        for aid in keep_map['audio']: cmd.extend(["-map", f"0:{aid}"])
        for sid in keep_map['subtitles']: cmd.extend(["-map", f"0:{sid}"])

        # Map External Subtitles
        for i in range(len(self.sub_files)):
            cmd.extend(["-map", f"{i+1}:0"])

        cmd.extend(["-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text"])
        cmd.append(output_path)

        self._run_cmd(cmd, "ffmpeg")

    def _run_cmd(self, cmd, tool_name):
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
            if result.returncode == 0:
                messagebox.showinfo("Success", f"File saved to:\n{cmd[-1] if tool_name == 'ffmpeg' else cmd[2]}")
            elif tool_name == "mkvmerge" and result.returncode == 1:
                messagebox.showwarning("Success with Warnings", f"Warnings:\n{result.stdout}")
            else:
                messagebox.showerror("Error", f"{tool_name} failed:\n{result.stderr}\n{result.stdout}")
        except Exception as e:
            messagebox.showerror("Error", f"Exception: {e}")
