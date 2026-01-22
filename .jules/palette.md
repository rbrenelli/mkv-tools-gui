## 2024-05-22 - Destructive Action Confirmation
**Learning:** Destructive list operations (like "Clear List") were implemented without user confirmation, leading to potential accidental data loss. This was flagged as a critical missing pattern.
**Action:** Always wrap destructive actions (clearing lists, deleting files) in a `messagebox.askyesno` check, ensuring `parent=self` is used for modal behavior.
