"""
ssi_engine.py - Engine TƯƠNG TÁC ĐẤT–CỌC (Soil–Structure Interaction) thuần NumPy.

Bổ sung cho mô hình bệ cứng tuyến tính (core/rigid_cap.py) những thứ nó KHÔNG
tính được, phục vụ thiết kế sơ bộ:
  1) DỌC TRỤC: giải hệ bệ cứng 3 bậc tự do (lún w, xoay θx, θy) với lò xo dọc
     trục từng cọc → lực dọc + ĐỘ LÚN + xoay bệ; xử lý được cọc độ cứng khác nhau.
     Khi mọi cọc cùng độ cứng, kết quả TRÙNG KHỚP công thức rigid_cap.pile_forces
     (dùng làm mỏ neo kiểm chứng — xem tests).
  2) NGANG: mỗi cọc là DẦM TRÊN NỀN WINKLER (beam on elastic foundation), giải
     phần tử hữu hạn 1D (dầm Euler–Bernoulli + lò xo nền phân bố) → chuyển vị đầu
     cọc và biểu đồ MÔMEN dọc thân, M_max. Kiểm chứng bằng nghiệm Hetenyi.

KHÔNG phụ thuộc thư viện ngoài (chỉ NumPy) → chạy mọi phiên bản Python, đóng gói
PyInstaller không rủi ro, miễn phí hoàn toàn. Đây là phương án thay cho OpenSeesPy
(bản 3.8 chỉ build cho Python 3.12, không nạp được trên 3.13).

Đơn vị: dùng nhất quán một hệ. Khuyến nghị kN, m, kN/m² (E), kN/m³ (k_s nền).
Quy ước lực dọc: DƯƠNG = nén (giống rigid_cap).
"""

import numpy as np

# Mô đun đàn hồi bê tông mặc định ~ C30 trong hệ ĐƠN VỊ TẤN–MÉT (T/m² ≈ 30 GPa).
# Engine làm việc thuần Tấn–m (khớp rigid_cap, [Po], tọa độ): lực=Tấn, dài=m,
# E=T/m², m(hệ số nền)=T/m⁴ → chuyển vị ra m, mômen ra T·m. Không quy đổi kN.
E_CONCRETE_DEFAULT = 2.96e6


# ============================================================================
# Đặc trưng tiết diện cọc tròn
# ============================================================================
def pile_section(d, E=E_CONCRETE_DEFAULT):
    """Trả về (A, I, EA, EI) của cọc tròn đặc đường kính d (m).

    A = πd²/4 (m²); I = πd⁴/64 (m⁴); EA, EI theo E (kN/m²).
    """
    A = np.pi * d ** 2 / 4.0
    I = np.pi * d ** 4 / 64.0
    return A, I, E * A, E * I


