
import shutil
import platform
import os
from utils.command_runner import CommandRunner

class DependencyService:
    def __init__(self):
        self.runner = CommandRunner()
        self._tools = {
            "mkvmerge": None,
            "mkvextract": None,
            "ffmpeg": None,
            "ffprobe": None
        }

    def check_dependencies(self) -> dict:
        """
        Checks for required tools in PATH.
        Returns a dict of tool_name -> path (or None if missing).
        """
        for tool in self._tools:
            path = shutil.which(tool)
            self._tools[tool] = path

        return self._tools

    def is_ready(self) -> bool:
        """Returns True if all tools are found."""
        return all(self._tools.values())

    def get_missing_tools(self) -> list:
        return [name for name, path in self._tools.items() if path is None]

    def get_tool_path(self, tool_name: str) -> str:
        return self._tools.get(tool_name)
