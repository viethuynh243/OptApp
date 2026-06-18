"""
nsga2_optimizer.py - Tối ưu đa mục tiêu bố trí cọc móng cầu bằng NSGA-II.

KHÁC BIỆT VỚI optimizer.py / refine_optimizer.py
------------------------------------------------
- optimizer.py        : quét lưới (grid search) + bệ cứng XẤP XỈ (mock).
- refine_optimizer.py : tinh chỉnh Pareto TẤT ĐỊNH (predict-verify-recalibrate).
- nsga2_optimizer.py  : THUẬT TOÁN DI TRUYỀN ĐA MỤC TIÊU (NSGA-II) thật sự
                        (quần thể, lai ghép SBX, đột biến đa thức, sắp xếp
                        không-bị-thống-trị, khoảng cách chen chúc), đánh giá
                        bằng MCOC EXACT (hoặc mock khi không có MCOC).

NSGA-II (Deb et al., 2002) gồm 4 thành phần cốt lõi:
    1. Fast non-dominated sorting        -> xếp hạng Pareto.
    2. Crowding distance                 -> giữ đa dạng trên mặt Pareto.
    3. Crowded-comparison tournament     -> chọn lọc.
    4. SBX crossover + polynomial mutation + elitism (mu+lambda).

XỬ LÝ RÀNG BUỘC: nguyên tắc "constrained-domination" (Deb):
    - khả thi  >  bất khả thi;
    - 2 bất khả thi: ai vi phạm (CV) nhỏ hơn thì trội hơn;
    - 2 khả thi   : so sánh Pareto trên các mục tiêu.

BIẾN QUYẾT ĐỊNH (genome) cho 1 phương án lưới:
    type in {A (trực giao), B (hoa mai/so le)}
    nx   in [1..nmax]   số cột
    ny   in [1..nmax]   số hàng
    sx   in [3d..6d]    bước lưới theo X (m)
    sy   in [3d..6d]    bước lưới theo Y (m)

MỤC TIÊU (đều CỰC TIỂU HÓA):
    f1 = số cọc            (tiết kiệm vật liệu / thi công)
    f2 = Pmax (T)          (dự trữ an toàn; càng nhỏ càng an toàn)

Kết quả trả về tương thích với optimizer.run_optimization (recommended,
all_valid_configs, ...) + bổ sung pareto_front, n_evals.
"""

import numpy as np

from core import rigid_cap
from core.blackbox import MCOCBlackbox
from core.refine_optimizer import grid_coords, min_spacing, footprint
from core.constants import (SPACING_MIN_FACTOR, SPACING_MAX_FACTOR, NMAX_AXIS,
                            effective_min_spacing,
                            ENABLE_LATERAL_CHECK, ENABLE_PM_INTERACTION)


# ===========================================================================
# Giải mã genome -> tọa độ
# ===========================================================================
def _grid_bounds(params):
    """Trả về (d, SAFE_D, max_x_allow, max_y_allow, nmax_x, nmax_y)."""
    d = params['D_PILE']
    SAFE_D = params.get('SAFE_D', d)
    maxx = params['L_X'] / 2.0 - SAFE_D if 'L_X' in params else 1e9
    maxy = params['L_Y'] / 2.0 - SAFE_D if 'L_Y' in params else 1e9
    # Số cọc tối đa theo phương sao cho bước lưới >= 3d (còn không thì 1 cọc)
    nmax_x = max(2, int(1 + np.floor(max(2 * maxx, 0) / (SPACING_MIN_FACTOR * d) + 1e-9)))
    nmax_y = max(2, int(1 + np.floor(max(2 * maxy, 0) / (SPACING_MIN_FACTOR * d) + 1e-9)))
    nmax_x = min(nmax_x, params.get('nmax_axis', NMAX_AXIS))
    nmax_y = min(nmax_y, params.get('nmax_axis', NMAX_AXIS))
    return d, SAFE_D, maxx, maxy, nmax_x, nmax_y


