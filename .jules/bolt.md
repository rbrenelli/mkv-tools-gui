## 2025-01-02 - Lazy Loading UI Frames
**Learning:** Initializing all UI components at startup in a multi-tab application significantly impacts startup time, even if those components are not immediately visible.
**Action:** Implement lazy loading for UI tabs/frames. Instantiate them only when the user first navigates to them. This spreads the initialization cost and speeds up the initial launch.

## 2025-01-02 - Defer Blocking Startup Checks
**Learning:** Performing blocking I/O (like file system checks for dependencies) in the `__init__` method of a GUI application delays the initial window rendering, creating a perception of sluggishness.
**Action:** Use `self.after(ms, callback)` to schedule non-critical checks or potentially blocking operations to run shortly *after* the main event loop has started. This allows the UI to paint immediately.
