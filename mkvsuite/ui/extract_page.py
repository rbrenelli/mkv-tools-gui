import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QButtonGroup, QHBoxLayout, QLabel, QMessageBox, QPushButton, QRadioButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from ..core import commands, naming
from ..core.paths import safe_output_path
from ..core.tools import find_tool
from .runner import InfoLoader, Job
from .widgets import (VIDEO_EXTS, VIDEO_FILTER, JobPanel, OnlyColumnDelegate, open_dir, open_files)

COL_TRACK, COL_CODEC, COL_LANG, COL_NAME, COL_OUT = range(5)
ROLE_TRACK = Qt.UserRole + 1
ROLE_PATH = Qt.UserRole + 2


class ExtractPage(QWidget):
    title = "Extract Tracks"

    def __init__(self, languages):
        super().__init__()
        self.setAcceptDrops(True)
        self._loaders = []
        self._custom_dir = None

        lay = QVBoxLayout(self)
        head = QLabel("Extract Tracks")
        head.setObjectName("pageTitle")
        lay.addWidget(head)
        hint = QLabel("Add one or more videos. Text subtitle tracks are ticked for you; tick anything else you want, "
                      "edit the output names if needed, then extract.")
        hint.setWordWrap(True)
        lay.addWidget(hint)

        bar = QHBoxLayout()
        add = QPushButton("Add videos…")
        add.clicked.connect(self.add_videos)
        folder = QPushButton("Add folder…")
        folder.clicked.connect(self.add_folder)
        clear = QPushButton("Clear")
        clear.clicked.connect(self.clear)
        self.subs_btn = QPushButton("Tick all subtitles")
        self.subs_btn.clicked.connect(lambda: self._tick(lambda t: t.type == "subtitles"))
        all_btn = QPushButton("Tick all")
        all_btn.clicked.connect(lambda: self._tick(lambda t: True))
        none_btn = QPushButton("Untick all")
        none_btn.clicked.connect(lambda: self._tick(lambda t: False))
        for b in (add, folder, clear):
            bar.addWidget(b)
        bar.addStretch(1)
        for b in (self.subs_btn, all_btn, none_btn):
            bar.addWidget(b)
        lay.addLayout(bar)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["Track", "Codec", "Language", "Name", "Output file name"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.tree.setItemDelegate(OnlyColumnDelegate(COL_OUT, self.tree))
        self.tree.setUniformRowHeights(True)
        self.tree.header().setStretchLastSection(True)
        self.tree.setColumnWidth(COL_TRACK, 200)
        self.tree.setColumnWidth(COL_CODEC, 120)
        self.tree.setColumnWidth(COL_LANG, 80)
        self.tree.setColumnWidth(COL_NAME, 150)
        self.empty = QLabel("Drop video files here, or use “Add videos…”")
        self.empty.setAlignment(Qt.AlignCenter)
        self.empty.setStyleSheet("color: gray; font-size: 15px;")
        lay.addWidget(self.empty, 1)
        lay.addWidget(self.tree, 1)
        self.tree.hide()

        out = QHBoxLayout()
        out.addWidget(QLabel("Save to:"))
        self.same_rb = QRadioButton("Same folder as each video")
        self.same_rb.setChecked(True)
        self.other_rb = QRadioButton("Folder:")
        self.dir_label = QLabel("(not chosen)")
        self.dir_label.setStyleSheet("color: gray;")
        pick = QPushButton("Choose…")
        pick.clicked.connect(self.choose_dir)
        grp = QButtonGroup(self)
        grp.addButton(self.same_rb)
        grp.addButton(self.other_rb)
        out.addWidget(self.same_rb)
        out.addWidget(self.other_rb)
        out.addWidget(self.dir_label, 1)
        out.addWidget(pick)
        lay.addLayout(out)

        self.panel = JobPanel()
        lay.addWidget(self.panel)
        self.go = QPushButton("Extract ticked tracks")
        self.go.setObjectName("primary")
        self.go.clicked.connect(self.extract)
        self.go.setEnabled(False)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.go)
        lay.addLayout(row)
        self.panel.busy_changed.connect(lambda busy: self.go.setEnabled(not busy and self.tree.topLevelItemCount() > 0))

    # ---- adding files
    def add_videos(self):
        paths = open_files(self, "Select videos", VIDEO_FILTER)
        self.add_paths(paths)

    def add_folder(self):
        d = open_dir(self, "Select a folder with videos")
        if d:
            self.add_paths(sorted(os.path.join(d, f) for f in os.listdir(d)
                                  if os.path.splitext(f)[1].lower() in VIDEO_EXTS))

    def add_paths(self, paths):
        known = {self.tree.topLevelItem(i).data(0, ROLE_PATH) for i in range(self.tree.topLevelItemCount())}
        new = [p for p in paths if p not in known]
        if not new:
            return
        loader = InfoLoader(new, self)
        loader.loaded.connect(self._add_file)
        loader.failed.connect(self._failed)
        loader.finished.connect(lambda l=loader: self._loaders.remove(l))
        self._loaders.append(loader)
        loader.start()

    def _failed(self, path, msg):
        QMessageBox.warning(self, "Could not read file", f"{os.path.basename(path)}\n\n{msg}")

    def _add_file(self, path, info):
        item = QTreeWidgetItem(self.tree, [os.path.basename(path)])
        item.setData(0, ROLE_PATH, path)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
        item.setToolTip(0, path)
        stem = naming.stem_of(path)
        taken = set()
        for t in info.tracks:
            if t.type not in ("video", "audio", "subtitles"):
                continue
            name = naming.default_name(stem, t, taken)
            taken.add(name)
            child = QTreeWidgetItem(item, [t.short, t.codec, t.language, t.name, name])
            child.setData(0, ROLE_TRACK, t)
            child.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
            child.setCheckState(0, Qt.Checked if t.type == "subtitles" and t.text_subtitles else Qt.Unchecked)
        item.setExpanded(True)
        self.empty.hide()
        self.tree.show()
        self.go.setEnabled(not self.panel.busy)

    def clear(self):
        self.tree.clear()
        self.tree.hide()
        self.empty.show()
        self.go.setEnabled(False)

    def _tick(self, pred):
        for i in range(self.tree.topLevelItemCount()):
            f = self.tree.topLevelItem(i)
            for j in range(f.childCount()):
                c = f.child(j)
                c.setCheckState(0, Qt.Checked if pred(c.data(0, ROLE_TRACK)) else Qt.Unchecked)

    def choose_dir(self):
        d = open_dir(self, "Choose where to save the tracks")
        if d:
            self._custom_dir = d
            self.dir_label.setText(d)
            self.other_rb.setChecked(True)

    # ---- running
    def extract(self):
        if not find_tool("mkvextract"):
            return
        jobs, all_outputs, problems = [], [], []
        for i in range(self.tree.topLevelItemCount()):
            f = self.tree.topLevelItem(i)
            src = f.data(0, ROLE_PATH)
            out_dir = self._custom_dir if (self.other_rb.isChecked() and self._custom_dir) else os.path.dirname(src)
            mapping = {}
            for j in range(f.childCount()):
                c = f.child(j)
                if c.checkState(0) != Qt.Checked:
                    continue
                target = safe_output_path(out_dir, c.text(COL_OUT))
                if not target:
                    problems.append(f"{os.path.basename(src)}: invalid file name for {c.data(0, ROLE_TRACK).short}")
                    continue
                mapping[c.data(0, ROLE_TRACK).id] = target
            if mapping:
                if len(set(mapping.values())) != len(mapping):
                    problems.append(f"{os.path.basename(src)}: two tracks have the same output name")
                outs = list(mapping.values())
                all_outputs += outs
                jobs.append(Job(f"Extracting {os.path.basename(src)}",
                                commands.build_extract(find_tool("mkvextract"), src, mapping), outs))
        if len(set(all_outputs)) != len(all_outputs):
            problems.append("Some tracks from different files would be written to the same file name.")
        if problems:
            QMessageBox.warning(self, "Check the names", "\n".join(problems))
            return
        if not jobs:
            QMessageBox.information(self, "Nothing to extract", "Tick at least one track.")
            return
        existing = [p for p in all_outputs if os.path.exists(p)]
        if existing:
            shown = "\n".join(os.path.basename(p) for p in existing[:8]) + ("\n…" if len(existing) > 8 else "")
            if QMessageBox.question(self, "Overwrite files?",
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
            files += sorted(os.path.join(d, f) for f in os.listdir(d) if os.path.splitext(f)[1].lower() in VIDEO_EXTS)
        self.add_paths(files)
