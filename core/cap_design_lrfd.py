"""
cap_design_lrfd.py - Thiết kế kết cấu ĐÀI CỌC theo TCVN 11823-5:2017 (Kết cấu bê
tông cầu — LRFD, tương đương AASHTO LRFD Section 5).

Thay TCVN 5574:2018 (core/cap_design.py) — vì TCVN 5574 là BTCT dân dụng/công
nghiệp, KHÔNG áp dụng cho thiết kế cầu. Kết cấu bê tông cầu phải theo TCVN 11823-5.

Triết lý LRFD:  hiệu ứng tải có hệ số  ≤  sức kháng có hệ số  =  φ · Rn

    Uốn      : Mu ≤ φ_f·Mn,  Mn = As·fy·(de − a/2), a = As·fy/(0,85·f'c·b)   (5.6.3)
    Cắt 1 ph : Vu ≤ φ_v·Vn,  Vn = Vc = 0,083·β·√f'c·bv·dv (β=2), Vn ≤ 0,25·f'c·bv·dv (5.7.3.3)
    Chọc thủng (cắt 2 phương): Vu ≤ φ_v·Vn,
               Vn = (0,17 + 0,33/βc)·√f'c·bo·dv ≤ 0,33·√f'c·bo·dv               (5.12.8.6)

╔══════════════════════════════════════════════════════════════════════════════╗
║ ⚠️ TRỊ THAM KHẢO theo AASHTO LRFD Section 5 (cơ sở của TCVN 11823-5). Các hệ  ║
║    số φ và công thức PHẢI được kỹ sư đối chiếu, nghiệm thu với bản TCVN        ║
║    11823-5:2017 trước khi dùng cho hồ sơ. Xem docs/project/MIGRATION_TCVN11823.md ║
╚══════════════════════════════════════════════════════════════════════════════╝

ĐƠN VỊ NỘI BỘ: N – mm – MPa (1 MPa = 1 N/mm²). Lực app theo Tấn → ×9,80665 ra kN
→ ×1000 ra N; kích thước m → ×1000 ra mm.
"""
import math
import numpy as np

from core import rigid_cap
from core.cap_design import TF_TO_KN, KN_TO_N, M_TO_MM

STANDARD = 'TCVN 11823-5:2017'

# ── Hệ số sức kháng φ (TCVN 11823-5 / AASHTO 5.5.4.2) — ⚠️ TRỊ THAM KHẢO ──────
PHI_FLEXURE = 0.90      # uốn, cấu kiện BTCT khống chế kéo (tension-controlled)
PHI_SHEAR = 0.90        # cắt & xoắn, bê tông trọng lượng thường
PHI_BEARING = 0.70      # ép mặt trên bê tông
PHI_STM_TIE = 0.90      # thanh kéo (tie) trong mô hình giàn ảo (thép)

# ── Cường độ vật liệu ─────────────────────────────────────────────────────────
# f'c (cường độ nén mẫu trụ, MPa). Quy đổi GẦN ĐÚNG từ cấp B (mẫu lập phương) ~0,78·B;
# nên khai trực tiếp params['FC']. ⚠️ trị quy đổi cần kỹ sư xác nhận.
FC_BY_GRADE = {'B15': 11.0, 'B20': 15.0, 'B25': 20.0, 'B30': 24.0, 'B35': 27.0,
               'B40': 31.0, 'C28': 28.0, 'C30': 30.0, 'C35': 35.0, 'C40': 40.0,
               'C45': 45.0, 'C50': 50.0}
# fy (giới hạn chảy cốt thép, MPa).
FY_BY_STEEL = {'CB240-T': 240.0, 'CB300-V': 300.0, 'CB400-V': 400.0, 'CB500-V': 500.0,
               'Grade60': 420.0, 'Grade75': 520.0}
ES = 200000.0           # mô đun đàn hồi cốt thép (MPa)


def materials(conc='C30', steel='CB400-V', params=None):
    """(f'c, fy, β1) theo cấp bê tông & nhóm thép (ưu tiên params['FC']/['FY']).

    β1 = hệ số khối ứng suất chữ nhật tương đương (AASHTO 5.6.2.2): 0,85 khi
    f'c ≤ 28 MPa; giảm 0,05 mỗi 7 MPa vượt 28; không nhỏ hơn 0,65.
    """
    params = params or {}
    fc = params.get('FC') or FC_BY_GRADE.get(conc, FC_BY_GRADE['C30'])
    fy = params.get('FY') or FY_BY_STEEL.get(steel, FY_BY_STEEL['CB400-V'])
    fc = float(fc); fy = float(fy)
    beta1 = 0.85 if fc <= 28.0 else max(0.65, 0.85 - 0.05 * (fc - 28.0) / 7.0)
    return fc, fy, beta1


