## 2024-05-23 - Path Traversal in File Output
**Vulnerability:** User input fields for filenames in `ExtractorFrame` and `CreatorFrame` allowed path traversal characters (e.g., `../../evil.sh`), enabling arbitrary file write outside the selected output directory.
**Learning:** `os.path.join` does not sanitize inputs; it trusts the developer. User input for "filename" is often implicitly trusted to be just a filename, but without validation, it can be a path.
**Prevention:** Always sanitize user-provided filenames using `os.path.basename` and strict character whitelisting before joining with a directory path.
