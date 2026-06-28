"""
tcvn.py - NGUỒN DUY NHẤT các tính toán theo TCVN 10304:2014 (Móng cọc - Tiêu chuẩn thiết kế).

Module gom 3 nhóm tính toán mà trước đây OptApp chưa làm đúng/đủ:

1) SỨC CHỊU TẢI THIẾT KẾ (Điều 7.1.11) — biến [Po]/[Ct] từ "một con số nhập tùy ý"
   thành sức chịu tải THIẾT KẾ Rc,d / Rt,d tính từ sức chịu tải tiêu chuẩn và các
   hệ số tin cậy:

        R_c,d = (γ0 / γn) * (R_c,k / γk)

   với  γ0 — hệ số điều kiện làm việc (1,0 cọc đơn; 1,15 móng nhiều cọc),
        γn — hệ số tin cậy tầm quan trọng công trình (cấp I/II/III = 1,2/1,15/1,1),
        γk — hệ số tin cậy theo đất (phụ thuộc cách xác định Rc,u và số cọc).

2) MÓNG KHỐI QUY ƯỚC (Điều 7.4) — kích thước khối móng quy ước mở rộng từ chu vi
   nhóm cọc theo góc φ_tb/4 trên suốt chiều dài cọc, dùng để kiểm nền dưới mũi cọc
   và làm cơ sở tính lún của cả nhóm cọc (không chỉ kiểm từng cọc rời).

3) LÚN MÓNG CỌC (Điều 7.4.2 + Phụ lục C, theo phương pháp cộng lún từng lớp của
   TCVN 9362) — đặt tải quy ước tại đáy khối móng quy ước, phân bố ứng suất theo
   sơ đồ 2:1 và cộng lún đàn hồi từng lớp S = Σ β·σ_zi·h_i / E_i (β = 0,8).

QUAN TRỌNG — số liệu địa chất: nhóm (2) và (3) cần số liệu đất nền (chiều dài cọc,
φ_tb, các lớp đất dưới mũi với E, h, γ). File input hiện hành của OptApp KHÔNG mang
các số liệu này; do đó khi thiếu, các hàm trả về kết quả có cờ ``evaluated=False`` để
báo cáo ghi rõ "CHƯA KIỂM — thiếu số liệu địa chất" thay vì âm thầm bỏ qua.

Đơn vị: lực theo Tấn (T) đồng bộ với MCOC; chiều dài theo m; mômen quán tính m^2;
mô đun biến dạng E theo T/m^2 (nếu nhập kPa thì quy đổi trước khi truyền vào).
"""

import math
import numpy as np


# ============================================================================
# 1. SỨC CHỊU TẢI THIẾT KẾ — Điều 7.1.11
# ============================================================================
# Hệ số tin cậy tầm quan trọng γn theo cấp công trình (Điều 7.1.11).
GAMMA_N_BY_LEVEL = {'I': 1.20, 'II': 1.15, 'III': 1.10, 1: 1.20, 2: 1.15, 3: 1.10}

# Mặc định an toàn khi người dùng chỉ khai báo Rc,k mà chưa nêu hệ số.
DEFAULT_GAMMA_0 = 1.15   # móng nhiều cọc (cọc đơn dùng 1,0)
DEFAULT_GAMMA_N = 1.15   # công trình cấp II
DEFAULT_GAMMA_K = 1.40   # Rc,u xác định bằng tính toán

# Hệ số tin cậy theo đất γk theo SỐ CỌC trong móng (Điều 7.1.11 — đài cao chịu nén
# hoặc cọc chịu kéo). Mỗi mục: (số cọc tối thiểu, γk khi Rc,u xác định bằng TÍNH TOÁN,
# γk khi xác định bằng THỬ TẢI TĨNH). Đối chiếu words_dict/TCVN10304-2014.md dòng 611-628.
GAMMA_K_BY_NPILES = [
    (21, 1.40, 1.25),   # 21 cọc trở lên
    (11, 1.55, 1.40),   # 11–20 cọc
    (6,  1.65, 1.50),   # 6–10 cọc
    (1,  1.75, 1.60),   # 1–5 cọc
]


