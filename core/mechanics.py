"""mechanics.py - Kiểm tra ràng buộc hình học + nội lực. Gom lỗi rồi kết luận.

R1/R2 tiền đề; R3 khoảng cách; R4 mép bệ; R5 nén; R5b nhổ; R6 uốn;
R7 lực ngang & R8 tương tác (tạm tắt - ngoài đề bài).
"""

import numpy as np
from core import rigid_cap
from core.blackbox import MCOCBlackbox
from core.constants import (SPACING_MAX_FACTOR, GEOM_TOL, get_safe_d,
                            get_m_limit, get_h_limit, effective_min_spacing,
                            ENABLE_LATERAL_CHECK, ENABLE_PM_INTERACTION,
                            ENFORCE_SPACING_MAX)


# ============================================================================
# KIỂM TRA TỔNG HỢP 1 PHƯƠNG ÁN (hình học + nội lực)
# ============================================================================
def check_layout(coords, nx, ny, sx, sy, layout_type, params, loads):
    """Kiểm tra đầy đủ 1 phương án bố trí cọc (hình học + nội lực).

    Gom lỗi hình học và nội lực rồi kết luận đạt/không đạt.
    Trả về (ok, pmax, pmin, mxmax, mymax, forces, thông_điệp).
    """
    # Tham số hình học và giới hạn khoảng cách tim-tim
    d = params['D_PILE']
    L_X = params['L_X']
    L_Y = params['L_Y']
    SAFE_D = get_safe_d(params)
    s_min = effective_min_spacing(params)
    s_max = SPACING_MAX_FACTOR * d
    # Tiền đề R1/R2: phải có cọc và có tổ hợp tải trọng
    if len(coords) == 0:
        return False, 0, 0, 0, 0, [], "Khong co coc"
    if len(loads) == 0:
        return False, 0, 0, 0, 0, [], "Chua nhap to hop tai trong"
    # Lỗi hình học (R3 khoảng cách, R4 mép bệ)
    geo_errors = _geometry_errors(coords, nx, ny, sx, sy, layout_type, d, L_X, L_Y, SAFE_D, s_min, s_max)
    # Gọi hộp đen đánh giá nội lực
    res, msg = MCOCBlackbox.evaluate_layout(coords, loads, params,
                                            params.get('exe_path', ''), params.get('mock_mode', True))
    if not res:
        return False, 0, 0, 0, 0, [], "Loi goi Hop Den: " + msg
    # Nội lực và các giới hạn cho phép
    pmax = res['pmax']
    pmin = res['pmin']
    mxmax = res.get('mxmax', 0)
    mymax = res.get('mymax', 0)
    P_LIMIT = params.get('P_LIMIT', 500.0)
    P_TENSION = params.get('P_TENSION', 0.0)
    M_LIMIT = get_m_limit(params)
    H_LIMIT = get_h_limit(params)
    # Kiểm tra từng tiêu chí nội lực, gom lỗi
    fail = []
    if pmax > P_LIMIT:                               # R5 nén
        fail.append(f"Pmax={pmax:.1f} > {P_LIMIT}")
    if P_TENSION > 0 and pmin < -P_TENSION:          # R5b nhổ
        fail.append(f"Pmin={pmin:.1f} < -{P_TENSION}")
    if mxmax > M_LIMIT:                              # R6 uốn quanh X
        fail.append(f"Mx={mxmax:.1f} > {M_LIMIT}")
    if mymax > M_LIMIT:                              # R6 uốn quanh Y
        fail.append(f"My={mymax:.1f} > {M_LIMIT}")
    if ENABLE_LATERAL_CHECK:                          # R7 lực ngang
        h = rigid_cap.hmax(coords, loads)
        if h > H_LIMIT:
            fail.append(f"Hmax={h:.1f} > {H_LIMIT}")
    if ENABLE_PM_INTERACTION and M_LIMIT != float('inf') and P_LIMIT > 0:  # R8 tương tác P-M
        it = pmax / P_LIMIT + max(mxmax, mymax) / M_LIMIT
        if it > 1.0 + 1e-6:
            fail.append(f"Tuong tac P-M={it:.2f} > 1.0")
    # Cộng dồn lỗi hình học rồi kết luận
    fail.extend(geo_errors)
    ok = len(fail) == 0
    final_msg = msg if ok else "Khong dat: " + ", ".join(fail)
    # Chuẩn hoá danh sách lực: nếu thiếu/lệch số cọc thì điền 0
    forces = res.get('forces', [])
    if not forces or len(forces) != len(coords):
        forces = [0.0] * len(coords)
    return ok, pmax, pmin, mxmax, mymax, forces, final_msg


# ============================================================================
# KIỂM TRA RÀNG BUỘC HÌNH HỌC (R3 khoảng cách, R4 mép bệ)
# ============================================================================
def _geometry_errors(coords, nx, ny, sx, sy, layout_type, d, L_X, L_Y, SAFE_D, s_min, s_max):
    """Kiểm tra ràng buộc hình học của bố trí, trả về danh sách lỗi.

    R4 mép bệ: cọc ngoài cùng + SAFE_D không vượt nửa kích thước bệ.
    R3 khoảng cách: cận dưới 3d (TCVN 10304:2014) là BẮT BUỘC; cận trên 6d chỉ là
    quy ước thực hành nên CHỈ loại phương án khi ENFORCE_SPACING_MAX=True, ngược
    lại vượt 6d không tính là lỗi (báo cáo nêu cảnh báo).
    """
    errors = []
    # in_range: chỉ kẹp cận trên khi bật cờ; nếu không, mọi giá trị >= s_min đều đạt.
    hi = (s_max + GEOM_TOL) if ENFORCE_SPACING_MAX else float('inf')
    in_range = lambda v: s_min - GEOM_TOL <= v <= hi
    # R4: kiểm tra cọc ngoài cùng so với mép bệ theo 2 phương
    max_x = np.max(np.abs(coords[:, 0]))
    max_y = np.max(np.abs(coords[:, 1]))
    if max_x + SAFE_D > L_X / 2 + GEOM_TOL:
        errors.append(f"Vi pham mep be (X={max_x:.2f})")
    if max_y + SAFE_D > L_Y / 2 + GEOM_TOL:
        errors.append(f"Vi pham mep be (Y={max_y:.2f})")
    # R3: kiểm sx/sy (Kiểu A) hoặc đường chéo (Kiểu B) theo in_range ở trên.
    if layout_type == "A":
        # Lưới trực giao: kiểm tra trực tiếp sx, sy
        if nx > 1 and not in_range(sx):
            errors.append("sx vi pham 3d-6d")
        if ny > 1 and not in_range(sy):
            errors.append("sy vi pham 3d-6d")
    elif layout_type == "B":
        # Hoa mai: sx theo phương ngang, hàng kề nhau lệch nên xét khoảng cách chéo
        if nx > 1 and not in_range(sx):
            errors.append("sx vi pham 3d-6d")
        diag = np.sqrt((sx / 2) ** 2 + sy ** 2)
        if ny > 1 and not in_range(diag):
            errors.append("khoang cach cheo vi pham 3d-6d")
    else:
        # Bố trí tuỳ biến: xét khoảng cách tim-tim nhỏ nhất thực tế
        s = rigid_cap.min_spacing(coords)
        if s < s_min - GEOM_TOL:
            errors.append(f"khoang cach tim-tim nho nhat {s:.2f}m < {s_min:.2f}m")
    return errors
