
import customtkinter as ctk
from utils.constants import *

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate):
        super().__init__(master, width=200, corner_radius=0)
        self.on_navigate = on_navigate

        self.logo = ctk.CTkLabel(self, text=APP_NAME, font=("Roboto Medium", 20))
        self.logo.grid(row=0, column=0, padx=20, pady=20)

        self.buttons = {}

        items = ["Extract", "Subtitles", "Create", "Settings"]
        for i, item in enumerate(items):
            btn = ctk.CTkButton(
                self,
                text=item,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                anchor="w",
                command=lambda x=item: self.on_navigate(x)
            )
            btn.grid(row=i+1, column=0, sticky="ew", padx=10, pady=5)
            self.buttons[item] = btn

        self.grid_rowconfigure(len(items)+1, weight=1)

    def set_active(self, name):
        for btn_name, btn in self.buttons.items():
            if btn_name == name:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color="transparent")
