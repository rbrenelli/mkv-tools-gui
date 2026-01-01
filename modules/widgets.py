import customtkinter as ctk
from tkinter import Toplevel
from utils.mkv_wrapper import get_mkv_info
from utils.ffmpeg_wrapper import get_ffmpeg_info
from utils import theme
import os

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return

        try:
            # Position tooltip slightly below and to the right of the cursor/widget
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

            self.tooltip_window = Toplevel(self.widget)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x}+{y}")
            self.tooltip_window.attributes('-topmost', True)

            label = ctk.CTkLabel(self.tooltip_window, text=self.text, corner_radius=6,
                                 fg_color=theme.COLOR_TOOLTIP_BG, text_color=theme.COLOR_TOOLTIP_TEXT,
                                 padx=10, pady=5, font=("Arial", 12))
            label.pack()
        except Exception as e:
            print(f"Error showing tooltip: {e}")

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class TrackListFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, languages=None, extract_mode=False, default_checked=True, **kwargs):
        # Remove label_text from kwargs to move it outside
        kwargs.pop("label_text", None)
        kwargs.pop("label_font", None)
        
        self.extract_mode = extract_mode
        self.default_checked = default_checked

        # Material Design Polish: Give it a surface look
        # Use a slightly lighter/distinct gray for the list background to create "depth"
        # Increased contrast for Light mode (Gray 200 vs Gray 100 was too subtle, now Gray 200 background)
        
        super().__init__(master, label_text="", corner_radius=6, border_width=1, 
                         fg_color=theme.COLOR_BG_LIST, **kwargs)
        self.languages = languages or [
             "eng (English)", "spa (Spanish)", "por (Portuguese)", "fra (French)", 
             "deu (German)", "ita (Italian)", "jpn (Japanese)", "chi (Chinese)", 
             "rus (Russian)", "kor (Korean)", "ara (Arabic)", "hin (Hindi)", "und (Undefined)"
        ]
        self.tracks = []
        self.track_widgets = {} # map tid -> dict of widgets/vars
        self.source_filename = "video" # Default base name for extraction
        self.generated_filenames = set()

        # Bind scroll events
        self._bind_mouse_wheel(self)

    def _bind_mouse_wheel(self, widget):
        """Recursively bind mouse wheel events to a widget and all its children."""
        widget.bind("<MouseWheel>", self._on_mouse_wheel)
        widget.bind("<Button-4>", self._on_mouse_wheel)
        widget.bind("<Button-5>", self._on_mouse_wheel)
        
        for child in widget.winfo_children():
            self._bind_mouse_wheel(child)

    def _on_mouse_wheel(self, event):
        """Propagate mouse wheel events to the canvas."""
        if event.num == 4: # Linux scroll up
            self._parent_canvas.yview_scroll(-1, "units")
        elif event.num == 5: # Linux scroll down
            self._parent_canvas.yview_scroll(1, "units")
        else: # Windows/macOS
            self._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
    def load_tracks(self, file_path):
        # Clear existing
        for widget in self.winfo_children():
            widget.destroy()
        self.track_widgets = {}
        self.tracks = []
        self.generated_filenames = set()

        if not file_path:
            return

        self.source_filename = os.path.splitext(os.path.basename(file_path))[0]

        info = None
        error_msg = None

        try:
            if file_path.lower().endswith('.mkv'):
                print(f"DEBUG: Loading MKV info for: {file_path}")
                info = get_mkv_info(file_path)
                print(f"DEBUG: MKV info loaded, tracks count: {len(info.get('tracks', [])) if info else 'None'}")
            else:
                print(f"DEBUG: Loading FFmpeg info for: {file_path}")
                info = get_ffmpeg_info(file_path)
                # ffmpeg_wrapper might return None on failure currently,
                # or we might want to standardize it later.
                if info is None:
                     error_msg = "Could not read file info (FFmpeg)."
                else:
                    print(f"DEBUG: FFmpeg info loaded, tracks count: {len(info.get('tracks', []))}")
        except Exception as e:
            error_msg = str(e)
            print(f"DEBUG: Exception loading tracks: {error_msg}")

        if error_msg:
            # Display Error
            err_lbl = ctk.CTkLabel(self, text=f"Error: {error_msg}", text_color="red", wraplength=400)
            err_lbl.pack(padx=10, pady=20)
            return

        if not info:
            # If info is None but no exception (shouldn't happen with updated mkv_wrapper but possible with ffmpeg)
            err_lbl = ctk.CTkLabel(self, text="No track information found.", text_color="orange")
            err_lbl.pack(padx=10, pady=20)
            return

        self.tracks = info.get("tracks", [])
        
        if not self.tracks:
            ctk.CTkLabel(self, text="No tracks found in this file.", text_color="gray").pack(padx=10, pady=20)
            return

        for i, track in enumerate(self.tracks):
            tid = track.get("id")
            ttype = track.get("type", "unknown")
            props = track.get("properties", {})
            codec = props.get("codec_id", "Unknown")
            lang = props.get("language", "und")
            name = props.get("track_name", "")
            
            # Row Frame - cleaner look with subtle background
            # Alternating colors: lighter/darker stripes
            stripe_color = theme.COLOR_LIST_STRIPE_EVEN if i % 2 == 0 else theme.COLOR_LIST_STRIPE_ODD
            
            row = ctk.CTkFrame(self, fg_color=stripe_color, corner_radius=4)
            row.pack(fill="x", padx=5, pady=2)
            
            # Keep Checkbox
            keep_var = ctk.BooleanVar(value=self.default_checked)
            chk = ctk.CTkCheckBox(row, text="", variable=keep_var, width=20)
            chk.pack(side="left", padx=(10, 5))
            
            if self.extract_mode:
                # -- EXTRACT MODE: Info + Output Filename --
                # Format: [TYPE] ID:x | Codec | Lang | Name -> Output Name Entry

                info_text = f"[{ttype.upper()}] ID:{tid} | {codec} | {lang}"
                if name:
                    info_text += f" | {name}"
                    
                ctk.CTkLabel(row, text=info_text, anchor="w", font=ctk.CTkFont(size=12), width=250).pack(side="left", padx=5)

                # Generate default output filename with duplicate handling
                default_out_name = self._generate_default_filename(track)
                out_name_var = ctk.StringVar(value=default_out_name)
                
                ctk.CTkLabel(row, text="Output:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=5)
                out_name_entry = ctk.CTkEntry(row, textvariable=out_name_var, height=28, placeholder_text="Output Filename")
                out_name_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=2)

                # Store minimal data
                self.track_widgets[tid] = {
                    "keep_var": keep_var,
                    "type": ttype,
                    "out_name_var": out_name_var
                }
            else:
                # -- EDIT MODE: Full controls --
                
                # Info Label (Compact)
                info_text = f"[{ttype.upper()}] ID:{tid} ({lang})"
                ctk.CTkLabel(row, text=info_text, width=160, anchor="w", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)

                # Default Checkbox
                is_default = (lang == "eng")
                default_var = ctk.BooleanVar(value=is_default)
                
                def on_default_click(var=default_var, type_chk=ttype):
                    if var.get():
                         for t_id, t_data in self.track_widgets.items():
                             if t_data.get("type") == type_chk and t_data.get("default_var") != var:
                                 t_data["default_var"].set(False)

                def_chk = ctk.CTkCheckBox(row, text="Default", variable=default_var, command=on_default_click, width=70)
                def_chk.pack(side="left", padx=10)
                
                # Language Dropdown
                current_lang_str = self.languages[-1]
                for l in self.languages:
                    code = l.split(" ")[0]
                    if code == lang:
                        current_lang_str = l
                        break
                
                lang_var = ctk.StringVar(value=current_lang_str)
                lang_menu = ctk.CTkOptionMenu(row, values=self.languages, variable=lang_var, width=140, height=28)
                lang_menu.pack(side="left", padx=10)
                
                # Name Entry
                name_var = ctk.StringVar(value=name)
                name_entry = ctk.CTkEntry(row, textvariable=name_var, height=28, placeholder_text="Track Title")
                name_entry.pack(side="left", fill="x", expand=True, padx=(10, 15), pady=5)
                
                self.track_widgets[tid] = {
                    "keep_var": keep_var,
                    "lang_var": lang_var,
                    "name_var": name_var,
                    "default_var": default_var,
                    "type": ttype
                }
            
            # Ensure new widgets are scrollable
            self._bind_mouse_wheel(row)

    def _generate_default_filename(self, track):
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

        parts = [self.source_filename]

        if lang and lang != "und":
            parts.append(lang)

        if name:
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '.', '_', '-')).strip()
            if safe_name:
                parts.append(safe_name)

        base_name = ".".join(parts)
        out_name = base_name + ext

        # Unique handling
        counter = 1
        while out_name in self.generated_filenames:
            out_name = f"{base_name}_{counter}{ext}"
            counter += 1

        self.generated_filenames.add(out_name)
        return out_name

    def select_all(self):
        for data in self.track_widgets.values():
            data["keep_var"].set(True)

    def deselect_all(self):
        for data in self.track_widgets.values():
            data["keep_var"].set(False)

    def get_selected_ids(self):
        """Returns a list of track IDs (int) that are checked."""
        selected = []
        for tid, data in self.track_widgets.items():
            if data["keep_var"].get():
                selected.append(tid)
        return selected

    def get_extraction_map(self):
        """
        For Extract Mode.
        Returns a dictionary: {track_id: output_filename} for selected tracks.
        """
        if not self.extract_mode:
            return {}

        mapping = {}
        for tid, data in self.track_widgets.items():
            if data["keep_var"].get():
                mapping[tid] = data["out_name_var"].get()
        return mapping

    def get_options(self):
        """
        Returns a tuple: (keep_track_ids, track_opts)
        keep_track_ids: dict like {'video': [0], 'audio': [1,2], 'subtitles': [3]}
        track_opts: list of strings for mkvmerge command (e.g. --language 0:eng)
        """
        keep_map = {'video': [], 'audio': [], 'subtitles': []}
        opts = []
        
        for tid, data in self.track_widgets.items():
            if data["keep_var"].get():
                ttype = data["type"].lower()
                
                if "video" in ttype:
                    keep_map['video'].append(str(tid))
                elif "audio" in ttype:
                    keep_map['audio'].append(str(tid))
                elif "subtitles" in ttype:
                    keep_map['subtitles'].append(str(tid))
                
                # Language change
                code = data["lang_var"].get().split(" ")[0]
                opts.extend(["--language", f"{tid}:{code}"])
                
                # Name change
                name = data["name_var"].get()
                opts.extend(["--track-name", f"{tid}:{name}"])

                # Default & Forced
                is_def = "1" if data["default_var"].get() else "0"
                opts.extend(["--default-track-flag", f"{tid}:{is_def}"])
                opts.extend(["--forced-display-flag", f"{tid}:0"])
            else:
                pass
                
        return keep_map, opts

