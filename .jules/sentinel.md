## 2024-05-22 - Path Traversal in File Extraction
**Vulnerability:** User-editable filename fields in `ExtractorFrame` were directly joined with the output directory without sanitization, allowing path traversal (e.g. `../../etc/passwd`).
**Learning:** trusting user input for filenames, even when "safe" defaults are provided, is dangerous if the input field is editable. `os.path.join` does not prevent traversal.
**Prevention:** Always use `os.path.basename` (or a dedicated sanitization function) on any user-provided filename before combining it with a directory path.
