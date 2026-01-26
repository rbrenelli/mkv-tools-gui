## 2023-10-27 - Path Traversal in Output Filenames
**Vulnerability:** User-controlled output filenames in `CreatorFrame`, `MixerFrame`, `EditorFrame`, and `ExtractorFrame` were concatenated with output directories without validation.
**Learning:** Even in desktop GUI apps, "save as" fields can be vectors for arbitrary file overwrite if users are tricked or make mistakes (e.g., `../../etc/passwd`).
**Prevention:** Always validate user-provided filenames using `utils.validation.is_safe_filename` before passing them to file system operations or subprocess calls. Explicitly block `..` and path separators (`/`, `\`).
