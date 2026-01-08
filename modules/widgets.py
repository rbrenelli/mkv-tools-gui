import customtkinter as ctk
from utils.mkv_wrapper import get_mkv_info
from utils.ffmpeg_wrapper import get_ffmpeg_info
from utils import theme
import os
import tkinter as tk

class ToolTip:
    """
    A simple tooltip utility for CustomTkinter widgets.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None

        # Bindings for mouse and keyboard accessibility
        self.widget.bind("<Enter>", self.schedule)
        self.widget.bind("<Leave>", self.hide)
        self.widget.bind("<ButtonPress>", self.hide)
        self.widget.bind("<FocusIn>", self.schedule)
        self.widget.bind("<FocusOut>", self.hide)

    def schedule(self, event=None):
        self.unschedule()
        self.id = self.widget.after(500, self.show)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
        self.id = None

    def show(self, event=None):
        if self.tip_window or not self.text:
            return

        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        except Exception:
            return

        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        self.tip_window.attributes('-topmost', True)

        # Use theme colors if possible, else high contrast defaults
        bg_color = theme.COLOR_BG_SIDEBAR[1] # Use dark theme sidebar color for tooltip background
        fg_color = "white"

        try:
             self.tip_window.configure(bg=bg_color)
        except:
             pass

        label = ctk.CTkLabel(self.tip_window, text=self.text, fg_color=bg_color, text_color=fg_color,
                             corner_radius=6, width=0, height=0, padx=8, pady=4, font=("Arial", 11))
        label.pack()

    def hide(self, event=None):
        self.unschedule()
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class TrackListFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, languages=None, extract_mode=False, default_checked=True, on_open=None, **kwargs):
        # Remove label_text from kwargs to move it outside
        kwargs.pop("label_text", None)
        kwargs.pop("label_font", None)
        
        self.extract_mode = extract_mode
        self.default_checked = default_checked
        self.on_open = on_open

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

        # Show empty state initially
        self._show_empty_state()

    def _get_content_frame(self):
        """Returns the internal frame where content is actually placed."""
        # Create a temporary widget to find the parent frame if needed
        # Or usually ctk exposes it. Let's try to be robust.
        # But standard ctk usage: self is the outer frame.
        # If we pack into self, ctk reparents to self.scrollable_frame (if it exists)
        # or we can assume there is a property.
        # Let's inspect using a temporary widget which is 100% reliable for CTk.
        try:
            return self.scrollable_frame
        except AttributeError:
            # Fallback if the version of CTk is different or structure varies
            pass

        # Fallback: Create a widget and check its master
        temp = ctk.CTkLabel(self)
        frame = temp.master
        temp.destroy()
        return frame

    def _clear_content(self):
        """Safely clears user content from the internal scrollable frame."""
        content_frame = self._get_content_frame()
        for widget in content_frame.winfo_children():
            widget.destroy()

    def _show_empty_state(self):
        """Displays a placeholder message when no file is loaded."""
        self._clear_content()

        msg = "No video loaded. Select a source file to view tracks."
        lbl = ctk.CTkLabel(self, text=msg, text_color="gray", wraplength=400)
        lbl.pack(padx=20, pady=(50, 10))

        if self.on_open:
            btn = ctk.CTkButton(self, text="Select Video File", command=self.on_open)
            btn.pack(padx=20, pady=(0, 50))
        else:
            # Add extra padding if no button
            lbl.pack(padx=20, pady=50)

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
        self._clear_content()
        self.track_widgets = {}
        self.tracks = []
        self.generated_filenames = set()

        if not file_path:
            self._show_empty_state()
            return

        # Show Loading State
        loading_lbl = ctk.CTkLabel(self, text="Loading tracks...", text_color="gray")
        loading_lbl.pack(pady=40)
        self.update() # Force UI update before heavy operation

        self.source_filename = os.path.splitext(os.path.basename(file_path))[0]

        info = None
        error_msg = None

        try:
            if file_path.lower().endswith('.mkv'):
                info = get_mkv_info(file_path)
            else:
                info = get_ffmpeg_info(file_path)
                # ffmpeg_wrapper might return None on failure currently,
                # or we might want to standardize it later.
                if info is None:
                     error_msg = "Could not read file info (FFmpeg)."
        except Exception as e:
            error_msg = str(e)

        # Clear loading indicator
        self._clear_content()

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
                ToolTip(def_chk, "Set as Default Track")
                
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

    def add_file_row(self, path, on_default_click_msg, on_remove_callback=None):
        """
        Adds a row for a subtitle file.
        on_default_click_msg: callback when 'default' box is clicked.
        on_remove_callback: (optional) callback when remove button is clicked. Receives row_data.
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
        ToolTip(def_chk, "Set as Default Track")
        
        row_data = {
            "path": path,
            "lang_var": lang_var,
            "name_var": name_var,
            "default_var": default_var,
            "widget": row,
            "lang_menu": lang_menu
        }

        # Remove Button (Micro-UX improvement)
        if on_remove_callback:
            # Using '✕' (U+2715) for a clean look
            rm_btn = ctk.CTkButton(row, text="✕", width=28, height=28,
                                   fg_color="transparent",
                                   text_color=theme.COLOR_BTN_CLEAR_TEXT,
                                   hover_color=theme.COLOR_BTN_CLEAR_HOVER,
                                   command=lambda: on_remove_callback(row_data))
            rm_btn.pack(side="left", padx=5)
            ToolTip(rm_btn, "Remove this file")

        self.rows.append(row_data)
        return row_data

    def remove_row(self, row_data):
        """Removes a specific row from the list."""
        if row_data in self.rows:
            self.rows.remove(row_data)
            row_data["widget"].destroy()

    def clear(self):
        for item in self.rows:
            item["widget"].destroy()
        self.rows = []
