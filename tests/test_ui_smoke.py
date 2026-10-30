"""Drives the real Qt UI offscreen: extract, add subtitles, edit in place. Skipped without PySide6/MKVToolNix."""
import os
import subprocess
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QEventLoop, QTimer
    from PySide6.QtWidgets import QApplication, QLineEdit, QMessageBox
    HAVE_QT = True
except ImportError:
    HAVE_QT = False

from mkvsuite.core.media import read_media as read_info
from mkvsuite.core.tools import missing_ffmpeg, missing_tools


def wait_for(signal, timeout_ms=20000):
    loop = QEventLoop()
    signal.connect(lambda *a: loop.quit())
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()


@unittest.skipUnless(HAVE_QT and not missing_tools(), "needs PySide6 and MKVToolNix")
class UiSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.Yes)   # auto-confirm dialogs
        QMessageBox.warning = staticmethod(lambda *a, **k: cls.fail_dialog(*a))
        from mkvsuite.ui.main_window import MainWindow
        from mkvsuite.ui.widgets import LanguageCombo, unwrap
        globals()["LanguageCombo"], globals()["unwrap"] = LanguageCombo, unwrap
        cls.win = MainWindow()

    @staticmethod
    def fail_dialog(*a):
        raise AssertionError("unexpected warning dialog: " + " ".join(str(x) for x in a[1:]))

    def make_files(self, d):
        en, pt = os.path.join(d, "en.srt"), os.path.join(d, "pt.srt")
        for p, text in ((en, "Hello"), (pt, "Olá")):
            with open(p, "w", encoding="utf-8") as f:
                f.write(f"1\n00:00:00,000 --> 00:00:01,000\n{text}\n")
        base = os.path.join(d, "Show.S01E01.mkv")
        subprocess.run(["mkvmerge", "-o", base, "--language", "0:eng", "--forced-display-flag", "0:1", en],
                       capture_output=True, check=True)
        return base, pt

    def test_extract_add_edit(self):
        with tempfile.TemporaryDirectory() as d:
            base, pt = self.make_files(d)

            # --- Extract
            ex = self.win.pages[0]
            ex.add_paths([base])
            wait_for(ex._loaders[0].finished) if ex._loaders else None
            self.app.processEvents()
            self.assertEqual(ex.tree.topLevelItemCount(), 1)
            ex.extract()
            wait_for(ex.panel.all_done)
            out = os.path.join(d, "Show.S01E01.eng.forced.srt")
            self.assertTrue(os.path.exists(out), os.listdir(d))

            # --- Add subtitles (detects Portuguese from 'pt.srt'; forced flag of the original survives)
            ad = self.win.pages[1]
            ad.load_video(base)
            ad.add_subs([pt])
            self.assertEqual(unwrap(ad.subs.cellWidget(0, 1), LanguageCombo).code(), "por")
            ad.save()
            wait_for(ad.panel.all_done)
            new = os.path.join(d, "Show.S01E01_subs.mkv")
            info = read_info(new)
            self.assertEqual([(t.language, t.forced) for t in info.tracks], [("eng", True), ("por", False)])

            # --- Edit in place: Czech (not in the old app's list) + name
            ed = self.win.pages[2]
            ed.load(new)
            unwrap(ed.table.cellWidget(1, 2), LanguageCombo).set_code("cze")
            unwrap(ed.table.cellWidget(1, 3), QLineEdit).setText("Cesky")
            ed.apply_in_place()
            wait_for(ed.panel.all_done)
            info = read_info(new)
            self.assertEqual((info.tracks[1].language, info.tracks[1].name), ("cze", "Cesky"))
            self.assertTrue(info.tracks[0].forced)

    @unittest.skipIf(missing_ffmpeg(), "ffmpeg not installed")
    def test_mp4_through_the_ui(self):
        with tempfile.TemporaryDirectory() as d:
            en, pt = os.path.join(d, "en.srt"), os.path.join(d, "pt.srt")
            for p, text in ((en, "Hello"), (pt, "Ol\u00e1")):
                with open(p, "w", encoding="utf-8") as f:
                    f.write(f"1\n00:00:00,000 --> 00:00:01,000\n{text}\n")
            mp4 = os.path.join(d, "Clip.mp4")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=d=2:s=160x120", "-i", en,
                            "-map", "0", "-map", "1", "-c:v", "libx264", "-c:s", "mov_text",
                            "-metadata:s:s:0", "language=eng", mp4], check=True)

            ex = self.win.pages[0]
            ex.clear()
            ex.add_paths([mp4])
            while ex._loaders:
                self.app.processEvents()
            self.assertEqual(ex.tree.topLevelItemCount(), 1)
            ex.extract()
            wait_for(ex.panel.all_done)
            out = os.path.join(d, "Clip.eng.srt")      # mov_text came out as a real .srt
            with open(out, encoding="utf-8") as f:
                self.assertIn("Hello", f.read())

            ad = self.win.pages[1]
            ad.subs.setRowCount(0)          # the page is shared with the previous test
            ad.load_video(mp4)
            self.assertEqual(ad.fmt.currentData(), ".mp4")   # follows the input
            ad.add_subs([pt])
            ad.save()
            wait_for(ad.panel.all_done)
            info = read_info(os.path.join(d, "Clip_subs.mp4"))
            self.assertEqual([t.language for t in info.of_type("subtitles")], ["eng", "por"])


if __name__ == "__main__":
    unittest.main()
