"""
lrfd.py - NGUỒN DUY NHẤT các tính toán theo TCVN 11823:2017 (Thiết kế cầu đường bộ),
triết lý LRFD (Load and Resistance Factor Design). Đặt SONG SONG với core/tcvn.py
(TCVN 10304:2014) để có thể chuyển đổi cơ sở thiết kế qua cờ ``DESIGN_BASIS``.

Triết lý LRFD — kiểm theo TRẠNG THÁI GIỚI HẠN:

        Σ γ_i · Q_i   ≤   φ · R_n

    Vế trái  = HIỆU ỨNG TẢI có hệ số (demand): tổ hợp các tải Q_i nhân hệ số tải γ_i
               theo trạng thái giới hạn (Cường độ I–V / Sử dụng I / Đặc biệt I–II),
               TCVN 11823-3 (Bảng 3.4.1-1).
    Vế phải  = SỨC KHÁNG có hệ số: sức kháng danh nghĩa R_n nhân hệ số sức kháng φ
               (TCVN 11823-10), φ chọn theo PHƯƠNG PHÁP xác định R_n; móng chỉ có
               1 cọc đỡ trụ → φ giảm 20%.

Cách lắp vào OptApp mà KHÔNG đụng đường nội lực (MCOC vẫn là oracle):
  * Phía sức kháng: ``apply_lrfd_capacities`` đặt ``P_LIMIT = φ·R_n`` (như Rc,d của
    core/tcvn.py nhưng theo 11823) → phép so ``pmax ≤ P_LIMIT`` sẵn có trở thành
    ``demand ≤ φ·R_n``.
  * Phía tải: ``demand_loads`` nhân hệ số γ vào tải TRƯỚC khi đưa vào đánh giá →
    ``pmax`` thành hiệu ứng tải có hệ số. (MCOC vẫn chạy 1 lần/phương án trên cả
    bộ tải, không tăng số lần gọi — xem ADR-001 + kế hoạch QĐ-2.)

╔══════════════════════════════════════════════════════════════════════════════╗
║ ⚠️  CẢNH BÁO TRỊ SỐ: các hệ số γ/φ dưới đây là TRỊ THAM KHẢO theo AASHTO LRFD  ║
║     (cơ sở của TCVN 11823) và PHẢI được kỹ sư đối chiếu, xác nhận với bản     ║
║     TCVN 11823-3:2017 (tải) và TCVN 11823-10:2017 (nền móng) trước khi dùng   ║
║     cho hồ sơ thật. Xem docs/project/MIGRATION_TCVN11823.md.                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Đơn vị: lực Tấn (T) đồng bộ MCOC; mômen T·m; chiều dài m.
"""

# ============================================================================
# 1. HỆ SỐ TẢI TRỌNG γ — TCVN 11823-3:2017 (Bảng 3.4.1-1) ⇄ AASHTO Table 3.4.1-1
# ============================================================================
# LOAD_FACTORS[trạng_thái][loại_tải] = (γ_max, γ_min).
# Loại tải (TCVN 11823-3): DC tĩnh tải kết cấu · DW tĩnh tải lớp phủ/tiện ích ·
# LL hoạt tải + xung kích (IM) · BR lực hãm · WS gió lên kết cấu · WL gió lên xe ·
# EQ động đất · CT lực va xe · IC lực va băng · WA áp lực nước · EV/EH đất.
# ⚠️ TRỊ THAM KHẢO — CẦN XÁC NHẬN với TCVN 11823-3.
LOAD_FACTORS = {
    'STRENGTH_I':   {'DC': (1.25, 0.90), 'DW': (1.50, 0.65), 'LL': (1.75, 1.75),
                     'BR': (1.75, 1.75), 'EV': (1.35, 1.00), 'EH': (1.50, 0.90), 'WA': (1.00, 1.00)},
    'STRENGTH_II':  {'DC': (1.25, 0.90), 'DW': (1.50, 0.65), 'LL': (1.35, 1.35),
                     'BR': (1.35, 1.35), 'EV': (1.35, 1.00), 'EH': (1.50, 0.90), 'WA': (1.00, 1.00)},
    'STRENGTH_III': {'DC': (1.25, 0.90), 'DW': (1.50, 0.65), 'LL': (0.00, 0.00),
                     'WS': (1.40, 1.40), 'EV': (1.35, 1.00), 'EH': (1.50, 0.90), 'WA': (1.00, 1.00)},
    'STRENGTH_IV':  {'DC': (1.50, 0.90), 'DW': (1.50, 0.65), 'LL': (0.00, 0.00),
                     'EV': (1.35, 1.00), 'EH': (1.50, 0.90), 'WA': (1.00, 1.00)},
    'STRENGTH_V':   {'DC': (1.25, 0.90), 'DW': (1.50, 0.65), 'LL': (1.35, 1.35),
                     'WS': (0.40, 0.40), 'WL': (1.00, 1.00), 'EV': (1.35, 1.00),
                     'EH': (1.50, 0.90), 'WA': (1.00, 1.00)},
    'SERVICE_I':    {'DC': (1.00, 1.00), 'DW': (1.00, 1.00), 'LL': (1.00, 1.00),
                     'WS': (0.30, 0.30), 'WL': (1.00, 1.00), 'EV': (1.00, 1.00),
                     'EH': (1.00, 1.00), 'WA': (1.00, 1.00)},
    'EXTREME_I':    {'DC': (1.25, 0.90), 'DW': (1.50, 0.65), 'LL': (0.50, 0.50),
                     'EQ': (1.00, 1.00), 'EV': (1.35, 1.00), 'EH': (1.50, 0.90), 'WA': (1.00, 1.00)},
    'EXTREME_II':   {'DC': (1.25, 0.90), 'DW': (1.50, 0.65), 'LL': (0.50, 0.50),
                     'CT': (1.00, 1.00), 'IC': (1.00, 1.00), 'EV': (1.35, 1.00),
                     'EH': (1.50, 0.90), 'WA': (1.00, 1.00)},
}