def resolve_gamma_k(n_piles, by_static_test=False):
    """γk theo số cọc trong móng (Điều 7.1.11, móng nhiều cọc đài cao / cọc chịu kéo).

    n_piles       : số cọc trong móng.
    by_static_test: True nếu Rc,u xác định bằng thử tải tĩnh (dùng cột trong ngoặc).
    Trả DEFAULT_GAMMA_K khi không xác định được số cọc.

    LƯU Ý vòng lặp phụ thuộc: [Po]=Rc,d cần γk, mà γk phụ thuộc số cọc — số cọc chỉ
    biết SAU khi tối ưu. Vì vậy hàm này dùng để (a) tính/kiểm γk ở khâu BÁO CÁO khi đã
    có số cọc, (b) làm mặc định khi params mang sẵn 'n_piles'. Ô γk nhập tay luôn ưu tiên.
    """
    n = int(n_piles or 0)
    for nmin, gk_calc, gk_test in GAMMA_K_BY_NPILES:
        if n >= nmin:
            return gk_test if by_static_test else gk_calc
    return DEFAULT_GAMMA_K


def design_axial_capacity(R_ck, gamma_0=DEFAULT_GAMMA_0,
                          gamma_n=DEFAULT_GAMMA_N, gamma_k=DEFAULT_GAMMA_K):
    """Sức chịu tải thiết kế của cọc theo Điều 7.1.11.

        R_c,d = (γ0 / γn) * (R_c,k / γk)

    Đầu vào:
        R_ck    : sức chịu tải tiêu chuẩn (T). Nếu xác định bằng tính toán thì
                  lấy bằng sức chịu tải cực hạn Rc,u (Rc,k = Rc,u).
        gamma_0 : hệ số điều kiện làm việc γ0.
        gamma_n : hệ số tin cậy tầm quan trọng γn.
        gamma_k : hệ số tin cậy theo đất γk.
    Trả về:
        Sức chịu tải thiết kế Rc,d (T). Trả 0.0 nếu thiếu/không hợp lệ.
    """
    if not R_ck or R_ck <= 0 or gamma_n <= 0 or gamma_k <= 0:
        return 0.0
    return (gamma_0 / gamma_n) * (R_ck / gamma_k)


def resolve_gamma_n(params):
    """Suy ra γn: ưu tiên GAMMA_N tường minh, sau đó theo cấp công trình."""
    if params.get('GAMMA_N'):
        return float(params['GAMMA_N'])
    level = params.get('IMPORTANCE_LEVEL')
    if level is not None:
        key = str(level).strip().upper()
        if key in GAMMA_N_BY_LEVEL:
            return GAMMA_N_BY_LEVEL[key]
        try:
            return GAMMA_N_BY_LEVEL[int(level)]
        except (ValueError, KeyError, TypeError):
            pass
    return DEFAULT_GAMMA_N


