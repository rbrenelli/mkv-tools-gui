import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView, QButtonGroup, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QRadioButton,
    QStackedWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from ..core import ffmpeg, naming, plan
from ..core.paths import safe_output_path
from .runner import InfoLoader, Job
from .widgets import (VIDEO_EXTS, VIDEO_FILTER, DropZone, JobPanel, RowDelegate, card, muted, open_dir, open_files,
                      page_header, show_problem)

COL_TRACK, COL_CODEC, COL_LANG, COL_NAME, COL_OUT = range(5)
ROLE_TRACK = Qt.UserRole + 1
ROLE_PATH = Qt.UserRole + 2
ROLE_INFO = Qt.UserRole + 3


def videos_in(folder):
    return sorted(os.path.join(folder, f) for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in VIDEO_EXTS)


class ExtractPage(QWidget):
    title = "Extract Tracks"

    def __init__(self, languages):
        super().__init__()
        self.setAcceptDrops(True)
        self._loaders = []
        self._custom_dir = None

        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        page_header(lay, "Extract Tracks",
                    "Add videos, tick the tracks you want, and save them as files. Text subtitles are ticked for you; "
                    "double-click an output name to change it.")

        bar = QHBoxLayout()
        bar.setSpacing(8)
        for text, cb in (("Add videos…", self.add_videos), ("Add folder…", self.add_folder),
                         ("Remove selected", self.remove_selected), ("Clear", self.clear)):
            b = QPushButton(text)
            b.clicked.connect(cb)
            bar.addWidget(b)
        bar.addStretch(1)
        for text, pred in (("Tick subtitles", lambda t: t.type == "subtitles"), ("Tick all", lambda t: True),
                           ("Untick all", lambda t: False)):
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, p=pred: self._tick(p))
            bar.addWidget(b)
        lay.addLayout(bar)

        self.stack = QStackedWidget()
        self.empty = DropZone("Drop videos here", "MKV, MP4, M4V, MOV, AVI — or a whole folder",
                              [("Add videos…", self.add_videos, True), ("Add folder…", self.add_folder, False)])
        self.stack.addWidget(self.empty)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["Track", "Codec", "Language", "Name", "Output file name"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.tree.setItemDelegate(RowDelegate(self.tree, edit_column=COL_OUT))
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setTextElideMode(Qt.ElideMiddle)
        self.tree.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tree.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tree.setIndentation(18)
        self.tree.header().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.tree.setMinimumHeight(220)
        h = self.tree.header()
        h.setStretchLastSection(True)
        h.setSectionResizeMode(COL_TRACK, QHeaderView.Interactive)
        h.setSectionResizeMode(COL_CODEC, QHeaderView.Interactive)
        h.setSectionResizeMode(COL_LANG, QHeaderView.Interactive)
        h.setSectionResizeMode(COL_NAME, QHeaderView.Interactive)
        for col, w in ((COL_TRACK, 170), (COL_CODEC, 200), (COL_LANG, 100), (COL_NAME, 170)):
            self.tree.setColumnWidth(col, w)
        self.tree.itemChanged.connect(lambda *_: self._update_button())
        self.stack.addWidget(self.tree)
        lay.addWidget(self.stack, 1)

        foot = QVBoxLayout()
        out = QHBoxLayout()
        out.addWidget(QLabel("Save to:"))
        self.same_rb = QRadioButton("Next to each video")
        self.same_rb.setChecked(True)
        self.other_rb = QRadioButton("Folder")
        grp = QButtonGroup(self)
        grp.addButton(self.same_rb)
        grp.addButton(self.other_rb)
        self.dir_label = muted("")
        pick = QPushButton("Choose…")
        pick.clicked.connect(self.choose_dir)
        out.addSpacing(8)
        out.addWidget(self.same_rb)
        out.addWidget(self.other_rb)
        out.addWidget(self.dir_label, 1)
        out.addWidget(pick)
        foot.addLayout(out)
        self.panel = JobPanel()
        foot.addWidget(self.panel)
        row = QHBoxLayout()
        row.addStretch(1)
        self.go = QPushButton("Extract")
        self.go.setObjectName("primary")
        self.go.clicked.connect(self.extract)
        row.addWidget(self.go)
        foot.addLayout(row)
        lay.addWidget(card(foot))
        self.panel.busy_changed.connect(lambda _b: self._update_button())
        self._update_button()

    # ---- adding files
    def add_videos(self):
        self.add_paths(open_files(self, "Select videos", VIDEO_FILTER))

    def add_folder(self):
        d = open_dir(self, "Select a folder with videos")
        if d:
            self.add_paths(videos_in(d))

    def add_paths(self, paths):
        known = {self.tree.topLevelItem(i).data(0, ROLE_PATH) for i in range(self.tree.topLevelItemCount())}
        new = [p for p in paths if p not in known]
        if not new:
            return
        loader = InfoLoader(new, self)
        loader.loaded.connect(self._add_file)
        loader.failed.connect(lambda path, msg: show_problem(self, "Could not read file", f"{os.path.basename(path)}\n\n{msg}"))
        loader.finished.connect(lambda l=loader: self._loaders.remove(l))
        self._loaders.append(loader)
        loader.start()

    def _add_file(self, path, info):
        self.tree.blockSignals(True)
        item = QTreeWidgetItem(self.tree, [os.path.basename(path)])
        item.setData(0, ROLE_PATH, path)
        item.setData(0, ROLE_INFO, info)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
        f = QFont(self.font())
        f.setBold(True)
        item.setFont(0, f)
        item.setToolTip(0, path)
        item.setFirstColumnSpanned(True)
        stem = naming.stem_of(path)
        taken = set()
        for t in info.tracks:
            name = naming.default_name(stem, t, taken)
            taken.add(name)
            child = QTreeWidgetItem(item, [t.short, t.codec, t.language, t.name, name])
            child.setData(0, ROLE_TRACK, t)
            child.setToolTip(COL_OUT, name)
            child.setToolTip(COL_CODEC, t.codec)
            child.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
            child.setCheckState(0, Qt.Checked if t.type == "subtitles" and t.text_subtitles else Qt.Unchecked)
        item.setExpanded(True)
        self.tree.blockSignals(False)
        self.stack.setCurrentWidget(self.tree)
        self._update_button()

    def remove_selected(self):
        for it in self.tree.selectedItems():
            top = it if it.parent() is None else it.parent()
            idx = self.tree.indexOfTopLevelItem(top)
            if idx >= 0:
                self.tree.takeTopLevelItem(idx)
        self._after_removal()

    def clear(self):
        self.tree.clear()
        self._after_removal()

    def _after_removal(self):
        if self.tree.topLevelItemCount() == 0:
            self.stack.setCurrentWidget(self.empty)
        self._update_button()

    def _tick(self, pred):
        self.tree.blockSignals(True)
        for i in range(self.tree.topLevelItemCount()):
            f = self.tree.topLevelItem(i)
            for j in range(f.childCount()):
                c = f.child(j)
                c.setCheckState(0, Qt.Checked if pred(c.data(0, ROLE_TRACK)) else Qt.Unchecked)
        self.tree.blockSignals(False)
        self.tree.viewport().update()
        self._update_button()

    def _ticked_count(self):
        n = 0
        for i in range(self.tree.topLevelItemCount()):
            f = self.tree.topLevelItem(i)
            n += sum(f.child(j).checkState(0) == Qt.Checked for j in range(f.childCount()))
        return n

    def _update_button(self):
        n = self._ticked_count()
        self.go.setText("Extract" if n == 0 else f"Extract {n} track{'s' if n != 1 else ''}")
        self.go.setEnabled(n > 0 and not self.panel.busy)

    def choose_dir(self):
        d = open_dir(self, "Choose where to save the tracks")
        if d:
            self._custom_dir = d
            self.dir_label.setText(d)
            self.other_rb.setChecked(True)

    # ---- running
    def extract(self):
        jobs, all_outputs, problems = [], [], []
        for i in range(self.tree.topLevelItemCount()):
            f = self.tree.topLevelItem(i)
            src = f.data(0, ROLE_PATH)
            info = f.data(0, ROLE_INFO)
            out_dir = self._custom_dir if (self.other_rb.isChecked() and self._custom_dir) else os.path.dirname(src)
            mapping = {}
            for j in range(f.childCount()):
                c = f.child(j)
                if c.checkState(0) != Qt.Checked:
                    continue
                t = c.data(0, ROLE_TRACK)
                target = safe_output_path(out_dir, c.text(COL_OUT))
                if not target:
                    problems.append(f"{os.path.basename(src)}: invalid file name for {t.short}")
                    continue
                mapping[t.id] = target
            if not mapping:
                continue
            if len(set(mapping.values())) != len(mapping):
                problems.append(f"{os.path.basename(src)}: two tracks have the same output name")
            try:
                p = plan.extract(info, mapping)
            except (plan.ToolMissing, ffmpeg.UnsupportedError) as e:
                show_problem(self, "Can't extract", e)
                return
            outs = list(mapping.values())
            all_outputs += outs
            jobs.append(Job(f"Extracting from {os.path.basename(src)}", p.argv, outs, p.kind, p.duration_ns))
        if len(set(all_outputs)) != len(all_outputs):
            problems.append("Some tracks from different files would be written to the same file name.")
        if problems:
            QMessageBox.warning(self, "Check the names", "\n".join(problems))
            return
        existing = [p for p in all_outputs if os.path.exists(p)]
        if existing:
            shown = "\n".join(os.path.basename(p) for p in existing[:8]) + ("\n…" if len(existing) > 8 else "")
            if QMessageBox.question(self, "Replace files?",
                                    f"{len(existing)} file(s) already exist and will be replaced:\n\n{shown}") != QMessageBox.Yes:
                return
        self.panel.run(jobs)

    # ---- drag and drop
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        files = [p for p in paths if os.path.isfile(p)]
        for d in (p for p in paths if os.path.isdir(p)):
            files += videos_in(d)
        self.add_paths(files)
