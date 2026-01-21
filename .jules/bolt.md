## 2025-01-02 - Lazy Loading UI Frames
**Learning:** Initializing all UI components at startup in a multi-tab application significantly impacts startup time, even if those components are not immediately visible.
**Action:** Implement lazy loading for UI tabs/frames. Instantiate them only when the user first navigates to them. This spreads the initialization cost and speeds up the initial launch.

## 2025-01-03 - Lazy Loading System Tools
**Learning:** Module-level calls to `shutil.which` (or `subprocess`) cause significant IO at import time, slowing down startup even on platforms where the tools aren't used.
**Action:** Wrap system tool detection in functions decorated with `@functools.lru_cache(maxsize=1)` to defer the cost until the first actual use.
