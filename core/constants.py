"""constants.py - Hằng số & giá trị mặc định dùng chung toàn dự án."""

# ============================================================================
# Hằng số hình học lưới cọc
# ============================================================================
SPACING_MIN_FACTOR = 3.0
SPACING_MAX_FACTOR = 6.0
BORED_CLEAR_MIN = 1.0

NX_MIN = 2
NX_MAX = 10
NMAX_AXIS = 14

EPS = 1e-9
GEOM_TOL = 1e-4

# ============================================================================
# Ràng buộc MỞ RỘNG ngoài đề bài (R1-R6). Tạm tắt theo yêu cầu.
# ============================================================================
ENABLE_LATERAL_CHECK = False    # R7: Hmax <= [H]
ENABLE_PM_INTERACTION = False   # R8: P/[Po] + M/[M] <= 1

DEFAULTS = {
    'L_X': 6.0, 'L_Y': 9.6, 'D_PILE': 1.2,
    'P_LIMIT': 500.0, 'P_TENSION': 0.0, 'M_LIMIT': 0.0,
    'H_LIMIT': 0.0, 'CLEAR_MIN': 0.0, 'mock_mode': True,
}


# ============================================================================
# Hàm đọc tham số an toàn (trả về mặc định khi thiếu/không hợp lệ)
# ============================================================================
def get_safe_d(params):
    """Khoảng cách an toàn tới mép bệ (SAFE_D); mặc định lấy đường kính cọc."""
    return params.get('SAFE_D', params.get('D_PILE', DEFAULTS['D_PILE']))


def get_m_limit(params):
    """Giới hạn mômen [M]; trả về vô cực nếu không khai báo (<= 0)."""
    raw = params.get('M_LIMIT', 0.0)
    return float('inf') if (raw is None or raw <= 0) else float(raw)


def get_h_limit(params):
    """Giới hạn lực ngang [H]; trả về vô cực nếu không khai báo (<= 0)."""
    raw = params.get('H_LIMIT', 0.0)
    return float('inf') if (raw is None or raw <= 0) else float(raw)


def effective_min_spacing(params):
    """Khoảng cách tim-tim nhỏ nhất hiệu dụng = max(hệ_số·d, d + thông thủy).

    Hệ số mặc định = SPACING_MIN_FACTOR (3d, theo tiêu chuẩn). Người dùng có thể
    GHI ĐÈ qua params['SPACING_MIN_FACTOR'] (vd cọc khoan nhồi 2.5d) — TÙY CHỌN,
    không đổi mặc định thuật toán: thiếu khóa này thì vẫn dùng 3d.
    """
    d = params.get('D_PILE', DEFAULTS['D_PILE'])
    factor = params.get('SPACING_MIN_FACTOR', None)
    factor = float(factor) if (factor and factor > 0) else SPACING_MIN_FACTOR
    base = factor * d
    clear = params.get('CLEAR_MIN', 0.0) or 0.0
    return max(base, d + clear) if clear > 0 else base
