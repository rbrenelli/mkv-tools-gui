import customtkinter as ctk
from tkinter import messagebox
from utils import file_dialogs
import os
import shutil
import subprocess
from utils.mkv_wrapper import get_mkv_info
from modules.widgets import TrackListFrame
from utils import theme

class EditorFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=10, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=0) # Existing Tracks Label - don't expand
        self.grid_rowconfigure(3, weight=1) # Track List - expand

        # Header
        self.header = ctk.CTkLabel(self, text="Edit MKV Tracks", 
                                    font=ctk.CTkFont(size=24, weight="bold"))
        self.header.grid(row=0, column=0, padx=10, pady=(10, 15), sticky="w")

        # Standard File Selection
        self.file_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.file_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.file_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.file_frame, text="Source MKV:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(0, 10))
        self.file_entry = ctk.CTkEntry(self.file_frame, placeholder_text="Select MKV file...", height=40)
        self.file_entry.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(self.file_frame, text="Browse", command=self.browse_file, width=100, height=40).grid(row=0, column=2, padx=(10, 0))

        # Tracks Label (External)
        self.tracks_label = ctk.CTkLabel(self, text="Existing Tracks", font=ctk.CTkFont(weight="bold"))
        self.tracks_label.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")

        # Track List
        self.track_list = TrackListFrame(self)
        self.track_list.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # Action Buttons
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=4, column=0, padx=10, pady=(10, 20), sticky="ew")
        
        self.save_btn = ctk.CTkButton(self.action_frame, text="Save Changes", command=self.save_changes, 
                                       state="disabled", height=45, font=ctk.CTkFont(size=14, weight="bold"))
        self.save_btn.pack(side="right")

        self.mkv_path = None

    def browse_file(self):
        file_path = file_dialogs.select_file("Select MKV File", filetypes=[("MKV Files", "*.mkv")])
        if file_path:
            self.mkv_path = file_path
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            self.track_list.load_tracks(file_path)
            self.save_btn.configure(state="normal")

    def save_changes(self):
        if not self.mkv_path:
            return

        output_path = file_dialogs.save_file(
            title="Save Edited MKV",
            defaultextension=".mkv", 
            filetypes=[("MKV Files", "*.mkv")],
            initialfile=os.path.splitext(os.path.basename(self.mkv_path))[0] + "_edited.mkv"
        )
        if not output_path:
            return

        mkvmerge = shutil.which("mkvmerge")
        if not mkvmerge:
            messagebox.showerror("Error", "mkvmerge not found.")
            return

        # Get options from widget
        keep_map, track_opts = self.track_list.get_options()
        
        # Build command
        # mkvmerge -o output --audio-tracks 1,2 --video-tracks 0 ... options input
        cmd = [mkvmerge, "-o", output_path]
        
        # Add keep tracks filters
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
            
        # Add track options (names, languages)
        cmd.extend(track_opts)
        
        # Input file
        cmd.append(self.mkv_path)


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
                messagebox.showerror("Error", f"mkvmerge failed:\n{result.stderr}\n\nStdout:\n{result.stdout}")
        except Exception as e:
            messagebox.showerror("Error", f"Exception: {e}")
