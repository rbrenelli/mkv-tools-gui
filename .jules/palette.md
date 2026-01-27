## 2024-05-23 - Destructive Action Confirmation
**Learning:** Users can easily lose their work (e.g., selected files) if destructive actions like "Clear List" are executed immediately without confirmation.
**Action:** Always implement a confirmation dialog (e.g., `messagebox.askyesno`) for destructive actions, and check if there is data to clear before prompting.
