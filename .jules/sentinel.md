## 2024-05-24 - Path Traversal in Extractor
**Vulnerability:** User-controlled filename input in the Extractor module allowed arbitrary file overwrite via path traversal (`../../`) or absolute paths when joined with the output directory.
**Learning:** `os.path.join` does not prevent directory traversal and treats absolute paths in the second argument as the new root, discarding the base directory. UI inputs for "filenames" must be treated as untrusted.
**Prevention:** Sanitize all user-provided filenames using `os.path.basename` (or rigorous validation) before using them in file path construction.