# ============================================================================
# Kiểm toán đơn lẻ (N–mm–MPa)
# ============================================================================
def flexure_As(Mu, fc, fy, beta1, b, de):
    """Cốt thép chịu uốn (AASHTO/TCVN 11823-5 §5.6.3). Mu = mô men CÓ HỆ SỐ [N·mm].

    Yêu cầu Mn = Mu/φ_f; giải As từ Mn = As·fy·(de − a/2), a = As·fy/(0,85·f'c·b).
    Kiểm khống chế kéo c/de ≤ 0,42 (đảm bảo εt ≥ 0,005 ⇒ φ_f = 0,9). Cốt tối thiểu
    theo ρ_min ≈ max(0,25·√f'c/fy ; 1,4/fy) (proxy ACI/AASHTO — cần xác nhận).
    """
    Mu = max(float(Mu), 0.0)
    rho_min = max(0.25 * math.sqrt(fc) / fy, 1.4 / fy)
    As_min = rho_min * b * de
    if Mu <= 0:
        return {'ok': True, 'As': As_min, 'As_req': 0.0, 'As_min': As_min,
                'Mu': 0.0, 'Mr': 0.0, 'c_over_de': 0.0, 'phi': PHI_FLEXURE, 'reason': ''}
    Mn_req = Mu / PHI_FLEXURE
    Rn = Mn_req / (b * de * de)
    disc = 1.0 - 2.0 * Rn / (0.85 * fc)
    if disc < 0:
        return {'ok': False, 'As': float('nan'), 'As_req': float('nan'), 'As_min': As_min,
                'Mu': Mu, 'Mr': float('nan'), 'c_over_de': float('nan'), 'phi': PHI_FLEXURE,
                'reason': 'Mu vuot kha nang tiet dien — tang chieu cao dai H hoac f\'c'}
    rho = (0.85 * fc / fy) * (1.0 - math.sqrt(disc))
    As_req = rho * b * de
    a = As_req * fy / (0.85 * fc * b)
    c = a / beta1
    c_over_de = c / de if de > 0 else float('inf')
    As = max(As_req, As_min)
    # sức kháng có hệ số với As thực dùng
    a2 = As * fy / (0.85 * fc * b)
    Mr = PHI_FLEXURE * As * fy * (de - a2 / 2.0)
    ok = bool(c_over_de <= 0.42 and Mr >= Mu - 1.0)
    return {'ok': ok, 'As': As, 'As_req': As_req, 'As_min': As_min, 'Mu': Mu,
            'Mr': Mr, 'c_over_de': c_over_de, 'phi': PHI_FLEXURE,
            'reason': '' if ok else 'c/de>0,42: tiet dien khong khong che keo — tang H/f\'c'}


def _dv(de, H_mm):
    """Chiều cao chịu cắt hiệu dụng dv (AASHTO 5.7.2.8): dv = max(0,9·de ; 0,72·h)."""
    return max(0.9 * de, 0.72 * H_mm)


def oneway_shear(Vu, fc, bv, de, H_mm):
    """Cắt một phương (AASHTO/TCVN 11823-5 §5.7.3.3, β=2 đơn giản hoá).

    Vc = 0,083·β·√f'c·bv·dv (β=2); Vn ≤ 0,25·f'c·bv·dv. Vr = φ_v·Vn. Vu = lực CẮT
    CÓ HỆ SỐ [N]. need_stirrups khi Vu > φ_v·Vc.
    """
    dv = _dv(de, H_mm)
    beta = 2.0
    Vc = 0.083 * beta * math.sqrt(fc) * bv * dv
    Vn = min(Vc, 0.25 * fc * bv * dv)
    Vr = PHI_SHEAR * Vn
    return {'Vu': Vu, 'Vc': Vc, 'Vn': Vn, 'Vr': Vr, 'dv': dv, 'phi': PHI_SHEAR,
            'need_stirrups': bool(Vu > PHI_SHEAR * Vc),
            'ratio': (Vu / Vr if Vr > 0 else float('inf')), 'ok': bool(Vu <= Vr)}


