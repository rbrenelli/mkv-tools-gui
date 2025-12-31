import customtkinter as ctk
from tkinter import messagebox
from utils import file_dialogs
import os
import subprocess
from utils.mkv_wrapper import get_mkv_info, extract_tracks
from utils.ffmpeg_wrapper import get_ffmpeg_info, extract_stream_cmd
from modules.widgets import TrackListFrame
from utils import theme

class ExtractorFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=10, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=0) # Tracks Label - don't expand
        self.grid_rowconfigure(3, weight=1) # Track List - expand

        # Header
        self.header = ctk.CTkLabel(self, text="Extract Tracks", 
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
        self.tracks_label = ctk.CTkLabel(self, text="Available Tracks", font=ctk.CTkFont(weight="bold"))
        self.tracks_label.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")

        # Track List
        self.track_list = TrackListFrame(self, extract_mode=True, default_checked=False)
        self.track_list.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # Selection Buttons
        self.sel_btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.sel_btn_frame.grid(row=4, column=0, padx=10, pady=(0, 5), sticky="w")
        
        ctk.CTkButton(self.sel_btn_frame, text="Select All", width=100, height=28, 
                      command=lambda: self.track_list.select_all()).pack(side="left", padx=(0, 10))
        ctk.CTkButton(self.sel_btn_frame, text="Deselect All", width=100, height=28, 
                      command=lambda: self.track_list.deselect_all()).pack(side="left")

        # Action Buttons
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=5, column=0, padx=10, pady=(10, 20), sticky="ew")
        
        self.extract_btn = ctk.CTkButton(self.action_frame, text="Extract Selected Tracks", command=self.extract_tracks, 
                                          state="disabled", height=45, font=ctk.CTkFont(size=14, weight="bold"))
        self.extract_btn.pack(side="right")
        self.tracks = []
        self.check_vars = {} # map track_id -> checkbox_var

    def browse_file(self):
        file_path = file_dialogs.select_file("Select Video File", filetypes=file_dialogs.VIDEO_FILE_TYPES)
        if file_path:
            self.mkv_path = file_path
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            self.load_tracks()

    def load_tracks(self):
        self.tracks = [] # Kept for internal reference if needed, but TrackListFrame handles display
        if self.mkv_path:
            self.track_list.load_tracks(self.mkv_path)
            # We also need to get the raw tracks for our internal mapping logic later
            # Ideally TrackListFrame exposes raw tracks, but we can also re-fetch or make it public.
            # For now, let's just let TrackListFrame handle the UI.
            # But wait, extract_tracks needs the track object to determine extension.
            # So we should fetch info here too or ask TrackListFrame.
            if self.mkv_path.lower().endswith('.mkv'):
                info = get_mkv_info(self.mkv_path)
            else:
                info = get_ffmpeg_info(self.mkv_path)

            if info:
                self.tracks = info.get("tracks", [])
                
        self.extract_btn.configure(state="normal")

    def extract_tracks(self):
        selected_ids = self.track_list.get_selected_ids()
        if not selected_ids:
            messagebox.showwarning("Warning", "No tracks selected.")
            return

        output_dir = file_dialogs.select_directory(title="Select Output Directory")
        if not output_dir:
            return

        track_map = {}
        base_name = os.path.splitext(os.path.basename(self.mkv_path))[0]
        
        # Keep track of generated filenames to handle duplicates
        used_filenames = set()

        # Sort selected_ids to ensure deterministic order (usually track order)
        for tid in sorted(selected_ids):
            # Find track info
            track = next((t for t in self.tracks if t["id"] == tid), None)
            if not track: 
                continue

            props = track.get("properties", {})
            codec = props.get("codec_id", "")
            lang = props.get("language", "und")
            name = props.get("track_name", "")
            
            # Determine extension
            ext = ".dat"
            if "SSA" in codec or "ASS" in codec: ext = ".ass"
            elif "SRT" in codec or "UTF8" in codec: ext = ".srt"
            elif "PGS" in codec: ext = ".sup"
            elif "VOBSUB" in codec: ext = ".sub"
            elif "AAC" in codec: ext = ".aac"
            elif "AC3" in codec: ext = ".ac3"
            elif "AVC" in codec or "H264" in codec: ext = ".h264"
            elif "HEVC" in codec or "H265" in codec: ext = ".h265"
            
            # Build filename parts
            parts = [base_name]
            
            # 1. Language Code
            if lang and lang != "und":
                parts.append(lang)
            
            # 2. Track Name (Sanitized)
            if name:
                # Allow alphanumeric, spaces, dots, underscores, dashes
                safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '.', '_', '-')).strip()
                if safe_name:
                    parts.append(safe_name)
                    
            current_base = ".".join(parts)
            out_name = current_base + ext
            
            # 3. Duplicate Handling
            counter = 1
            while out_name in used_filenames:
                # Append counter before extension
                out_name = f"{current_base}_{counter}{ext}"
                counter += 1
            
            used_filenames.add(out_name)
            track_map[tid] = os.path.join(output_dir, out_name)

        if self.mkv_path.lower().endswith('.mkv'):
            success, msg = extract_tracks(self.mkv_path, track_map)
            if success:
                messagebox.showinfo("Success", "Tracks extracted successfully.")
            else:
                messagebox.showerror("Error", f"Extraction failed:\n{msg}")
        else:
            # Non-MKV extraction using ffmpeg
            errors = []
            for tid, output_path in track_map.items():
                cmd = extract_stream_cmd(self.mkv_path, tid, output_path)
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                    if result.returncode != 0:
                        errors.append(f"Track {tid}: {result.stderr}")
                except Exception as e:
                    errors.append(f"Track {tid}: {str(e)}")

            if not errors:
                messagebox.showinfo("Success", "Tracks extracted successfully.")
            else:
                messagebox.showerror("Error", f"Extraction failed for some tracks:\n" + "\n".join(errors))
