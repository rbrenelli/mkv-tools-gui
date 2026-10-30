import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget, QMainWindow,
)

from .. import launcher
from ..core import languages
from ..core.tools import INSTALL_HINT, missing_tools
from .edit_page import EditPage
from .extract_page import ExtractPage
from .subs_page import AddSubsPage
from .widgets import settings

RESOURCES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")
ICON_PATH = os.path.join(RESOURCES, "icon.png")

STYLE = """
QLabel#pageTitle { font-size: 22px; font-weight: bold; padding-bottom: 4px; }
QPushButton#primary { background-color: #2563eb; color: white; padding: 8px 18px; border-radius: 5px; font-weight: bold; }
QPushButton#primary:hover { background-color: #1d4ed8; }
QPushButton#primary:disabled { background-color: #9ca3af; color: #e5e7eb; }
QListWidget#nav { font-size: 14px; border: none; }
QListWidget#nav::item { padding: 11px 14px; }
QFrame#banner { background: #fef3c7; border: 1px solid #f59e0b; border-radius: 6px; }
QFrame#banner QLabel { color: #78350f; }
"""


class MainWindow(QMainWindow):
    def __init__(self, files=()):
        super().__init__()
        self.setWindowTitle("MKV Tool Suite")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.resize(1100, 720)
        self.setStyleSheet(STYLE)

        langs = languages.load_languages()
        self.pages = [ExtractPage(langs), AddSubsPage(langs), EditPage(langs)]

        central = QWidget()
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setFixedWidth(190)
        for p in self.pages:
            self.nav.addItem(QListWidgetItem(p.title))
        outer.addWidget(self.nav)
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        outer.addWidget(line)

        right = QVBoxLayout()
        right.setContentsMargins(18, 14, 18, 14)
        self.banner = self._make_banner()
        right.addWidget(self.banner)
        self.stack = QStackedWidget()
        for p in self.pages:
            self.stack.addWidget(p)
        right.addWidget(self.stack, 1)
        holder = QWidget()
        holder.setLayout(right)
        outer.addWidget(holder, 1)
        self.setCentralWidget(central)

        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav.setCurrentRow(0)

        if files:
            self.pages[0].add_paths([f for f in files if os.path.isfile(f)])
        QTimer.singleShot(400, self._offer_launcher)

    def _make_banner(self):
        miss = missing_tools()
        box = QFrame()
        box.setObjectName("banner")
        lay = QHBoxLayout(box)
        lay.addWidget(QLabel(f"MKVToolNix is not installed (missing: {', '.join(miss)}).  "
                             f"Install it with:  <b>{INSTALL_HINT}</b>"))
        lay.addStretch(1)
        copy = QPushButton("Copy command")
        copy.clicked.connect(lambda: QGuiApplication.clipboard().setText(INSTALL_HINT))
        lay.addWidget(copy)
        box.setVisible(bool(miss))
        if miss:
            for p in self.pages:
                p.setEnabled(False)
        return box

    def _offer_launcher(self):
        """When running as an AppImage, offer to add the app to the menu/launcher (the clickable icon)."""
        exe = launcher.appimage_path()
        if not exe or launcher.is_installed(exe) or settings().value("launcher_declined", False, type=bool):
            return
        box = QMessageBox(self)
        box.setWindowTitle("Add to your app menu?")
        box.setText("Add MKV Tool Suite to your app menu so you can start it with a click?")
        box.setInformativeText("This adds a launcher and an icon in your user folder only. "
                               "You can remove it later with:  --uninstall-launcher")
        yes = box.addButton("Add launcher", QMessageBox.AcceptRole)
        box.addButton("Not now", QMessageBox.RejectRole)
        never = box.addButton("Don't ask again", QMessageBox.DestructiveRole)
        box.exec()
        if box.clickedButton() is yes:
            launcher.install(exe, ICON_PATH)
        elif box.clickedButton() is never:
            settings().setValue("launcher_declined", True)