DEFAULT_LOAD_TYPE = 'LL'      # tải nhập không gắn loại → coi là hoạt tải (thường chi phối móng)
DEFAULT_STRENGTH_STATE = 'STRENGTH_I'   # trạng thái cường độ chi phối mặc định cho kiểm cọc dọc trục
GAMMA_EQ_DEFAULT = 0.50       # hệ số hoạt tải γ_EQ ở trạng thái Đặc biệt I (0/0,5/1,0 theo chủ đầu tư)

# Các thành phần lực/mômen của một dòng tải được nhân CÙNG một hệ số γ của loại tải đó.
_LOAD_COMPONENTS = ('N', 'Mx', 'My', 'Mz', 'Hx', 'Hy')


# ============================================================================
# 2. HỆ SỐ SỨC KHÁNG φ — TCVN 11823-10:2017 (Bảng 10.5.5.2.3-1 / -2.4-1)
# ============================================================================
# RESISTANCE_FACTORS[(loại_cọc, tác_động)][phương_pháp] = φ.
#   loại_cọc : 'driven' (cọc đóng) | 'drilled' (cọc khoan nhồi)
#   tác_động : 'compression' (nén dọc trục) | 'uplift' (kéo/nhổ)
#   phương_pháp xác định R_n: thử tải tĩnh / thử động / phân tích tĩnh / CPT...
# ⚠️ TRỊ THAM KHẢO theo AASHTO §10.5.5.2 — CẦN XÁC NHẬN với TCVN 11823-10 (Bảng 10/11).
RESISTANCE_FACTORS = {
    ('driven', 'compression'): {'static_load_test': 0.75, 'dynamic_test': 0.65,
                                'wave_equation': 0.50, 'static_analysis': 0.50,
                                'cpt': 0.50, 'default': 0.45},
    ('driven', 'uplift'):      {'static_load_test': 0.60, 'static_analysis': 0.35,
                                'default': 0.35},
    ('drilled', 'compression'):{'static_load_test': 0.70, 'static_analysis': 0.50,
                                'cpt': 0.55, 'default': 0.45},
    ('drilled', 'uplift'):     {'static_load_test': 0.60, 'static_analysis': 0.40,
                                'default': 0.35},
}

DEFAULT_PILE_TYPE = 'driven'
DEFAULT_RESIST_METHOD = 'static_analysis'   # thận trọng khi chưa khai phương pháp
SINGLE_PILE_FACTOR = 0.80                   # móng 1 cọc đỡ trụ → φ × 0,8 (TCVN 11823-10)
EXTREME_PHI = 1.00                          # trạng thái Đặc biệt thường lấy φ = 1,0


