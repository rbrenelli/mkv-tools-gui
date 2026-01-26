## 2024-05-23 - Confirmation for Destructive Actions
**Learning:** Destructive list operations (like 'Clear List') in CustomTkinter frames need explicit confirmation dialogs using `messagebox.askyesno(parent=self)`.
**Action:** Always wrap `clear()` methods in a confirmation check, ensuring `parent=self` is passed for correct modal behavior.
