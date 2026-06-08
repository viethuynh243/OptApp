import sys
try:
    from tkinterdnd2 import TkinterDnD
except ImportError:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Lỗi", "Vui lòng cài đặt thư viện tkinterdnd2 trước khi chạy:\npip install tkinterdnd2")
    sys.exit(1)

from ui.main_window import MainWindow

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = MainWindow(root)
    root.mainloop()