# ============================================================================
# 1) BÀI TOÁN DỌC TRỤC: hệ bệ cứng (lún + xoay) với lò xo dọc trục
# ============================================================================
def axial_distribution(coords, load, ka=None):
    """Phân phối lực dọc trục + độ lún/xoay bệ bằng hệ bệ cứng 3 bậc tự do.

    Ẩn số u = (d0, a, b): d0 = lún tại TÂM nhóm cọc; a, b = độ dốc xoay theo x, y.
    Chuyển vị (lún) đầu cọc i: δ_i = d0 + a·dx_i + b·dy_i, với dx,dy lệch so tâm.
    Lực dọc cọc: P_i = k_i · δ_i (DƯƠNG = nén).

    Đầu vào:
        coords : (n,2) tọa độ tim cọc (m).
        load   : dict {'N','Mx','My'} quy về GỐC tọa độ (như rigid_cap).
        ka     : độ cứng dọc trục mỗi cọc — None (đều = 1, chỉ cần cho phân phối),
                 vô hướng (đều), hoặc mảng (n,) (cọc khác nhau). Đơn vị kN/m.

    Trả về dict:
        forces      : (n,) lực dọc trục mỗi cọc (cùng đơn vị N).
        settle_cap  : lún tại tâm nhóm cọc d0 (m) — chỉ có ý nghĩa khi ka đúng đơn vị.
        rot_x, rot_y: độ dốc xoay bệ quanh trục x (b) và y (a) (rad/m ~ rad).
        delta       : (n,) lún đầu từng cọc (m).

    Khi ka đồng nhất, forces TRÙNG công thức rigid_cap.pile_forces (độc lập trị số ka).
    """
    coords = np.asarray(coords, dtype=float)
    n = len(coords)
    if n == 0:
        return {'forces': np.zeros(0), 'settle_cap': 0.0,
                'rot_x': 0.0, 'rot_y': 0.0, 'delta': np.zeros(0)}

    cx = coords[:, 0].mean()
    cy = coords[:, 1].mean()
    dx = coords[:, 0] - cx
    dy = coords[:, 1] - cy

    if ka is None:
        k = np.ones(n)
    else:
        k = np.asarray(ka, dtype=float)
        if k.ndim == 0:
            k = np.full(n, float(k))

    N = float(load.get('N', 0.0))
    Mx = float(load.get('Mx', 0.0))
    My = float(load.get('My', 0.0))
    # Quy mômen tải về TÂM nhóm cọc (khử lệch tâm) — giống rigid_cap
    Mx_t = Mx - N * cy
    My_t = My - N * cx

    # Hệ 3x3: K·[d0,a,b]ᵀ = [N, My_t, Mx_t]ᵀ
    #   Eq lực dọc:  Σk·d0 + Σk·dx·a + Σk·dy·b = N
    #   Eq mômen y:  Σk·dx·d0 + Σk·dx²·a + Σk·dx·dy·b = My_t
    #   Eq mômen x:  Σk·dy·d0 + Σk·dx·dy·a + Σk·dy²·b = Mx_t
    Sk = k.sum()
    Skx = (k * dx).sum(); Sky = (k * dy).sum()
    Skxx = (k * dx * dx).sum(); Skyy = (k * dy * dy).sum(); Skxy = (k * dx * dy).sum()
    K = np.array([[Sk,  Skx,  Sky],
                  [Skx, Skxx, Skxy],
                  [Sky, Skxy, Skyy]], dtype=float)
    rhs = np.array([N, My_t, Mx_t], dtype=float)
    # Chống suy biến (cọc thẳng hàng) — thêm nhiễu rất nhỏ trên đường chéo
    K[np.diag_indices(3)] += 1e-12 * (abs(np.diag(K)).max() + 1.0)
    d0, a, b = np.linalg.solve(K, rhs)

    delta = d0 + a * dx + b * dy
    forces = k * delta
    return {'forces': forces, 'settle_cap': float(d0),
            'rot_x': float(b), 'rot_y': float(a), 'delta': delta}


# ============================================================================
# 2) BÀI TOÁN NGANG: dầm Euler–Bernoulli trên nền Winkler (FE 1D)
# ============================================================================
def _beam_element_K(le, EI):
    """Ma trận độ cứng dầm Euler–Bernoulli 2 nút (DOF [w1,θ1,w2,θ2])."""
    return EI / le ** 3 * np.array([
        [12,    6 * le,   -12,    6 * le],
        [6 * le, 4 * le ** 2, -6 * le, 2 * le ** 2],
        [-12,   -6 * le,    12,   -6 * le],
        [6 * le, 2 * le ** 2, -6 * le, 4 * le ** 2]], dtype=float)


def _winkler_element_K(le, k_line):
    """Ma trận độ cứng lò xo nền phân bố (Winkler) — dạng nhất quán (consistent).

    k_line = mô đun nền theo CHIỀU DÀI (kN/m mỗi đơn vị dài × chuyển vị) = k_s·d.
    """
    return k_line * le / 420.0 * np.array([
        [156,    22 * le,    54,   -13 * le],
        [22 * le, 4 * le ** 2, 13 * le, -3 * le ** 2],
        [54,    13 * le,   156,   -22 * le],
        [-13 * le, -3 * le ** 2, -22 * le, 4 * le ** 2]], dtype=float)


