
import customtkinter as ctk
from modules.viewmodels.settings_vm import SettingsViewModel

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, vm: SettingsViewModel):
        super().__init__(master, fg_color="transparent")
        self.vm = vm

        self.grid_columnconfigure(0, weight=1)

        # Appearance
        self.frame_app = ctk.CTkFrame(self)
        self.frame_app.grid(row=0, column=0, sticky="ew", padx=20, pady=20)

        ctk.CTkLabel(self.frame_app, text="Appearance", font=("Roboto Medium", 16)).pack(anchor="w", padx=20, pady=10)

        self.option_menu = ctk.CTkOptionMenu(
            self.frame_app,
            values=["System", "Light", "Dark"],
            command=self.vm.set_theme
        )
        self.option_menu.pack(padx=20, pady=10, anchor="w")
        self.option_menu.set("System")

        # Dependencies
        self.frame_deps = ctk.CTkFrame(self)
        self.frame_deps.grid(row=1, column=0, sticky="ew", padx=20, pady=20)

        ctk.CTkLabel(self.frame_deps, text="Dependencies", font=("Roboto Medium", 16)).pack(anchor="w", padx=20, pady=10)

        tools = self.vm.get_tool_status()
        for tool, path in tools.items():
            f = ctk.CTkFrame(self.frame_deps, fg_color="transparent")
            f.pack(fill="x", padx=20, pady=5)

            ctk.CTkLabel(f, text=tool).pack(side="left")

            status = "✓ Found" if path else "X Missing"
            color = "green" if path else "red"
            ctk.CTkLabel(f, text=status, text_color=color).pack(side="right")
