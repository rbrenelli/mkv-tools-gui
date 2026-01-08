
import customtkinter as ctk
import typing
from utils.constants import *

class FileDropZone(ctk.CTkFrame):
    def __init__(self, master, on_drop: typing.Callable[[str], None], text="Drop File Here"):
        super().__init__(master, fg_color=COLOR_BG_LIST, corner_radius=10, border_width=2, border_color=COLOR_ACCENT)
        self.on_drop = on_drop

        self.label = ctk.CTkLabel(self, text=text, font=("Roboto Medium", 16))
        self.label.place(relx=0.5, rely=0.5, anchor="center")

        # Simulating drag and drop for now as TkinterDnD2 requires specific setup often complex in simple refactors
        # But we will add a button "Select File" overlaying it to ensure functionality

        self.btn = ctk.CTkButton(self, text="Select File", command=self.select_file)
        self.btn.place(relx=0.5, rely=0.7, anchor="center")

    def select_file(self):
        try:
            from utils.linux_dialogs import LinuxDialogs
            filename = LinuxDialogs.askopenfilename(title="Select File")
            if filename:
                self.on_drop(filename)
        except Exception as e:
            print(f"Error opening file dialog: {e}")