def decode(ind, params):
    """genome dict -> (spec, coords). Sửa chữa nx/ny cho hợp lệ, kẹp sx/sy."""
    d, SAFE_D, maxx, maxy, nmax_x, nmax_y = _grid_bounds(params)
    t = ind['type']
    nx = int(round(ind['nx']))
    ny = int(round(ind['ny']))
    nx = int(np.clip(nx, 1, nmax_x))
    ny = int(np.clip(ny, 1, nmax_y))
    if t == 'B':                       # hoa mai cần ít nhất 2x2
        nx = max(nx, 2)
        ny = max(ny, 2)

    s_max = SPACING_MAX_FACTOR * d
    sx_edge = s_max if nx <= 1 else min(s_max, 2.0 * maxx / (nx - 1))
    sy_edge = s_max if ny <= 1 else min(s_max, 2.0 * maxy / (ny - 1))
    # Kẹp bước lưới vào [eps, giới hạn mép]. Nếu nhỏ hơn 3d -> sẽ bị phạt (CV).
    sx = float(min(max(ind['sx'], 1e-3), max(sx_edge, 1e-3)))
    sy = float(min(max(ind['sy'], 1e-3), max(sy_edge, 1e-3)))

    spec = {'type': t, 'nx': nx, 'ny': ny,
            'sx': round(sx, 3), 'sy': round(sy, 3), 'cx': 0.0, 'cy': 0.0}
    coords = grid_coords(spec)
    return spec, coords


def _spec_key(spec):
    """Khóa nhận dạng duy nhất của một spec lưới (dùng làm khóa cache)."""
    return (spec['type'], spec['nx'], spec['ny'],
            round(spec['sx'], 3), round(spec['sy'], 3))


# ===========================================================================
# Đánh giá: mục tiêu + vi phạm ràng buộc (constraint violation)
# ===========================================================================
def evaluate(ind, params, loads, evaluator, cache, counters):
    """
    Trả về dict kết quả cho 1 cá thể:
        {spec, coords, n, pmax, pmin, mxmax, mymax, obj=(n,pmax), cv, ok}
    cv = tổng vi phạm ràng buộc (>=0). cv≈0 => khả thi.
    Có cache theo spec_key để KHÔNG gọi MCOC trùng lặp.
    """
    spec, coords = decode(ind, params)
    key = _spec_key(spec)
    if key in cache:
        return cache[key]

    d = params['D_PILE']
    SAFE_D = params.get('SAFE_D', d)
    Po = params.get('P_LIMIT', 500.0)
    Ct = params.get('P_TENSION', 0.0) or 0.0
    M_raw = params.get('M_LIMIT', 0.0)
    Mmax = M_raw if (M_raw and M_raw > 0) else 0.0

    n = len(coords)
    if n < 1:                          # lưới rỗng -> phạt nặng, loại ngay
        rec = {'spec': spec, 'coords': coords, 'n': 0, 'pmax': 1e9, 'pmin': 0.0,
               'mxmax': 0.0, 'mymax': 0.0, 'obj': (1e9, 1e9), 'cv': 1e9,
               'ok': False, 'msg': 'khong co coc'}
        cache[key] = rec
        return rec

    res = evaluator(np.asarray(coords, dtype=float))
    counters['n_evals'] += 1
    pmax = float(res['pmax'])
    pmin = float(res.get('pmin', 0.0))
    mxmax = float(res.get('mxmax', 0.0))
    mymax = float(res.get('mymax', 0.0))

    # ---- Vi phạm ràng buộc (chuẩn hóa để các thành phần tương đương) -------
    s_min = effective_min_spacing(params)        # max(3d, d + thông thủy)
    s_max = SPACING_MAX_FACTOR * d
    H_limit = params.get('H_LIMIT', 0.0) or 0.0
    hmax_val = rigid_cap.hmax(coords, loads)

    cv = 0.0
    cv += max(0.0, pmax - Po) / max(Po, 1.0)                     # R5 nén
    if Ct > 0:
        cv += max(0.0, (-Ct) - pmin) / max(Ct, 1.0)             # R5b nhổ
    # R3 khoảng cách: dùng NGUỒN DUY NHẤT rigid_cap.spacing_values để ĐỒNG NHẤT
    # với check_layout/báo cáo/audit. Kiểu B kiểm ĐƯỜNG CHÉO √((sx/2)²+sy²),
    # vì sx,sy mỗi cái ≤ 6d vẫn cho đường chéo tới ~6.7d > 6d — min_spacing bỏ sót.
    for _lbl, sp_val, chk_up in rigid_cap.spacing_values(
            spec['type'], spec['nx'], spec['ny'], spec['sx'], spec['sy'], coords):
        cv += max(0.0, s_min - sp_val) / s_min                  # R3 dưới (+ thông thủy)
        if chk_up:
            cv += max(0.0, sp_val - s_max) / s_max              # R3 trên (kể cả đường chéo)
    mx = float(np.max(np.abs(coords[:, 0])))
    my = float(np.max(np.abs(coords[:, 1])))
    if 'L_X' in params:
        cv += max(0.0, mx + SAFE_D - params['L_X'] / 2.0) / (params['L_X'] / 2.0)
    if 'L_Y' in params:
        cv += max(0.0, my + SAFE_D - params['L_Y'] / 2.0) / (params['L_Y'] / 2.0)
    if Mmax > 0:
        cv += max(0.0, mxmax - Mmax) / Mmax + max(0.0, mymax - Mmax) / Mmax  # R6 uốn
    if ENABLE_LATERAL_CHECK and H_limit > 0:                     # R7 (tạm tắt)
        cv += max(0.0, hmax_val - H_limit) / H_limit
    if ENABLE_PM_INTERACTION and Mmax > 0 and Po > 0:           # R8 (tạm tắt)
        cv += max(0.0, (pmax / Po + max(mxmax, mymax) / Mmax) - 1.0)

    ok = cv <= 1e-9
    # Mục tiêu phụ (sau khi đủ số cọc + đạt Pmax<=Po):
    #   'compact' -> footprint nhỏ nhất (bệ gọn, tiết kiệm bê tông) [mặc định]
    #   'pmax'    -> Pmax nhỏ nhất (trải rộng, dự trữ an toàn)
    foot = footprint(coords)
    secondary = pmax if params.get('_secondary') == 'pmax' else foot
    rec = {'spec': spec, 'coords': coords, 'n': n, 'pmax': pmax, 'pmin': pmin,
           'mxmax': mxmax, 'mymax': mymax, 'hmax': hmax_val, 'footprint': foot,
           'secondary': secondary, 'obj': (float(n), secondary),
           'cv': cv, 'ok': ok, 'msg': 'OK' if ok else 'vi pham CV=%.4f' % cv}
    cache[key] = rec
    return rec


