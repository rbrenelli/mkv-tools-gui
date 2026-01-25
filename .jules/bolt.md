## 2025-01-02 - Lazy Loading UI Frames
**Learning:** Initializing all UI components at startup in a multi-tab application significantly impacts startup time, even if those components are not immediately visible.
**Action:** Implement lazy loading for UI tabs/frames. Instantiate them only when the user first navigates to them. This spreads the initialization cost and speeds up the initial launch.

## 2025-01-02 - Module Level I/O
**Learning:** Top-level executable code (like `shutil.which`) in utility modules runs immediately on import. If these modules are imported early (e.g., by the main window), they block startup.
**Action:** Use `functools.lru_cache` to wrap static configuration checks into lazy getter functions. This defers the cost until the value is actually needed.
