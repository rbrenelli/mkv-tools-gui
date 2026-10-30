import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QSplitter,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..core import commands, languages as langmod, naming
from ..core.model import MkvError, read_info
from ..core.paths import safe_output_path
from ..core.tools import find_tool
from .runner import Job
from .widgets import (SUB_EXTS, SUB_FILTER, VIDEO_EXTS, VIDEO_FILTER, JobPanel, LanguageCombo, centered, last_dir,
                      open_dir, open_files, remember_dir)


class AddSubsPage(QWidget):
    title = "Add Subtitles"

    def __init__(self, languages):
        super().__init__()
        self.languages = languages
        self.info = None
        self.setAcceptDrops(True)

        lay = QVBoxLayout(self)
        head = QLabel("Add Subtitles")
        head.setObjectName("pageTitle")
        lay.addWidget(head)
        hint = QLabel("Pick a video, add subtitle files (for example your translations), and save a new MKV. "
                      "Nothing is re-encoded, and the original file is never touched.")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        row = QHBoxLayout()
        row.addWidget(QLabel("Video:"))
        self.video_edit = QLineEdit()
        self.video_edit.setReadOnly(True)
        self.video_edit.setPlaceholderText("Choose or drop a video…")
        b = QPushButton("Choose…")
        b.clicked.connect(self.choose_video)
        row.addWidget(self.video_edit, 1)
        row.addWidget(b)
        lay.addLayout(row)

        split = QSplitter(Qt.Vertical)
        top = QWidget()
        tl = QVBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.addWidget(QLabel("Tracks in the video (untick to leave one out of the new file)"))
        self.tracks = QTableWidget(0, 6)
        self.tracks.setHorizontalHeaderLabels(["Keep", "Track", "Codec", "Language", "Name", "Flags"])
        self.tracks.verticalHeader().hide()
        self.tracks.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tracks.setSelectionMode(QTableWidget.NoSelection)
        self.tracks.setAlternatingRowColors(True)
        h = self.tracks.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.Stretch)
        tl.addWidget(self.tracks)
        split.addWidget(top)

        bottom = QWidget()
        bl = QVBoxLayout(bottom)
        bl.setContentsMargins(0, 0, 0, 0)
        bar = QHBoxLayout()
        bar.addWidget(QLabel("Subtitles to add"))
        bar.addStretch(1)
        add = QPushButton("Add subtitle files…")
        add.clicked.connect(self.choose_subs)
        self.clear_btn = QPushButton("Remove all")
        self.clear_btn.clicked.connect(self.clear_subs)
        bar.addWidget(add)
        bar.addWidget(self.clear_btn)
        bl.addLayout(bar)
        self.subs = QTableWidget(0, 6)
        self.subs.setHorizontalHeaderLabels(["File", "Language", "Track name", "Default", "Forced", ""])
        self.subs.verticalHeader().hide()
        self.subs.setEditTriggers(QTableWidget.NoEditTriggers)
        self.subs.setSelectionMode(QTableWidget.NoSelection)
        self.subs.setAlternatingRowColors(True)
        h = self.subs.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        h.setSectionResizeMode(1, QHeaderView.Interactive)
        self.subs.setColumnWidth(1, 200)
        h.setSectionResizeMode(2, QHeaderView.Interactive)
        self.subs.setColumnWidth(2, 160)
        for c in (3, 4, 5):
            h.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        bl.addWidget(self.subs)
        split.addWidget(bottom)
        split.setSizes([200, 260])
        lay.addWidget(split, 1)

        out = QHBoxLayout()
        out.addWidget(QLabel("Save as:"))
        self.name_edit = QLineEdit()
        out.addWidget(self.name_edit, 1)
        self.dir_label = QLabel("")
        self.dir_label.setStyleSheet("color: gray;")
        pick = QPushButton("Folder…")
        pick.clicked.connect(self.choose_dir)
        out.addWidget(self.dir_label)
        out.addWidget(pick)
        lay.addLayout(out)

        self.panel = JobPanel()
        lay.addWidget(self.panel)
        self.go = QPushButton("Add subtitles and save")
        self.go.setObjectName("primary")
        self.go.setEnabled(False)
        self.go.clicked.connect(self.save)
        r = QHBoxLayout()
        r.addStretch(1)
        r.addWidget(self.go)
        lay.addLayout(r)
        self.out_dir = ""
        self.panel.busy_changed.connect(lambda busy: self.go.setEnabled(not busy and self._ready()))

    # ---- video
    def choose_video(self):
        p = open_files(self, "Select a video", VIDEO_FILTER, multiple=False)
        if p:
            self.load_video(p)

    def load_video(self, path):
        try:
            info = read_info(path)
        except MkvError as e:
            QMessageBox.warning(self, "Could not read file", f"{os.path.basename(path)}\n\n{e}")
            return
        self.info = info
        self.video_edit.setText(path)
        stem = naming.stem_of(path)
        self.name_edit.setText(f"{stem}_subs.mkv")
        self.out_dir = os.path.dirname(path)
        self.dir_label.setText(self.out_dir)
        self.tracks.setRowCount(0)
        for t in info.tracks:
            r = self.tracks.rowCount()
            self.tracks.insertRow(r)
            keep = QCheckBox()
            keep.setChecked(True)
            self.tracks.setCellWidget(r, 0, centered(keep))
            flags = ", ".join(x for x, on in (("default", t.default), ("forced", t.forced)) if on)
            for c, v in enumerate([t.short, t.codec, t.language, t.name, flags], start=1):
                self.tracks.setItem(r, c, QTableWidgetItem(v))
        self.go.setEnabled(self._ready())

    def _keep_ids(self):
        return {t.id for r, t in enumerate(self.info.tracks)
                if self.tracks.cellWidget(r, 0).findChild(QCheckBox).isChecked()}

    # ---- subtitles
    def choose_subs(self):
        self.add_subs(open_files(self, "Select subtitle files", SUB_FILTER))

    def add_subs(self, paths):
        for p in paths:
            self._add_row(p)
        self.go.setEnabled(self._ready())

    def _add_row(self, path):
        r = self.subs.rowCount()
        self.subs.insertRow(r)
        item = QTableWidgetItem(os.path.basename(path))
        item.setData(Qt.UserRole, path)
        item.setToolTip(path)
        self.subs.setItem(r, 0, item)
        code = langmod.detect_language(path, self.languages) or "und"
        combo = LanguageCombo(self.languages, code)
        name = QLineEdit(self._lang_name(code))
        combo.changed.connect(lambda c=combo, n=name: n.setText(self._lang_name(c.code())))
        default = QCheckBox()
        forced = QCheckBox()
        default.toggled.connect(lambda on, d=default: self._only_one_default(d, on))
        remove = QPushButton("Remove")
        remove.clicked.connect(lambda _=False, it=item: self._remove(it))
        self.subs.setCellWidget(r, 1, combo)
        self.subs.setCellWidget(r, 2, name)
        self.subs.setCellWidget(r, 3, centered(default))
        self.subs.setCellWidget(r, 4, centered(forced))
        self.subs.setCellWidget(r, 5, remove)
        self.subs.setRowHeight(r, 36)

    def _lang_name(self, code):
        for l in self.languages:
            if l.code == code:
                return "" if code == "und" else l.name
        return ""

    def _only_one_default(self, box, on):
        if not on:
            return
        for r in range(self.subs.rowCount()):
            other = self.subs.cellWidget(r, 3).findChild(QCheckBox)
            if other is not box:
                other.setChecked(False)

    def _remove(self, item):
        self.subs.removeRow(item.row())
        self.go.setEnabled(self._ready())

    def clear_subs(self):
        if self.subs.rowCount() and QMessageBox.question(
                self, "Remove all?", "Remove all subtitle files from the list?") != QMessageBox.Yes:
            return
        self.subs.setRowCount(0)
        self.go.setEnabled(self._ready())

    def _ready(self):
        return bool(self.info) and self.subs.rowCount() > 0 and not self.panel.busy

    def choose_dir(self):
        d = open_dir(self, "Choose where to save")
        if d:
            self.out_dir = d
            self.dir_label.setText(d)

    # ---- run
    def _sub_inputs(self):
        out = []
        for r in range(self.subs.rowCount()):
            out.append(commands.SubInput(
                path=self.subs.item(r, 0).data(Qt.UserRole),
                language=self.subs.cellWidget(r, 1).code(),
                name=self.subs.cellWidget(r, 2).text().strip(),
                default=self.subs.cellWidget(r, 3).findChild(QCheckBox).isChecked(),
                forced=self.subs.cellWidget(r, 4).findChild(QCheckBox).isChecked()))
        return out

    def save(self):
        mkvmerge = find_tool("mkvmerge")
        if not (mkvmerge and self.info):
            return
        name = self.name_edit.text().strip()
        if name and not name.lower().endswith(".mkv"):
            name += ".mkv"
        output = safe_output_path(self.out_dir, name)
        if not output:
            QMessageBox.warning(self, "File name", "Please enter a file name.")
            return
        if os.path.abspath(output) == os.path.abspath(self.info.path):
            QMessageBox.warning(self, "File name", "The new file can't have the same name as the original video.")
            return
        if os.path.exists(output) and QMessageBox.question(
                self, "Overwrite?", f"{os.path.basename(output)} already exists. Replace it?") != QMessageBox.Yes:
            return
        subs = self._sub_inputs()
        edits = {}
        if any(s.default for s in subs):  # the new default replaces the old default subtitle
            for t in self.info.of_type("subtitles"):
                if t.default:
                    edits[t.id] = commands.TrackEdit(default=False)
        cmd = commands.build_mux(mkvmerge, output, self.info, keep_ids=self._keep_ids(), edits=edits, subs=subs)
        self.panel.run([Job(f"Writing {os.path.basename(output)}", cmd, [output])])

    # ---- drag and drop
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        subs = [p for p in paths if os.path.splitext(p)[1].lower() in SUB_EXTS]
        vids = [p for p in paths if os.path.splitext(p)[1].lower() in VIDEO_EXTS]
        if vids:
            self.load_video(vids[0])
        if subs:
            self.add_subs(subs)
