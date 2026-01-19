## 2025-01-02 - Lazy Loading UI Frames
**Learning:** Initializing all UI components at startup in a multi-tab application significantly impacts startup time, even if those components are not immediately visible.
**Action:** Implement lazy loading for UI tabs/frames. Instantiate them only when the user first navigates to them. This spreads the initialization cost and speeds up the initial launch.

## 2025-01-02 - Startup Dependency Checks & Imports
**Learning:** `shutil.which` and system binary checks at module level (import time) and synchronous `check_missing_dependencies` in `__init__` block the main thread, delaying UI rendering significantly on cold starts.
**Action:** Use `functools.lru_cache` for lazy binary path resolution and move comprehensive dependency checks to a background thread, using `after()` to callback the UI if needed.