def resistance_factor(pile_type=DEFAULT_PILE_TYPE, action='compression',
                      method=DEFAULT_RESIST_METHOD, single_pile=False, extreme=False):
    """Hệ số sức kháng φ (TCVN 11823-10) theo loại cọc + tác động + phương pháp.

    single_pile=True → φ × 0,8 (móng 1 cọc đỡ trụ). extreme=True → trạng thái Đặc
    biệt, lấy φ=1,0. Phương pháp/loại không có trong bảng → dùng 'default' (bảo thủ).
    """
    if extreme:
        phi = EXTREME_PHI
    else:
        table = RESISTANCE_FACTORS.get((pile_type, action))
        if not table:
            table = RESISTANCE_FACTORS.get((DEFAULT_PILE_TYPE, action), {'default': 0.45})
        phi = table.get(method, table.get('default', 0.45))
    if single_pile:
        phi *= SINGLE_PILE_FACTOR
    return phi


def factored_resistance(R_n, pile_type=DEFAULT_PILE_TYPE, action='compression',
                        method=DEFAULT_RESIST_METHOD, single_pile=False, extreme=False):
    """Sức kháng có hệ số φ·R_n (TCVN 11823-10). R_n ≤ 0 → trả 0,0."""
    if not R_n or R_n <= 0:
        return 0.0
    return resistance_factor(pile_type, action, method, single_pile, extreme) * float(R_n)


# ============================================================================
# 3. ÁP HỆ SỐ TẢI — sinh hiệu ứng tải có hệ số (demand)
# ============================================================================
def _factor_row(row, gamma):
    """Nhân hệ số γ vào mọi thành phần lực/mômen của một dòng tải (giữ metadata)."""
    out = dict(row)
    for k in _LOAD_COMPONENTS:
        if k in out and out[k] is not None:
            out[k] = float(out[k]) * gamma
    out['_gamma'] = gamma
    return out


def _row_gamma(row, state, use_min=False):
    """γ của một dòng tải ở trạng thái `state` theo loại tải (DEFAULT_LOAD_TYPE nếu trống)."""
    lt = str(row.get('load_type', DEFAULT_LOAD_TYPE) or DEFAULT_LOAD_TYPE).upper()
    table = LOAD_FACTORS.get(state, {})
    gmax, gmin = table.get(lt, (1.0, 1.0))
    return gmin if use_min else gmax


def lrfd_load_factoring_enabled(params):
    """Có áp hệ số tải LRFD không?

    Bật khi cơ sở là TCVN 11823 VÀ người dùng đã khai báo LRFD (gắn 'load_type'
    cho ≥1 dòng, HOẶC bật cờ params['LRFD_ENABLE']). Nếu CHƯA khai báo → KHÔNG nhân
    hệ số (γ=1,0) để giữ tương thích/không âm thầm đổi kết quả; báo cáo ghi rõ
    "CHƯA cấu hình tải LRFD".
    """
    if design_basis(params) != 'TCVN11823':
        return False
    if params.get('LRFD_ENABLE'):
        return True
    loads = params.get('_loads_for_lrfd_check')
    return False if loads is None else any('load_type' in (ld or {}) for ld in loads)


def factor_loads(loads, state=DEFAULT_STRENGTH_STATE, params=None, use_min=False):
    """Nhân hệ số γ của trạng thái `state` vào danh sách tải → danh sách tải CÓ HỆ SỐ.

    params=None hoặc factoring tắt → trả về tải nguyên (γ=1,0). Mỗi dòng dùng γ theo
    loại tải của nó (DEFAULT_LOAD_TYPE nếu không gắn). Bỏ qua dòng có γ=0 (vd hoạt
    tải ở Cường độ III/IV) để không pha loãng bao hình.
    """
    if not loads:
        return list(loads or [])
    if params is not None and not lrfd_load_factoring_enabled(params):
        return list(loads)
    out = []
    for ld in loads:
        g = _row_gamma(ld, state, use_min)
        if g == 0.0:
            continue
        out.append(_factor_row(ld, g))
    return out or list(loads)


def demand_loads(loads, params):
    """Bộ tải CÓ HỆ SỐ để kiểm cường độ (mặc định Cường độ I; cấu hình qua
    params['STRENGTH_STATE']). Dùng làm `loads` đưa vào đánh giá → pmax thành hiệu
    ứng tải có hệ số. Factoring tắt → trả tải nguyên."""
    state = (params or {}).get('STRENGTH_STATE', DEFAULT_STRENGTH_STATE)
    return factor_loads(loads, state, params)


