import os

from PySide6.QtCore import QSettings, QSize, Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QScrollArea, QCheckBox, QComboBox, QCompleter, QFileDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit,
    QProgressBar, QPushButton, QStyledItemDelegate, QVBoxLayout, QWidget,
)

from ..core.plan import ToolMissing
from .runner import JobRunner


def settings():
    return QSettings("rbrenelli", "mkv-tool-suite")


def last_dir():
    d = settings().value("last_dir", os.path.expanduser("~"))
    return d if os.path.isdir(d) else os.path.expanduser("~")


def remember_dir(path):
    d = path if os.path.isdir(path) else os.path.dirname(path)
    if d:
        settings().setValue("last_dir", d)


def open_files(parent, title, filt, multiple=True):
    fn = QFileDialog.getOpenFileNames if multiple else QFileDialog.getOpenFileName
    res, _ = fn(parent, title, last_dir(), filt)
    if res:
        remember_dir(res[0] if multiple else res)
    return res


def open_dir(parent, title):
    d = QFileDialog.getExistingDirectory(parent, title, last_dir())
    if d:
        remember_dir(d)
    return d


def show_problem(parent, title, error):
    """Friendly dialog for ToolMissing / unsupported combinations / other errors."""
    QMessageBox.warning(parent, title, str(error))


VIDEO_FILTER = "Video files (*.mkv *.mp4 *.m4v *.mov *.avi *.webm *.mka);;All files (*)"
SUB_FILTER = "Subtitles (*.srt *.ass *.ssa *.vtt *.sup *.idx *.sub);;All files (*)"
SUB_EXTS = {".srt", ".ass", ".ssa", ".sup", ".vtt", ".idx", ".sub"}
VIDEO_EXTS = {".mkv", ".mka", ".webm", ".mp4", ".m4v", ".mov", ".avi"}
ROW_HEIGHT = 40


def card(layout, margins=(18, 16, 18, 16), spacing=10):
    """A rounded, bordered container holding `layout`. Returns the QFrame."""
    f = QFrame()
    f.setObjectName("card")
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    f.setLayout(layout)
    return f


def scroll_body():
    """A scrolling content area. Returns (scroll_area, layout_to_fill). Keep action bars outside it."""
    body = QWidget()
    lay = QVBoxLayout(body)
    lay.setContentsMargins(0, 0, 10, 0)
    lay.setSpacing(12)
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    area.setWidget(body)
    return area, lay


def page_header(layout, title, description):
    t = QLabel(title)
    t.setObjectName("pageTitle")
    layout.addWidget(t)
    d = QLabel(description)
    d.setObjectName("muted")
    d.setWordWrap(True)
    layout.addWidget(d)
    layout.addSpacing(6)


def muted(text):
    l = QLabel(text)
    l.setObjectName("muted")
    l.setWordWrap(True)
    return l


def section(text):
    l = QLabel(text)
    l.setObjectName("sectionTitle")
    return l


