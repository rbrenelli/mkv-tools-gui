## 2025-01-02 - Lazy Loading UI Frames
**Learning:** Initializing all UI components at startup in a multi-tab application significantly impacts startup time, even if those components are not immediately visible.
**Action:** Implement lazy loading for UI tabs/frames. Instantiate them only when the user first navigates to them. This spreads the initialization cost and speeds up the initial launch.

## 2025-01-02 - Async Startup Checks
**Learning:** Synchronous dependency checks on the main thread delayed initial frame render by ~130ms. Using self.after() to schedule a background check allows the UI to paint immediately.
**Action:** Move all non-critical startup checks to background threads triggered via after().
