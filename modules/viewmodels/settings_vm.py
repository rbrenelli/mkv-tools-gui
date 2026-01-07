
from services.dependency_service import DependencyService
import customtkinter as ctk

class SettingsViewModel:
    def __init__(self, dependency_service: DependencyService):
        self.deps = dependency_service

    def get_tool_status(self) -> dict:
        self.deps.check_dependencies()
        return self.deps._tools

    def set_theme(self, mode: str):
        # mode: "System", "Dark", "Light"
        ctk.set_appearance_mode(mode)
