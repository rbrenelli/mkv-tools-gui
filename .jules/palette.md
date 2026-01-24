## 2026-01-24 - Blocking Operations & UI Feedback
**Learning:** Blocking operations on the main thread in Tkinter freeze the UI, preventing loading states unless `update_idletasks()` is forced.
**Action:** Use `processing_state` context manager (or `update_idletasks()`) to provide immediate feedback (e.g., "Processing...") before starting heavy synchronous tasks.
