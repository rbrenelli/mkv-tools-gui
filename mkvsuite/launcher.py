"""Add/remove an app-menu launcher (the clickable icon) for an AppImage. No GUI imports."""
import os
import shutil

APP_ID = "mkv-tool-suite"


def _dirs():
    data = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return (os.path.join(data, "applications"), os.path.join(data, "icons", "hicolor", "256x256", "apps"))


def desktop_path():
    return os.path.join(_dirs()[0], f"{APP_ID}.desktop")


def appimage_path():
    """Path of the running AppImage (set by the AppImage runtime), else None."""
    p = os.environ.get("APPIMAGE")
    return p if p and os.path.isfile(p) else None


def desktop_entry(exec_path, icon="mkv-tool-suite"):
    exec_q = '"' + exec_path.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=MKV Tool Suite\n"
        "Comment=Extract, add and edit tracks in MKV files\n"
        f"Exec={exec_q} %f\n"
        f"Icon={icon}\n"
        "Categories=AudioVideo;Video;\n"
        "MimeType=video/x-matroska;\n"
        "Terminal=false\n"
        f"StartupWMClass={APP_ID}\n"
    )


def is_installed(exec_path=None):
    p = desktop_path()
    if not os.path.isfile(p):
        return False
    if exec_path is None:
        return True
    with open(p, encoding="utf-8") as f:
        return exec_path in f.read()


def install(exec_path, icon_png):
    apps, icons = _dirs()
    os.makedirs(apps, exist_ok=True)
    os.makedirs(icons, exist_ok=True)
    shutil.copyfile(icon_png, os.path.join(icons, f"{APP_ID}.png"))
    with open(desktop_path(), "w", encoding="utf-8") as f:
        f.write(desktop_entry(exec_path))
    return desktop_path()


def uninstall():
    apps, icons = _dirs()
    for p in (desktop_path(), os.path.join(icons, f"{APP_ID}.png")):
        try:
            os.remove(p)
        except OSError:
            pass
