## 2025-01-18 - [Modal Dialogs in CustomTkinter]
**Learning:** Standard `tkinter.messagebox` dialogs should explicitly use `parent=self` (or the specific frame/window) when used within a `customtkinter` application. This ensures the dialog is modal to the application window rather than potentially floating independently or getting lost behind other windows.
**Action:** Always include `parent=self` when adding `messagebox` calls in `ctk` frames.
