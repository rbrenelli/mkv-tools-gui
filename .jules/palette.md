# Palette's Journal

## 2024-05-22 - Destructive Action Confirmation
**Learning:** Users can accidentally clear their work with a single click on "Clear List" buttons, causing frustration.
**Action:** Always wrap destructive list operations (like "Clear All") with a confirmation dialog (`messagebox.askyesno`) and check if there is data to clear first.