def service_loads(loads, params):
    """Bộ tải trạng thái SỬ DỤNG I (γ≈1,0) — dùng cho kiểm lún/biến dạng."""
    return factor_loads(loads, 'SERVICE_I', params)


# ============================================================================
# 4. CỜ CƠ SỞ THIẾT KẾ + ÁP SỨC KHÁNG vào params
# ============================================================================
def design_basis(params=None):
    """Cơ sở thiết kế hiện hành: params['DESIGN_BASIS'] > hằng số constants.DESIGN_BASIS."""
    if params and params.get('DESIGN_BASIS'):
        return str(params['DESIGN_BASIS']).upper().replace(' ', '').replace(':', '')
    try:
        from core.constants import DESIGN_BASIS as DB
    except Exception:
        DB = 'TCVN10304'
    return str(DB).upper().replace(' ', '').replace(':', '')


def apply_lrfd_capacities(params):
    """Chuẩn hóa [Po]/[Ct] thành SỨC KHÁNG CÓ HỆ SỐ φ·R_n theo TCVN 11823-10.

    Idempotent (cờ ``_lrfd_applied``). Quy tắc:
      * Có ``R_N`` (sức kháng nén danh nghĩa) → ``P_LIMIT = φ·R_N``; ``R_N_T`` → kéo
        ``P_TENSION = φ_uplift·R_N_T``. φ theo (PILE_TYPE, RESISTANCE_METHOD); móng 1
        cọc (``SINGLE_PILE`` hoặc n_piles==1) → φ×0,8.
      * KHÔNG có R_N → giữ ``P_LIMIT``/``P_TENSION`` người dùng nhập, coi đã là φ·R_n
        (nguồn = 'input').
    Đính kèm metadata ``_capacity_source`` = 'tcvn_11823_10' | 'input', ``_lrfd_factors``.
    Trả về chính ``params`` (sửa tại chỗ).
    """
    if params.get('_lrfd_applied'):
        return params

    R_n = params.get('R_N') or params.get('RN') or 0.0
    R_nt = params.get('R_N_T') or params.get('RNT') or 0.0
    pile_type = str(params.get('PILE_TYPE', DEFAULT_PILE_TYPE) or DEFAULT_PILE_TYPE).lower()
    method = str(params.get('RESISTANCE_METHOD', DEFAULT_RESIST_METHOD) or DEFAULT_RESIST_METHOD).lower()
    single = bool(params.get('SINGLE_PILE')) or (params.get('n_piles') == 1)

    if R_n and R_n > 0:
        phi_c = resistance_factor(pile_type, 'compression', method, single)
        params['P_LIMIT'] = phi_c * float(R_n)
        phi_t = resistance_factor(pile_type, 'uplift', method, single)
        if R_nt and R_nt > 0:
            params['P_TENSION'] = phi_t * float(R_nt)
        params['_capacity_source'] = 'tcvn_11823_10'
        params['_lrfd_factors'] = {'phi_c': phi_c, 'phi_t': phi_t, 'R_n': float(R_n),
                                   'R_n_t': float(R_nt or 0.0), 'pile_type': pile_type,
                                   'method': method, 'single_pile': single}
    else:
        params['_capacity_source'] = 'input'
        params['_lrfd_factors'] = {'pile_type': pile_type, 'method': method,
                                   'single_pile': single, 'note': 'P_LIMIT nhap tay coi la phi*Rn'}

    params['_lrfd_applied'] = True
    return params


def apply_design_basis(params, loads=None):
    """Áp cơ sở thiết kế theo cờ DESIGN_BASIS (điểm vào DUY NHẤT cho tầng tối ưu/UI).

    * TCVN11823 → ``apply_lrfd_capacities`` (φ·R_n) + (nếu bật) trả bộ tải CÓ HỆ SỐ.
    * TCVN10304 (hoặc khác) → ``core.tcvn.apply_design_capacities`` (Rc,d) như cũ.

    Trả về (params, loads_demand): loads_demand là tải dùng để ĐÁNH GIÁ (đã nhân hệ
    số nếu LRFD bật; nguyên bản nếu không). Truyền `loads` để LRFD nhận diện cấu hình.
    """
    if loads is not None:
        params['_loads_for_lrfd_check'] = loads
    if design_basis(params) == 'TCVN11823':
        apply_lrfd_capacities(params)
        out_loads = demand_loads(loads, params) if loads is not None else loads
        return params, out_loads
    else:
        from core import tcvn
        tcvn.apply_design_capacities(params)
        return params, loads
