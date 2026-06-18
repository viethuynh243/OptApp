"""cap_suggest.py - GỢI Ý xử lý khi BỆ CHẬT (tùy chọn, do người dùng kiểm soát).

Khi bệ hiện tại không chứa đủ cọc để gánh tải ở khoảng cách tối thiểu, module này
cung cấp 2 con số cho kỹ sư QUYẾT ĐỊNH (không tự áp dụng, không đổi thuật toán):

    1) cap_max_piles  : bệ hiện tại nhét được TỐI ĐA bao nhiêu cọc ở k/c tối thiểu.
    2) suggest_min_cap: lưới ÍT CỌC NHẤT thỏa ràng buộc LỰC (Pmax≤[Po], Pmin≥−[Ct])
       khi BỎ QUA mép bệ (R4), kèm bệ NHỎ NHẤT chứa nó (= "nới bệ" tối thiểu).

Dùng mô hình bệ cứng (rigid_cap) để ước lượng nhanh — không gọi MCOC. Kết quả chỉ
mang tính ĐỀ XUẤT; thiết kế chi tiết vẫn phải chạy MCOC/FEM.
"""
import math
import numpy as np

from core import rigid_cap
from core.generator import generate_coords
from core.constants import (effective_min_spacing, get_safe_d, NMAX_AXIS)


def _axis_capacity(length, safe_d, s_min):
    """Số cọc tối đa trên 1 phương: (n-1)·s_min + 2·safe_d ≤ length."""
    avail = (length or 0.0) - 2.0 * safe_d
    if avail < 0 or s_min <= 0:
        return 0
    # +1e-9: tránh hụt 1 cọc khi avail là bội số đúng của s_min (sai số dấu phẩy).
    return int(avail / s_min + 1e-9) + 1


def cap_max_piles(params):
    """Sức chứa bệ hiện tại (lưới trực giao) ở k/c tối thiểu hiệu dụng.

    Trả về dict {nx, ny, n, s_min, safe_d}. n=0 nghĩa là bệ không đủ cho 1 cọc.
    """
    safe_d = get_safe_d(params)
    s_min = effective_min_spacing(params)
    nx = _axis_capacity(params.get('L_X', 0.0), safe_d, s_min)
    ny = _axis_capacity(params.get('L_Y', 0.0), safe_d, s_min)
    return {'nx': nx, 'ny': ny, 'n': nx * ny, 's_min': s_min, 'safe_d': safe_d}


def _round_up(value, step):
    if step and step > 0:
        return math.ceil(value / step - 1e-9) * step
    return value


def _min_cap_for(coords, safe_d, round_to):
    """Bệ nhỏ nhất chứa coords với mép cách tim ≥ safe_d (làm tròn lên)."""
    c = np.asarray(coords, float)
    span_x = float(c[:, 0].max() - c[:, 0].min())
    span_y = float(c[:, 1].max() - c[:, 1].min())
    return (_round_up(span_x + 2.0 * safe_d, round_to),
            _round_up(span_y + 2.0 * safe_d, round_to))


def suggest_min_cap(params, loads, evaluator=None, round_to=0.1, max_axis=None):
    """Tìm lưới ÍT CỌC NHẤT đạt LỰC (bỏ qua mép bệ) + bệ tối thiểu chứa nó.

    Đầu vào:
        params   : tham số bài toán (D_PILE, P_LIMIT, P_TENSION, SAFE_D,
                   tùy chọn SPACING_MIN_FACTOR/CLEAR_MIN).
        loads    : danh sách tổ hợp tải.
        evaluator: callable(coords)->{pmax,pmin,...}. None → dùng bệ cứng rigid_cap.
        round_to : bội số làm tròn bệ (m).
        max_axis : số cọc tối đa mỗi phương khi quét (mặc định NMAX_AXIS).

    Trả về dict gợi ý {nx, ny, n, sx, sy, type, pmax, pmin, cap_lx, cap_ly} của
    phương án ÍT CỌC nhất, hoặc None nếu không tìm được trong giới hạn.
    """
    if not loads:
        return None
    Po = params.get('P_LIMIT', 0.0) or 0.0
    Ct = params.get('P_TENSION', 0.0) or 0.0
    if Po <= 0:
        return None
    safe_d = get_safe_d(params)
    s_min = effective_min_spacing(params)
    max_axis = int(max_axis or NMAX_AXIS)

    def _eval(coords):
        if evaluator is not None:
            r = evaluator(np.asarray(coords, float))
            return r.get('pmax', 0.0), r.get('pmin', 0.0)
        return rigid_cap.pmax_pmin(np.asarray(coords, float), loads)

    best = None  # (cap_area, n, dict)
    # Quét lưới trực giao ÍT NHẤT 2×2 (nhóm cọc thực) ở ĐÚNG k/c tối thiểu. Mục
    # tiêu = bệ DIỆN TÍCH NHỎ NHẤT (tránh dải 1×N phi thực tế), đồng hạng thì ít
    # cọc hơn. Bố trí tinh sẽ do bộ tối ưu chính lo sau khi đã đủ bệ.
    for nx in range(2, max_axis + 1):
        for ny in range(2, max_axis + 1):
            coords = generate_coords(nx, ny, s_min, s_min, 'A')
            n = len(coords)
            cap_lx, cap_ly = _min_cap_for(coords, safe_d, round_to)
            area = cap_lx * cap_ly
            if best is not None and (area, n) >= (best[0], best[1]):
                continue  # đã có bệ nhỏ hơn (hoặc bằng, ít cọc hơn)
            pmax, pmin = _eval(coords)
            ok = (pmax <= Po + 1e-3) and (Ct <= 0 or pmin >= -Ct - 1e-3)
            if not ok:
                continue
            cand = {'nx': nx, 'ny': ny, 'n': n, 'sx': s_min, 'sy': s_min,
                    'type': 'A', 'pmax': pmax, 'pmin': pmin,
                    'cap_lx': cap_lx, 'cap_ly': cap_ly}
            best = (area, n, cand)
    return best[2] if best else None
