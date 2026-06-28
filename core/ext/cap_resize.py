"""
cap_resize.py - Đổi KÍCH THƯỚC BỆ (L_X, L_Y) cho vừa phương án tối ưu (TCVN).

Sau khi tối ưu ra bố trí cọc + đường kính, kích thước bệ ban đầu thường còn dư.
Module tính lại bệ vừa khít theo TCVN 10304:2014:

    - Cấu tạo (Điều 8): tim cọc ngoài cùng phải cách mép bệ một khoảng an toàn
      SAFE_D (mặc định = đường kính cọc d). Suy ra kích thước tối thiểu theo
      mỗi phương:  L = (toạ_độ_max - toạ_độ_min) + 2·SAFE_D.
    - Làm tròn LÊN bội số thi công (vd 0.1 m hoặc 0.5 m) để dễ ván khuôn.

Không bao giờ làm bệ NHỎ hơn mức cần để cọc vẫn nằm trong bệ (an toàn R4).
Bố trí lưới trong dự án căn giữa (cx=cy=0) nên kết quả đối xứng quanh tâm.
"""

import math
import numpy as np


# ===========================================================================
# Tính kích thước bệ tối thiểu (vừa khít) + làm tròn thi công
# ===========================================================================
def _round_up(value, step):
    """Làm tròn LÊN value tới bội số step gần nhất (có dung sai chống sai số)."""
    if step <= 0:
        return value
    return math.ceil(value / step - 1e-9) * step


def recommend_cap_size(coords, safe_d, round_to=0.1):
    """Đề xuất (L_X, L_Y) nhỏ nhất chứa cọc với mép cách tim ≥ safe_d.

    Đầu vào:
        coords  : tọa độ cọc (n, 2) (m).
        safe_d  : khoảng cách an toàn tim cọc tới mép bệ (m) — TCVN, mặc định d.
        round_to: bội số làm tròn lên (m).

    Trả về (L_X, L_Y) đã làm tròn lên. coords rỗng -> (0.0, 0.0).
    """
    coords = np.asarray(coords, dtype=float)
    if coords.size == 0:
        return 0.0, 0.0
    span_x = float(coords[:, 0].max() - coords[:, 0].min())
    span_y = float(coords[:, 1].max() - coords[:, 1].min())
    raw_x = span_x + 2.0 * safe_d
    raw_y = span_y + 2.0 * safe_d
    return _round_up(raw_x, round_to), _round_up(raw_y, round_to)


# ===========================================================================
# Áp dụng đổi kích thước bệ vào params + báo cáo
# ===========================================================================
def resize_cap(params, coords, d, cfg):
    """Tính (và tùy chọn áp dụng) kích thước bệ mới cho phương án tối ưu.

    Đầu vào:
        params : tham số bài toán (chứa L_X, L_Y hiện tại; SAFE_D nếu có).
        coords : tọa độ cọc phương án tối ưu (m).
        d      : đường kính cọc phương án tối ưu (m) — dùng làm SAFE_D mặc định.
        cfg    : ExtConfig (round_to, cap_resize).

    Trả về (new_params, report). report gồm:
        {'old_LX','old_LY','new_LX','new_LY','safe_d','round_to','applied',
         'saved_area','saved_pct'}.
    new_params là bản sao params; L_X/L_Y được ghi đè nếu cfg.cap_resize=True.
    """
    safe_d = params.get('SAFE_D', d)
    old_lx = float(params.get('L_X', 0.0) or 0.0)
    old_ly = float(params.get('L_Y', 0.0) or 0.0)
    new_lx, new_ly = recommend_cap_size(coords, safe_d, cfg.cap_round_to)

    old_area = old_lx * old_ly
    new_area = new_lx * new_ly
    saved_area = old_area - new_area
    saved_pct = (saved_area / old_area * 100.0) if old_area > 0 else 0.0

    new_params = dict(params)
    if cfg.cap_resize:
        new_params['L_X'] = new_lx
        new_params['L_Y'] = new_ly

    report = {
        'old_LX': old_lx, 'old_LY': old_ly,
        'new_LX': new_lx, 'new_LY': new_ly,
        'safe_d': safe_d, 'round_to': cfg.cap_round_to,
        'applied': cfg.cap_resize,
        'saved_area': saved_area, 'saved_pct': saved_pct,
    }
    return new_params, report
