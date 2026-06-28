"""widget_utils.py - Hàm tiện ích GUI thuần (không phụ thuộc state MainWindow).

Trích từ ui/main_window.py (Plan 023, Pha 2) — giữ NGUYÊN hành vi.
"""
import re as _re
import unicodedata

from tkinter import ttk


def to_safe_filename(text: str) -> str:
    """
    Chuyển chuỗi tiếng Việt (có dấu) sang tên file an toàn (ASCII, không dấu).
    Ví dụ:
        'Phương án đề xuất' -> 'Phuong_an_de_xuat'
        'Kết quả Tối Ưu' -> 'Ket_qua_Toi_uu'
    """
    # Bước 1: chuẩn hóa Unicode NFD — tách dấu ra khỏi ký tự cơ sở
    nfd = unicodedata.normalize('NFD', text)
    # Bước 2: loại bỏ các combining diacritical marks (category Mn)
    ascii_approx = ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')
    # Bước 3: xử lý riêng đ/Đ (không phải combining, phải xử lý trước)
    ascii_approx = ascii_approx.replace('đ', 'd').replace('Đ', 'D')
    # Bước 4: thay khoảng trắng bằng gạch dưới, xóa ký tự đặc biệt
    safe = _re.sub(r'[^A-Za-z0-9_\-]', '_', ascii_approx)
    # Bước 5: rút gọn nhiều gạch dưới liên tiếp
    safe = _re.sub(r'_+', '_', safe).strip('_')
    return safe


def set_state_recursive(widget, enabled):
    """Bật/mờ đệ quy mọi widget con (ttk dùng state(), tk dùng config)."""
    for w in widget.winfo_children():
        try:
            if isinstance(w, ttk.Widget):
                w.state(['!disabled'] if enabled else ['disabled'])
            else:
                w.config(state=('normal' if enabled else 'disabled'))
        except Exception:
            pass
        set_state_recursive(w, enabled)


def safe_float(raw, default=0.0):
    """Ép 1 giá trị về float; chuỗi rỗng / sai định dạng / None -> default."""
    raw = raw.strip() if isinstance(raw, str) else raw
    if raw == '' or raw is None:
        return default
    try:
        return float(raw)
    except (ValueError, TypeError):
        return default