def apply_design_capacities(params):
    """Chuẩn hóa [Po]/[Ct] thành sức chịu tải THIẾT KẾ Rc,d/Rt,d (Điều 7.1.11).

    Quy tắc (idempotent — gọi lại nhiều lần vẫn an toàn):
      * Nếu params có ``R_C_K`` (sức chịu nén tiêu chuẩn) → tính Rc,d và GHI ĐÈ
        ``P_LIMIT``; tương tự ``R_T_K`` → Rt,d ghi đè ``P_TENSION`` (kéo dùng γk
        riêng ``GAMMA_K_T`` nếu có, mặc định dùng chung γk).
      * Nếu KHÔNG có Rc,k → giữ nguyên ``P_LIMIT``/``P_TENSION`` do người dùng nhập
        và coi đó ĐÃ là sức chịu tải thiết kế (nguồn = 'input').

    Đính kèm metadata để báo cáo truy vết:
        params['_capacity_source'] = 'tcvn_7.1.11' | 'input'
        params['_tcvn_factors']    = {gamma_0, gamma_n, gamma_k, R_ck, R_tk}
        params['_tcvn_applied']    = True   (cờ chống áp dụng trùng)
    Trả về chính ``params`` (đã sửa tại chỗ) để tiện gọi inline.
    """
    if params.get('_tcvn_applied'):
        return params

    R_ck = params.get('R_C_K') or params.get('RC_K') or 0.0
    R_tk = params.get('R_T_K') or params.get('RT_K') or 0.0
    g0 = float(params.get('GAMMA_0', DEFAULT_GAMMA_0))
    gn = resolve_gamma_n(params)
    # γk: ưu tiên ô nhập tay (GAMMA_K) → tự suy theo số cọc nếu có 'n_piles' (Đ.7.1.11)
    # → mặc định 1,40. Xem resolve_gamma_k về vòng lặp phụ thuộc số cọc.
    gk = params.get('GAMMA_K')
    if gk is None and params.get('n_piles'):
        gk = resolve_gamma_k(params['n_piles'], bool(params.get('GAMMA_K_STATIC_TEST')))
    gk = float(gk) if gk else DEFAULT_GAMMA_K
    gk_t = float(params.get('GAMMA_K_T', gk))

    if R_ck and R_ck > 0:
        params['P_LIMIT'] = design_axial_capacity(R_ck, g0, gn, gk)
        if R_tk and R_tk > 0:
            params['P_TENSION'] = design_axial_capacity(R_tk, g0, gn, gk_t)
        params['_capacity_source'] = 'tcvn_7.1.11'
    else:
        params['_capacity_source'] = 'input'

    params['_tcvn_factors'] = {'gamma_0': g0, 'gamma_n': gn, 'gamma_k': gk,
                               'gamma_k_t': gk_t, 'R_ck': float(R_ck or 0.0),
                               'R_tk': float(R_tk or 0.0)}
    params['_tcvn_applied'] = True
    return params


# ============================================================================
# 2. MÓNG KHỐI QUY ƯỚC — Điều 7.4
# ============================================================================
def equivalent_block(coords, params):
    """Kích thước móng khối quy ước (Điều 7.4).

    Khối quy ước mở rộng từ chu vi nhóm cọc ra ngoài một góc φ_tb/4 trên suốt
    chiều dài cọc Lc:
        B_qu = (span_x + d) + 2·Lc·tan(φ_tb/4)
        L_qu = (span_y + d) + 2·Lc·tan(φ_tb/4)
    với span_x, span_y là khoảng cách tim cọc ngoài cùng theo 2 phương; d cộng
    thêm để tính tới mép cọc biên.

    Cần: params['pile_length'] (Lc, m) và params['phi_tb'] (độ). Thiếu → trả về
    dict với evaluated=False kèm lý do.
    """
    Lc = params.get('pile_length') or params.get('PILE_LENGTH') or 0.0
    phi = params.get('phi_tb') or params.get('PHI_TB') or 0.0
    d = params.get('D_PILE', 0.0)
    if Lc <= 0 or phi <= 0:
        return {'evaluated': False,
                'reason': 'Thieu chieu dai coc (pile_length) hoac phi_tb de tinh mong khoi quy uoc'}

    coords = np.asarray(coords, dtype=float)
    span_x = float(coords[:, 0].max() - coords[:, 0].min())
    span_y = float(coords[:, 1].max() - coords[:, 1].min())
    # a = h·tg(φ/4) MỖI BÊN (CT 40). Đ.7.4.4: "lấy KHÔNG QUÁ 2d trong trường hợp dưới
    # mũi cọc là nền đất dính có chỉ số sệt IL > 0,6" → chặn khi bật cờ soft_clay_below.
    a_side = Lc * math.tan(math.radians(phi) / 4.0)
    capped = False
    if params.get('soft_clay_below') and d > 0:
        if a_side > 2.0 * d:
            a_side = 2.0 * d
            capped = True
    spread = 2.0 * a_side
    B_qu = span_x + d + spread
    L_qu = span_y + d + spread
    cap_depth = params.get('cap_depth') or params.get('CAP_DEPTH') or 0.0
    return {'evaluated': True, 'B_qu': B_qu, 'L_qu': L_qu,
            'A_qu': B_qu * L_qu, 'base_depth': cap_depth + Lc,
            'spread': spread, 'a_side': a_side, 'a_capped_2d': capped,
            'phi_tb': phi, 'Lc': Lc}


