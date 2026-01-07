
import customtkinter as ctk
from utils.linux_dialogs import LinuxDialogs
from modules.viewmodels.subtitle_vm import SubtitleViewModel
from modules.views.components.drop_zone import FileDropZone
from modules.views.components.progress_modal import ProgressBarModal
from modules.views.components.modal import ModalDialog

class SubtitleView(ctk.CTkFrame):
    def __init__(self, master, vm: SubtitleViewModel):
        super().__init__(master, fg_color="transparent")
        self.vm = vm

        self.vm.on_list_updated = self.refresh_list
        self.vm.on_error = self.show_error
        self.vm.on_progress = self.update_progress
        self.vm.on_complete = self.on_complete

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # List expands

        # 1. Video Input
        self.video_frame = ctk.CTkFrame(self)
        self.video_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)

        self.video_label = ctk.CTkLabel(self.video_frame, text="No Video Selected")
        self.video_label.pack(side="left", padx=10)

        ctk.CTkButton(self.video_frame, text="Select Video", command=self.select_video).pack(side="right", padx=10, pady=10)

        # 2. Add Subtitle Button / Drop
        self.drop_zone = FileDropZone(self, on_drop=self.vm.add_subtitle, text="Drop Subtitle Files Here")
        self.drop_zone.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        # 3. Subtitle List
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Subtitles to Add")
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)

        # 4. Save
        self.save_btn = ctk.CTkButton(self, text="Save New File", command=self.on_save)
        self.save_btn.grid(row=3, column=0, pady=20)

        self.progress_modal = None

    def select_video(self):
        filename = LinuxDialogs.askopenfilename(title="Select Video", filetypes=[("Video Files", "*.mkv *.mp4 *.avi *.mov")])
        if filename:
            self.vm.set_video(filename)
            self.video_label.configure(text=filename)

    def refresh_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for i, sub in enumerate(self.vm.subtitles):
            f = ctk.CTkFrame(self.scroll_frame)
            f.pack(fill="x", pady=2)

            ctk.CTkLabel(f, text=sub.filename).pack(side="left", padx=5)
            ctk.CTkLabel(f, text=sub.language_name).pack(side="left", padx=5)

            ctk.CTkButton(f, text="X", width=30, fg_color="red", command=lambda idx=i: self.vm.remove_subtitle(idx)).pack(side="right", padx=5)

    def on_save(self):
        filename = LinuxDialogs.asksaveasfilename(title="Save As", defaultextension=".mkv")
        if filename:
            self.progress_modal = ProgressBarModal(self)
            self.vm.save_file(filename)

    def show_error(self, msg):
        self.after(0, lambda: self._show_error_safe(msg))

    def _show_error_safe(self, msg):
        if self.progress_modal:
            self.progress_modal.close()
            self.progress_modal = None
        ModalDialog(self, "Error", msg)

    def update_progress(self, text):
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