# ===========================================================================
# Toán tử NSGA-II
# ===========================================================================
def _constrained_dominates(a, b):
    """a có trội hơn b không (nguyên tắc constrained-domination)."""
    if a['ok'] and not b['ok']:
        return True
    if b['ok'] and not a['ok']:
        return False
    if not a['ok'] and not b['ok']:
        return a['cv'] < b['cv'] - 1e-12
    # cả hai khả thi -> Pareto trên mục tiêu (cực tiểu)
    af, bf = a['obj'], b['obj']
    le = all(x <= y + 1e-12 for x, y in zip(af, bf))
    lt = any(x < y - 1e-12 for x, y in zip(af, bf))
    return le and lt


def fast_non_dominated_sort(pop):
    """Trả về danh sách các front (mỗi front là list chỉ số trong pop)."""
    S = [[] for _ in pop]
    nd = [0] * len(pop)
    fronts = [[]]
    for p in range(len(pop)):
        for q in range(len(pop)):
            if p == q:
                continue
            if _constrained_dominates(pop[p], pop[q]):
                S[p].append(q)
            elif _constrained_dominates(pop[q], pop[p]):
                nd[p] += 1
        if nd[p] == 0:
            pop[p]['rank'] = 0
            fronts[0].append(p)
    i = 0
    while fronts[i]:
        nxt = []
        for p in fronts[i]:
            for q in S[p]:
                nd[q] -= 1
                if nd[q] == 0:
                    pop[q]['rank'] = i + 1
                    nxt.append(q)
        i += 1
        fronts.append(nxt)
    fronts.pop()
    return fronts