def beam_on_winkler(EI, k_line, length, n_elem=40,
                    head_shear=0.0, head_moment=0.0,
                    head_fixed=False, supports=None, point_loads=None):
    """Giải dầm Euler–Bernoulli trên nền Winkler (FE 1D, lò xo nhất quán).

    Trục s chạy dọc dầm 0..length. DOF mỗi nút: (w chuyển vị ngang, θ góc xoay).

    Đầu vào:
        EI       : độ cứng uốn (kN·m²).
        k_line   : mô đun nền theo chiều dài (kN/m/m = k_s·d). Vô hướng hoặc mảng
                   (n_node,) để mô tả nền phân lớp dọc thân.
        length   : chiều dài dầm (m).
        n_elem   : số phần tử.
        head_shear, head_moment : lực cắt & mômen đặt tại nút ĐẦU (s=0).
        head_fixed : True → ngàm xoay đầu (θ=0) mô phỏng đầu cọc liên kết bệ cứng.
        supports : list (node_index, 'w'|'th') các bậc bị khóa (ngoài head_fixed).
        point_loads : list (s_pos, P) tải ngang tập trung (để kiểm chứng dầm vô hạn).

    Trả về dict: s (n_node,), w, theta, M (mômen tại nút), y_head, M_max.
    """
    n_node = n_elem + 1
    le = length / n_elem
    s = np.linspace(0.0, length, n_node)
    ndof = 2 * n_node

    if np.isscalar(k_line):
        k_nodes = np.full(n_node, float(k_line))
    else:
        k_nodes = np.asarray(k_line, dtype=float)

    K = np.zeros((ndof, ndof))
    for e in range(n_elem):
        kl = 0.5 * (k_nodes[e] + k_nodes[e + 1])  # trung bình trên phần tử
        Ke = _beam_element_K(le, EI) + _winkler_element_K(le, kl)
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        K[np.ix_(idx, idx)] += Ke

    F = np.zeros(ndof)
    F[0] += head_shear          # lực cắt tại đầu (DOF w nút 0)
    F[1] += head_moment         # mômen tại đầu (DOF θ nút 0)
    if point_loads:
        for s_pos, P in point_loads:
            j = int(round(s_pos / le))
            F[2 * j] += P

    fixed = set()
    if head_fixed:
        fixed.add(1)            # khóa θ tại nút 0
    if supports:
        for node, dof in supports:
            fixed.add(2 * node + (0 if dof == 'w' else 1))

    free = [i for i in range(ndof) if i not in fixed]
    u = np.zeros(ndof)
    Kff = K[np.ix_(free, free)]
    u[free] = np.linalg.solve(Kff, F[free])

    w = u[0::2]
    theta = u[1::2]

    # Mômen tại từng nút từ lực phần tử (lấy trung bình các phần tử kề nút)
    M_nodes = np.zeros(n_node)
    count = np.zeros(n_node)
    for e in range(n_elem):
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        fe = _beam_element_K(le, EI) @ u[idx]   # [V1,M1,V2,M2]
        # Quy ước mômen uốn: tại nút trái = -M1, nút phải = +M2 (lực nút → nội lực)
        M_nodes[e] += -fe[1]; count[e] += 1
        M_nodes[e + 1] += fe[3]; count[e + 1] += 1
    M_nodes /= np.maximum(count, 1)

    return {'s': s, 'w': w, 'theta': theta, 'M': M_nodes,
            'y_head': float(w[0]), 'M_max': float(np.max(np.abs(M_nodes)))}


def characteristic_beta(EI, k_line):
    """Tham số đặc trưng β = (k_line/(4·EI))^(1/4) của dầm trên nền Winkler (1/m)."""
    return (k_line / (4.0 * EI)) ** 0.25


# ============================================================================
# HIỆU ỨNG NHÓM CỌC: p-multiplier (AASHTO LRFD) + tỷ số lún nhóm
# ============================================================================
# AASHTO LRFD Bảng 10.7.2.4-1: hệ số nhân p-y theo hàng & khoảng cách tâm-tâm.
_PM_3D = {1: 0.70, 2: 0.50, 3: 0.35}   # tại k/c 3D (hàng dẫn đầu / 2 / 3+)
_PM_5D = {1: 1.00, 2: 0.85, 3: 0.70}   # tại k/c 5D


