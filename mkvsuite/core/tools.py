"""Locating the MKVToolNix command-line tools (installed from apt, never bundled)."""
import os
import shutil

REQUIRED_TOOLS = ("mkvmerge", "mkvextract", "mkvpropedit")
INSTALL_HINT = "sudo apt install mkvtoolnix"


def find_tool(name):
    return shutil.which(name)


def missing_tools():
    return [t for t in REQUIRED_TOOLS if not find_tool(t)]


def clean_env(env=None):
    """
    Environment for running the *system* MKVToolNix tools from inside a bundled app.

    PyInstaller/AppImage point LD_LIBRARY_PATH at the bundled libraries (our own Qt, ICU, ...).
    The system mkvmerge links against the system copies, so inheriting that path can break it.
    PyInstaller keeps the original value in LD_LIBRARY_PATH_ORIG.
    """
    env = dict(os.environ if env is None else env)
    if "LD_LIBRARY_PATH_ORIG" in env:
        orig = env.pop("LD_LIBRARY_PATH_ORIG")
        if orig:
            env["LD_LIBRARY_PATH"] = orig
        else:
            env.pop("LD_LIBRARY_PATH", None)
    return env
