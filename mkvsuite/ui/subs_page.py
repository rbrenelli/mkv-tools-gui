import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..core import commands, ffmpeg, languages as langmod, naming, plan
from ..core.media import read_media
from ..core.model import MkvError
from ..core.paths import safe_output_path
from .runner import Job
from .widgets import (ROW_HEIGHT, SUB_EXTS, SUB_FILTER, VIDEO_EXTS, VIDEO_FILTER, JobPanel, LanguageCombo, card,
                      centered, muted, open_dir, open_files, padded, page_header, scroll_body, section, show_problem, unwrap)


def make_table(columns):
    t = QTableWidget(0, len(columns))
    t.setHorizontalHeaderLabels(columns)
    t.verticalHeader().hide()
    t.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setSelectionMode(QAbstractItemView.NoSelection)
    t.setFocusPolicy(Qt.NoFocus)
    t.setShowGrid(False)
    t.setAlternatingRowColors(True)
    t.setTextElideMode(Qt.ElideMiddle)
    t.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    t.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    t.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
    return t


class AddSubsPage(QWidget):
    title = "Add Subtitles"

    def __init__(self, languages):
        super().__init__()
        self.languages = languages
        self.info = None
        self.out_dir = ""
        self.setAcceptDrops(True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        area, lay = scroll_body()
        root.addWidget(area, 1)
        page_header(lay, "Add Subtitles",
                    "Pick a video, add subtitle files (for example your translations) and save a new file. "
                    "Nothing is re-encoded and the original is never touched.")

        # --- video + its tracks
        vbox = QVBoxLayout()
        row = QHBoxLayout()
        self.video_edit = QLineEdit()
        self.video_edit.setReadOnly(True)
        self.video_edit.setPlaceholderText("Choose a video, or drop one on this window…")
        b = QPushButton("Choose video…")
        b.clicked.connect(self.choose_video)
        row.addWidget(self.video_edit, 1)
        row.addWidget(b)
        vbox.addLayout(row)
        self.tracks_title = section("Tracks in the video")
        vbox.addWidget(self.tracks_title)
        self.tracks = make_table(["Keep", "Track", "Codec", "Language", "Name", "Flags"])
        self.tracks.setMinimumHeight(130)
        h = self.tracks.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Interactive)
        for c, w in ((0, 70), (1, 130), (2, 200), (3, 110), (5, 130)):
            self.tracks.setColumnWidth(c, w)
        h.setSectionResizeMode(4, QHeaderView.Stretch)
        vbox.addWidget(self.tracks)
        lay.addWidget(card(vbox), 2)

        # --- subtitles to add
        sbox = QVBoxLayout()
        bar = QHBoxLayout()
        bar.addWidget(section("Subtitles to add"))
        bar.addStretch(1)
        add = QPushButton("Add subtitle files…")
        add.clicked.connect(self.choose_subs)
        rm = QPushButton("Remove all")
        rm.clicked.connect(self.clear_subs)
        bar.addWidget(add)
        bar.addWidget(rm)
        sbox.addLayout(bar)
        self.empty_hint = muted("No subtitle files yet. Add .srt / .ass files, or drop them on this window.")
        sbox.addWidget(self.empty_hint)
        self.subs = make_table(["File", "Language", "Track name", "Default", "Forced", ""])
        self.subs.setMinimumHeight(130)
        h = self.subs.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.Interactive)
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        for c, w in ((1, 230), (2, 190), (3, 80), (4, 80), (5, 110)):
            self.subs.setColumnWidth(c, w)
        sbox.addWidget(self.subs)
        lay.addWidget(card(sbox), 3)

        # --- output + run
        obox = QVBoxLayout()
        orow = QHBoxLayout()
        orow.addWidget(QLabel("Save as:"))
        self.fmt = QComboBox()
        self.fmt.addItem("MKV", ".mkv")
        self.fmt.addItem("MP4", ".mp4")
        self.fmt.currentIndexChanged.connect(self._fmt_changed)
        self.name_edit = QLineEdit()
        self.ext_label = QLabel(".mkv")
        pick = QPushButton("Folder…")
        pick.clicked.connect(self.choose_dir)
        orow.addWidget(self.fmt)
        orow.addWidget(self.name_edit, 1)
        orow.addWidget(self.ext_label)
        orow.addWidget(pick)
        obox.addLayout(orow)
        self.fmt_hint = muted("")
        obox.addWidget(self.fmt_hint)
        self.panel = JobPanel()
        obox.addWidget(self.panel)
        r = QHBoxLayout()
        r.addStretch(1)
        self.go = QPushButton("Add subtitles and save")
        self.go.setObjectName("primary")
        self.go.setEnabled(False)
        self.go.clicked.connect(self.save)
        r.addWidget(self.go)
        obox.addLayout(r)
        root.addWidget(card(obox))
        self.panel.busy_changed.connect(lambda _b: self._refresh())
        self._fmt_changed()
        self._refresh()

    # ---- video
    def choose_video(self):
        p = open_files(self, "Select a video", VIDEO_FILTER, multiple=False)
        if p:
            self.load_video(p)

    def load_video(self, path):
        try:
            info = read_media(path)
        except MkvError as e:
            show_problem(self, "Could not read file", f"{os.path.basename(path)}\n\n{e}")
            return
        self.info = info
        self.video_edit.setText(path)
        self.name_edit.setText(f"{naming.stem_of(path)}_subs")
        self.out_dir = os.path.dirname(path)
        self._set_dir_note()
        self.fmt.setCurrentIndex(1 if os.path.splitext(path)[1].lower() in ffmpeg.MP4_EXTS else 0)
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
        self._refresh()

    def _keep_ids(self):
        return {t.id for r, t in enumerate(self.info.tracks) if unwrap(self.tracks.cellWidget(r, 0), QCheckBox).isChecked()}

    # ---- subtitles
    def choose_subs(self):
        self.add_subs(open_files(self, "Select subtitle files", SUB_FILTER))

    def add_subs(self, paths):
        for p in paths:
            self._add_row(p)
        self._refresh()

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
        default, forced = QCheckBox(), QCheckBox()
        default.toggled.connect(lambda on, d=default: self._only_one_default(d, on))
        remove = QPushButton("Remove")
        remove.setObjectName("rowbtn")
        remove.clicked.connect(lambda _=False, it=item: self._remove(it))
        self.subs.setCellWidget(r, 1, padded(combo))
        self.subs.setCellWidget(r, 2, padded(name))
        self.subs.setCellWidget(r, 3, centered(default))
        self.subs.setCellWidget(r, 4, centered(forced))
        self.subs.setCellWidget(r, 5, padded(remove))
        self.subs.setRowHeight(r, ROW_HEIGHT + 10)

    def _lang_name(self, code):
        for l in self.languages:
            if l.code == code:
                return "" if code == "und" else l.name
        return ""

    def _only_one_default(self, box, on):
        if not on:
            return
        for r in range(self.subs.rowCount()):
            other = unwrap(self.subs.cellWidget(r, 3), QCheckBox)
            if other is not box:
                other.setChecked(False)

    def _remove(self, item):
        self.subs.removeRow(item.row())
        self._refresh()

    def clear_subs(self):
        if self.subs.rowCount() and QMessageBox.question(
                self, "Remove all?", "Remove all subtitle files from the list?") != QMessageBox.Yes:
            return
        self.subs.setRowCount(0)
        self._refresh()

    def _refresh(self):
        self.empty_hint.setVisible(self.subs.rowCount() == 0)
        ready = bool(self.info) and self.subs.rowCount() > 0 and not self.panel.busy
        self.go.setEnabled(ready)

    def _set_dir_note(self):
        if not self.panel.busy:
            self.panel.status.setText(f"Will be saved in {self.out_dir}")

    def _fmt_changed(self):
        mp4 = self.fmt.currentData() == ".mp4"
        self.ext_label.setText(self.fmt.currentData())
        self.fmt_hint.setText("MP4 keeps only text subtitles (SRT/ASS become mov_text), and track names may not show "
                              "in every player. Pick MKV to keep everything." if mp4 else "")
        self.fmt_hint.setVisible(mp4)

    def choose_dir(self):
        d = open_dir(self, "Choose where to save")
        if d:
            self.out_dir = d
            self._set_dir_note()

    # ---- run
    def _sub_inputs(self):
        out = []
        for r in range(self.subs.rowCount()):
            out.append(commands.SubInput(
                path=self.subs.item(r, 0).data(Qt.UserRole),
                language=unwrap(self.subs.cellWidget(r, 1), LanguageCombo).code(),
                name=unwrap(self.subs.cellWidget(r, 2), QLineEdit).text().strip(),
                default=unwrap(self.subs.cellWidget(r, 3), QCheckBox).isChecked(),
                forced=unwrap(self.subs.cellWidget(r, 4), QCheckBox).isChecked()))
        return out

    def save(self):
        if not self.info:
            return
        name = self.name_edit.text().strip()
        if name.lower().endswith((".mkv", ".mp4")):
            name = os.path.splitext(name)[0]
        output = safe_output_path(self.out_dir, name + self.fmt.currentData()) if name else None
        if not output:
            QMessageBox.warning(self, "File name", "Please enter a file name.")
            return
        if os.path.abspath(output) == os.path.abspath(self.info.path):
            QMessageBox.warning(self, "File name", "The new file can't have the same name as the original video.")
            return
        if os.path.exists(output) and QMessageBox.question(
                self, "Replace file?", f"{os.path.basename(output)} already exists. Replace it?") != QMessageBox.Yes:
            return
        subs = self._sub_inputs()
        edits = {}
        if any(s.default for s in subs):  # the new default replaces the old default subtitle
            for t in self.info.of_type("subtitles"):
                if t.default:
                    edits[t.id] = commands.TrackEdit(default=False)
        try:
            p = plan.mux(self.info, output, keep_ids=self._keep_ids(), edits=edits, subs=subs)
        except (plan.ToolMissing, ffmpeg.UnsupportedError) as e:
            show_problem(self, "Can't do that", e)
            return
        self.panel.run([Job(f"Writing {os.path.basename(output)}", p.argv, [output], p.kind, p.duration_ns)])

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
