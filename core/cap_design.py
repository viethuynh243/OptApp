"""
cap_design.py - Thiết kế kết cấu ĐÀI CỌC theo TCVN 5574:2018.

Đầu vào là bố trí cọc + phản lực cọc (từ mô hình bệ cứng rigid_cap) + hình học
đài/cột + vật liệu. Xuất ra cốt thép chịu uốn, kiểm tra chọc thủng (quanh cột và
quanh cọc), cắt một phương, và cờ "đài sâu" gợi ý mô hình giàn ảo (STM).

Tham chiếu: TCVN 5574:2018 — Điều 8.1.2 (uốn), 8.1.3 (cắt), 8.1.6 (chọc thủng);
cường độ tính toán Rb/Rbt (Điều 6.1.2) đã đối chiếu words_dict/TCVN5574-2018.md;
p-multiplier/STM theo AASHTO LRFD & thực hành. Hằng số tách thành dict để override.

ĐƠN VỊ NỘI BỘ: N – mm – MPa (1 MPa = 1 N/mm²). Lực app theo Tấn → ×9.80665 ra kN
→ ×1000 ra N; kích thước m → ×1000 ra mm. As trả về mm², mô men N·mm.
"""
import math
import numpy as np

from core import rigid_cap

TF_TO_KN = 9.80665          # kN cho 1 Tấn-lực
KN_TO_N = 1000.0
M_TO_MM = 1000.0

# Cường độ TÍNH TOÁN TCVN 5574:2018 (MPa) — đối chiếu words_dict/TCVN5574-2018.md
# (dòng Rb ~1689: B20=11.5/B25=14.5/B30=17.0; dòng Rbt ~1700: 0.90/1.05/1.15)
RB = {'B15': 8.5, 'B20': 11.5, 'B25': 14.5, 'B30': 17.0, 'B35': 19.5, 'B40': 22.0}
RBT = {'B15': 0.75, 'B20': 0.90, 'B25': 1.05, 'B30': 1.15, 'B35': 1.30, 'B40': 1.40}
RS = {'CB240-T': 210.0, 'CB300-V': 260.0, 'CB400-V': 350.0, 'CB500-V': 435.0}
ES = 200000.0             # mô đun đàn hồi cốt thép Es (MPa) — TCVN 5574 Bảng 13 (2,0e5)
# εb2: biến dạng tương đối của bê tông khi nén ứng với Rb, tác dụng NGẮN HẠN.
# = 0,0035 theo TCVN 5574:2018 (mục 6.1.4.2; xem words_dict/TCVN5574-2018.md dòng 2250).
EPS_B2 = 0.0035
MU_MIN = 0.001           # hàm lượng cốt thép tối thiểu chịu uốn 0,1% (TCVN 5574 ~dòng 11887)


def materials(conc='B25', steel='CB400-V'):
    """Trả về (Rb, Rbt, Rs, ξ_R) theo cấp bê tông & nhóm thép.

    ξ_R = 0,8 / (1 + ε_s,el/ε_b2), với ε_s,el = Rs/Es — đúng CT(31) TCVN 5574:2018
    (Điều 8.1.2.2.3; words_dict/TCVN5574-2018.md dòng 3469-3487). Hệ số 0,8 dùng cho
    bê tông tới B60; B70–B100 & bê tông hạt nhỏ thay bằng 0,7 (ngoài dải B15–B40 ở đây).
    """
    rb = RB.get(conc, RB['B25'])
    rbt = RBT.get(conc, RBT['B25'])
    rs = RS.get(steel, RS['CB400-V'])
    xi_R = 0.8 / (1.0 + (rs / ES) / EPS_B2)     # CT(31) TCVN 5574:2018
    return rb, rbt, rs, xi_R