# ============================================================================
# 3. LÚN MÓNG CỌC — TCVN 10304:2014 Đ.7.4.4 (móng khối quy ước theo TCVN 9362:2012)
# ============================================================================
# Đ.7.4.4: lún móng cọc = biến dạng đàn hồi thân cọc (Se) + lún móng khối quy ước,
# tính như móng nông trên nền thiên nhiên theo TCVN 9362:2012 (cộng lún từng lớp).
BETA_SETTLEMENT = 0.8       # hệ số cộng lún từng lớp TCVN 9362 (hệ số không thứ nguyên)
BETA_E_PILE = 0.5           # β cho biến dạng đàn hồi thân cọc Se (dải 0,3–0,7, CT 21)


def _boussinesq_center(B, L, z):
    """Hệ số ứng suất thẳng đứng σz/p tại TÂM móng chữ nhật B×L ở độ sâu z theo
    nghiệm Boussinesq/Newmark — cơ sở của bảng tra ứng suất TCVN 9362 (thay xấp xỉ 2:1).

        σz/p = 4·I_góc(m,n),  m=(B/2)/z, n=(L/2)/z
    atan2 tự cộng π khi mẫu (s−m²n²) âm. z=0 → 1,0.
    """
    if z <= 0:
        return 1.0
    m = (B / 2.0) / z
    n = (L / 2.0) / z
    m2, n2 = m * m, n * n
    s = m2 + n2 + 1.0
    rt = math.sqrt(s)
    term1 = (2.0 * m * n * rt / (s + m2 * n2)) * ((m2 + n2 + 2.0) / s)
    term2 = math.atan2(2.0 * m * n * rt, s - m2 * n2)
    return 4.0 * (term1 + term2) / (4.0 * math.pi)


def _pile_elastic_shortening(N, params):
    """Se = β·N·Lc/(E·A) — biến dạng đàn hồi thân cọc (CT 21; β=0,3–0,7, dùng 0,5).

    Cần mô đun thân cọc E (T/m², params['E_b']) và diện tích cọc A (m², params['F_o']
    hoặc π·d²/4). Thiếu → trả (0.0, False) để báo cáo nêu rõ "bỏ qua Se".
    Trả (Se [m], đã_tính?).
    """
    Lc = params.get('pile_length') or params.get('PILE_LENGTH') or 0.0
    E = params.get('E_b') or params.get('E_B') or 0.0
    d = params.get('D_PILE', 0.0) or 0.0
    A = params.get('F_o') or params.get('F_O') or (math.pi * d * d / 4.0 if d > 0 else 0.0)
    if E <= 0 or A <= 0 or Lc <= 0 or N <= 0:
        return 0.0, False
    return BETA_E_PILE * N * Lc / (E * A), True


