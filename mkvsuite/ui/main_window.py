import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget, QMainWindow,
)

from .. import launcher
from ..core import languages
from ..core.tools import FFMPEG_HINT, INSTALL_HINT, missing_ffmpeg, missing_tools
from . import theme
from .edit_page import EditPage
from .extract_page import ExtractPage
from .subs_page import AddSubsPage
from .widgets import settings

RESOURCES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")
ICON_PATH = os.path.join(RESOURCES, "icon.png")


class MainWindow(QMainWindow):
    def __init__(self, files=()):
        super().__init__()
        self.setWindowTitle("MKV Tool Suite")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.setMinimumSize(1000, 560)
        self.resize(1180, 780)
        geo = settings().value("geometry")
        if geo:
            self.restoreGeometry(geo)

        langs = languages.load_languages()
        self.pages = [ExtractPage(langs), AddSubsPage(langs), EditPage(langs)]
        for p in self.pages:
            p.setMinimumWidth(700)

        central = QWidget()
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # --- sidebar
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(240)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(14, 18, 14, 14)
        head = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(QPixmap(ICON_PATH).scaled(34, 34, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        name = QLabel("MKV Tool Suite")
        name.setObjectName("appName")
        head.addWidget(logo)
        head.addWidget(name, 1)
        sl.addLayout(head)
        sl.addSpacing(14)
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setFocusPolicy(Qt.NoFocus)
        for p in self.pages:
            self.nav.addItem(QListWidgetItem(p.title))
        sl.addWidget(self.nav, 1)
        self.theme_btn = QPushButton()
        self.theme_btn.clicked.connect(self.toggle_theme)
        sl.addWidget(self.theme_btn)
        outer.addWidget(side)

        # --- content
        right = QVBoxLayout()
        right.setContentsMargins(22, 18, 14, 14)
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
        self._mode = settings().value("theme", "system")
        self._apply_theme()

        if files:
            self.pages[0].add_paths([f for f in files if os.path.isfile(f)])
        QTimer.singleShot(400, self._offer_launcher)

    # ---- theme
    def _apply_theme(self):
        resolved = theme.apply(QApplication.instance(), self._mode)
        self.theme_btn.setText("Switch to light" if resolved == "dark" else "Switch to dark")
        self._resolved = resolved

    def toggle_theme(self):
        self._mode = "light" if self._resolved == "dark" else "dark"
        settings().setValue("theme", self._mode)
        self._apply_theme()

    def closeEvent(self, e):
        settings().setValue("geometry", self.saveGeometry())
        super().closeEvent(e)

    # ---- tools banner
    def _make_banner(self):
        lines = []
        miss = missing_tools()
        if miss:
            lines.append(f"MKVToolNix is not installed (missing: {', '.join(miss)}). Install it with:  <b>{INSTALL_HINT}</b>")
        if missing_ffmpeg():
            lines.append(f"MP4/AVI/MOV files need ffmpeg. Install it with:  <b>{FFMPEG_HINT}</b>")
        box = QFrame()
        box.setObjectName("banner")
        lay = QHBoxLayout(box)
        lay.setContentsMargins(14, 10, 14, 10)
        text = QLabel("<br>".join(lines))
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay.addWidget(text, 1)
        copy = QPushButton("Copy command")
        copy.clicked.connect(lambda: QGuiApplication.clipboard().setText(
            "sudo apt install " + " ".join(x for x, need in (("mkvtoolnix", bool(miss)), ("ffmpeg", bool(missing_ffmpeg()))) if need)))
        lay.addWidget(copy)
        box.setVisible(bool(lines))
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
                               "You can remove it later by running the app with --uninstall-launcher.")
        yes = box.addButton("Add launcher", QMessageBox.AcceptRole)
        box.addButton("Not now", QMessageBox.RejectRole)
        never = box.addButton("Don't ask again", QMessageBox.DestructiveRole)
        box.exec()
        if box.clickedButton() is yes:
            launcher.install(exe, ICON_PATH)
        elif box.clickedButton() is never:
            settings().setValue("launcher_declined", True)
