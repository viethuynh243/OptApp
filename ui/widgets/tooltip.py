"""tooltip.py - Chú thích nhỏ hiện ra khi rê chuột vào widget.

Trích từ ui/main_window.py (Plan 023, Pha 2) — giữ NGUYÊN hành vi.
"""
import tkinter as tk


class Tooltip:
    """Chú thích nhỏ hiện ra khi rê chuột vào widget (di chuột ra thì ẩn).

    Dùng Toplevel không viền chứa 1 Label. Gắn vào widget bằng cách khởi tạo:
        Tooltip(widget, "Nội dung chú thích").
    """

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self._tip = None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _show(self, _event=None):
        if self._tip or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 16
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        except Exception:
            return
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self._tip, text=self.text, justify="left",
                 background="#ffffe0", foreground="#333",
                 relief="solid", borderwidth=1,
                 font=("Arial", 8), wraplength=260, padx=6, pady=3).pack()

    def _hide(self, _event=None):
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None
