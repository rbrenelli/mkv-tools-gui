## 2024-05-22 - Path Traversal in User-Provided Filenames
**Vulnerability:** User input for output filenames in multiple modules (Extractor, Creator, Mixer, Editor) was directly joined with the output directory path without sanitization, allowing potential path traversal (e.g., `../../file`) or creation of files with unsafe characters.
**Learning:** Even in a desktop GUI application, user input for filesystem paths must be treated as untrusted, especially when constructing paths for external tool execution or file writing.
**Prevention:** Always use a sanitization function (like `utils.security.sanitize_filename`) that enforces a whitelist of allowed characters and strips directory components (`os.path.basename`) before using user input in file paths.
