
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# Colors (Ported from theme.py)
COLOR_BG_MAIN = ("#f9fafb", "#111827")  # Gray 50 / Gray 900
COLOR_BG_SIDEBAR = ("#ffffff", "#1f2937")  # White / Gray 800
COLOR_ACCENT = "#3b82f6"  # Blue 500
COLOR_HOVER = "#2563eb"   # Blue 600
COLOR_BTN_TEXT = ("gray10", "gray90")
COLOR_BTN_HOVER = ("gray85", "gray25")
COLOR_BG_LIST = ("#e5e7eb", "#1f2937")
COLOR_LIST_STRIPE_EVEN = ("#ffffff", "#111827")
COLOR_ERROR = ("#ef4444", "#f87171") # Red
COLOR_SUCCESS = ("#10b981", "#34d399") # Green

# App Constants
APP_NAME = "MKV Tool Suite"
APP_VERSION = "2.0.0"
GITHUB_REPO_URL = "https://github.com/user/mkv-tools-gui"

# Extensions
VALID_VIDEO_EXTS = ['.mkv', '.mp4', '.m4v', '.mov', '.avi']
VALID_SUBTITLE_EXTS = ['.srt', '.ass', '.vtt', '.sub', '.ssa']