def settlement(coords, loads, params):
    """Độ lún móng cọc theo TCVN 10304:2014 Đ.7.4.4 (mô hình móng khối quy ước).

        S = Se + S_khối
    Se = biến dạng đàn hồi thân cọc (CT 21); S_khối = lún móng khối quy ước tính như
    móng nông trên nền thiên nhiên theo TCVN 9362:2012 — cộng lún từng lớp:
        S_khối = Σ β · σ_zi · h_i / E_i        (β = 0,8)
    Ứng suất gây lún σ_zi tại TÂM khối lấy theo nghiệm Boussinesq (cơ sở bảng tra
    TCVN 9362), KHÔNG dùng xấp xỉ 2:1. Vùng nén lún tới khi σ_zi ≤ 0,2·σ'_vz (khi có
    γ để tính ứng suất bản thân), ngược lại lấy hết các lớp khai báo.

    Cần:
        params['soil_below'] : list lớp đất DƯỚI đáy khối quy ước, mỗi lớp dict
            {'h': dày (m), 'E': mô đun biến dạng (T/m^2), 'gamma': dung trọng (T/m^3, tùy chọn)}
        equivalent_block(...) tính được (cần pile_length, phi_tb).
        Se cần thêm E_b (mô đun thân cọc) + (F_o hoặc D_PILE).
        params['S_LIMIT'] : độ lún giới hạn S_gh (m, tùy chọn) để kết luận đạt/không.
    Thiếu số liệu → trả dict evaluated=False kèm lý do.
    """
    block = equivalent_block(coords, params)
    if not block.get('evaluated'):
        return {'evaluated': False, 'reason': block['reason']}

    layers = params.get('soil_below') or params.get('SOIL_BELOW')
    if not layers:
        return {'evaluated': False,
                'reason': 'Thieu so lieu cac lop dat duoi mui coc (soil_below) de tinh lun'}

    # Tải dọc trục lớn nhất (T) trên mọi tổ hợp -> áp lực đáy khối quy ước.
    N = max((float(ld.get('N', 0.0)) for ld in loads), default=0.0)
    B, L, A = block['B_qu'], block['L_qu'], block['A_qu']
    if A <= 0:
        return {'evaluated': False, 'reason': 'Dien tich khoi quy uoc khong hop le'}

    # Áp lực gây lún p_gl tại đáy khối (trừ ứng suất bản thân tại đáy nếu có γ).
    base_depth = block['base_depth']
    gamma_avg = params.get('gamma_avg') or params.get('GAMMA_AVG') or 0.0
    sigma_v0_base = gamma_avg * base_depth if gamma_avg > 0 else 0.0
    p_gl = N / A - sigma_v0_base

    # Se: biến dạng đàn hồi thân cọc (cộng nếu đủ số liệu E_b + diện tích cọc).
    S_e, se_ok = _pile_elastic_shortening(N, params)

    if p_gl <= 0:
        S_limit0 = params.get('S_LIMIT') or params.get('S_GH')
        return {'evaluated': True, 'S': S_e, 'S_block': 0.0, 'S_e': S_e,
                'se_evaluated': se_ok,
                'S_limit': float(S_limit0) if S_limit0 else None,
                'ok': (S_e <= float(S_limit0)) if S_limit0 else None,
                'p_gl': p_gl, 'block': block, 'layers': [],
                'note': 'Ap luc gay lun <= 0 (tai nho hon ung suat ban than) — chi con Se'}

    S_block = 0.0
    z = 0.0                                   # độ sâu tính từ đáy khối quy ước
    detail = []
    for ly in layers:
        h = float(ly.get('h', 0.0))
        E = float(ly.get('E', 0.0))
        if h <= 0 or E <= 0:
            continue
        z_mid = z + h / 2.0
        # Ứng suất gây lún giữa lớp theo nghiệm Boussinesq tại TÂM khối (TCVN 9362).
        sigma_z = p_gl * _boussinesq_center(B, L, z_mid)
        # Dừng khi vào vùng ổn định (σz <= 0,2 σ'vz) nếu tính được ứng suất bản thân.
        if gamma_avg > 0 and sigma_z <= 0.2 * gamma_avg * (base_depth + z_mid):
            break
        ds = BETA_SETTLEMENT * sigma_z * h / E
        S_block += ds
        detail.append({'z_mid': z_mid, 'sigma_z': sigma_z, 'h': h, 'E': E, 'ds': ds})
        z += h

    S = S_e + S_block
    S_limit = params.get('S_LIMIT') or params.get('S_GH')
    ok = (S <= float(S_limit)) if S_limit else None
    return {'evaluated': True, 'S': S, 'S_block': S_block, 'S_e': S_e,
            'se_evaluated': se_ok, 'S_limit': float(S_limit) if S_limit else None,
            'ok': ok, 'p_gl': p_gl, 'block': block, 'layers': detail}
