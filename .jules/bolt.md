## 2024-05-23 - Deferred Startup Dependency Check
**Learning:** In `tkinter`/`customtkinter` apps, heavy synchronous operations in `__init__` (like `shutil.which` calls) block the initial window rendering.
**Action:** Always use `self.after(ms, callback)` to schedule non-critical startup checks, allowing the main loop to start and the window to appear immediately ("First Paint").
