## 2025-01-02 - Lazy Loading UI Frames
**Learning:** Initializing all UI components at startup in a multi-tab application significantly impacts startup time, even if those components are not immediately visible.
**Action:** Implement lazy loading for UI tabs/frames. Instantiate them only when the user first navigates to them. This spreads the initialization cost and speeds up the initial launch.

## 2025-01-02 - Async Startup Dependency Checks
**Learning:** Performing synchronous dependency checks (involving `shutil.which` or I/O) on the main thread blocks the GUI from appearing, causing a poor perceived startup performance.
**Action:** Move startup checks to a background thread. If checks pass, do nothing; if they fail, use `after()` to trigger the UI setup wizard on the main thread. This makes the app feel instant.
