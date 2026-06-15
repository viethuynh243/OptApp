"""
optimizer.py - Quét lưới (Grid Search) tìm cấu hình cọc tối ưu.

Mục đích: với mỗi kiểu bố trí (Kiểu A trục giao / Kiểu B so le), quét toàn bộ
tổ hợp (nx, ny) trong giới hạn, sinh phương án bằng generator, kiểm tra ràng
buộc bằng mechanics, rồi so sánh Kiểu A và Kiểu B để chọn phương án tối ưu.

Quan hệ module:
    - core.generator : sinh tọa độ lưới cọc (generate_coords).
    - core.mechanics : kiểm tra ràng buộc R1-R6 cho từng phương án (check_layout).
    - core.rigid_cap : tính lực ngang tổng hợp (hmax) cho mỗi ứng viên.

Tiêu chí chọn: ít cọc nhất -> Pmax nhỏ nhất -> ưu tiên giữ phương án gốc.
"""

import numpy as np
from core import rigid_cap
from core.generator import generate_coords
from core.mechanics import check_layout
from core.constants import (SPACING_MAX_FACTOR, NX_MIN, NX_MAX,
                            get_safe_d, effective_min_spacing)


# ============================================================================
# Vòng lặp quét lưới chính
# ============================================================================
def run_optimization(params, loads):
    """
    Quét lưới (Grid Search) tìm cấu hình cọc tối ưu, so sánh Kiểu A vs Kiểu B.

    Với mỗi (kiểu, nx, ny): dùng khoảng cách LỚN NHẤT có thể (sx_max, sy_max)
    vì khoảng cách càng lớn -> mômen quán tính càng lớn -> Pmax càng nhỏ.
    Lọc sớm ràng buộc khoảng cách (R3) trước khi sinh tọa độ để tiết kiệm.
    Tiêu chí chọn: ít cọc nhất -> Pmax nhỏ nhất -> ưu tiên giữ phương án gốc.
    """
    L_X = params['L_X']
    L_Y = params['L_Y']
    d = params['D_PILE']
    SAFE_D = get_safe_d(params)
    s_min = effective_min_spacing(params)   # max(3d, d + thông thủy)
    s_max = SPACING_MAX_FACTOR * d          # khoảng cách tối đa 6d

    best_configs = {'A': None, 'B': None}
    best_n = {'A': float('inf'), 'B': float('inf')}
    all_valid_configs = []
    all_candidates = []  # Tất cả ứng viên kể cả không đạt

    # --- Quét toàn bộ tổ hợp (kiểu, nx, ny) --------------------------------
    for layout_type in ["A", "B"]:
        for nx in range(NX_MIN, NX_MAX + 1):
            for ny in range(NX_MIN, NX_MAX + 1):
                # Khoảng cách LỚN NHẤT có thể: giới hạn trên 6d (R3),
                # giới hạn dưới bởi mép bệ (R4).
                sx_max = min(s_max, (L_X - 2*SAFE_D)/(nx-1) if nx > 1 else 0)
                sy_max = min(s_max, (L_Y - 2*SAFE_D)/(ny-1) if ny > 1 else 0)

                # Chốt bước lưới (sx, sy) sao cho thỏa ràng buộc khoảng cách R3:
                # - Kiểu A: cọc gần nhất cách sx hoặc sy -> đều phải trong [3d, 6d].
                # - Kiểu B (so le): hàng kề nhau lệch sx/2 nên khoảng cách gần nhất
                #   là ĐƯỜNG CHÉO sqrt((sx/2)^2 + sy^2), KHÔNG phải sy. Ở bước lớn
                #   nhất đường chéo thường vượt 6d, nên GIẢM sy để kéo đường chéo
                #   về đúng 6d (vẫn giữ sy lớn nhất có thể -> mômen quán tính lớn).
                if layout_type == "A":
                    if sx_max < s_min or sy_max < s_min:
                        continue
                    sx, sy = sx_max, sy_max
                else:
                    sx = sx_max
                    if sx < s_min:
                        continue
                    # sy lớn nhất sao cho đường chéo <= 6d, và không vượt mép bệ
                    sy_diag_cap = np.sqrt(max(s_max**2 - (sx / 2.0)**2, 0.0))
                    sy = min(sy_max, sy_diag_cap)
                    diag = np.sqrt((sx / 2.0)**2 + sy**2)
                    # Đường chéo phải >= 3d; nếu mép bệ ép sy quá nhỏ thì loại.
                    if sy <= 0 or diag < s_min - 1e-9:
                        continue

                # Sinh tọa độ ứng viên rồi gọi mechanics kiểm tra ràng buộc
                coords = generate_coords(nx, ny, sx, sy, layout_type)
                n = len(coords)

                ok, pmax, pmin, mxmax, mymax, forces, msg = check_layout(coords, nx, ny, sx, sy, layout_type, params, loads)

                candidate = {
                    'type': layout_type,
                    'nx': nx, 'ny': ny,
                    'sx': sx, 'sy': sy,
                    'n': n,
                    'coords': coords,
                    'pmax': pmax,
                    'pmin': pmin,
                    'mxmax': mxmax,
                    'mymax': mymax,
                    'hmax': rigid_cap.hmax(coords, loads),   # lực ngang tổng hợp lớn nhất
                    'forces': forces,
                    'ok': ok,
                    'msg': msg
                }
                all_candidates.append(candidate)

                # Cập nhật phương án ít cọc nhất theo từng kiểu
                if ok:
                    all_valid_configs.append(candidate)
                    if n < best_n[layout_type]:
                        best_n[layout_type] = n
                        best_configs[layout_type] = candidate

    # ============================================================================
    # Chọn phương án khuyến nghị
    # ============================================================================
    # Sắp xếp theo số cọc, rồi đến Pmax (ưu tiên ít cọc + an toàn hơn)
    all_valid_configs.sort(key=lambda x: (x['n'], x['pmax']))
    all_candidates.sort(key=lambda x: (x['n'], x['pmax']))

    recommended = None
    reason = "Khong co"

    # So sánh trực tiếp Kiểu A vs Kiểu B: ưu tiên ít cọc, hòa thì xét Pmax
    if best_configs['A'] and best_configs['B']:
        if best_configs['B']['n'] < best_configs['A']['n']:
            recommended = best_configs['B']
            reason = f"Kieu So le tiet kiem coc nhat (chi {best_configs['B']['n']} coc)."
        elif best_configs['A']['n'] < best_configs['B']['n']:
            recommended = best_configs['A']
            reason = f"Kieu Truc giao tiet kiem coc nhat (chi {best_configs['A']['n']} coc)."
        else:
            if best_configs['B']['pmax'] < best_configs['A']['pmax']:
                recommended = best_configs['B']
                reason = f"Cung {best_configs['A']['n']} coc, nhung kieu So le co P_max = {best_configs['B']['pmax']:.1f} T an toan hon."
            else:
                recommended = best_configs['A']
                reason = f"Cung {best_configs['A']['n']} coc, nhung kieu Truc giao co P_max = {best_configs['A']['pmax']:.1f} T an toan hon."
    elif best_configs['A']:
        recommended = best_configs['A']
        reason = "Chi kieu Truc giao thoa man dieu kien."
    elif best_configs['B']:
        recommended = best_configs['B']
        reason = "Chi kieu So le thoa man dieu kien."

    # ============================================================================
    # Đối chiếu với phương án gốc trong file
    # ============================================================================
    original_config = None
    if 'original_coords' in params:
        orig_coords = np.array(params['original_coords'])
        orig_nx = 0
        orig_ny = 0

        # Đánh giá phương án gốc dựa trên RÀNG BUỘC MỚI của người dùng (P_LIMIT, D_PILE hiện tại)
        ok, pmax, pmin, mxmax, mymax, forces, msg = check_layout(orig_coords, orig_nx, orig_ny, 0, 0, "Goc", params, loads)
        original_config = {
            'type': 'Goc',
            'coords': orig_coords,
            'n': len(orig_coords),
            'ok': ok,
            'pmax': pmax,
            'pmin': pmin,
            'mxmax': mxmax,
            'mymax': mymax,
            'hmax': rigid_cap.hmax(orig_coords, loads),
            'forces': forces,
            'msg': msg
        }

        # Ưu tiên phương án gốc nếu nó đạt và các phương án lưới không tiết kiệm cọc hơn
        if ok and (recommended is None or recommended['n'] >= len(orig_coords)):
            recommended = {
                'type': 'Goc',
                'nx': 0, 'ny': 0,
                'sx': 0, 'sy': 0,
                'n': len(orig_coords),
                'coords': orig_coords,
                'pmax': pmax,
                'pmin': pmin,
                'mxmax': mxmax,
                'mymax': mymax,
                'forces': forces,
                'ok': True,
                'msg': 'Su dung phuong an goc'
            }
            reason = f"Phuong an goc trong file DAT (Pmax={pmax:.1f}T). Cac phuong an luoi deu khong tiet kiem coc hon."
        elif recommended is None and not ok:
            clean_msg = msg.replace("Khong dat: ", "")
            reason = f"Phuong an goc KHONG DAT ({clean_msg}). Can thay doi cau hinh dai coc, mong coc hoac gioi han uon."

    # Cảnh báo độ tin cậy R6 ở chế độ mock: mômen đầu cọc là ước lượng heuristic.
    warning = None
    m_limit = params.get('M_LIMIT', 0) or 0
    is_mock = params.get('mock_mode', True) or not params.get('exe_path')
    if is_mock and m_limit > 0:
        warning = ("Momen dau coc o che do mock la UOC LUONG (heuristic ~ 1/so coc); "
                   "ket qua kiem tra [M] (R6) chi tin cay khi cham bang MCOC.")

    return {
        'best_A': best_configs['A'],
        'best_B': best_configs['B'],
        'recommended': recommended,
        'reason': reason,
        'all_valid_configs': all_valid_configs,
        'all_candidates': all_candidates,
        'original_config': original_config,
        'warning': warning,
    }
