import os

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QCompleter, QFileDialog, QHBoxLayout, QLabel, QPlainTextEdit, QProgressBar,
    QPushButton, QStyledItemDelegate, QVBoxLayout, QWidget,
)

from .runner import Job, JobRunner


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


VIDEO_FILTER = "Matroska video (*.mkv *.mka *.mks *.webm);;All files (*)"
SUB_FILTER = "Subtitles (*.srt *.ass *.ssa *.sup *.vtt *.idx *.sub);;All files (*)"
SUB_EXTS = {".srt", ".ass", ".ssa", ".sup", ".vtt", ".idx", ".sub"}
VIDEO_EXTS = {".mkv", ".mka", ".mks", ".webm", ".mp4", ".m4v", ".avi", ".mov"}


class LanguageCombo(QComboBox):
    """Searchable language picker. A code that is not in the list is added, so it is never lost."""
    changed = Signal()

    def __init__(self, languages, code="und", parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self._known = {}
        for l in languages:
            self.addItem(l.label, l.code)
            self._known[l.code] = l.label
        comp = QCompleter(self.model(), self)
        comp.setFilterMode(Qt.MatchContains)
        comp.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(comp)
        self.set_code(code)
        self.currentIndexChanged.connect(lambda _i: self.changed.emit())
        self.setMinimumWidth(170)

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


class OnlyColumnDelegate(QStyledItemDelegate):
    """Allows in-place editing for a single column of a tree/table."""
    def __init__(self, column, parent=None):
        super().__init__(parent)
        self._col = column

    def createEditor(self, parent, option, index):
        return super().createEditor(parent, option, index) if index.column() == self._col else None


def centered(widget):
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setAlignment(Qt.AlignCenter)
    lay.addWidget(widget)
    return w


class JobPanel(QWidget):
    """Progress bar, status line, cancel button and a log, for running a queue of jobs one by one."""
    busy_changed = Signal(bool)
    all_done = Signal(int, int)   # succeeded, failed

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        self.status = QLabel("")
        self.status.setWordWrap(True)
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setTextVisible(False)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel)
        self.details_btn = QPushButton("Details")
        self.details_btn.setCheckable(True)
        row.addWidget(self.bar, 1)
        row.addWidget(self.cancel_btn)
        row.addWidget(self.details_btn)
        lay.addWidget(self.status)
        lay.addLayout(row)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(2000)
        self.log.setMinimumHeight(110)
        self.log.hide()
        self.details_btn.toggled.connect(self.log.setVisible)
        lay.addWidget(self.log)

        self._runner = JobRunner(self)
        self._runner.progress.connect(self._on_progress)
        self._runner.line.connect(self.log.appendPlainText)
        self._runner.finished.connect(self._on_finished)
        self._jobs, self._index, self._ok, self._failed = [], 0, 0, 0
        self.busy = False
        self._set_idle()

    def _set_idle(self):
        self.cancel_btn.setEnabled(False)
        self.bar.setValue(0)

    def run(self, jobs):
        if self.busy or not jobs:
            return
        self._jobs, self._index, self._ok, self._failed = list(jobs), 0, 0, 0
        self.log.clear()
        self.busy = True
        self.cancel_btn.setEnabled(True)
        self.busy_changed.emit(True)
        self._start_current()

    def cancel(self):
        self._jobs = self._jobs[: self._index + 1]  # stop after the running job
        self._runner.cancel()

    def _start_current(self):
        job = self._jobs[self._index]
        n = len(self._jobs)
        self.status.setText(f"{job.title}" + (f"  ({self._index + 1} of {n})" if n > 1 else ""))
        self.log.appendPlainText(f"$ {' '.join(job.argv)}")
        self._runner.start(job.argv)

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
            self.log.appendPlainText(("Cancelled." if cancelled else "Error: " + outcome.error))
            if not cancelled:
                self.details_btn.setChecked(True)
        self._index += 1
        if self._index < len(self._jobs):
            self._start_current()
            return
        self.busy = False
        self._set_idle()
        if self._failed == 0:
            self.bar.setValue(1000)
            self.status.setText("Done." if self._ok == 1 else f"Done — {self._ok} files.")
        else:
            self.status.setText(f"{self._failed} failed, {self._ok} succeeded. See Details.")
        self.busy_changed.emit(False)
        self.all_done.emit(self._ok, self._failed)