def p_multiplier(row, s_over_D):
    """Hệ số nhân p-y (P_m) của một hàng cọc theo AASHTO LRFD 10.7.2.4-1.

    row       : số thứ tự hàng tính từ hàng DẪN ĐẦU (1 = trước theo chiều tải).
    s_over_D  : khoảng cách tâm-tâm hàng / đường kính cọc, đo theo PHƯƠNG TẢI.
                None hoặc ≥5 → 1.0 (hết hiệu ứng nhóm). 3D↔5D nội suy tuyến tính;
                <3D giữ giá trị 3D (AASHTO không khuyến nghị <3D).
    """
    r = min(int(row), 3)
    if s_over_D is None:
        return 1.0                  # không xác định k/c (1 hàng / không tải) → đơn lẻ
    s = float(s_over_D)
    if s >= 5.0:
        return _PM_5D[r]            # ≥5D: dùng giá trị bảng 5D (hàng dẫn đầu = 1.0)
    if s <= 3.0:
        return _PM_3D[r]
    t = (s - 3.0) / 2.0            # 3D↔5D nội suy tuyến tính
    return _PM_3D[r] + t * (_PM_5D[r] - _PM_3D[r])


def lateral_group_pmult(coords, d, load):
    """Gán hàng & hệ số p-multiplier cho từng cọc theo PHƯƠNG TẢI NGANG.

    Hàng được định nghĩa vuông góc phương tải; hàng dẫn đầu (P_m lớn nhất) ở
    phía trước theo chiều đẩy của hợp lực (Hx,Hy). Các hàng sau bị "che" → P_m
    giảm. Trả về (pmult (n,), info).
    """
    coords = np.asarray(coords, dtype=float)
    n = len(coords)
    Hx = float(load.get('Hx', 0.0)); Hy = float(load.get('Hy', 0.0))
    Hmag = (Hx ** 2 + Hy ** 2) ** 0.5
    if n == 0 or Hmag < 1e-9 or d <= 0:
        return np.ones(n), {'rows': 1, 's_over_D': None}

    u = np.array([Hx, Hy]) / Hmag          # hướng tải đơn vị
    proj = coords @ u                       # chiếu tâm cọc lên hướng tải
    order = np.argsort(-proj)               # giảm dần: hàng dẫn đầu trước
    tol = 0.5 * d
    rows_proj = []                          # proj đại diện mỗi hàng (giảm dần)
    row_of = np.zeros(n, dtype=int)
    for i in order:
        placed = False
        for r, pv in enumerate(rows_proj):
            if abs(proj[i] - pv) <= tol:
                row_of[i] = r; placed = True; break
        if not placed:
            rows_proj.append(proj[i]); row_of[i] = len(rows_proj) - 1
    n_rows = len(rows_proj)
    if n_rows >= 2:
        gaps = np.abs(np.diff(np.sort(rows_proj)[::-1]))
        s_over_D = float(np.mean(gaps)) / d
    else:
        s_over_D = None
    pmult = np.array([p_multiplier(row_of[i] + 1, s_over_D) for i in range(n)])
    return pmult, {'rows': n_rows, 's_over_D': s_over_D, 'row_of': row_of.tolist()}


def group_settlement_ratio(n, omega=0.5):
    """Tỷ số lún nhóm R_s ≈ n^ω (Poulos; ω≈0.4–0.6, mặc định 0.5).

    Dùng khuếch đại lún cọc đơn lên lún nhóm để kể tương tác đất–cọc–đất mà mô
    hình lò xo độc lập (axial_distribution) chưa xét.
    """
    return float(max(1, int(n))) ** float(omega)


