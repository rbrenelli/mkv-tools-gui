import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..core import commands, naming
from ..core.model import MkvError, read_info
from ..core.paths import safe_output_path
from ..core.tools import find_tool
from .runner import Job
from .widgets import (VIDEO_EXTS, VIDEO_FILTER, JobPanel, LanguageCombo, centered, open_dir, open_files)

C_KEEP, C_TRACK, C_CODEC, C_LANG, C_NAME, C_DEFAULT, C_FORCED, C_ENABLED = range(8)


class EditPage(QWidget):
    title = "Edit Tracks"

    def __init__(self, languages):
        super().__init__()
        self.languages = languages
        self.info = None
        self.setAcceptDrops(True)

        lay = QVBoxLayout(self)
        head = QLabel("Edit Tracks")
        head.setObjectName("pageTitle")
        lay.addWidget(head)
        hint = QLabel("Change language, name and flags. “Apply in place” edits the file directly and takes a "
                      "moment, even for huge files. Removing tracks needs “Save as new file…”.")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        row = QHBoxLayout()
        row.addWidget(QLabel("File:"))
        self.file_edit = QLineEdit()
        self.file_edit.setReadOnly(True)
        self.file_edit.setPlaceholderText("Choose or drop a file…")
        b = QPushButton("Choose…")
        b.clicked.connect(self.choose)
        row.addWidget(self.file_edit, 1)
        row.addWidget(b)
        lay.addLayout(row)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Keep", "Track", "Codec", "Language", "Name", "Default", "Forced", "Enabled"])
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setAlternatingRowColors(True)
        h = self.table.horizontalHeader()
        for c in (C_KEEP, C_TRACK, C_CODEC, C_DEFAULT, C_FORCED, C_ENABLED):
            h.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(C_LANG, QHeaderView.Interactive)
        self.table.setColumnWidth(C_LANG, 200)
        h.setSectionResizeMode(C_NAME, QHeaderView.Stretch)
        lay.addWidget(self.table, 1)

        self.panel = JobPanel()
        lay.addWidget(self.panel)
        r = QHBoxLayout()
        r.addStretch(1)
        self.copy_btn = QPushButton("Save as new file…")
        self.copy_btn.clicked.connect(self.save_copy)
        self.inplace_btn = QPushButton("Apply in place")
        self.inplace_btn.setObjectName("primary")
        self.inplace_btn.clicked.connect(self.apply_in_place)
        r.addWidget(self.copy_btn)
        r.addWidget(self.inplace_btn)
        lay.addLayout(r)
        self._set_enabled(False)
        self.panel.busy_changed.connect(lambda busy: self._set_enabled(not busy and self.info is not None))
        self.panel.all_done.connect(self._after_job)

    def _set_enabled(self, on):
        self.copy_btn.setEnabled(on)
        self.inplace_btn.setEnabled(on)

    # ---- loading
    def choose(self):
        p = open_files(self, "Select a file", VIDEO_FILTER, multiple=False)
        if p:
            self.load(p)

    def load(self, path):
        try:
            info = read_info(path)
        except MkvError as e:
            QMessageBox.warning(self, "Could not read file", f"{os.path.basename(path)}\n\n{e}")
            return
        self.info = info
        self.file_edit.setText(path)
        self.table.setRowCount(0)
        for t in info.tracks:
            r = self.table.rowCount()
            self.table.insertRow(r)
            keep = QCheckBox()
            keep.setChecked(True)
            self.table.setCellWidget(r, C_KEEP, centered(keep))
            self.table.setItem(r, C_TRACK, QTableWidgetItem(t.short))
            self.table.setItem(r, C_CODEC, QTableWidgetItem(t.codec))
            self.table.setCellWidget(r, C_LANG, LanguageCombo(self.languages, t.language))
            self.table.setCellWidget(r, C_NAME, QLineEdit(t.name))
            for col, val in ((C_DEFAULT, t.default), (C_FORCED, t.forced), (C_ENABLED, t.enabled)):
                cb = QCheckBox()
                cb.setChecked(val)
                self.table.setCellWidget(r, col, centered(cb))
            self.table.cellWidget(r, C_DEFAULT).findChild(QCheckBox).toggled.connect(
                lambda on, row=r: self._exclusive_default(row, on))
            self.table.setRowHeight(r, 36)
        self._set_enabled(not self.panel.busy)

    def _box(self, r, col):
        return self.table.cellWidget(r, col).findChild(QCheckBox)

    def _exclusive_default(self, row, on):
        if not on:
            return
        type_ = self.info.tracks[row].type
        for r, t in enumerate(self.info.tracks):
            if r != row and t.type == type_:
                self._box(r, C_DEFAULT).setChecked(False)

    # ---- reading the table back
    def _edits(self):
        edits = {}
        for r, t in enumerate(self.info.tracks):
            e = commands.TrackEdit()
            lang = self.table.cellWidget(r, C_LANG).code()
            name = self.table.cellWidget(r, C_NAME).text().strip()
            if lang != t.language:
                e.language = lang
            if name != t.name:
                e.name = name
            for col, attr, orig in ((C_DEFAULT, "default", t.default), (C_FORCED, "forced", t.forced),
                                    (C_ENABLED, "enabled", t.enabled)):
                v = self._box(r, col).isChecked()
                if v != orig:
                    setattr(e, attr, v)
            if not e.is_empty():
                edits[t.id] = e
        return edits

    def _keep_ids(self):
        return {t.id for r, t in enumerate(self.info.tracks) if self._box(r, C_KEEP).isChecked()}

    # ---- actions
    def apply_in_place(self):
        exe = find_tool("mkvpropedit")
        if not (exe and self.info):
            return
        if len(self._keep_ids()) != len(self.info.tracks):
            QMessageBox.information(self, "Removing tracks",
                                    "Removing tracks needs a new file. Use “Save as new file…”, or tick every track again.")
            return
        edits = self._edits()
        if not edits:
            QMessageBox.information(self, "No changes", "Nothing was changed.")
            return
        if QMessageBox.question(self, "Edit the original file?",
                                f"This changes {os.path.basename(self.info.path)} directly.\n"
                                "The video and audio are not touched, but the file itself is modified. Continue?") != QMessageBox.Yes:
            return
        cmd = commands.build_propedit(exe, self.info.path, self.info, edits)
        self.panel.run([Job(f"Updating {os.path.basename(self.info.path)}", cmd)])

    def save_copy(self):
        exe = find_tool("mkvmerge")
        if not (exe and self.info):
            return
        from PySide6.QtWidgets import QFileDialog
        from .widgets import last_dir, remember_dir
        stem = naming.stem_of(self.info.path)
        suggested = os.path.join(os.path.dirname(self.info.path), f"{stem}_edited.mkv")
        path, _ = QFileDialog.getSaveFileName(self, "Save as", suggested, "Matroska (*.mkv)")
        if not path:
            return
        if not path.lower().endswith(".mkv"):
            path += ".mkv"
        if os.path.abspath(path) == os.path.abspath(self.info.path):
            QMessageBox.warning(self, "File name", "Choose a different name, or use “Apply in place”.")
            return
        remember_dir(path)
        cmd = commands.build_mux(exe, path, self.info, keep_ids=self._keep_ids(), edits=self._edits())
        self.panel.run([Job(f"Writing {os.path.basename(path)}", cmd, [path])])

    def _after_job(self, ok, failed):
        if ok and not failed and self.info and self.panel.status.text().startswith("Done"):
            self.load(self.info.path)   # show what is really in the file now (in-place case)

    # ---- drag and drop
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for u in e.mimeData().urls():
            p = u.toLocalFile()
            if os.path.splitext(p)[1].lower() in VIDEO_EXTS:
                self.load(p)
                break