# ============================================================================
# Các hàm kiểm toán đơn lẻ (đơn vị N–mm–MPa)
# ============================================================================
def flexure_As(M, rb, rs, xi_R, b, h0):
    """Cốt thép chịu uốn tiết diện chữ nhật cốt đơn (TCVN 5574 Điều 8.1.2).

    M [N·mm], rb/rs [MPa], b/h0 [mm] → dict(As [mm²], các hệ số, cờ đạt).
    """
    M = max(float(M), 0.0)
    if M <= 0:
        As_min = MU_MIN * b * h0
        return {'ok': True, 'As': As_min, 'As_req': 0.0, 'As_min': As_min,
                'xi': 0.0, 'xi_R': xi_R, 'zeta': 1.0, 'alpha_m': 0.0, 'M': M,
                'reason': ''}
    alpha_m = M / (rb * b * h0 ** 2)
    disc = 1.0 - 2.0 * alpha_m
    if disc < 0:
        return {'ok': False, 'As': float('nan'), 'As_req': float('nan'),
                'As_min': MU_MIN * b * h0, 'xi': float('nan'), 'xi_R': xi_R,
                'zeta': float('nan'), 'alpha_m': alpha_m, 'M': M,
                'reason': 'α_m>0.5: bê tông nén vỡ — tăng chiều cao đài H hoặc cấp BT'}
    xi = 1.0 - math.sqrt(disc)
    zeta = 0.5 * (1.0 + math.sqrt(disc))
    As_req = M / (rs * zeta * h0)
    As_min = MU_MIN * b * h0
    ok = bool(xi <= xi_R)
    return {'ok': ok, 'As': max(As_req, As_min), 'As_req': As_req, 'As_min': As_min,
            'xi': xi, 'xi_R': xi_R, 'zeta': zeta, 'alpha_m': alpha_m, 'M': M,
            'reason': '' if ok else 'ξ>ξ_R: vùng nén quá lớn — tăng H/cấp BT'}


def punching_column(F, bc, hc, h0, rbt):
    """Chọc thủng quanh CỘT chữ nhật (TCVN 5574 Điều 8.1.6, lực đúng tâm).

    F = lực gây chọc thủng [N] (= N_cột − Σ phản lực cọc trong tháp). Chu vi tới
    hạn tại h0/2: u_m = 2·(bc+hc+2·h0). F_b,ult = Rbt·u_m·h0.
    """
    um = 2.0 * (bc + hc + 2.0 * h0)
    F_ult = rbt * um * h0
    return {'F': F, 'F_ult': F_ult, 'u_m': um,
            'ratio': (F / F_ult if F_ult > 0 else float('inf')), 'ok': bool(F <= F_ult)}


def punching_pile(P, D_pile, h0, rbt):
    """Chọc thủng quanh một CỌC (cọc đâm ngược lên qua đài). u_m = π·(D+h0)."""
    um = math.pi * (D_pile + h0)
    F_ult = rbt * um * h0
    return {'F': P, 'F_ult': F_ult, 'u_m': um,
            'ratio': (P / F_ult if F_ult > 0 else float('inf')), 'ok': bool(P <= F_ult)}


def oneway_shear(Q, rbt, b, h0, C=None, rb=None):
    """Cắt một phương theo tiết diện nghiêng (TCVN 5574:2018 Điều 8.1.3).

    Khả năng chịu cắt của BÊ TÔNG (CT 90): Q_b = φb2·Rbt·b·h0²/C, φb2 = 1,5; kẹp
    0,5·Rbt·b·h0 ≤ Q_b ≤ 2,5·Rbt·b·h0. C = hình chiếu tiết diện nghiêng, h0 ≤ C ≤ 2h0.
    Nếu KHÔNG truyền C → dùng cận dưới 0,5·Rbt·b·h0 (an toàn, tương thích ngược).
    Giới hạn nén dải bê tông giữa các vết nứt nghiêng (CT 88): Q ≤ 0,3·Rb·b·h0
    (nếu truyền rb; không thì lùi về 2,5·Rbt·b·h0). Đối chiếu TCVN 5574:2018 dòng
    5189-5282; φb2=1,5 (dòng 5280).
    """
    PHI_B2 = 1.5
    if C and C > 0 and h0 > 0:
        Cc = min(max(C, h0), 2.0 * h0)                  # kẹp h0 ≤ C ≤ 2h0
        q_conc = PHI_B2 * rbt * b * h0 * h0 / Cc
        q_conc = min(max(q_conc, 0.5 * rbt * b * h0), 2.5 * rbt * b * h0)
    else:
        q_conc = 0.5 * rbt * b * h0                      # cận dưới (an toàn) khi thiếu C
    q_max = (0.3 * rb * b * h0) if (rb and rb > 0) else (2.5 * rbt * b * h0)
    return {'Q': Q, 'Q_concrete': q_conc, 'Q_max': q_max, 'C': (C or 0.0),
            'need_stirrups': bool(Q > q_conc), 'ok': bool(Q <= q_max),
            'ratio': (Q / q_max if q_max > 0 else float('inf'))}


