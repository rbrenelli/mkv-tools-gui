"""Spike: minimal Qt window to validate PySide6 + AppImage + launcher on the Chromebook."""
import json
import shutil
import sys

from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHeaderView, QLabel, QMainWindow, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MKV Tool Suite (Qt spike)")
        self.resize(900, 520)
        self.setAcceptDrops(True)

        root = QWidget()
        lay = QVBoxLayout(root)

        self.status = QLabel()
        self.status.setWordWrap(True)
        lay.addWidget(self.status)

        self.btn = QPushButton("Open MKV…  (or drop a file here)")
        self.btn.clicked.connect(self.pick)
        lay.addWidget(self.btn)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Type", "Codec", "Language", "Name"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        lay.addWidget(self.table)
        self.setCentralWidget(root)

        self.mkvmerge = shutil.which("mkvmerge")
        if self.mkvmerge:
            self.status.setText(f"mkvmerge found: {self.mkvmerge}")
        else:
            self.status.setText("mkvmerge not found. Install with: sudo apt install mkvtoolnix")
            self.btn.setEnabled(False)

        self.proc = None

    def pick(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select video", "", "Video (*.mkv *.mp4 *.avi *.mov);;All files (*)")
        if path:
            self.load(path)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        if urls and self.mkvmerge:
            self.load(urls[0].toLocalFile())

    def load(self, path):
        # Non-blocking: the window stays responsive while mkvmerge runs.
        self.status.setText(f"Reading {path} …")
        self.proc = QProcess(self)
        self.proc.finished.connect(lambda code, _s, p=path: self.done(p, code))
        self.proc.start(self.mkvmerge, ["-J", path])

    def done(self, path, code):
        out = bytes(self.proc.readAllStandardOutput()).decode("utf-8", "replace")
        if code not in (0, 1):
            err = bytes(self.proc.readAllStandardError()).decode("utf-8", "replace")
            self.status.setText(f"mkvmerge failed ({code}): {err or out}")
            return
        tracks = json.loads(out).get("tracks", [])
        self.table.setRowCount(len(tracks))
        for r, t in enumerate(tracks):
            p = t.get("properties", {})
            for c, v in enumerate([t["id"], t["type"], t.get("codec", ""), p.get("language", ""), p.get("track_name", "")]):
                self.table.setItem(r, c, QTableWidgetItem(str(v)))
        self.status.setText(f"{path} — {len(tracks)} tracks")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("mkv-tool-suite")
    app.setDesktopFileName("mkv-tool-suite")
    w = Window()
    w.show()
    if "--shot" in sys.argv:  # headless screenshot for checking the look
        if len(sys.argv) > 3:
            w.load(sys.argv[3])
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: (w.grab().save(sys.argv[2]), app.quit()))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
