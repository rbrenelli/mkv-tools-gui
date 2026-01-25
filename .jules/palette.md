## 2024-05-23 - Destructive Action Patterns
**Learning:** Users can accidentally clear lists of files without confirmation, leading to data loss (time spent selecting files).
**Action:** Always implement a confirmation dialog (`messagebox.askyesno`) for "Clear List" or "Remove All" actions. Also, disable the button when the list is empty to provide visual guidance on system state (Empty State).