def stm_tie(P, a_horiz, h0, rs, z_factor=0.9):
    """Lực kéo thanh giằng (tie) theo mô hình giàn ảo (STM) cho đài SÂU.

    z = z_factor·h0; T = P·a/z; As_tie = T/Rs. Cờ deep khi a/h0 < 1.0.

    NGUỒN: TCVN 5574:2018 chỉ nêu DÙNG mô hình thanh–giàn cho cấu kiện NGẮN mà KHÔNG
    định lượng z hay ngưỡng a/h0. Các trị z=0,9·h0 và ngưỡng đài sâu a/h0<1,0 lấy theo
    THỰC HÀNH ACI 318 / AASHTO LRFD — mang tính THAM KHẢO, không phải trị số TCVN.
    """
    z = z_factor * h0
    T = P * a_horiz / z if z > 0 else 0.0
    theta = math.degrees(math.atan2(z, a_horiz)) if a_horiz > 0 else 90.0
    return {'T': T, 'As_tie': (T / rs if rs > 0 else float('nan')),
            'theta_deg': theta, 'deep': bool((a_horiz / h0) < 1.0) if h0 > 0 else False}


# ============================================================================
# Hàm tổng hợp: thiết kế đài từ bố trí cọc + tải
# ============================================================================
def _governing_forces(coords, loads):
    """Tổ hợp CHI PHỐI (Pmax lớn nhất): trả (forces_pile [Tấn], N_combo [Tấn])."""
    coords = np.asarray(coords, dtype=float)
    P = rigid_cap.forces_all_loads(coords, loads)     # (n_load, n_pile), Tấn
    if P.size == 0:
        return np.zeros(len(coords)), 0.0
    gov = int(np.argmax(P.max(axis=1)))
    N_combo = float(loads[gov].get('N', 0.0))
    return P[gov], N_combo