class LanguageCombo(QComboBox):
    """Searchable language picker. A code that is not in the list is added, so it is never lost."""
    changed = Signal()

    def __init__(self, languages, code="und", parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        for l in languages:
            self.addItem(l.label, l.code)
        comp = QCompleter(self.model(), self)
        comp.setFilterMode(Qt.MatchContains)
        comp.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(comp)
        self.set_code(code)
        self.currentIndexChanged.connect(lambda _i: self.changed.emit())
        self.setMinimumWidth(190)
        self.lineEdit().setPlaceholderText("Search language…")

    def set_code(self, code):
        i = self.findData(code)
        if i < 0:
            self.addItem(f"{code}", code)
            i = self.count() - 1
        self.setCurrentIndex(i)

    def code(self):
        i = self.findText(self.currentText())
        return self.itemData(i if i >= 0 else self.currentIndex()) or "und"

    def wheelEvent(self, e):  # don't change the value while scrolling a long list
        e.ignore()


class RowDelegate(QStyledItemDelegate):
    """Comfortable row height, and (optionally) editing limited to one column."""
    def __init__(self, parent=None, edit_column=None, height=ROW_HEIGHT - 6):
        super().__init__(parent)
        self._col, self._h = edit_column, height

    def sizeHint(self, option, index):
        s = super().sizeHint(option, index)
        return QSize(s.width(), max(s.height(), self._h))

    def createEditor(self, parent, option, index):
        if self._col is not None and index.column() != self._col:
            return None
        return super().createEditor(parent, option, index)


def centered(widget):
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(4, 0, 4, 0)
    lay.setAlignment(Qt.AlignCenter)
    lay.addWidget(widget)
    return w


def padded(widget, h=6, v=4):
    """Keeps an input from touching the cell borders."""
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(h, v, h, v)
    lay.addWidget(widget)
    return w


def unwrap(cell, cls):
    """Get the real widget back out of centered()/padded()."""
    return cell.findChild(cls)


class DropZone(QFrame):
    """The empty state: a big, friendly target with the main actions."""
    def __init__(self, title, hint, buttons, parent=None):
        super().__init__(parent)
        self.setObjectName("dropzone")
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(12)
        t = QLabel(title)
        t.setObjectName("sectionTitle")
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet("font-size: 16pt;")
        lay.addWidget(t)
        h = muted(hint)
        h.setWordWrap(False)
        h.setAlignment(Qt.AlignCenter)
        lay.addWidget(h)
        row = QHBoxLayout()
        row.setAlignment(Qt.AlignCenter)
        for text, cb, primary in buttons:
            b = QPushButton(text)
            if primary:
                b.setObjectName("primary")
            b.clicked.connect(cb)
            row.addWidget(b)
        lay.addSpacing(6)
        lay.addLayout(row)


class JobPanel(QWidget):
    """Status line, thin progress bar, cancel, and an optional log, for running a queue of jobs one by one."""
    busy_changed = Signal(bool)
    all_done = Signal(int, int)   # succeeded, failed

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self.status = QLabel("Ready.")
        self.status.setObjectName("muted")
        self.status.setWordWrap(True)
        row = QHBoxLayout()
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setTextVisible(False)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("rowbtn")
        self.cancel_btn.clicked.connect(self.cancel)
        self.details_btn = QPushButton("Details")
        self.details_btn.setObjectName("rowbtn")
        self.details_btn.setCheckable(True)
        row.addWidget(self.bar, 1)
        row.addWidget(self.cancel_btn)
        row.addWidget(self.details_btn)
        lay.addWidget(self.status)
        lay.addLayout(row)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(2000)
        self.log.setMinimumHeight(120)
        self.log.setMaximumHeight(220)
        self.log.hide()
        self.details_btn.toggled.connect(self.log.setVisible)
        lay.addWidget(self.log)

        self._runner = JobRunner(self)
        self._runner.progress.connect(self._on_progress)
        self._runner.line.connect(self.log.appendPlainText)
        self._runner.finished.connect(self._on_finished)
        self._jobs, self._index, self._ok, self._failed = [], 0, 0, 0
        self.busy = False
        self.cancel_btn.setEnabled(False)

    def run(self, jobs):
        if self.busy or not jobs:
            return
        self._jobs, self._index, self._ok, self._failed = list(jobs), 0, 0, 0
        self.log.clear()
        self.busy = True
        self.bar.setValue(0)
        self.cancel_btn.setEnabled(True)
        self.busy_changed.emit(True)
        self._start_current()

    def cancel(self):
        self._jobs = self._jobs[: self._index + 1]  # stop after the running job
        self._runner.cancel()

    def _start_current(self):
        job = self._jobs[self._index]
        n = len(self._jobs)
        self.status.setText(f"{job.title}" + (f"   ({self._index + 1} of {n})" if n > 1 else ""))
        self.log.appendPlainText(f"$ {' '.join(job.argv)}")
        self._runner.start(job.argv, job.kind, job.duration_ns)

    def _on_progress(self, pct):
        n = max(len(self._jobs), 1)
        self.bar.setValue(int((self._index + pct / 100) / n * 1000))

    def _on_finished(self, outcome, cancelled):
        job = self._jobs[self._index]
        if outcome.ok:
            self._ok += 1
            if outcome.warnings:
                self.log.appendPlainText("Warnings:\n" + outcome.warnings)
        else:
            self._failed += 1
            for p in job.outputs:  # don't leave half-written files behind
                try:
                    os.remove(p)
                except OSError:
                    pass
            self.log.appendPlainText("Cancelled." if cancelled else "Error: " + outcome.error)
            if not cancelled:
                self.details_btn.setChecked(True)
        self._index += 1
        if self._index < len(self._jobs):
            self._start_current()
            return
        self.busy = False
        self.cancel_btn.setEnabled(False)
        if self._failed == 0:
            self.bar.setValue(1000)
            self.status.setText("Done." if self._ok == 1 else f"Done — {self._ok} files.")
        else:
            self.status.setText(f"{self._failed} failed, {self._ok} succeeded. See Details.")
        self.busy_changed.emit(False)
        self.all_done.emit(self._ok, self._failed)
