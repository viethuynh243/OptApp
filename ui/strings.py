"""strings.py - Chuỗi/khóa UI dùng chung (NGUỒN DUY NHẤT).

Chỉ đặt ở đây các chuỗi được SO KHỚP ở nhiều nơi (đặt ↔ kiểm tra) để không lệch
khi sửa một chỗ mà quên chỗ khác — tránh "bệ của phương án nào đi theo phương án
đó" hỏng vì nhãn không khớp, hay radio chế độ xem không trùng nhánh vẽ.

KHÔNG đặt ở đây các chuỗi chỉ HIỂN THỊ (nhãn frame, tiêu đề) — chúng không ảnh
hưởng luồng điều khiển.
"""

# --- Nhãn phương án trong combobox (so khớp ở results/simulation/file_ops) ---
CFG_GOC = "Phương án gốc"
CFG_DEXUAT = "Phương án đề xuất"
CFG_PREFIX = "Phương án "        # dùng cho f"{CFG_PREFIX}{i+1}" và startswith(...)

# --- Khóa CHẾ ĐỘ XEM: đặt ở radio Tab 1 (interactive_tab) PHẢI trùng nhánh vẽ
#     kiểm ở SimulationView.update_simulation ---
VIEW_LAYOUT = "layout"
VIEW_AUDIT = "audit"
VIEW_MODEL3D = "model3d"
VIEW_SSI = "ssi"
VIEW_CAPDESIGN = "capdesign"
