import os

from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QHBoxLayout, QHeaderView, QLineEdit, QMessageBox, QPushButton, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from ..core import commands, ffmpeg, naming, plan
from ..core.media import read_media
from ..core.model import MkvError
from .runner import Job
from .subs_page import make_table
from .widgets import (ROW_HEIGHT, VIDEO_EXTS, VIDEO_FILTER, JobPanel, LanguageCombo, card, centered, muted, open_files,
                      padded, page_header, remember_dir, scroll_body, show_problem, unwrap)

C_KEEP, C_TRACK, C_LANG, C_NAME, C_DEFAULT, C_FORCED, C_ENABLED = range(7)


class EditPage(QWidget):
    title = "Edit Tracks"

    def __init__(self, languages):
        super().__init__()
        self.languages = languages
        self.info = None
        self._inplace = False
        self.setAcceptDrops(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        area, lay = scroll_body()
        root.addWidget(area, 1)
        page_header(lay, "Edit Tracks",
                    "Change language, name and flags. “Apply in place” (MKV only) edits the file directly and takes "
                    "seconds, even for huge files. Removing tracks, or MP4 files, need “Save as new file…”.")

        box = QVBoxLayout()
        row = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setReadOnly(True)
        self.file_edit.setPlaceholderText("Choose a video, or drop one on this window…")
        b = QPushButton("Choose video…")
        b.clicked.connect(self.choose)
        row.addWidget(self.file_edit, 1)
        row.addWidget(b)
        box.addLayout(row)
        self.table = make_table(["Keep", "Track", "Language", "Name", "Default", "Forced", "Enabled"])
        self.table.setMinimumHeight(240)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Interactive)
        for c, w in ((C_KEEP, 64), (C_TRACK, 240), (C_LANG, 210), (C_DEFAULT, 84), (C_FORCED, 78), (C_ENABLED, 86)):
            self.table.setColumnWidth(c, w)
        h.setSectionResizeMode(C_NAME, QHeaderView.Stretch)
        box.addWidget(self.table, 1)
        self.note = muted("")
        box.addWidget(self.note)
        lay.addWidget(card(box), 1)

        fbox = QVBoxLayout()
        self.panel = JobPanel()
        fbox.addWidget(self.panel)
        r = QHBoxLayout()
        r.addStretch(1)
        self.copy_btn = QPushButton("Save as new file…")
        self.copy_btn.clicked.connect(self.save_copy)
        self.inplace_btn = QPushButton("Apply in place")
        self.inplace_btn.setObjectName("primary")
        self.inplace_btn.clicked.connect(self.apply_in_place)
        r.addWidget(self.copy_btn)
        r.addWidget(self.inplace_btn)
        fbox.addLayout(r)
        root.addWidget(card(fbox))
        self.panel.busy_changed.connect(lambda _b: self._refresh())
        self.panel.all_done.connect(self._after_job)
        self._refresh()

    def _refresh(self):
        on = self.info is not None and not self.panel.busy
        self.copy_btn.setEnabled(on)
        self.inplace_btn.setEnabled(on and self.info.backend == "mkvtoolnix")

    # ---- loading
    def choose(self):
        p = open_files(self, "Select a video", VIDEO_FILTER, multiple=False)
        if p:
            self.load(p)

    def load(self, path):
        try:
            info = read_media(path)
        except MkvError as e:
            show_problem(self, "Could not read file", f"{os.path.basename(path)}\n\n{e}")
            return
        self.info = info
        self.file_edit.setText(path)
        mkv = info.backend == "mkvtoolnix"
        self.note.setText("" if mkv else "This is not an MKV file: changes are saved to a new file, and the "
                                          "“Enabled” flag isn't available.")
        self.note.setVisible(not mkv)
        self.table.setRowCount(0)
        for t in info.tracks:
            r = self.table.rowCount()
            self.table.insertRow(r)
            keep = QCheckBox()
            keep.setChecked(True)
            self.table.setCellWidget(r, C_KEEP, centered(keep))
            item = QTableWidgetItem(f"{t.short}  ·  {t.codec}")
            item.setToolTip(f"{t.short}  ·  {t.codec}")
            self.table.setItem(r, C_TRACK, item)
            self.table.setCellWidget(r, C_LANG, padded(LanguageCombo(self.languages, t.language)))
            self.table.setCellWidget(r, C_NAME, padded(QLineEdit(t.name)))
            for col, val in ((C_DEFAULT, t.default), (C_FORCED, t.forced), (C_ENABLED, t.enabled)):
                cb = QCheckBox()
                cb.setChecked(val)
                cb.setEnabled(mkv or col != C_ENABLED)
                self.table.setCellWidget(r, col, centered(cb))
            unwrap(self.table.cellWidget(r, C_DEFAULT), QCheckBox).toggled.connect(
                lambda on, row=r: self._exclusive_default(row, on))
            self.table.setRowHeight(r, ROW_HEIGHT + 10)
        self._refresh()

    def _box(self, r, col):
        return unwrap(self.table.cellWidget(r, col), QCheckBox)

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
            lang = unwrap(self.table.cellWidget(r, C_LANG), LanguageCombo).code()
            name = unwrap(self.table.cellWidget(r, C_NAME), QLineEdit).text().strip()
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
        if not self.info:
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
                                "Video and audio are not touched, but the file itself is modified. Continue?") != QMessageBox.Yes:
            return
        try:
            p = plan.propedit(self.info, edits)
        except (plan.ToolMissing, ffmpeg.UnsupportedError) as e:
            show_problem(self, "Can't do that", e)
            return
        self._inplace = True
        self.panel.run([Job(f"Updating {os.path.basename(self.info.path)}", p.argv)])

    def save_copy(self):
        if not self.info:
            return
        stem = naming.stem_of(self.info.path)
        mp4_in = os.path.splitext(self.info.path)[1].lower() in ffmpeg.MP4_EXTS
        suggested = os.path.join(os.path.dirname(self.info.path), f"{stem}_edited{'.mp4' if mp4_in else '.mkv'}")
        filters = "MP4 (*.mp4);;Matroska (*.mkv)" if mp4_in else "Matroska (*.mkv);;MP4 (*.mp4)"
        path, chosen = QFileDialog.getSaveFileName(self, "Save as", suggested, filters)
        if not path:
            return
        if os.path.splitext(path)[1].lower() not in (".mkv", ".mp4"):
            path += ".mp4" if "mp4" in chosen.lower() else ".mkv"
        if os.path.abspath(path) == os.path.abspath(self.info.path):
            QMessageBox.warning(self, "File name", "Choose a different name, or use “Apply in place”.")
            return
        remember_dir(path)
        try:
            p = plan.mux(self.info, path, keep_ids=self._keep_ids(), edits=self._edits())
        except (plan.ToolMissing, ffmpeg.UnsupportedError) as e:
            show_problem(self, "Can't do that", e)
            return
        self.panel.run([Job(f"Writing {os.path.basename(path)}", p.argv, [path], p.kind, p.duration_ns)])

    def _after_job(self, ok, failed):
        if self._inplace and ok and not failed and self.info:
            self.load(self.info.path)   # show what is really in the file now
        self._inplace = False

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
