"""
refine_optimizer.py - Tối ưu hóa kiểu HỘP ĐEN + TINH CHỈNH TỪNG BƯỚC TRÊN LƯỚI.

NGUYÊN TẮC BỐ TRÍ (kiến thức móng cọc cầu):
    - Cọc LUÔN nằm trên lưới điểm đều, đối xứng qua tâm bệ, theo 2 dạng:
        Kiểu A (lưới trực giao)  :  o o o     Kiểu B (hoa mai / so le):  o o o
                                    o o o                                  o o
                                    o o o                                 o o o
    - KHÔNG bao giờ bỏ cọc đơn lẻ (mất đối xứng, mất gối đỡ góc).
    - Kích thước lưới (sx, sy) co dãn từng bước nhỏ trong miền giới hạn
      khoảng cách tim-đến-tim (3d..6d) và khoảng cách mép bệ.

CÁC BƯỚC TINH CHỈNH (mỗi vòng chọn 1 bước tốt nhất):
    (a) co sx một nấc nhỏ          (b) co sy một nấc nhỏ
    (c) bỏ nguyên 1 CỘT (nx-1)     (d) bỏ nguyên 1 HÀNG (ny-1)
    (e) chuyển lưới A -> hoa mai B (tiết kiệm floor(ny/2) cọc)

Mỗi bước được DỰ BÁO trước bằng công thức bệ cứng (hệ số hiệu chỉnh
K = Pmax_MCOC / Pmax_be_cung, cập nhật lại sau mỗi lần gọi MCOC), sau đó
phương án dự báo khả thi sẽ được gọi MCOC kiểm chứng thật. Vòng lặp dừng
khi không còn bước nào cho kết quả ĐẠT tốt hơn.

Tiêu chí "tốt hơn": (1) ít cọc hơn; (2) cùng số cọc thì bệ gọn hơn.
"""

import numpy as np

from core import rigid_cap


# ============================================================================
# Công thức bệ cứng (chỉ để DỰ BÁO, kết quả thật luôn do MCOC quyết định).
# Ủy quyền (delegate) sang core.rigid_cap để tránh viết lặp công thức.
# ============================================================================
def rigid_forces(coords, loads):
    """Ma trận lực (len(loads), n) theo bệ cứng — xem rigid_cap.forces_all_loads."""
    return rigid_cap.forces_all_loads(coords, loads)


def rigid_pmax_pmin(coords, loads):
    """(Pmax, Pmin) bệ cứng — xem rigid_cap.pmax_pmin."""
    return rigid_cap.pmax_pmin(coords, loads)


# Alias tương thích ngược (mechanics, nsga2, tests đang import từ đây)
min_spacing = rigid_cap.min_spacing


def footprint(coords):
    """Tổng kích thước bao (rộng + cao) của cụm cọc — đo độ gọn của bệ."""
    coords = np.asarray(coords, dtype=float)
    w = coords[:, 0].max() - coords[:, 0].min()
    h = coords[:, 1].max() - coords[:, 1].min()
    return w + h


# ============================================================================
# Lưới điểm: nhận diện và sinh tọa độ
# ============================================================================
def grid_coords(spec):
    """Sinh tọa độ từ spec lưới {type,nx,ny,sx,sy,cx,cy} - luôn đối xứng."""
    t, nx, ny = spec['type'], spec['nx'], spec['ny']
    sx, sy = spec['sx'], spec['sy']
    cx, cy = spec.get('cx', 0.0), spec.get('cy', 0.0)
    pts = []
    for j in range(ny):
        y = cy + (j - (ny - 1) / 2.0) * sy
        if t == 'A' or j % 2 == 0:
            cols = nx
        else:
            cols = nx - 1
        if cols <= 0:
            continue
        for i in range(cols):
            x = cx + (i - (cols - 1) / 2.0) * sx
            pts.append([x, y])
    return np.round(np.array(pts), 3)


