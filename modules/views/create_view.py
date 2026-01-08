
import customtkinter as ctk
from utils.linux_dialogs import LinuxDialogs
from modules.viewmodels.create_vm import CreateViewModel
from modules.views.components.drop_zone import FileDropZone
from modules.views.components.progress_modal import ProgressBarModal
from modules.views.components.modal import ModalDialog

class CreateView(ctk.CTkFrame):
    def __init__(self, master, vm: CreateViewModel):
        super().__init__(master, fg_color="transparent")
        self.vm = vm

        self.vm.on_list_updated = self.refresh_list
        self.vm.on_error = self.show_error
        self.vm.on_progress = self.update_progress
        self.vm.on_complete = self.on_complete

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Inputs
        self.drop_zone = FileDropZone(self, on_drop=self.vm.add_input, text="Drop Video/Audio/Subs Here")
        self.drop_zone.grid(row=0, column=0, sticky="ew", padx=20, pady=20)

        # 2. List
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Input Files")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # 3. Options
        self.opt_frame = ctk.CTkFrame(self)
        self.opt_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)

        ctk.CTkLabel(self.opt_frame, text="Output Format:").pack(side="left", padx=10)

        self.fmt_var = ctk.StringVar(value="mkv")
        self.seg_btn = ctk.CTkSegmentedButton(
            self.opt_frame,
            values=["mkv", "mp4"],
            variable=self.fmt_var,
            command=self.vm.set_output_format
        )
        self.seg_btn.pack(side="left", padx=10)

        self.create_btn = ctk.CTkButton(self.opt_frame, text="Create Video", command=self.on_create)
        self.create_btn.pack(side="right", padx=10, pady=10)

        self.progress_modal = None

    def refresh_list(self):
        if hasattr(self, "_track_widgets"):
            for w in self._track_widgets:
                w.destroy()
        self._track_widgets = []

        for i, item in enumerate(self.vm.inputs):
            f = ctk.CTkFrame(self.scroll_frame)
            f.pack(fill="x", pady=2)
            self._track_widgets.append(f)

            ctk.CTkLabel(f, text=item["path"]).pack(side="left", padx=5)
            ctk.CTkButton(f, text="X", width=30, fg_color="red", command=lambda idx=i: self.vm.remove_input(idx)).pack(side="right", padx=5)

    def on_create(self):
        ext = f".{self.fmt_var.get()}"
        filename = LinuxDialogs.asksaveasfilename(title="Save Video", defaultextension=ext)
        if filename:
            self.progress_modal = ProgressBarModal(self)
            self.vm.create_video(filename)

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
