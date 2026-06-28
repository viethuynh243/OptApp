"""test_cap_suggest.py - Kiểm thử xử lý BỆ CHẬT (tùy chọn người dùng kiểm soát).

Bảo đảm: (1) mặc định k/c tối thiểu KHÔNG đổi (3d); (2) override SPACING_MIN_FACTOR
có tác dụng; (3) cap_max_piles/suggest_min_cap cho số liệu hợp lệ — KHÔNG đổi thuật
toán tối ưu.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.constants import effective_min_spacing, SPACING_MIN_FACTOR
from core.cap_suggest import cap_max_piles, suggest_min_cap, _axis_capacity


def test_min_spacing_default_unchanged():
    """Không khai báo hệ số -> vẫn 3d (mặc định thuật toán giữ nguyên)."""
    assert abs(effective_min_spacing({'D_PILE': 1.2}) - 3.6) < 1e-9
    assert SPACING_MIN_FACTOR == 3.0


def test_min_spacing_override():
    """Override hệ số do người dùng chọn (vd cọc khoan nhồi 2.5d)."""
    assert abs(effective_min_spacing({'D_PILE': 1.2, 'SPACING_MIN_FACTOR': 2.5}) - 3.0) < 1e-9
    # Giá trị <=0 hoặc rỗng -> lùi về mặc định 3d
    assert abs(effective_min_spacing({'D_PILE': 1.2, 'SPACING_MIN_FACTOR': 0}) - 3.6) < 1e-9


def test_axis_capacity_exact_multiple():
    """Bội số đúng của s_min không bị hụt 1 cọc (sai số dấu phẩy)."""
    # avail = 9.6 - 2*1.2 = 7.2; s_min = 2.4 -> đúng 4 cọc (3 nhịp)
    assert _axis_capacity(9.6, 1.2, 2.4) == 4
    assert _axis_capacity(8.0, 1.2, 3.6) == 2   # avail 5.6 / 3.6 -> 1 nhịp -> 2 cọc


def test_cap_max_piles():
    p = {'L_X': 8.0, 'L_Y': 9.6, 'D_PILE': 1.2, 'SAFE_D': 1.2}
    cm = cap_max_piles(p)
    # avail_x=5.6/3.6 -> 2 cọc ; avail_y=7.2/3.6 -> 3 cọc (3d)
    assert cm['nx'] == 2 and cm['ny'] == 3
    assert cm['n'] == 6 and abs(cm['s_min'] - 3.6) < 1e-9


def test_suggest_min_cap_basic():
    """Gợi ý nới bệ: lưới >=2x2, bệ đủ chứa, Pmax<=[Po]; không có loads -> None."""
    p = {'L_X': 8.0, 'L_Y': 9.6, 'D_PILE': 1.2, 'SAFE_D': 1.2, 'P_LIMIT': 600.0}
    loads = [{'Hx': 0, 'Hy': 0, 'N': 2400.0, 'Mx': 0, 'My': 500.0, 'Mz': 0}]
    s = suggest_min_cap(p, loads)
    assert s is not None
    assert s['nx'] >= 2 and s['ny'] >= 2
    assert s['pmax'] <= p['P_LIMIT'] + 1e-3
    # Bệ đề xuất phải đủ chứa lưới (span + 2*safe_d)
    assert s['cap_lx'] >= (s['nx'] - 1) * s['sx'] + 2 * p['SAFE_D'] - 1e-9
    assert suggest_min_cap(p, []) is None        # thiếu tải -> None
    assert suggest_min_cap({'P_LIMIT': 0}, loads) is None  # thiếu [Po] -> None


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            fn(); print('[OK]', name)
