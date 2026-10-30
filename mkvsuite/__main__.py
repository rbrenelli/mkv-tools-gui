import argparse
import sys


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mkv-tool-suite", description="MKV Tool Suite")
    ap.add_argument("files", nargs="*", help="video files to open in Extract Tracks")
    ap.add_argument("--selftest", metavar="MKV", help="check the MKVToolNix tools work from this build, then exit")
    ap.add_argument("--install-launcher", action="store_true", help="add the app-menu launcher for this AppImage")
    ap.add_argument("--uninstall-launcher", action="store_true", help="remove the app-menu launcher")
    ap.add_argument("--shot", metavar="PNG", help="(testing) save a screenshot of each page and exit")
    args, qt_args = ap.parse_known_args(argv)

    if args.selftest:
        return selftest(args.selftest)
    if args.uninstall_launcher or args.install_launcher:
        from . import launcher
        from .ui.main_window import ICON_PATH
        if args.uninstall_launcher:
            launcher.uninstall()
            print("Launcher removed.")
            return 0
        exe = launcher.appimage_path()
        if not exe:
            print("Not running as an AppImage; nothing to install.", file=sys.stderr)
            return 1
        print("Launcher installed:", launcher.install(exe, ICON_PATH))
        return 0

    from PySide6.QtWidgets import QApplication
    app = QApplication([sys.argv[0]] + qt_args)
    app.setApplicationName("mkv-tool-suite")
    app.setOrganizationName("rbrenelli")
    app.setDesktopFileName("mkv-tool-suite")
    from .ui.main_window import MainWindow
    win = MainWindow(args.files)
    win.show()
    if args.shot:
        from PySide6.QtCore import QTimer

        def grab():
            base = args.shot[:-4] if args.shot.endswith(".png") else args.shot
            for i, p in enumerate(win.pages):
                win.nav.setCurrentRow(i)
                app.processEvents()
                win.grab().save(f"{base}-{i}.png")
            app.quit()
        QTimer.singleShot(1500, grab)
    return app.exec()


def selftest(path):
    """Runs the same code the GUI uses, without a display. Used by CI on the packaged build."""
    from .core import languages, tools
    from .core.model import read_info
    missing = tools.missing_tools()
    if missing:
        print("missing tools:", ", ".join(missing))
        return 2
    info = read_info(path)
    langs = languages.load_languages()
    print(f"OK: {len(info.tracks)} tracks, {len(langs)} languages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