def crowding_distance(pop, front):
    """Gán 'crowd' cho các cá thể trong 1 front (trên không gian mục tiêu)."""
    for idx in front:
        pop[idx]['crowd'] = 0.0
    if len(front) <= 2:
        for idx in front:
            pop[idx]['crowd'] = float('inf')
        return
    n_obj = len(pop[front[0]]['obj'])
    for m in range(n_obj):
        order = sorted(front, key=lambda i: pop[i]['obj'][m])
        pop[order[0]]['crowd'] = float('inf')
        pop[order[-1]]['crowd'] = float('inf')
        fmin = pop[order[0]]['obj'][m]
        fmax = pop[order[-1]]['obj'][m]
        span = fmax - fmin
        if span <= 1e-12:
            continue
        for k in range(1, len(order) - 1):
            prev_ = pop[order[k - 1]]['obj'][m]
            next_ = pop[order[k + 1]]['obj'][m]
            pop[order[k]]['crowd'] += (next_ - prev_) / span


def _crowded_better(a, b):
    """Toán tử so sánh chen chúc: rank thấp hơn, hoặc cùng rank crowd lớn hơn."""
    if a['rank'] != b['rank']:
        return a['rank'] < b['rank']
    return a.get('crowd', 0.0) > b.get('crowd', 0.0)


def _tournament(pop, rng):
    """Chọn lọc đấu loại: bốc ngẫu nhiên 2 cá thể, trả về cá thể trội hơn."""
    i, j = rng.integers(0, len(pop), size=2)
    a, b = pop[i], pop[j]
    return a if _crowded_better(a, b) else b


# ---- Lai ghép / đột biến ---------------------------------------------------
def _sbx(x1, x2, lo, hi, eta, rng):
    """Simulated Binary Crossover (lai ghép nhị phân mô phỏng) cho 1 biến thực."""
    if abs(x1 - x2) < 1e-12 or hi - lo < 1e-12:
        return x1, x2
    x1, x2 = min(x1, x2), max(x1, x2)
    u = rng.random()
    beta = 1.0 + 2.0 * (x1 - lo) / (x2 - x1)
    alpha = 2.0 - beta ** (-(eta + 1))
    bq = (u * alpha) ** (1.0 / (eta + 1)) if u <= 1.0 / alpha \
        else (1.0 / (2.0 - u * alpha)) ** (1.0 / (eta + 1))
    c1 = 0.5 * ((x1 + x2) - bq * (x2 - x1))
    beta = 1.0 + 2.0 * (hi - x2) / (x2 - x1)
    alpha = 2.0 - beta ** (-(eta + 1))
    bq = (u * alpha) ** (1.0 / (eta + 1)) if u <= 1.0 / alpha \
        else (1.0 / (2.0 - u * alpha)) ** (1.0 / (eta + 1))
    c2 = 0.5 * ((x1 + x2) + bq * (x2 - x1))
    return float(np.clip(c1, lo, hi)), float(np.clip(c2, lo, hi))


def _poly_mutate(x, lo, hi, eta, rng):
    """Polynomial mutation (đột biến đa thức) cho 1 biến thực."""
    if hi - lo < 1e-12:
        return x
    u = rng.random()
    dx = hi - lo
    if u < 0.5:
        delta = (2.0 * u) ** (1.0 / (eta + 1)) - 1.0
    else:
        delta = 1.0 - (2.0 * (1.0 - u)) ** (1.0 / (eta + 1))
    return float(np.clip(x + delta * dx, lo, hi))


def _crossover(p1, p2, params, rng, eta=15):
    """Lai ghép 2 cha mẹ -> 2 con: type đồng nhất, nx/ny/sx/sy theo SBX."""
    d, SAFE_D, maxx, maxy, nmax_x, nmax_y = _grid_bounds(params)
    s_lo, s_hi = SPACING_MIN_FACTOR * d, SPACING_MAX_FACTOR * d
    c1, c2 = dict(p1), dict(p2)
    # type: lai ghép đồng nhất (uniform)
    if rng.random() < 0.5:
        c1['type'], c2['type'] = p2['type'], p1['type']
    # nx, ny: SBX trên số thực rồi làm tròn
    for g, lo, hi in (('nx', 1, nmax_x), ('ny', 1, nmax_y)):
        a, b = _sbx(float(p1[g]), float(p2[g]), lo, hi, eta, rng)
        c1[g], c2[g] = int(round(a)), int(round(b))
    # sx, sy: SBX thực
    for g in ('sx', 'sy'):
        a, b = _sbx(float(p1[g]), float(p2[g]), s_lo, s_hi, eta, rng)
        c1[g], c2[g] = a, b
    return c1, c2


