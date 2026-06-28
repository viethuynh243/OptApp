"""constants.py - Hằng số GIAO DIỆN của OptApp (gom magic numbers UI 1 nơi).

Chỉ chứa hằng số TRÌNH BÀY/điều khiển GUI. Hằng số NGHIỆP VỤ (k/c cọc, TCVN...)
nằm ở core/constants.py và core/tcvn.py — KHÔNG đặt ở đây.
"""

# --- Cửa sổ chính ---
WINDOW_GEOMETRY = "1560x960"      # kích thước mở mặc định (WxH)
WINDOW_MIN_W = 1180               # bề rộng tối thiểu
WINDOW_MIN_H = 760                # chiều cao tối thiểu

# --- Tham số NSGA-II theo ngữ cảnh chạy (pop_size, n_gen, max_evals) ---
# Tab 1 (tương tác): quét rộng hơn cho chất lượng; Tab 2 (hàng loạt): gọn để nhanh.
NSGA2_INTERACTIVE = {'pop_size': 20, 'n_gen': 10, 'max_evals': 140}
NSGA2_EXTENDED = {'pop_size': 16, 'n_gen': 8, 'max_evals': 140}   # luồng mở rộng (quét đường kính)
NSGA2_BATCH = {'pop_size': 16, 'n_gen': 10, 'max_evals': 50}
