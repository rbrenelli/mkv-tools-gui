
import customtkinter as ctk

class ModalDialog(ctk.CTkToplevel):
    def __init__(self, master, title, message):
        super().__init__(master)
        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)

        self.label = ctk.CTkLabel(self, text=message, wraplength=350)
        self.label.pack(pady=20, padx=20)

        self.btn = ctk.CTkButton(self, text="OK", command=self.destroy)
        self.btn.pack(pady=10)

        # Modal behavior
        self.transient(master)
        self.grab_set()
        master.wait_window(self)
