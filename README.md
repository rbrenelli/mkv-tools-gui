# MKV Tool Suite

A desktop app for the everyday jobs on video files: **pull subtitles out**, **put translated subtitles back in**,
and **fix track languages, names and flags**. It is a friendly front end for
[MKVToolNix](https://mkvtoolnix.download/) (and `ffmpeg` for MP4), built with Python and Qt 6, and shipped as a
single AppImage for **x86_64** and **aarch64** (including ChromeOS Linux / Crostini).

## What it does

- **Extract Tracks** — add one video, many videos, or a whole folder. Text subtitles are ticked for you; tick any
  other track you want. Output names are generated (`Show.S01E01.eng.srt`) and editable. Several files at once,
  with progress and a Cancel button.
- **Add Subtitles** — pick a video, add subtitle files (`.srt`, `.ass`, …) and save a new MKV or MP4. The language
  is guessed from the file name (`pt.srt`, `Movie.pt-BR.srt`). Nothing is re-encoded and the original is never touched.
- **Edit Tracks** — change language (searchable ISO 639-2 list), name, and the default / forced / enabled flags.
  **Apply in place** (MKV) takes seconds even for huge files. Dropping tracks, or editing an MP4, saves a new file.
- MKV, MP4, M4V, MOV, AVI and WebM; drag-and-drop; remembers the last folder; light and dark themes.

Existing flags (for example *forced*) are preserved unless you change them.

## Install

1. Install the tools the app drives (the app shows this command if something is missing):

   ```bash
   sudo apt install mkvtoolnix        # MKV
   sudo apt install ffmpeg            # only needed for MP4 / AVI / MOV
   ```

2. Download the AppImage for your machine from the
   [latest release](https://github.com/rbrenelli/mkv-tools-gui/releases/latest):
   `MKVToolSuite-aarch64.AppImage` (ARM, e.g. a Chromebook) or `MKVToolSuite-x86_64.AppImage` (Intel/AMD).

3. Make it executable and run it:

   ```bash
   chmod +x MKVToolSuite-*.AppImage
   ./MKVToolSuite-*.AppImage
   ```

   On first launch it offers to add itself to your app menu (the clickable icon). Keep the AppImage where it is —
   the launcher points at it. You can also run `./MKVToolSuite-*.AppImage --install-launcher` or
   `--uninstall-launcher` yourself.

AppImages need FUSE 2 (`libfuse2` / `libfuse2t64`). If it is missing, run with
`--appimage-extract-and-run` or install it with apt.

Open files straight from the command line too: `./MKVToolSuite-*.AppImage movie.mkv`.

## Run from source

```bash
sudo apt install python3-venv mkvtoolnix ffmpeg
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m mkvsuite
```

## Tests

```bash
.venv/bin/python -m unittest tests.test_core tests.test_ffmpeg tests.test_ui_smoke
```

The tests run the real `mkvmerge`, `mkvextract`, `mkvpropedit` and `ffmpeg`, and drive the real UI offscreen.
Tests that need a tool that is not installed are skipped.

## How it is organised

```
mkvsuite/core/   no GUI code: track model, command builders, naming, languages, job/exit-code handling,
                 and the planner that picks MKVToolNix or ffmpeg per file and output format
mkvsuite/ui/     the Qt interface (PySide6): pages, theme, background job runner
mkvsuite/launcher.py   app-menu launcher install/uninstall
packaging/       AppImage files (AppRun, .desktop)
.github/workflows/appimage.yml   tests + AppImage build for x86_64 and aarch64
```

- MKV files go through `mkvmerge` / `mkvextract` / `mkvpropedit`; other formats go through `ffprobe` / `ffmpeg`.
- Long jobs run in the background; the window never freezes.
- MP4 limits: it can only hold text subtitles (picture subtitles such as PGS need MKV), and track names may not
  show in every player.

## Releasing

Push a version tag; CI runs the tests, builds both AppImages and publishes a GitHub Release:

```bash
git tag -a v0.1.1 -m "..." && git push origin v0.1.1
```

## Troubleshooting

- **"MKVToolNix is not installed"** — `sudo apt install mkvtoolnix`.
- **MP4 files won't open** — `sudo apt install ffmpeg`.
- **Mouse pointer too large (ChromeOS)** — the app corrects Crostini's cursor size; set
  `MKVSUITE_KEEP_CURSOR_SIZE=1` to turn that off.
