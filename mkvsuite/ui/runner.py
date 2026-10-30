"""Running MKVToolNix commands without blocking the window."""
import os
from dataclasses import dataclass, field

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QThread, Signal

from ..core import jobs
from ..core.model import MkvError, read_info
from ..core.tools import clean_env


@dataclass
class Job:
    title: str
    argv: list
    outputs: list = field(default_factory=list)  # partial files to remove if the job fails or is cancelled


class JobRunner(QObject):
    """One external process. Emits progress (0-100), output lines, and finished(Outcome, cancelled)."""
    progress = Signal(int)
    line = Signal(str)
    finished = Signal(object, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc = None
        self._buf = ""
        self._text = []
        self._cancelled = False

    def start(self, argv):
        self._buf, self._text, self._cancelled = "", [], False
        self._proc = QProcess(self)
        env = QProcessEnvironment()
        for k, v in clean_env().items():
            env.insert(k, v)
        self._proc.setProcessEnvironment(env)
        self._proc.setProcessChannelMode(QProcess.MergedChannels)
        self._proc.readyReadStandardOutput.connect(self._read)
        self._proc.finished.connect(self._done)
        self._proc.errorOccurred.connect(self._error)
        self._proc.start(argv[0], argv[1:])

    def cancel(self):
        if self._proc and self._proc.state() != QProcess.NotRunning:
            self._cancelled = True
            self._proc.kill()

    def _read(self):
        self._buf += bytes(self._proc.readAllStandardOutput()).decode("utf-8", "replace").replace("\r", "\n")
        *lines, self._buf = self._buf.split("\n")
        for ln in lines:
            self._handle(ln)

    def _handle(self, ln):
        pct = jobs.progress_from_line(ln)
        if pct is not None:
            self.progress.emit(pct)
        elif ln.strip() and not jobs.is_noise(ln):
            self._text.append(ln)
            self.line.emit(ln)

    def _error(self, err):
        if err == QProcess.FailedToStart:
            self.finished.emit(jobs.Outcome(False, error=f"Could not start {self._proc.program()}"), False)

    def _done(self, code, _status):
        if self._buf.strip():
            self._handle(self._buf)
            self._buf = ""
        if self._cancelled:
            self.finished.emit(jobs.Outcome(False, error="Cancelled"), True)
        else:
            self.finished.emit(jobs.interpret(code, "\n".join(self._text)), False)


class InfoLoader(QThread):
    """Reads track info for several files off the UI thread."""
    loaded = Signal(str, object)   # path, MediaInfo
    failed = Signal(str, str)      # path, message

    def __init__(self, paths, parent=None):
        super().__init__(parent)
        self._paths = list(paths)

    def run(self):
        for p in self._paths:
            try:
                self.loaded.emit(p, read_info(p))
            except MkvError as e:
                self.failed.emit(p, str(e))
