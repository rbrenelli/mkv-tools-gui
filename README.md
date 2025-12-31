# MKV Tool Suite

A unified, modern GUI for managing MKV files on Linux. Built with Python and CustomTkinter, it provides a sleek interface for common `mkvmerge` tasks such as extracting tracks, adding subtitles, editing track properties, and creating new MKV containers.

![UI Screenshot](https://via.placeholder.com/800x450?text=MKV+Tool+Suite+Preview)

## Features

The suite includes four powerful modules unified in a single dashboard:

1.  **Extract Tracks**: View all tracks (Video, Audio, Subtitles) in an MKV file and extract specific ones to their original formats (e.g., `.srt`, `.aac`).
    *   *New*: Select/Deselect All buttons for quick batch extraction.
2.  **Add Subtitles (Batch)**: Add external subtitle files to an existing MKV without re-encoding.
    *   Supports intelligent language detection from filenames.
    *   Alternating row colors and unified "Material Design" look.
3.  **Edit Tracks**: Modify track properties like "Default", "Forced", "Language", and "Track Name" for existing tracks in an MKV.
    *   Re-muxes the file efficiently to apply changes.
4.  **Create MKV**: Create a fresh MKV container by combining a video file with external subtitles.

## Prerequisites

This application is designed for **Linux** (e.g., Ubuntu, Debian, Chromebook/Crostini).

To run this app, your system needs the following installed:

*   **Python 3.6+**
*   **Zenity**: Used for the native-looking file selection dialogs. (Essential for Chromebooks)
*   **MKVToolNix**: Specifically `mkvmerge`, used for all file operations.
*   **Python Tkinter**: The GUI backend.

## Installation

2.  **Navigate to the folder**
    Assuming you unzipped this folder, go into it:
    ```bash
    cd mkv_tool_suite
    ```

3.  **Make scripts executable**
    Run this command to allow the scripts to run:
    ```bash
    chmod +x setup_chromebook.sh run.sh
    ```

4.  **Install Dependencies**
    Run the setup script. It will install Python, MKVToolNix, and set everything up.
    *You may be asked for your password.*
    ```bash
    ./setup_chromebook.sh
    ```

## Running the App

Once installed, you can launch the app anytime with this command:

```bash
./run.sh
```

## Troubleshooting

-   **"Command not found"**:
    Make sure you are inside the `mkv_tool_suite` folder by typing `ls` and checking if you see `run.sh`.
-   **Dependencies missing**:
    Run `./setup_chromebook.sh` again to fix any missing installations.