def punching_column(Vu, bc, hc, de, H_mm, fc):
    """Chọc thủng quanh CỘT — cắt 2 phương (AASHTO/TCVN 11823-5 §5.12.8.6).

    βc = cạnh dài/cạnh ngắn cột. Chu vi tới hạn tại dv/2: bo = 2(bc+hc) + 4·(dv/2)·2
    = 2(bc+hc)+4·dv (mỗi phương +dv). Vn = (0,17+0,33/βc)·√f'c·bo·dv ≤ 0,33·√f'c·bo·dv.
    """
    dv = _dv(de, H_mm)
    bo = 2.0 * (bc + hc) + 4.0 * dv
    beta_c = max(bc, hc) / max(min(bc, hc), 1e-9)
    vn_unit = min((0.17 + 0.33 / beta_c) * math.sqrt(fc), 0.33 * math.sqrt(fc))
    Vn = vn_unit * bo * dv
    Vr = PHI_SHEAR * Vn
    return {'Vu': Vu, 'Vn': Vn, 'Vr': Vr, 'bo': bo, 'dv': dv, 'beta_c': beta_c,
            'phi': PHI_SHEAR, 'ratio': (Vu / Vr if Vr > 0 else float('inf')),
            'ok': bool(Vu <= Vr)}


def punching_pile(P, D_pile, de, H_mm, fc):
    """Chọc thủng quanh một CỌC (tròn). bo = π·(D + dv); dùng cận 0,33·√f'c (βc=1)."""
    dv = _dv(de, H_mm)
    bo = math.pi * (D_pile + dv)
    Vn = 0.33 * math.sqrt(fc) * bo * dv
    Vr = PHI_SHEAR * Vn
    return {'Vu': P, 'Vn': Vn, 'Vr': Vr, 'bo': bo, 'dv': dv, 'phi': PHI_SHEAR,
            'ratio': (P / Vr if Vr > 0 else float('inf')), 'ok': bool(P <= Vr)}


def stm_tie(P, a_horiz, de, fy, z_factor=0.9):
    """Thanh kéo giàn ảo (STM) — TCVN 11823-5 §5.8 (AASHTO STM). z=z_factor·de;
    T = P·a/z; As_tie = T/(φ_tie·fy). Cờ deep khi a/de < 1,0. ⚠️ z, ngưỡng đài sâu
    theo thực hành AASHTO/ACI — cần xác nhận."""
    z = z_factor * de
    T = P * a_horiz / z if z > 0 else 0.0
    theta = math.degrees(math.atan2(z, a_horiz)) if a_horiz > 0 else 90.0
    return {'T': T, 'As_tie': (T / (PHI_STM_TIE * fy) if fy > 0 else float('nan')),
            'theta_deg': theta, 'phi': PHI_STM_TIE,
            'deep': bool((a_horiz / de) < 1.0) if de > 0 else False}


# ============================================================================
# Tổng hợp: thiết kế đài theo 11823-5 (giữ shape kết quả tương thích UI/report)
# ============================================================================
def _governing_forces(coords, loads):
    coords = np.asarray(coords, dtype=float)
    P = rigid_cap.forces_all_loads(coords, loads)     # (n_load, n_pile), Tấn (đã có hệ số nếu LRFD)
    if P.size == 0:
        return np.zeros(len(coords)), 0.0
    gov = int(np.argmax(P.max(axis=1)))
    return P[gov], float(loads[gov].get('N', 0.0))


