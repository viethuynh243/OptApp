"""
main.py - Điểm khởi chạy GIAO DIỆN (GUI) của OptApp - Tối ưu bố trí cọc móng cầu.

Script này mở cửa sổ chính của ứng dụng (kéo - thả file đầu vào, nhập thông số,
chạy tối ưu và xem kết quả). Yêu cầu thư viện tkinterdnd2 để hỗ trợ kéo - thả.

Cách chạy:
    cd d:/Project/TEDI/OptApp
    python main.py
"""

import sys

# ============================================================================
# Kiểm tra phụ thuộc: bắt buộc phải có tkinterdnd2 (hỗ trợ kéo - thả file)
# Nếu thiếu, hiện hộp thoại lỗi bằng tkinter chuẩn rồi thoát chương trình.
# ============================================================================
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

# ============================================================================
# Khởi tạo cửa sổ chính và chạy vòng lặp sự kiện của giao diện
# ============================================================================
if __name__ == "__main__":
    root = TkinterDnD.Tk()           # Cửa sổ gốc có hỗ trợ kéo - thả
    app = MainWindow(root)           # Dựng toàn bộ giao diện chính
    root.mainloop()                  # Vào vòng lặp sự kiện (chạy ứng dụng)
