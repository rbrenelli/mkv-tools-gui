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

        ctk.CTkLabel(self.file_frame, text="Source Video:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(0, 10))
        self.file_entry = ctk.CTkEntry(self.file_frame, placeholder_text="Select video file...", height=40)
        self.file_entry.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(self.file_frame, text="Browse", command=self.browse_file, width=100, height=40).grid(row=0, column=2, padx=(10, 0))

        # Tracks Label (External)
        self.tracks_label = ctk.CTkLabel(self, text="Available Tracks (Edit output filename in list)", font=ctk.CTkFont(weight="bold"))
        self.tracks_label.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")

        # Track List
        self.track_list = TrackListFrame(self, extract_mode=True, default_checked=False, on_open=self.browse_file)
        self.track_list.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # Selection Buttons
        self.sel_btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.sel_btn_frame.grid(row=4, column=0, padx=10, pady=(0, 5), sticky="w")
        
        ctk.CTkButton(self.sel_btn_frame, text="Select All", width=100, height=28, 
                      command=lambda: self.track_list.select_all()).pack(side="left", padx=(0, 10))
        ctk.CTkButton(self.sel_btn_frame, text="Deselect All", width=100, height=28, 
                      command=lambda: self.track_list.deselect_all()).pack(side="left")

        # Output Directory (Transparency)
        self.out_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.out_frame.grid(row=5, column=0, padx=10, pady=(10, 0), sticky="ew")

        ctk.CTkButton(self.out_frame, text="Select Output Directory", command=self.select_out_dir, width=160).pack(side="left", padx=(0, 10))
        self.out_dir_var = ctk.StringVar(value="Same as Source")
        self.out_dir_lbl = ctk.CTkLabel(self.out_frame, textvariable=self.out_dir_var, text_color="gray")
        self.out_dir_lbl.pack(side="left", padx=5)

        # Action Buttons
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=6, column=0, padx=10, pady=(10, 20), sticky="ew")
        
        self.extract_btn = ctk.CTkButton(self.action_frame, text="Extract Selected Tracks", command=self.extract_tracks, 
                                          state="disabled", height=45, font=ctk.CTkFont(size=14, weight="bold"))
        self.extract_btn.pack(side="right")

        self.video_path = None
        self.selected_out_dir = None

    def browse_file(self):
        file_path = file_dialogs.select_file("Select Video File", filetypes=file_dialogs.VIDEO_FILE_TYPES)
        if file_path:
            self.video_path = file_path
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            self.track_list.load_tracks(file_path)

            # Reset output dir
            self.selected_out_dir = None
            self.out_dir_var.set(os.path.dirname(file_path))

            self.extract_btn.configure(state="normal")

    def select_out_dir(self):
        d = file_dialogs.select_directory("Select Output Directory")
        if d:
            self.selected_out_dir = d
            self.out_dir_var.set(d)

    @staticmethod
    def _get_safe_output_path(output_dir, filename):
        """
        Sanitizes filename to prevent path traversal and joins with output_dir.
        """
        # Sentinel: Prevent path traversal by using basename
        safe_filename = os.path.basename(filename)
        return os.path.join(output_dir, safe_filename)

    def extract_tracks(self):
        # Get mapping from TrackListFrame
        track_map_raw = self.track_list.get_extraction_map()
        if not track_map_raw:
            messagebox.showwarning("Warning", "No tracks selected.")
            return

        # Determine output directory
        output_dir = self.selected_out_dir if self.selected_out_dir else os.path.dirname(self.video_path)

        # Finalize full paths
        final_track_map = {} # id -> full path
        for tid, filename in track_map_raw.items():
            if not filename:
                messagebox.showwarning("Warning", f"Filename missing for Track ID {tid}")
                return
            final_track_map[tid] = self._get_safe_output_path(output_dir, filename)

        if self.video_path.lower().endswith('.mkv'):
            success, msg = extract_tracks(self.video_path, final_track_map)
            if success:
                messagebox.showinfo("Success", f"Tracks extracted to:\n{output_dir}")
            else:
                messagebox.showerror("Error", f"Extraction failed:\n{msg}")
        else:
            # Non-MKV extraction using ffmpeg
            errors = []
            for tid, output_path in final_track_map.items():
                cmd = extract_stream_cmd(self.video_path, tid, output_path)
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                    if result.returncode != 0:
                        errors.append(f"Track {tid}: {result.stderr}")
                except Exception as e:
                    errors.append(f"Track {tid}: {str(e)}")

            if not errors:
                messagebox.showinfo("Success", f"Tracks extracted to:\n{output_dir}")
            else:
                messagebox.showerror("Error", f"Extraction failed for some tracks:\n" + "\n".join(errors))