class FileListFrame(ctk.CTkScrollableFrame):
    """
    A unified list for adding external files (subtitles, etc.)
    Mimics the visual style of TrackListFrame (alternating rows, background).
    """
    def __init__(self, master, languages=None, **kwargs):
        kwargs.pop("label_text", None)
        # Unified background: Gray 200 / Gray 800
        super().__init__(master, label_text="", corner_radius=6, border_width=1, 
                         fg_color=theme.COLOR_BG_LIST, **kwargs)
        
        self.languages = languages or [
             "eng (English)", "spa (Spanish)", "por (Portuguese)", "fra (French)", 
             "deu (German)", "ita (Italian)", "jpn (Japanese)", "chi (Chinese)", 
             "rus (Russian)", "kor (Korean)", "ara (Arabic)", "hin (Hindi)", "und (Undefined)"
        ]
        self.rows = []
        self._bind_mouse_wheel(self)

    def _bind_mouse_wheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mouse_wheel)
        widget.bind("<Button-4>", self._on_mouse_wheel)
        widget.bind("<Button-5>", self._on_mouse_wheel)
        for child in widget.winfo_children():
            self._bind_mouse_wheel(child)

    def _on_mouse_wheel(self, event):
        if event.num == 4: self._parent_canvas.yview_scroll(-1, "units")
        elif event.num == 5: self._parent_canvas.yview_scroll(1, "units")
        else: self._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def add_file_row(self, path, on_default_click_msg):
        """
        Adds a row for a subtitle file.
        on_default_click_msg: callback when 'default' box is clicked.
        Returns a dict of widget variables.
        """
        import os
        
        i = len(self.rows)
        stripe_color = theme.COLOR_LIST_STRIPE_EVEN if i % 2 == 0 else theme.COLOR_LIST_STRIPE_ODD
        
        row = ctk.CTkFrame(self, fg_color=stripe_color, corner_radius=4)
        row.pack(fill="x", padx=5, pady=2)
        
        self._bind_mouse_wheel(row)
        
        # Filename label
        lbl = ctk.CTkLabel(row, text=os.path.basename(path), width=200, anchor="w")
        lbl.pack(side="left", padx=5)
        
        # Language detection (simple)
        initial_lang = self.languages[0]
        
        lang_var = ctk.StringVar(value=initial_lang)
        lang_menu = ctk.CTkOptionMenu(row, values=self.languages, variable=lang_var, width=150)
        lang_menu.pack(side="left", padx=5)
        
        # Track Name Entry
        name_var = ctk.StringVar(value="")
        name_entry = ctk.CTkEntry(row, textvariable=name_var, width=150)
        name_entry.pack(side="left", padx=5)

        # Default Checkbox
        default_var = ctk.BooleanVar(value=False)
        def_chk = ctk.CTkCheckBox(row, text="Def.", variable=default_var, 
                                  command=lambda: on_default_click_msg(default_var), width=50)
        def_chk.pack(side="left", padx=5)
        
        row_data = {
            "path": path,
            "lang_var": lang_var,
            "name_var": name_var,
            "default_var": default_var,
            "widget": row,
            "lang_menu": lang_menu
        }
        self.rows.append(row_data)
        return row_data

    def clear(self):
        for item in self.rows:
            item["widget"].destroy()
        self.rows = []
