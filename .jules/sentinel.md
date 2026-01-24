## 2024-05-23 - Path Traversal in Output Filename
**Vulnerability:** Users could overwrite arbitrary files by manually entering a relative or absolute path (e.g., `../../etc/passwd` or `/tmp/malicious`) in the output filename field, which was naively joined with the output directory.
**Learning:** `os.path.join` does not sanitize input; if a component is an absolute path, it discards previous components. If it contains separators, it allows traversal.
**Prevention:** Explicitly validate that user-provided filenames are "safe" (contain no path separators and match their own basename) before using them in file operations.