def design_cap_lrfd(coords, params, loads, calib=1.0):
    """Thiết kế đài cọc theo TCVN 11823-5:2017 (LRFD). Trả dict cùng shape với
    core.cap_design.design_cap (+ khoá 'standard', các kiểm theo φ·Rn)."""
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
        return {'ok': False, 'missing': missing, 'standard': STANDARD}

    conc = params.get('conc_grade', 'C30')
    steel = params.get('steel_grade', 'CB400-V')
    fc, fy, beta1 = materials(conc, steel, params)

    de = (H - cover) * M_TO_MM                      # chiều cao làm việc de [mm]
    H_mm = H * M_TO_MM
    Lx = (coords[:, 0].max() - coords[:, 0].min()) + D
    Ly = (coords[:, 1].max() - coords[:, 1].min()) + D
    Lx_mm, Ly_mm = max(Lx, D) * M_TO_MM, max(Ly, D) * M_TO_MM
    bc, hc = col_b * M_TO_MM, col_h * M_TO_MM
    D_mm = D * M_TO_MM

    f_pile, N_combo = _governing_forces(coords, loads)
    f_pile = np.asarray(f_pile, float) * calib
    P_N = f_pile * TF_TO_KN * KN_TO_N               # phản lực cọc CÓ HỆ SỐ [N]
    N_col_N = N_combo * TF_TO_KN * KN_TO_N
    cx, cy = coords[:, 0].mean(), coords[:, 1].mean()
    x = (coords[:, 0] - cx) * M_TO_MM
    y = (coords[:, 1] - cy) * M_TO_MM

    # ── UỐN: tiết diện nguy hiểm tại mép cột ──────────────────────────────
    def flexure_dir(coord_mm, half_col, b_mm):
        M_pos = float(np.sum(np.maximum(coord_mm - half_col, 0.0)
                             * np.where(coord_mm > half_col, P_N, 0.0)))
        M_neg = float(np.sum(np.maximum(-coord_mm - half_col, 0.0)
                             * np.where(-coord_mm > half_col, P_N, 0.0)))
        return flexure_As(max(M_pos, M_neg), fc, fy, beta1, b_mm, de)

    flex_x = flexure_dir(x, bc / 2.0, Ly_mm)
    flex_y = flexure_dir(y, hc / 2.0, Lx_mm)

    # ── CHỌC THỦNG quanh cột: trừ phản lực cọc trong chu vi tới hạn (dv/2) ──
    dv = _dv(de, H_mm)
    half_tx = bc / 2.0 + dv / 2.0
    half_ty = hc / 2.0 + dv / 2.0
    inside = (np.abs(x) <= half_tx) & (np.abs(y) <= half_ty)
    Vu_punch = max(N_col_N - float(np.sum(P_N[inside])), 0.0)
    punch_col = punching_column(Vu_punch, bc, hc, de, H_mm, fc)
    punch_col['n_inside'] = int(inside.sum())

    i_pmax = int(np.argmax(P_N))
    punch_pile = punching_pile(float(P_N[i_pmax]), D_mm, de, H_mm, fc)
    punch_pile['pile_index'] = i_pmax

    # ── CẮT MỘT PHƯƠNG: tiết diện nguy hiểm tại dv tính từ mép cột ─────────
    def shear_dir(coord_mm, half_col, b_mm):
        crit = half_col + dv                       # tiết diện cách mép cột 1 dv (AASHTO)
        posm = coord_mm > crit
        negm = -coord_mm > crit
        Vu = max(float(np.sum(np.where(posm, P_N, 0.0))),
                 float(np.sum(np.where(negm, P_N, 0.0))))
        return oneway_shear(Vu, fc, b_mm, de, H_mm)

    shear_x = shear_dir(x, bc / 2.0, Ly_mm)
    shear_y = shear_dir(y, hc / 2.0, Lx_mm)

    a_far = float(np.max(np.abs(x) - bc / 2.0))
    stm = stm_tie(float(np.max(P_N)), max(a_far, 1.0), de, fy)

    checks_ok = (flex_x['ok'] and flex_y['ok'] and punch_col['ok']
                 and punch_pile['ok'] and shear_x['ok'] and shear_y['ok'])
    return {
        'ok': True, 'standard': STANDARD,
        'status': 'ĐẠT' if checks_ok else 'KHÔNG ĐẠT',
        'mat': {'conc': conc, 'steel': steel, 'fc': fc, 'fy': fy, 'beta1': beta1,
                'phi_f': PHI_FLEXURE, 'phi_v': PHI_SHEAR},
        'geom': {'H': H, 'cover': cover, 'h0_mm': de, 'dv_mm': dv, 'Lx': Lx, 'Ly': Ly,
                 'col_b': col_b, 'col_h': col_h, 'D': D, 'N_col_T': N_combo},
        'flexure': {'x': flex_x, 'y': flex_y},
        'punching': {'column': punch_col, 'pile': punch_pile},
        'shear': {'x': shear_x, 'y': shear_y},
        'stm': stm,
    }