def _mutate(ind, params, rng, pm=None, eta=20):
    """Đột biến 1 cá thể: mỗi gene đột biến với xác suất pm (mặc định 1/5 gene)."""
    d, SAFE_D, maxx, maxy, nmax_x, nmax_y = _grid_bounds(params)
    s_lo, s_hi = SPACING_MIN_FACTOR * d, SPACING_MAX_FACTOR * d
    if pm is None:
        pm = 1.0 / 5.0                      # 5 gene
    out = dict(ind)
    if rng.random() < pm:
        out['type'] = 'B' if ind['type'] == 'A' else 'A'
    if rng.random() < pm:
        out['nx'] = int(np.clip(ind['nx'] + rng.choice([-1, 1]), 1, nmax_x))
    if rng.random() < pm:
        out['ny'] = int(np.clip(ind['ny'] + rng.choice([-1, 1]), 1, nmax_y))
    if rng.random() < pm:
        out['sx'] = _poly_mutate(float(ind['sx']), s_lo, s_hi, eta, rng)
    if rng.random() < pm:
        out['sy'] = _poly_mutate(float(ind['sy']), s_lo, s_hi, eta, rng)
    return out


def _random_individual(params, rng):
    """Sinh ngẫu nhiên 1 cá thể (genome) khởi tạo quần thể ban đầu."""
    d, SAFE_D, maxx, maxy, nmax_x, nmax_y = _grid_bounds(params)
    return {
        'type': 'A' if rng.random() < 0.5 else 'B',
        'nx': int(rng.integers(2, nmax_x + 1)),
        'ny': int(rng.integers(2, nmax_y + 1)),
        'sx': float(rng.uniform(SPACING_MIN_FACTOR * d, SPACING_MAX_FACTOR * d)),
        'sy': float(rng.uniform(SPACING_MIN_FACTOR * d, SPACING_MAX_FACTOR * d)),
    }


def _build_seed_genomes(params):
    """Danh sách genome TẤT ĐỊNH gieo vào quần thể khởi tạo.

    Vùng khả thi của bài toán bố trí cọc thường là một "lát rất mỏng" (khoảng
    cách cọc bị kẹp gần đúng 3d do giới hạn mép bệ; Kiểu B còn bị siết thêm bởi
    ràng buộc đường chéo R3), nên toán tử ngẫu nhiên của NSGA-II RẤT khó trúng
    — dẫn tới báo "không có phương án" dù lời giải tồn tại (rõ nhất ở luồng mở
    rộng: ngân sách nhỏ + R7/R8 bật). Hàm này bảo đảm vùng khả thi (nếu có)
    luôn được đánh giá, không phụ thuộc may rủi của hạt giống ngẫu nhiên:
        1) Phương án GỐC của kỹ sư (giải mã thành lưới) — đã biết hợp lý.
        2) Liệt kê toàn bộ lưới type×nx×ny ở vài bước lưới đại diện.

    Trùng lặp sau khi giải mã (clamp về cùng spec) được cache khử ở evaluate,
    nên số lần gọi MCOC THỰC = số spec phân biệt, không lãng phí.
    """
    from core.refine_optimizer import detect_grid
    d, SAFE_D, maxx, maxy, nmax_x, nmax_y = _grid_bounds(params)
    seeds = []

    # 1) Phương án gốc (nếu nhận diện được thành lưới đều / hoa mai)
    orig = params.get('original_coords')
    if orig is not None and len(orig) >= 2:
        try:
            spec = detect_grid(np.asarray(orig, dtype=float))
        except Exception:
            spec = None
        if spec:
            seeds.append({'type': spec['type'], 'nx': spec['nx'], 'ny': spec['ny'],
                          'sx': float(spec['sx'] or SPACING_MIN_FACTOR * d),
                          'sy': float(spec['sy'] or SPACING_MIN_FACTOR * d)})

    # 2) Liệt kê lưới type×nx×ny. Hai điều CỐT YẾU để tập hạt giống đủ NHỎ mà vẫn
    #    PHỦ vùng khả thi trong ngân sách max_evals (lỗi cũ: 178 spec, lưới khả thi
    #    nằm tận #109 -> hết ngân sách trước khi tới nó -> báo "vô nghiệm"):
    #      - BỎ lưới 1 hàng/1 cột (nx<2 hoặc ny<2) — gần như vô dụng.
    #      - Chỉ 2 bước lưới: 3d (dày nhất -> nhiều cọc, hợp tải lớn) và 6d (thưa
    #        -> ít cọc; decode tự kẹp về cận mép). Bước trung gian do tiến hóa lo.
    #    SẮP XẾP theo SỐ CỌC TĂNG DẦN: khớp mục tiêu "ít cọc nhất" và bảo đảm khi
    #    ngân sách hẹp vẫn quét đủ phổ số cọc (cả ít lẫn nhiều).
    s_facs = (SPACING_MIN_FACTOR, SPACING_MAX_FACTOR)
    combos = [(t, nx, ny)
              for t in ('A', 'B')
              for nx in range(2, nmax_x + 1)
              for ny in range(2, nmax_y + 1)]
    combos.sort(key=lambda c: (c[1] * c[2], c[1], c[2]))   # ít cọc trước
    for t, nx, ny in combos:
        for sf in s_facs:
            seeds.append({'type': t, 'nx': nx, 'ny': ny,
                          'sx': sf * d, 'sy': sf * d})
    return seeds


