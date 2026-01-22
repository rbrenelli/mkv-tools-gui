## 2025-01-02 - Lazy Loading UI Frames
**Learning:** Initializing all UI components at startup in a multi-tab application significantly impacts startup time, even if those components are not immediately visible.
**Action:** Implement lazy loading for UI tabs/frames. Instantiate them only when the user first navigates to them. This spreads the initialization cost and speeds up the initial launch.

## 2025-05-18 - Async Dependency Checks
**Learning:** Performing synchronous filesystem checks (e.g., `shutil.which`) during application startup blocks the main UI thread, causing a delay before the window appears.
**Action:** Move dependency checks to a background thread. Use `threading.Thread` to run the check and `self.after(0, callback)` to schedule UI updates (like showing a setup wizard) back on the main thread. This ensures the main window appears instantly.
