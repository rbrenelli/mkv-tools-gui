import customtkinter as ctk
from tkinter import messagebox
from utils import file_dialogs
import os
import shutil
import subprocess
from utils.mkv_wrapper import get_mkv_info
from utils.ffmpeg_wrapper import get_ffmpeg_info
from utils.dependency_manager import DependencyManager
from modules.widgets import TrackListFrame
from utils import theme

class EditorFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=10, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=0) # Existing Tracks Label - don't expand
        self.grid_rowconfigure(3, weight=1) # Track List - expand

        # Header
        self.header = ctk.CTkLabel(self, text="Edit Video Tracks",
                                    font=ctk.CTkFont(size=24, weight="bold"))
        self.header.grid(row=0, column=0, padx=10, pady=(10, 15), sticky="w")

        # Standard File Selection
        self.file_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.file_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.file_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.file_frame, text="Source File:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(0, 10))
        self.file_entry = ctk.CTkEntry(self.file_frame, placeholder_text="Select video file...", height=40)
        self.file_entry.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(self.file_frame, text="Browse", command=self.browse_file, width=100, height=40).grid(row=0, column=2, padx=(10, 0))

        # Tracks Label (External)
        self.tracks_label = ctk.CTkLabel(self, text="Existing Tracks", font=ctk.CTkFont(weight="bold"))
        self.tracks_label.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")

        # Track List
        self.track_list = TrackListFrame(self)
        self.track_list.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # Output Options Frame
        self.out_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.out_frame.grid(row=4, column=0, padx=10, pady=(5, 0), sticky="ew")

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
        self.action_frame.grid(row=5, column=0, padx=10, pady=(10, 20), sticky="ew")
        
        self.save_btn = ctk.CTkButton(self.action_frame, text="Save Changes", command=self.save_changes, 
                                       state="disabled", height=45, font=ctk.CTkFont(size=14, weight="bold"))
        self.save_btn.pack(side="right")

        self.video_path = None

    def browse_file(self):
        file_path = file_dialogs.select_file("Select Video File", filetypes=[("Video Files", "*.mkv *.mp4 *.avi *.mov"), ("All Files", "*.*")])
        if file_path:
            self.video_path = file_path
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            self.track_list.load_tracks(file_path)

            dirname = os.path.dirname(file_path)
            basename = os.path.splitext(os.path.basename(file_path))[0]
            self.out_dir_var.set(dirname)
            self.out_name_var.set(basename + "_edited")

            # Auto-select format based on input
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".mp4": self.out_fmt_var.set("mp4")
            else: self.out_fmt_var.set("mkv")

            self.save_btn.configure(state="normal")

    def select_out_dir(self):
        d = file_dialogs.select_directory("Select Output Directory")
        if d:
            self.out_dir_var.set(d)

    def save_changes(self):
        if not self.video_path: return

        out_fmt = self.out_fmt_var.get()
        out_name = self.out_name_var.get()
        out_dir = self.out_dir_var.get()

        if not out_name or not out_dir:
            messagebox.showwarning("Warning", "Please specify output directory and filename.")
            return

        if not out_name.lower().endswith(f".{out_fmt}"):
            out_name += f".{out_fmt}"

        output_path = os.path.join(out_dir, out_name)

        if out_fmt == "mkv":
            self._save_mkv(output_path)
        else:
            self._save_mp4(output_path)

    def _save_mkv(self, output_path):
        mkvmerge = DependencyManager().get_binary_path("mkvmerge")
        if not mkvmerge:
            messagebox.showerror("Error", "mkvmerge not found.")
            return

        keep_map, track_opts = self.track_list.get_options()
        
        cmd = [mkvmerge, "-o", output_path]
        
        if keep_map['video']: cmd.extend(["--video-tracks", ",".join(keep_map['video'])])
        else: cmd.append("--no-video")
            
        if keep_map['audio']: cmd.extend(["--audio-tracks", ",".join(keep_map['audio'])])
        else: cmd.append("--no-audio")
            
        if keep_map['subtitles']: cmd.extend(["--subtitle-tracks", ",".join(keep_map['subtitles'])])
        else: cmd.append("--no-subtitles")
            
        cmd.extend(track_opts)
        cmd.append(self.video_path)

        self._run_cmd(cmd, "mkvmerge")

    def _save_mp4(self, output_path):
        ffmpeg = DependencyManager().get_binary_path("ffmpeg")
        if not ffmpeg:
            messagebox.showerror("Error", "ffmpeg not found.")
            return

        cmd = [ffmpeg, "-y", "-i", self.video_path]
        keep_map, _ = self.track_list.get_options()

        for vid in keep_map['video']: cmd.extend(["-map", f"0:{vid}"])
        for aid in keep_map['audio']: cmd.extend(["-map", f"0:{aid}"])
        for sid in keep_map['subtitles']: cmd.extend(["-map", f"0:{sid}"])

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