def _environmental_selection(combined, pop_size):
    """Chọn lọc môi trường NSGA-II: lấy pop_size cá thể tốt nhất từ combined
    theo front không-bị-thống-trị + khoảng cách chen chúc (dùng chung cho cả
    bước khởi tạo lẫn vòng tiến hóa)."""
    fronts = fast_non_dominated_sort(combined)
    new_pop = []
    for fr in fronts:
        crowding_distance(combined, fr)
        if len(new_pop) + len(fr) <= pop_size:
            new_pop.extend(combined[i] for i in fr)
        else:
            remaining = pop_size - len(new_pop)
            fr_sorted = sorted(fr, key=lambda i: combined[i].get('crowd', 0.0),
                               reverse=True)
            new_pop.extend(combined[i] for i in fr_sorted[:remaining])
            break
    return new_pop


# ===========================================================================
# Vòng lặp chính NSGA-II
# ===========================================================================
def run_nsga2(params, loads, evaluator=None, pop_size=40, n_gen=30,
              seed=0, log=None, max_evals=None, secondary='compact'):
    """
    Chạy NSGA-II tìm mặt Pareto cho bài toán bố trí cọc.

    secondary : mục tiêu phụ (sau khi đủ số cọc + đạt Pmax<=Po):
        'compact' (mặc định) -> bệ GỌN nhất (footprint min) -> tiết kiệm bê tông;
        'pmax'               -> Pmax nhỏ nhất (trải rộng, dự trữ an toàn).

    Tham số:
        evaluator : hàm coords(np.ndarray) -> {'pmax','pmin','mxmax','mymax'}.
                    None  -> dùng MOCK (bệ cứng + hiệu chỉnh K) từ blackbox.
                    Để đánh giá MCOC EXACT, truyền
                    MCOCBlackbox.make_real_evaluator(params).
        pop_size  : kích thước quần thể.
        n_gen     : số thế hệ.
        seed      : hạt giống ngẫu nhiên (tái lập).
        max_evals : trần số lần gọi evaluator thật (hữu ích khi MCOC chậm).
                    Khi vượt trần, chỉ dùng kết quả đã cache.

    Trả về dict:
        recommended, reason, pareto_front, all_valid_configs,
        all_evaluated, n_evals, eval_mode
    """
    log = log or (lambda m: None)
    rng = np.random.default_rng(seed)
    params['_secondary'] = secondary   # 'compact' (footprint) | 'pmax'

    eval_mode = 'mock'
    if evaluator is None:
        evaluator = MCOCBlackbox.make_mock_evaluator(params, loads)
    else:
        eval_mode = 'MCOC-exact'
    log("NSGA-II | pop=%d, gen=%d, danh gia=%s" % (pop_size, n_gen, eval_mode))
    # Mômen đầu cọc ở mock là ước lượng -> R6 chỉ tin cậy khi chấm MCOC.
    if eval_mode == 'mock' and (params.get('M_LIMIT', 0) or 0) > 0:
        log("CANH BAO: che do mock - momen dau coc la uoc luong; kiem tra [M] "
            "(R6) chi tin cay khi danh gia bang MCOC.")

    cache = {}
    counters = {'n_evals': 0}

    def _eval_pop(individuals):
        """Đánh giá cả một nhóm cá thể, tôn trọng trần max_evals và cache."""
        out = []
        for ind in individuals:
            if max_evals is not None and counters['n_evals'] >= max_evals:
                # Hết ngân sách: chỉ nhận cá thể đã có trong cache
                spec, _ = decode(ind, params)
                rec = cache.get(_spec_key(spec))
                if rec is None:
                    continue
            else:
                rec = evaluate(ind, params, loads, evaluator, cache, counters)
            rec = dict(rec)
            rec['genome'] = ind
            out.append(rec)
        return out

    # ---- Khởi tạo quần thể -------------------------------------------------
    # Gieo TẤT ĐỊNH trước (phương án gốc + liệt kê lưới) rồi mới bù ngẫu nhiên.
    # Hạt giống được đánh giá TRƯỚC nên giành ngân sách max_evals; bảo đảm vùng
    # khả thi (nếu tồn tại) luôn nằm trong cache để xét 'recommended' — kể cả khi
    # ngân sách nhỏ (luồng mở rộng) hay R7/R8 siết chặt vùng khả thi.
    seeded = _eval_pop(_build_seed_genomes(params))
    log("Gieo tat dinh: %d hat giong (goc + liet ke luoi), kha thi=%d"
        % (len(seeded), sum(1 for r in seeded if r['ok'])))
    rand_pop = _eval_pop([_random_individual(params, rng) for _ in range(pop_size)])
    pop = _environmental_selection(seeded + rand_pop, pop_size) or seeded
    fronts = fast_non_dominated_sort(pop)
    for fr in fronts:
        crowding_distance(pop, fr)

    # ---- Tiến hóa ----------------------------------------------------------
    for gen in range(n_gen):
        if not pop:                     # hết ngân sách ngay từ khởi tạo -> dừng
            break
        offspring_genomes = []
        while len(offspring_genomes) < pop_size:
            p1 = _tournament(pop, rng)['genome']
            p2 = _tournament(pop, rng)['genome']
            c1, c2 = _crossover(p1, p2, params, rng)
            offspring_genomes.append(_mutate(c1, params, rng))
            if len(offspring_genomes) < pop_size:
                offspring_genomes.append(_mutate(c2, params, rng))

        offspring = _eval_pop(offspring_genomes)
        combined = pop + offspring
        pop = _environmental_selection(combined, pop_size)

        feas = [r for r in pop if r['ok']]
        best = min(feas, key=lambda r: r['obj']) if feas else None
        log("  Gen %2d | n_evals=%d | kha thi=%d/%d%s"
            % (gen + 1, counters['n_evals'], len(feas), len(pop),
               " | tot nhat: %d coc, Pmax=%.1f T" % (best['n'], best['pmax'])
               if best else ""))
        if max_evals is not None and counters['n_evals'] >= max_evals:
            log("  -> Da cham tran %d lan goi danh gia, dung tien hoa." % max_evals)
            break

    # ---- Tổng hợp kết quả từ TẤT CẢ cá thể đã đánh giá (cache) -------------
    # Sắp xếp & xét thống trị theo (số cọc, mục tiêu phụ) — mục tiêu phụ là
    # footprint (compact) hoặc pmax tùy 'secondary'.
    all_evaluated = list(cache.values())
    valid = [r for r in all_evaluated if r['ok']]
    valid.sort(key=lambda r: (r['n'], r['secondary']))

    # Mặt Pareto cuối cùng (chỉ các phương án khả thi, không bị thống trị)
    pareto = []
    for r in valid:
        dominated = False
        for s in valid:
            if s is r:
                continue
            if (s['n'] <= r['n'] and s['secondary'] <= r['secondary'] and
                    (s['n'] < r['n'] or s['secondary'] < r['secondary'])):
                dominated = True
                break
        if not dominated:
            pareto.append(r)
    pareto.sort(key=lambda r: (r['n'], r['secondary']))

    def _to_config(r):
        """Chuyển bản ghi đánh giá nội bộ sang dict cấu hình trả ra ngoài."""
        sp = r['spec']
        return {'type': sp['type'], 'nx': sp['nx'], 'ny': sp['ny'],
                'sx': sp['sx'], 'sy': sp['sy'], 'n': r['n'],
                'coords': r['coords'], 'pmax': r['pmax'], 'pmin': r['pmin'],
                'mxmax': r['mxmax'], 'mymax': r['mymax'],
                'hmax': r.get('hmax', 0.0), 'ok': r['ok'], 'msg': r['msg']}

    all_valid_configs = [_to_config(r) for r in valid]
    pareto_front = [_to_config(r) for r in pareto]

    recommended = None
    # Chẩn đoán khi bệ quá hẹp cho 2 hàng cọc ở khoảng cách 3d — nguyên nhân
    # hình học phổ biến nhất khiến không có phương án; báo rõ để người dùng biết
    # cần NỚI kích thước bệ (hoặc giảm tải / tăng đường kính) thay vì loay hoay.
    d = params.get('D_PILE', 1.0)
    SAFE_D = params.get('SAFE_D', d)
    narrow_x = ('L_X' in params) and (params['L_X'] - 2 * SAFE_D < SPACING_MIN_FACTOR * d - 1e-6)
    narrow_y = ('L_Y' in params) and (params['L_Y'] - 2 * SAFE_D < SPACING_MIN_FACTOR * d - 1e-6)
    if narrow_x or narrow_y:
        need = SPACING_MIN_FACTOR * d + 2 * SAFE_D
        reason = ("Khong co phuong an: be qua hep cho 2 hang coc o khoang cach toi thieu "
                  "3d=%.2f m (can be rong it nhat ~%.2f m moi phuong). Hay NOI kich thuoc "
                  "be (L_X/L_Y), giam tai, hoac tang duong kinh." % (SPACING_MIN_FACTOR * d, need))
    else:
        reason = ("Khong co phuong an kha thi: da liet ke toan bo luoi trong pham vi be/"
                  "khoang cach hien tai, moi bo tri deu vuot [Po]/[Ct]/[M]"
                  + ("/[H]" if (params.get('H_LIMIT', 0) or 0) > 0 else "")
                  + ". Can noi be, giam tai, hoac tang suc chiu tai/duong kinh.")
    if valid:
        recommended = _to_config(valid[0])
        muc_tieu = "be GON nhat" if secondary != 'pmax' else "Pmax nho nhat"
        reason = ("NSGA-II (%s, %d the he, %d lan danh gia): uu tien it coc nhat, "
                  "sau do %s - %d coc, Pmax=%.1f T / Po=%.1f T. "
                  "Mat Pareto co %d phuong an khong bi thong tri."
                  % (eval_mode, n_gen, counters['n_evals'], muc_tieu,
                     recommended['n'], recommended['pmax'],
                     params.get('P_LIMIT', 0.0), len(pareto_front)))
    log(reason)

    return {
        'recommended': recommended,
        'reason': reason,
        'pareto_front': pareto_front,
        'all_valid_configs': all_valid_configs,
        'all_evaluated': [_to_config(r) for r in all_evaluated],
        'n_evals': counters['n_evals'],
        'eval_mode': eval_mode,
        # tương thích lời gọi cũ (UI/export dùng best_A/best_B):
        'best_A': next((c for c in all_valid_configs if c['type'] == 'A'), None),
        'best_B': next((c for c in all_valid_configs if c['type'] == 'B'), None),
        'original_config': None,
    }