def design_cap(coords, params, loads, calib=1.0):
    """Thiết kế đài cọc cho tổ hợp chi phối. Trả dict kết quả đầy đủ hoặc cờ thiếu.

    params cần: D_PILE, cap_thickness (H), cover, col_b, col_h, conc_grade,
    steel_grade. Thiếu hình học bắt buộc → trả {'ok': False, 'missing': [...]}.

    CƠ SỞ THIẾT KẾ: nếu DESIGN_BASIS='TCVN11823' → uỷ quyền cho core.cap_design_lrfd
    (TCVN 11823-5:2017 — bê tông cầu, LRFD). TCVN 5574:2018 (dưới đây) KHÔNG dùng cho
    cầu — chỉ giữ cho cơ sở 'TCVN10304' (đối chiếu/hồi quy).
    """
    from core import lrfd as _lrfd
    if _lrfd.design_basis(params) == 'TCVN11823':
        from core import cap_design_lrfd
        return cap_design_lrfd.design_cap_lrfd(coords, params, loads, calib)

    coords = np.asarray(coords, dtype=float)
    n = len(coords)
    missing = []
    H = params.get('cap_thickness')
    cover = params.get('cover') or 0.10
    col_b = params.get('col_b')
    col_h = params.get('col_h')
    D = params.get('D_PILE') or 1.0
    if not H or H <= 0:
        missing.append('chiều cao đài H')
    if not col_b or col_b <= 0:
        missing.append('bề rộng cột bx')
    if not col_h or col_h <= 0:
        missing.append('bề cao cột by')
    if n == 0 or not loads:
        missing.append('bố trí cọc / tổ hợp tải')
    if missing:
        return {'ok': False, 'missing': missing}

    conc = params.get('conc_grade', 'B25')
    steel = params.get('steel_grade', 'CB400-V')
    rb, rbt, rs, xi_R = materials(conc, steel)

    # Hình học (m) → mm; lực cọc (Tấn) → N
    h0 = (H - cover) * M_TO_MM                 # chiều cao làm việc [mm]
    Lx = (coords[:, 0].max() - coords[:, 0].min()) + D   # bề rộng đài ~ bao cọc + d
    Ly = (coords[:, 1].max() - coords[:, 1].min()) + D
    Lx_mm, Ly_mm = max(Lx, D) * M_TO_MM, max(Ly, D) * M_TO_MM
    bc, hc = col_b * M_TO_MM, col_h * M_TO_MM
    D_mm = D * M_TO_MM

    f_pile, N_combo = _governing_forces(coords, loads)
    f_pile = np.asarray(f_pile, float) * calib
    P_N = f_pile * TF_TO_KN * KN_TO_N          # phản lực cọc [N] (dương=nén)
    N_col_N = N_combo * TF_TO_KN * KN_TO_N
    # tâm cột ~ trọng tâm nhóm cọc (đặt gốc tại tâm)
    cx, cy = coords[:, 0].mean(), coords[:, 1].mean()
    x = (coords[:, 0] - cx) * M_TO_MM
    y = (coords[:, 1] - cy) * M_TO_MM

    # ── UỐN: tiết diện nguy hiểm tại MÉP CỘT theo 2 phương ───────────────
    def flexure_dir(coord_mm, half_col, b_mm):
        # mô men của cọc NGOÀI mép cột, lấy bên bất lợi hơn (±)
        M_pos = float(np.sum(np.maximum(coord_mm - half_col, 0.0)
                             * np.where(coord_mm > half_col, P_N, 0.0)))
        M_neg = float(np.sum(np.maximum(-coord_mm - half_col, 0.0)
                             * np.where(-coord_mm > half_col, P_N, 0.0)))
        M = max(M_pos, M_neg)
        return flexure_As(M, rb, rs, xi_R, b_mm, h0)

    flex_x = flexure_dir(x, bc / 2.0, Ly_mm)   # thép theo phương X, b = bề rộng Y
    flex_y = flexure_dir(y, hc / 2.0, Lx_mm)   # thép theo phương Y, b = bề rộng X

    # ── CHỌC THỦNG quanh cột: trừ phản lực cọc TRONG tháp (mép cột + h0/2) ─
    half_tx = bc / 2.0 + h0 / 2.0
    half_ty = hc / 2.0 + h0 / 2.0
    inside = (np.abs(x) <= half_tx) & (np.abs(y) <= half_ty)
    F_punch = N_col_N - float(np.sum(P_N[inside]))
    punch_col = punching_column(max(F_punch, 0.0), bc, hc, h0, rbt)
    punch_col['n_inside'] = int(inside.sum())

    # ── CHỌC THỦNG quanh cọc chịu nén lớn nhất ────────────────────────────
    i_pmax = int(np.argmax(P_N))
    punch_pile = punching_pile(float(P_N[i_pmax]), D_mm, h0, rbt)
    punch_pile['pile_index'] = i_pmax

    # ── CẮT MỘT PHƯƠNG: tiết diện nguy hiểm tại MÉP CỘT, theo phương bất lợi ───
    def shear_dir(coord_mm, half_col, b_mm):
        posm = coord_mm > half_col          # cọc ngoài mép cột phía dương
        negm = -coord_mm > half_col         # ...phía âm
        Qp = float(np.sum(np.where(posm, P_N, 0.0)))
        Qn = float(np.sum(np.where(negm, P_N, 0.0)))
        Q, mask = (Qp, posm) if Qp >= Qn else (Qn, negm)
        # C = hình chiếu tiết diện nghiêng = k/c từ mép cột tới TRỌNG TÂM lực cọc ngoài mép.
        sumP = float(np.sum(P_N[mask])) if mask.any() else 0.0
        if Q > 0 and sumP > 0:
            C = float(np.sum((np.abs(coord_mm[mask]) - half_col) * P_N[mask]) / sumP)
        else:
            C = h0
        return oneway_shear(Q, rbt, b_mm, h0, C=C, rb=rb)

    shear_x = shear_dir(x, bc / 2.0, Ly_mm)
    shear_y = shear_dir(y, hc / 2.0, Lx_mm)

    # ── STM: cờ đài sâu theo cọc xa nhất ──────────────────────────────────
    a_far = float(np.max(np.abs(x) - bc / 2.0))    # cánh tay ngang lớn nhất [mm]
    stm = stm_tie(float(np.max(P_N)), max(a_far, 1.0), h0, rs)

    checks_ok = (flex_x['ok'] and flex_y['ok'] and punch_col['ok']
                 and punch_pile['ok'] and shear_x['ok'] and shear_y['ok'])
    return {
        'ok': True, 'status': 'ĐẠT' if checks_ok else 'KHÔNG ĐẠT',
        'mat': {'conc': conc, 'steel': steel, 'Rb': rb, 'Rbt': rbt, 'Rs': rs, 'xi_R': xi_R},
        'geom': {'H': H, 'cover': cover, 'h0_mm': h0, 'Lx': Lx, 'Ly': Ly,
                 'col_b': col_b, 'col_h': col_h, 'D': D, 'N_col_T': N_combo},
        'flexure': {'x': flex_x, 'y': flex_y},
        'punching': {'column': punch_col, 'pile': punch_pile},
        'shear': {'x': shear_x, 'y': shear_y},
        'stm': stm,
    }
