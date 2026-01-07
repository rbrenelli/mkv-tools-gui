
import customtkinter as ctk
from utils.linux_dialogs import LinuxDialogs
from modules.viewmodels.extract_vm import ExtractViewModel
from modules.views.components.drop_zone import FileDropZone
from modules.views.components.progress_modal import ProgressBarModal
from modules.views.components.modal import ModalDialog

class ExtractView(ctk.CTkFrame):
    def __init__(self, master, vm: ExtractViewModel):
        super().__init__(master, fg_color="transparent")
        self.vm = vm

        # Setup VM callbacks
        self.vm.on_file_loaded = self.on_file_loaded
        self.vm.on_error = self.show_error
        self.vm.on_progress = self.update_progress
        self.vm.on_complete = self.on_complete

        # UI Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Drop Zone
        self.drop_zone = FileDropZone(self, on_drop=self.vm.load_file)
        self.drop_zone.grid(row=0, column=0, sticky="ew", padx=20, pady=20)

        # 2. Track List
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Tracks")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))

        # 3. Actions
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)

        self.extract_btn = ctk.CTkButton(self.action_frame, text="Extract Selected", command=self.on_extract)
        self.extract_btn.pack(side="right")

        self.progress_modal = None

    def on_file_loaded(self, media_file):
        # Clear existing
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        self.drop_zone.label.configure(text=f"Loaded: {media_file.filename}")

        # Headers
        headers = ["Select", "ID", "Type", "Lang", "Name", "Output Name"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.scroll_frame, text=h, font=("Roboto", 12, "bold")).grid(row=0, column=i, padx=5, pady=5, sticky="w")

        # Rows
        for i, track in enumerate(media_file.tracks):
            r = i + 1

            # Checkbox
            var = ctk.BooleanVar(value=track.selected)
            chk = ctk.CTkCheckBox(
                self.scroll_frame,
                text="",
                variable=var,
                width=20,
                command=lambda t=track.id, v=var: self.vm.toggle_track_selection(t, v.get())
            )
            chk.grid(row=r, column=0, padx=5, pady=2)

            ctk.CTkLabel(self.scroll_frame, text=str(track.id)).grid(row=r, column=1, padx=5)
            ctk.CTkLabel(self.scroll_frame, text=track.type).grid(row=r, column=2, padx=5)
            ctk.CTkLabel(self.scroll_frame, text=track.language).grid(row=r, column=3, padx=5)
            ctk.CTkLabel(self.scroll_frame, text=track.name or "-").grid(row=r, column=4, padx=5)

            # Output Name Entry
            entry = ctk.CTkEntry(self.scroll_frame, width=200)
            entry.grid(row=r, column=5, padx=5)
            entry.bind("<FocusOut>", lambda e, t=track.id, ent=entry: self.vm.set_track_output_name(t, ent.get()))

    def on_extract(self):
        output_dir = LinuxDialogs.askdirectory()
        if output_dir:
            self.progress_modal = ProgressBarModal(self)
            self.vm.extract_selected(output_dir)

    def show_error(self, msg):
        self.after(0, lambda: self._show_error_safe(msg))

    def _show_error_safe(self, msg):
        if self.progress_modal:
            self.progress_modal.close()
            self.progress_modal = None
        ModalDialog(self, "Error", msg)

    def update_progress(self, percent, text):
        self.after(0, lambda: self._update_progress_safe(text))

    def _update_progress_safe(self, text):
        if self.progress_modal:
            self.progress_modal.update_text(text)

    def on_complete(self, msg):
        self.after(0, lambda: self._on_complete_safe(msg))

    def _on_complete_safe(self, msg):
        if self.progress_modal:
            self.progress_modal.close()
            self.progress_modal = None
        ModalDialog(self, "Success", msg)