# ============================================================================
# 3) TỔNG HỢP: phân tích SSI cho một tổ hợp tải
# ============================================================================
def analyze(coords, params, load):
    """Phân tích SSI sơ bộ cho 1 tổ hợp tải, trả kết quả gọn cho UI/báo cáo.

    params cần (có default an toàn):
        D_PILE      : đường kính cọc d (m).
        pile_length : chiều dài cọc Lc (m) — thiếu thì lấy minh hoạ.
        E_concrete  : mô đun bê tông (kN/m²) — mặc định C30.
        ks_soil     : mô đun nền k_s (kN/m³) cho lò xo ngang — mặc định 10000.
        head_fixed  : True nếu đầu cọc ngàm vào bệ cứng (mặc định True).

    Trả về dict:
        axial   : kết quả axial_distribution (forces, settle_cap, rot...).
        lateral : {y_head, M_max, beta, H_pile} của cọc CHỊU NGANG LỚN NHẤT.
        meta    : thông số đã dùng (kèm cờ minh hoạ nếu thiếu chiều dài cọc).
    """
    from core.rigid_cap import horizontal_forces

    coords = np.asarray(coords, dtype=float)
    n = len(coords)
    d = float(params.get('D_PILE', 1.0))
    E = float(params.get('E_concrete', E_CONCRETE_DEFAULT))
    ks = float(params.get('ks_soil', 1.0e4))
    head_fixed = bool(params.get('head_fixed', True))
    Lc = float(params.get('pile_length') or params.get('PILE_LENGTH') or 0.0)
    illustrative = Lc <= 0
    if illustrative:
        Lc = max(8.0, 12.0 * d)

    A, I, EA, EI = pile_section(d, E)
    # ƯU TIÊN dùng EI, EA THẬT từ file MCOC (E_b·J_o, E_b·F_o) nếu có — chính xác hơn.
    E_b = params.get('E_b'); J_o = params.get('J_o'); F_o = params.get('F_o')
    if E_b and J_o and float(E_b) > 0 and float(J_o) > 0:
        EI = float(E_b) * float(J_o)
        EA = float(E_b) * (float(F_o) if F_o else A)

    # Độ cứng dọc trục mỗi cọc (cọc đàn hồi ngàm mũi): k_a = EA/Lc (đều nhau ⇒ khớp rigid_cap)
    ka = EA / Lc
    axial = axial_distribution(coords, load, ka=ka)
    # Lún nhóm: khuếch đại lún bệ theo tỷ số R_s = n^0.5 (Poulos) khi bật hiệu ứng nhóm.
    group = bool(params.get('group_effect', False))
    Rs = group_settlement_ratio(n) if group else 1.0
    axial['settle_group'] = axial['settle_cap'] * Rs
    axial['Rs'] = Rs

    # Mô hình nền ngang: ưu tiên PHƯƠNG PHÁP "m" (TCVN 10304 Phụ lục A) khi file có
    # hệ số nền m — Cz=m·z (tăng tuyến tính theo độ sâu), k theo chiều dài = m·z·d.
    # Không có m → lò xo hằng k = ks·d (ks T/m³).
    m_soil = params.get('m_soil')
    use_m = bool(m_soil and float(m_soil) > 0)

    # Ngang: chọn cọc bất lợi nhất rồi giải dầm Winkler. Có hiệu ứng nhóm thì giảm
    # mô đun nền theo p-multiplier (cọc bị "che" → nền mềm hơn → chuyển vị/mômen lớn hơn).
    lateral = None
    if n > 0:
        Hxi, Hyi = horizontal_forces(coords, load)
        Hmag = np.sqrt(Hxi ** 2 + Hyi ** 2)
        if group:
            pmult, pinfo = lateral_group_pmult(coords, d, load)
            score = Hmag / np.maximum(pmult, 1e-6)   # bất lợi ~ chuyển vị: H/(độ cứng)
            i_worst = int(np.argmax(score))
            pm = float(pmult[i_worst])
        else:
            pinfo = {'rows': None, 's_over_D': None}
            i_worst = int(np.argmax(Hmag))
            pm = 1.0
        H_pile = float(Hmag[i_worst])
        n_elem = 60
        s_nodes = np.linspace(0.0, Lc, n_elem + 1)
        if use_m:
            k_line = float(m_soil) * s_nodes * d * pm     # k(z)=m·z·d (TCVN 10304 PL A)
            k_ref = float(m_soil) * Lc * d * pm           # k đại diện ở mũi (cho β)
        else:
            k_line = np.full(n_elem + 1, ks * d * pm)
            k_ref = ks * d * pm
        beam = beam_on_winkler(EI, k_line, Lc, n_elem=n_elem,
                               head_shear=H_pile, head_fixed=head_fixed)
        lateral = {'y_head': beam['y_head'], 'M_max': beam['M_max'],
                   'beta': characteristic_beta(EI, max(k_ref, 1e-9)), 'H_pile': H_pile,
                   'pile_index': i_worst, 'profile': beam,
                   'pmult': pm, 'rows': pinfo.get('rows'),
                   's_over_D': pinfo.get('s_over_D'), 'model': ('m' if use_m else 'ks')}

    return {'axial': axial, 'lateral': lateral,
            'meta': {'d': d, 'E': E, 'ks': ks, 'Lc': Lc, 'EI': EI, 'EA': EA,
                     'head_fixed': head_fixed, 'Lc_illustrative': illustrative,
                     'group_effect': group, 'Rs': Rs,
                     'lateral_model': ('m' if use_m else 'ks'),
                     'm_soil': (float(m_soil) if use_m else None)}}