def _coords_match(a, b, tol=5e-3):
    """So sánh 2 tập điểm (không phụ thuộc thứ tự)."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if a.shape != b.shape:
        return False
    ka = a[np.lexsort((a[:, 1], a[:, 0]))]
    kb = b[np.lexsort((b[:, 1], b[:, 0]))]
    return np.allclose(ka, kb, atol=tol)


def detect_grid(coords, tol=1e-2):
    """
    Nhận diện lưới từ tọa độ gốc. Trả về spec {'type','nx','ny','sx','sy',
    'cx','cy'} hoặc None nếu không phải lưới đều / hoa mai.
    """
    coords = np.asarray(coords, dtype=float)
    n = len(coords)
    if n < 2:
        return None

    cx = float(coords[:, 0].mean())
    cy = float(coords[:, 1].mean())

    ys = sorted(set(np.round(coords[:, 1], 2)))
    rows = [coords[np.abs(coords[:, 1] - y) < tol] for y in ys]
    ny = len(rows)
    row_counts = [len(r) for r in rows]
    nx = max(row_counts)

    # sy: khoảng cách hàng đều
    if ny > 1:
        dys = np.diff(ys)
        if np.max(dys) - np.min(dys) > tol:
            return None
        sy = float(np.mean(dys))
    else:
        sy = 0.0

    # sx: từ hàng dài nhất
    row_long = sorted(rows[int(np.argmax(row_counts))][:, 0])
    if nx > 1:
        dxs = np.diff(row_long)
        if np.max(dxs) - np.min(dxs) > tol:
            return None
        sx = float(np.mean(dxs))
    else:
        sx = 0.0

    for t in ('A', 'B'):
        spec = {'type': t, 'nx': nx, 'ny': ny, 'sx': sx, 'sy': sy,
                'cx': cx, 'cy': cy}
        try:
            if _coords_match(grid_coords(spec), coords):
                return spec
        except Exception:
            pass
    return None


def grid_label(spec):
    """Tạo nhãn mô tả ngắn gọn cho một spec lưới (kiểu, kích thước, bước)."""
    name = "luoi" if spec['type'] == 'A' else "hoa mai"
    return "%s %dx%d, sx=%.2f sy=%.2f" % (name, spec['nx'], spec['ny'],
                                          spec['sx'], spec['sy'])


# ============================================================================
# Ràng buộc
# ============================================================================
def check_constraints(coords, res, params):
    """Kiểm tra R1/R2/R3/R4 cho 1 kết quả MCOC. Trả về (ok, [lỗi])."""
    d = params['D_PILE']
    SAFE_D = params.get('SAFE_D', d)
    P_LIMIT = params.get('P_LIMIT', 500.0)
    P_TENSION = params.get('P_TENSION', 0.0)
    M_LIMIT = params.get('M_LIMIT', 0.0) or 0.0

    errs = []
    if res['pmax'] > P_LIMIT + 1e-6:
        errs.append("Pmax=%.1f > Po=%.1f" % (res['pmax'], P_LIMIT))
    if P_TENSION > 0 and res['pmin'] < -P_TENSION - 1e-6:
        errs.append("Pmin=%.1f < -Ct=%.1f" % (res['pmin'], P_TENSION))
    if M_LIMIT > 0:
        if res.get('mxmax', 0) > M_LIMIT:
            errs.append("Mx=%.1f > M=%.1f" % (res['mxmax'], M_LIMIT))
        if res.get('mymax', 0) > M_LIMIT:
            errs.append("My=%.1f > M=%.1f" % (res['mymax'], M_LIMIT))

    # Sàn khoảng cách tim-tim: 3d nhưng không khắt hơn hiện trạng gốc
    floor = params.get('_spacing_floor', 3.0 * d)
    s_min = min_spacing(coords)
    if s_min < floor - 1e-4:
        errs.append("khoang cach %.2f < gioi han %.2f" % (s_min, floor))

    arr = np.asarray(coords, dtype=float)
    max_x_allow = params.get('_max_x_allow',
                             params['L_X'] / 2 - SAFE_D if 'L_X' in params else float('inf'))
    max_y_allow = params.get('_max_y_allow',
                             params['L_Y'] / 2 - SAFE_D if 'L_Y' in params else float('inf'))
    if np.max(np.abs(arr[:, 0])) > max_x_allow + 1e-4:
        errs.append("vi pham mep be X")
    if np.max(np.abs(arr[:, 1])) > max_y_allow + 1e-4:
        errs.append("vi pham mep be Y")

    return (len(errs) == 0), errs


def _spacing_ok(spec, floor):
    """Khoảng cách tim-tim nhỏ nhất của lưới >= sàn cho phép."""
    sx, sy, t = spec['sx'], spec['sy'], spec['type']
    if spec['nx'] > 1 and sx < floor - 1e-6:
        return False
    if spec['ny'] > 1:
        if t == 'A':
            if sy < floor - 1e-6:
                return False
        else:  # hoa mai: hàng kề nhau lệch sx/2
            diag = np.hypot(sx / 2.0, sy)
            if diag < floor - 1e-6:
                return False
    return True


def _edge_ok(spec, params):
    """Kiểm tra lưới có nằm trong giới hạn mép bệ X/Y cho phép hay không."""
    coords = grid_coords(spec)
    mx = float(np.max(np.abs(coords[:, 0])))
    my = float(np.max(np.abs(coords[:, 1])))
    return mx <= params.get('_max_x_allow', float('inf')) + 1e-4 and \
        my <= params.get('_max_y_allow', float('inf')) + 1e-4


# ============================================================================
# Sinh các BƯỚC TINH CHỈNH ứng viên từ lưới hiện tại
# ============================================================================
def candidate_moves(spec, params, allow_removal):
    """Trả về list (spec_mới, mô_tả). Luôn giữ lưới đều/hoa mai đối xứng."""
    d = params['D_PILE']
    floor = params.get('_spacing_floor', 3.0 * d)
    step = params.get('refine_step', 0.0) or max(0.25 * d, 0.10)  # nấc co (m)
    s_max = 6.0 * d

    out = []
    nx, ny, sx, sy = spec['nx'], spec['ny'], spec['sx'], spec['sy']

    def add(sp, label):
        """Thêm phương án ứng viên nếu thỏa sàn khoảng cách và mép bệ."""
        if not _spacing_ok(sp, floor):
            return
        if not _edge_ok(sp, params):
            return
        out.append((sp, label))

    # (a) co sx một nấc
    if nx > 1:
        lo = floor if spec['type'] == 'A' else max(
            floor, 2.0 * np.sqrt(max(floor ** 2 - sy ** 2, 0.0)))
        new_sx = max(sx - step, lo)
        if new_sx < sx - 1e-6:
            sp = dict(spec, sx=round(new_sx, 3))
            add(sp, "co sx %.2f->%.2f" % (sx, new_sx))

    # (b) co sy một nấc
    if ny > 1:
        if spec['type'] == 'A':
            lo = floor
        else:
            lo = np.sqrt(max(floor ** 2 - (sx / 2.0) ** 2, 0.0))
        new_sy = max(sy - step, lo)
        if new_sy < sy - 1e-6:
            sp = dict(spec, sy=round(new_sy, 3))
            add(sp, "co sy %.2f->%.2f" % (sy, new_sy))

    if allow_removal:
        # (c) bỏ nguyên 1 CỘT: giãn sx tối đa để bù lại (ưu tiên khả thi)
        if nx > 2:
            for sx2 in ((min(s_max, 2 * params.get('_max_x_allow', 1e9) / (nx - 2)),
                         sx)):
                sx2 = round(min(max(sx2, floor), s_max), 3)
                sp = dict(spec, nx=nx - 1, sx=sx2)
                add(sp, "bo 1 cot -> %dx%d (sx=%.2f)" % (nx - 1, ny, sx2))

        # (d) bỏ nguyên 1 HÀNG
        if ny > 2:
            for sy2 in ((min(s_max, 2 * params.get('_max_y_allow', 1e9) / (ny - 2)),
                         sy)):
                sy2 = round(min(max(sy2, floor), s_max), 3)
                sp = dict(spec, ny=ny - 1, sy=sy2)
                add(sp, "bo 1 hang -> %dx%d (sy=%.2f)" % (nx, ny - 1, sy2))

        # (e) chuyển lưới A -> hoa mai B (tiết kiệm floor(ny/2) cọc)
        if spec['type'] == 'A' and nx >= 2 and ny >= 2:
            sy_b = max(sy, np.sqrt(max(floor ** 2 - (sx / 2.0) ** 2, 0.0)))
            sp = dict(spec, type='B', sy=round(sy_b, 3))
            add(sp, "chuyen sang hoa mai %dx%d" % (nx, ny))

    # Loại trùng lặp
    uniq, seen = [], set()
    for sp, lb in out:
        key = (sp['type'], sp['nx'], sp['ny'], round(sp['sx'], 3), round(sp['sy'], 3))
        if key not in seen:
            seen.add(key)
            uniq.append((sp, lb))
    return uniq


# ============================================================================
# TỐI ƯU PARETO TOÀN CỤC (predict - verify - recalibrate)
# ============================================================================
def _n_piles(t, nx, ny):
    """Số cọc của một lưới theo kiểu A (trực giao) hoặc B (hoa mai/so le)."""
    if t == 'A':
        return nx * ny
    return nx * ((ny + 1) // 2) + (nx - 1) * (ny // 2)


def enumerate_configs(params, n_max, mode, grid0, nmax_axis=14):
    """
    Liệt kê TOÀN BỘ họ lưới chuẩn khả thi về hình học:
    (kiểu A/B) x nx x ny, với sx_max/sy_max theo mép bệ và 6d.
    """
    d = params['D_PILE']
    floor = params.get('_spacing_floor', 3.0 * d)
    s_max = 6.0 * d
    maxx = params.get('_max_x_allow', 1e9)
    maxy = params.get('_max_y_allow', 1e9)

    types = ('A', 'B')
    if mode == 'spacing' and grid0 is not None:
        types = (grid0['type'],)

    out = []
    for t in types:
        for nx in range(1, nmax_axis + 1):
            for ny in range(1, nmax_axis + 1):
                if t == 'B' and (nx < 2 or ny < 2):
                    continue
                if mode == 'spacing' and grid0 is not None and \
                        (t, nx, ny) != (grid0['type'], grid0['nx'], grid0['ny']):
                    continue
                n = _n_piles(t, nx, ny)
                if n < 2 or n > n_max:
                    continue
                sx = s_max if nx == 1 else min(s_max, 2 * maxx / (nx - 1))
                sy = s_max if ny == 1 else min(s_max, 2 * maxy / (ny - 1))
                ctr = params.get('_grid_center', (0.0, 0.0))
                cx = grid0.get('cx', ctr[0]) if grid0 else ctr[0]
                cy = grid0.get('cy', ctr[1]) if grid0 else ctr[1]
                spec = {'type': t, 'nx': nx, 'ny': ny,
                        'sx': round(sx, 3), 'sy': round(sy, 3),
                        'cx': cx, 'cy': cy}
                if not _spacing_ok(spec, floor):
                    continue
                out.append(spec)
    return out


def _scaled(spec_or_coords, k):
    """Co đều một cấu hình (spec lưới hoặc tọa độ tùy biến) với hệ số k."""
    if isinstance(spec_or_coords, dict):
        sp = dict(spec_or_coords)
        sp['sx'] = round(sp['sx'] * k, 3)
        sp['sy'] = round(sp['sy'] * k, 3)
        return sp, grid_coords(sp)
    coords = np.asarray(spec_or_coords, float)
    ctr = coords.mean(axis=0)
    return None, np.round(ctr + (coords - ctr) * k, 3)


def solve_min_scale(base, loads, Kc, params, target):
    """
    Tìm hệ số co k NHỎ NHẤT sao cho dự báo Kc*Pmax_be_cung(k) <= target
    và khoảng cách >= sàn. base: spec lưới hoặc tọa độ tùy biến.
    Trả về (k, coords) hoặc (None, None) nếu ngay k=1 đã vượt target.
    """
    d = params['D_PILE']
    floor = params.get('_spacing_floor', 3.0 * d)

    _, c1 = _scaled(base, 1.0)
    if len(c1) < 2:
        return None, None
    ms1 = min_spacing(c1)
    if ms1 < floor - 1e-6:
        return None, None
    pm1, _ = rigid_pmax_pmin(c1, loads)
    if pm1 * Kc > target + 1e-9:
        return None, None                     # không khả thi ngay ở k=1

    k_lo = min(1.0, floor / ms1)              # giới hạn sàn khoảng cách
    lo, hi = k_lo, 1.0
    for _ in range(24):                        # tìm kiếm nhị phân (binary search)
        mid = 0.5 * (lo + hi)
        _, c = _scaled(base, mid)
        pm, _ = rigid_pmax_pmin(c, loads)
        if pm * Kc <= target:
            hi = mid
        else:
            lo = mid
    k = round(hi, 4)
    _, c = _scaled(base, k)
    return k, c


def run_pareto_refinement(params, loads, evaluator, log=None, budget=25):
    """
    TỐI ƯU PARETO + HỘP ĐEN MCOC:
      1. Gọi MCOC tính phương án gốc -> hệ số hiệu chỉnh K.
      2. Liệt kê toàn bộ họ lưới chuẩn; với mỗi cấu hình giải hệ số co nhỏ
         nhất theo DỰ BÁO (bệ cứng x K) -> tập ứng viên trên mặt Pareto
         (số cọc, độ gọn bệ).
      3. Kiểm chứng ứng viên tốt nhất bằng MCOC thật:
           - ĐẠT  -> thành phương án đương nhiệm, tiếp tục tìm tốt hơn;
           - KHÔNG ĐẠT -> lưu hệ số hiệu chỉnh RIÊNG của cấu hình đó,
             tính lại dự báo (ứng viên tự động bị đẩy lùi trên mặt Pareto).
      4. Lặp đến khi không còn ứng viên nào TRỘI HƠN phương án đương nhiệm
         hoặc hết ngân sách gọi MCOC.
    """
    log = log or (lambda m: print(m))
    from core import tcvn
    tcvn.apply_design_capacities(params)   # [Po]/[Ct] -> Rc,d/Rt,d (Điều 7.1.11) nếu có Rc,k
    coords0 = np.asarray(params['original_coords'], dtype=float)
    history = []
    n_calls = [0]
    mode = params.get('refine_mode', 'full')
    P_LIMIT = params.get('P_LIMIT', 500.0)
    P_TENSION = params.get('P_TENSION', 0.0)
    target = params.get('target_ratio', 0.99) * P_LIMIT

    # --- Nới lỏng ràng buộc theo hiện trạng gốc -----------------------------
    d = params['D_PILE']
    SAFE_D = params.get('SAFE_D', d)
    s0 = min_spacing(coords0)
    floor = 3.0 * d
    if s0 < floor - 1e-4:
        log("CHU Y: khoang cach coc goc %.2f m < 3d=%.2f m -> dung san %.2f m."
            % (s0, floor, s0))
        floor = s0
    params['_spacing_floor'] = floor
    mx0 = float(np.max(np.abs(coords0[:, 0])))
    my0 = float(np.max(np.abs(coords0[:, 1])))
    if 'L_X' in params:
        params['_max_x_allow'] = max(params['L_X'] / 2 - SAFE_D, mx0)
    if 'L_Y' in params:
        params['_max_y_allow'] = max(params['L_Y'] / 2 - SAFE_D, my0)

    grid0 = detect_grid(coords0)
    params['_grid_center'] = (float(coords0[:, 0].mean()), float(coords0[:, 1].mean()))
    log("Che do: %s | muc tieu: giam so coc + co khoang cach (Pareto)"
        % ("toan cuc" if mode != 'spacing' else "chi co khoang cach"))
    log("Luoi goc: " + (grid_label(grid0) if grid0 else "bo tri tuy bien doi xung"))

    def evaluate(coords, label):
        """Gọi MCOC đánh giá 1 phương án, kiểm tra ràng buộc và ghi nhật ký."""
        n_calls[0] += 1
        res = evaluator(np.asarray(coords, dtype=float))
        ok, errs = check_constraints(coords, res, params)
        rec = {'label': label, 'coords': np.asarray(coords, dtype=float),
               'n': len(coords), 'ok': ok, 'errs': errs,
               'pmax': res['pmax'], 'pmin': res['pmin'],
               'mxmax': res.get('mxmax', 0.0), 'mymax': res.get('mymax', 0.0),
               'footprint': footprint(coords)}
        history.append(rec)
        log("  [%s] n=%d, Pmax=%.2f T, %s" %
            (label, rec['n'], rec['pmax'],
             "DAT" if ok else "KHONG DAT (" + "; ".join(errs) + ")"))
        return rec

    # --- Bước 0: MCOC phương án gốc ------------------------------------------
    log("Buoc 0: goi MCOC danh gia phuong an goc (%d coc)" % len(coords0))
    original = evaluate(coords0, "goc")
    pm_r0, _ = rigid_pmax_pmin(coords0, loads)
    K_global = original['pmax'] / pm_r0 if pm_r0 > 1e-9 else 1.0
    log("He so hieu chinh K (MCOC/be cung) = %.4f" % K_global)

    incumbent = original if original['ok'] else None
    if incumbent is None:
        log("Phuong an goc KHONG DAT -> tim phuong an DAT trong ho luoi chuan...")

    # Họ cấu hình ứng viên:
    #   - mode toàn cục: TOÀN BỘ họ lưới chuẩn trong bệ (kể cả khi gốc là
    #     bố trí tùy biến) + phương án co đều giữ nguyên hình dạng gốc
    #   - mode 'spacing': chỉ co khoảng cách của chính cấu hình gốc
    bases = []
    if mode != 'spacing':
        cfgs = enumerate_configs(params, n_max=len(coords0), mode=mode, grid0=grid0)
        bases += [(b, "%s %dx%d" % ("luoi" if b['type'] == 'A' else "hoa mai",
                                    b['nx'], b['ny'])) for b in cfgs]
    elif grid0 is not None:
        cfgs = enumerate_configs(params, n_max=len(coords0), mode=mode, grid0=grid0)
        bases += [(b, "%s %dx%d" % ("luoi" if b['type'] == 'A' else "hoa mai",
                                    b['nx'], b['ny'])) for b in cfgs]
    if grid0 is None:
        bases.append((coords0, "co deu cum"))  # giữ nguyên hình dạng gốc
    log("Ho phuong an ung vien: %d cau hinh" % len(bases))

    cfg_K = {}        # hệ số hiệu chỉnh RIÊNG từng cấu hình (sau khi MCOC chạy)
    tested = set()    # (key, k) đã kiểm chứng

    def cfg_key(base):
        """Khóa nhận dạng cấu hình (kiểu, nx, ny) hoặc ('custom',) nếu tùy biến."""
        if isinstance(base, dict):
            return (base['type'], base['nx'], base['ny'])
        return ('custom',)

    while n_calls[0] < budget:
        # Mặt Pareto dự báo với hệ số hiệu chỉnh mới nhất
        cands = []
        for base, name in bases:
            Kc = cfg_K.get(cfg_key(base), K_global)
            k, c = solve_min_scale(base, loads, Kc, params, target)
            if k is None:
                continue
            if (cfg_key(base), round(k, 3)) in tested:
                continue
            pm_pred = rigid_pmax_pmin(c, loads)[0] * Kc
            pmin_pred = rigid_pmax_pmin(c, loads)[1] * Kc
            if P_TENSION > 0 and pmin_pred < -P_TENSION:
                continue
            cands.append({'base': base, 'name': name, 'k': k, 'coords': c,
                          'n': len(c), 'fp': footprint(c), 'pred': pm_pred})

        # Chỉ giữ ứng viên TRỘI HƠN phương án đương nhiệm (ít cọc hơn,
        # hoặc bằng cọc nhưng gọn hơn)
        if incumbent is not None:
            cands = [r for r in cands
                     if (r['n'], r['fp']) < (incumbent['n'],
                                             incumbent['footprint'] - 1e-6)]
        if not cands:
            log("Khong con ung vien nao troi hon -> DUNG.")
            break

        # Lọc mặt Pareto (không bị ứng viên khác trội hơn về cả n và fp)
        cands.sort(key=lambda r: (r['n'], r['fp'], r['pred']))
        front = []
        best_fp = float('inf')
        for r in cands:
            if r['fp'] < best_fp - 1e-9:
                front.append(r)
                best_fp = r['fp']
        log("Mat Pareto du bao: %s"
            % ", ".join("(%d coc, be %.1f m, ~%.0f T)" % (r['n'], r['fp'], r['pred'])
                        for r in front[:6]))

        cand = front[0]    # ưu tiên ít cọc nhất
        label = "%s k=%.3f" % (cand['name'], cand['k'])
        log("Kiem chung MCOC: %s (du bao Pmax~%.1f T)" % (label, cand['pred']))
        rec = evaluate(cand['coords'], label)
        tested.add((cfg_key(cand['base']), round(cand['k'], 3)))

        # Hiệu chỉnh hệ số K riêng của cấu hình này theo kết quả thật
        pm_r = rigid_pmax_pmin(cand['coords'], loads)[0]
        if pm_r > 1e-9:
            cfg_K[cfg_key(cand['base'])] = rec['pmax'] / pm_r

        if rec['ok']:
            if incumbent is None or \
               (rec['n'], rec['footprint']) < (incumbent['n'], incumbent['footprint']):
                incumbent = rec
                log("  -> Phuong an duong nhiem MOI: %d coc, be %.1f m, Pmax=%.1f T"
                    % (rec['n'], rec['footprint'], rec['pmax']))
        # KHÔNG ĐẠT: cfg_K đã được cập nhật, vòng sau dự báo sẽ tự đẩy lùi

    best = incumbent
    if best is None:
        reason = ("Phuong an goc KHONG DAT va khong tim duoc phuong an luoi "
                  "chuan nao DAT trong pham vi be/khoang cach cho phep.")
    elif best is original:
        reason = ("Phuong an goc da TOI UU PARETO (%d coc, Pmax=%.1f T): "
                  "khong cau hinh luoi chuan nao it coc hon/gon hon ma van dat."
                  % (best['n'], best['pmax']))
    else:
        g = detect_grid(best['coords'])
        kieu = grid_label(g) if g else "bo tri tuy bien (co deu)"
        reason = ("TOI UU PARETO sau %d lan goi MCOC: %s, %d coc (giam %d), "
                  "Pmax=%.1f T / Po=%.1f T."
                  % (n_calls[0], kieu, best['n'],
                     original['n'] - best['n'], best['pmax'], P_LIMIT))
    log(reason)

    return {'best': best, 'original': original, 'history': history,
            'n_calls': n_calls[0], 'reason': reason}


# ============================================================================
# Vòng lặp chính
# ============================================================================
def run_refinement(params, loads, evaluator, log=None, max_iter=60,
                   mcoc_per_iter=4):
    """
    Tinh chỉnh phương án gốc bằng vòng lặp Hộp Đen trên LƯỚI ĐIỂM.

    params phải có: D_PILE, P_LIMIT, original_coords (+ SAFE_D, P_TENSION...)
    params['refine_mode']:
        'full'    (mặc định) - co khoảng cách VÀ giảm số cọc (bỏ hàng/cột,
                               chuyển hoa mai)
        'spacing'            - chỉ co khoảng cách, giữ nguyên số cọc
    evaluator(coords) -> dict {'pmax','pmin','mxmax','mymax'} (gọi MCOC)
    """
    log = log or (lambda m: print(m))
    coords0 = np.asarray(params['original_coords'], dtype=float)
    history = []
    n_calls = [0]
    allow_removal = params.get('refine_mode', 'full') != 'spacing'
    log("Che do: %s" % ("co khoang cach + giam so coc" if allow_removal
                        else "chi co khoang cach (giu nguyen so coc)"))

    # ---- Nới lỏng ràng buộc theo HIỆN TRẠNG gốc (không khắt hơn gốc) ------
    d = params['D_PILE']
    SAFE_D = params.get('SAFE_D', d)
    s0 = min_spacing(coords0)
    floor = 3.0 * d
    if s0 < floor - 1e-4:
        log("CHU Y: khoang cach coc goc %.2f m < 3d=%.2f m -> dung san %.2f m."
            % (s0, floor, s0))
        floor = s0
    params['_spacing_floor'] = floor

    mx0 = float(np.max(np.abs(coords0[:, 0])))
    my0 = float(np.max(np.abs(coords0[:, 1])))
    if 'L_X' in params:
        lim = params['L_X'] / 2 - SAFE_D
        if mx0 > lim + 1e-4:
            log("CHU Y: coc goc cach mep be X < SAFE_D -> giu muc hien trang.")
        params['_max_x_allow'] = max(lim, mx0)
    if 'L_Y' in params:
        lim = params['L_Y'] / 2 - SAFE_D
        if my0 > lim + 1e-4:
            log("CHU Y: coc goc cach mep be Y < SAFE_D -> giu muc hien trang.")
        params['_max_y_allow'] = max(lim, my0)

    # ---- Nhận diện lưới gốc -------------------------------------------------
    grid = detect_grid(coords0)
    if grid is None:
        log("CHU Y: phuong an goc la bo tri doi xung TUY BIEN (khong phai "
            "luoi deu/hoa mai chuan) -> giu nguyen HINH DANG bo tri, chi co "
            "deu toan cum tung buoc nho; khong giam so coc.")
    else:
        log("Luoi goc: " + grid_label(grid))

    def evaluate(coords, label):
        """Gọi MCOC đánh giá 1 phương án, kiểm tra ràng buộc và ghi nhật ký."""
        n_calls[0] += 1
        res = evaluator(np.asarray(coords, dtype=float))
        ok, errs = check_constraints(coords, res, params)
        rec = {
            'label': label, 'coords': np.asarray(coords, dtype=float),
            'n': len(coords), 'ok': ok, 'errs': errs,
            'pmax': res['pmax'], 'pmin': res['pmin'],
            'mxmax': res.get('mxmax', 0.0), 'mymax': res.get('mymax', 0.0),
            'footprint': footprint(coords),
        }
        history.append(rec)
        log("  [%s] n=%d, Pmax=%.2f T, %s" %
            (label, rec['n'], rec['pmax'],
             "DAT" if ok else "KHONG DAT (" + "; ".join(errs) + ")"))
        return rec

    # ---- Bước 0: MCOC đánh giá phương án gốc -------------------------------
    log("Buoc 0: goi MCOC danh gia phuong an goc (%d coc)" % len(coords0))
    original = evaluate(coords0, "goc")
    best = original
    best_grid = grid

    if not original['ok']:
        return {
            'best': None, 'original': original, 'history': history,
            'n_calls': n_calls[0],
            'reason': "Phuong an goc KHONG DAT (%s) - khong the tinh chinh tu day."
                      % "; ".join(original['errs']),
        }
    cur = original
    cur_grid = grid
    P_LIMIT = params.get('P_LIMIT', 500.0)
    P_TENSION = params.get('P_TENSION', 0.0)
    step = params.get('refine_step', 0.0) or max(0.25 * d, 0.10)

    it = 0
    while it < max_iter:
        it += 1

        # Hệ số hiệu chỉnh K cập nhật từ lần gọi MCOC gần nhất
        pm_rigid, _ = rigid_pmax_pmin(cur['coords'], loads)
        K = cur['pmax'] / pm_rigid if pm_rigid > 1e-9 else 1.0

        # Sinh và dự báo các bước ứng viên
        cands = []
        if cur_grid is not None:
            moves = [(sp, lb, grid_coords(sp))
                     for sp, lb in candidate_moves(cur_grid, params, allow_removal)]
        else:
            # Bố trí tùy biến: CO ĐỀU toàn cụm một nấc nhỏ quanh trọng tâm,
            # giữ nguyên hình dạng; không bỏ cọc.
            moves = []
            s_min = min_spacing(cur['coords'])
            if s_min > floor + 1e-4 and s_min < float('inf'):
                k = max((s_min - step) / s_min, floor / s_min)
                ctr = cur['coords'].mean(axis=0)
                c2 = np.round(ctr + (cur['coords'] - ctr) * k, 3)
                moves.append((None, "co deu cum k=%.3f" % k, c2))

        for sp, lb, c in moves:
            if len(c) < 1:
                continue
            pmax_pred, pmin_pred = rigid_pmax_pmin(c, loads)
            pmax_pred *= K
            pmin_pred *= K
            if pmax_pred > 1.03 * P_LIMIT:
                continue
            if P_TENSION > 0 and pmin_pred < -1.03 * P_TENSION:
                continue
            cands.append({'spec': sp, 'label': lb, 'coords': c,
                          'n': len(c), 'fp': footprint(c),
                          'pred': pmax_pred})

        if not cands:
            log("Vong %d: khong con buoc tinh chinh kha thi -> DUNG." % it)
            break

        # Ưu tiên: ít cọc nhất -> bệ gọn nhất -> dự báo thấp nhất
        cands.sort(key=lambda r: (r['n'], r['fp'], r['pred']))

        improved = False
        for cand in cands[:mcoc_per_iter]:
            # Bước phải thực sự tốt hơn hiện tại
            if (cand['n'], cand['fp']) >= (cur['n'], cur['footprint'] - 1e-6):
                continue
            log("Vong %d: %s (du bao Pmax~%.1f T)" % (it, cand['label'], cand['pred']))
            rec = evaluate(cand['coords'], "v%d-%s" % (it, cand['label']))
            if rec['ok']:
                cur = rec
                cur_grid = cand['spec']
                if (rec['n'], rec['footprint']) < (best['n'], best['footprint']):
                    best = rec
                    best_grid = cand['spec']
                improved = True
                break

        if not improved:
            log("Vong %d: khong con buoc nao DAT tot hon -> DUNG." % it)
            break

    saved = original['n'] - best['n']
    if best is original:
        reason = ("Phuong an goc da toi uu (%d coc, Pmax=%.1f T): "
                  "moi buoc co luoi/giam coc deu khong dat."
                  % (best['n'], best['pmax']))
    else:
        kieu = grid_label(best_grid) if best_grid else "bo tri tuy bien (co deu)"
        reason = ("Tinh chinh xong sau %d lan goi MCOC: %s, %d coc (giam %d), "
                  "Pmax=%.1f T / Po=%.1f T."
                  % (n_calls[0], kieu, best['n'], saved,
                     best['pmax'], P_LIMIT))
    log(reason)

    return {
        'best': best, 'original': original, 'history': history,
        'n_calls': n_calls[0], 'reason': reason,
        'best_grid': best_grid,
    }
