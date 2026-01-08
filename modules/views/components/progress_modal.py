
import customtkinter as ctk

class ProgressBarModal(ctk.CTkToplevel):
    def __init__(self, master, title="Processing..."):
        super().__init__(master)
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)

        self.label = ctk.CTkLabel(self, text="Please wait...")
        self.label.pack(pady=(20, 10))

        self.progress = ctk.CTkProgressBar(self, width=300)
        self.progress.pack(pady=10)
        self.progress.start()

        self.cancel_btn = ctk.CTkButton(self, text="Cancel", fg_color="red", command=self.destroy)
        self.cancel_btn.pack(pady=10)

        self.transient(master)
        self.grab_set()

    def update_text(self, text):
        self.label.configure(text=text)

    def close(self):
        self.destroy()
