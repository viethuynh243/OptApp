"""
refine_optimizer.py - Toi uu hoa kieu HOP DEN + TINH CHINH TUNG BUOC TREN LUOI.

NGUYEN TAC BO TRI (kien thuc mong coc cau):
    - Coc LUON nam tren luoi diem deu, doi xung qua tam be, theo 2 dang:
        Kieu A (luoi truc giao)  :  o o o     Kieu B (hoa mai / so le):  o o o
                                    o o o                                  o o
                                    o o o                                 o o o
    - KHONG bao gio bo coc don le (mat doi xung, mat goi do goc).
    - Kich thuoc luoi (sx, sy) co dan tung buoc nho trong mien gioi han
      khoang cach tim-den-tim (3d..6d) va khoang cach mep be.

CAC BUOC TINH CHINH (moi vong chon 1 buoc tot nhat):
    (a) co sx mot nac nho          (b) co sy mot nac nho
    (c) bo nguyen 1 COT (nx-1)     (d) bo nguyen 1 HANG (ny-1)
    (e) chuyen luoi A -> hoa mai B (tiet kiem floor(ny/2) coc)

Moi buoc duoc DU BAO truoc bang cong thuc be cung (he so hieu chinh
K = Pmax_MCOC / Pmax_be_cung, cap nhat lai sau moi lan goi MCOC), sau do
phuong an du bao kha thi se duoc goi MCOC kiem chung that. Vong lap dung
khi khong con buoc nao cho ket qua DAT tot hon.

Tieu chi "tot hon": (1) it coc hon; (2) cung so coc thi be gon hon.
"""

import numpy as np


# ============================================================================
# Cong thuc be cung (chi de DU BAO, ket qua that luon do MCOC quyet dinh)
# ============================================================================
def rigid_forces(coords, loads):
    coords = np.asarray(coords, dtype=float)
    n = len(coords)
    cx, cy = coords[:, 0].mean(), coords[:, 1].mean()
    dx = coords[:, 0] - cx
    dy = coords[:, 1] - cy
    Ix = float(np.sum(dy ** 2)) or 1e-9
    Iy = float(np.sum(dx ** 2)) or 1e-9
    P = np.zeros((len(loads), n))
    for k, ld in enumerate(loads):
        P[k, :] = ld.get('N', 0.0) / n + ld.get('Mx', 0.0) * dy / Ix \
                  + ld.get('My', 0.0) * dx / Iy
    return P


def rigid_pmax_pmin(coords, loads):
    P = rigid_forces(coords, loads)
    return float(P.max()), float(P.min())


def min_spacing(coords):
    coords = np.asarray(coords, dtype=float)
    n = len(coords)
    if n < 2:
        return float('inf')
    d2 = np.sum((coords[:, None, :] - coords[None, :, :]) ** 2, axis=2)
    d2[np.diag_indices(n)] = np.inf
    return float(np.sqrt(d2.min()))


def footprint(coords):
    coords = np.asarray(coords, dtype=float)
    w = coords[:, 0].max() - coords[:, 0].min()
    h = coords[:, 1].max() - coords[:, 1].min()
    return w + h


# ============================================================================
# Luoi diem: nhan dien va sinh toa do
# ============================================================================
def grid_coords(spec):
    """Sinh toa do tu spec luoi {type,nx,ny,sx,sy,cx,cy} - luon doi xung."""
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
    """So sanh 2 tap diem (khong phu thuoc thu tu)."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if a.shape != b.shape:
        return False
    ka = a[np.lexsort((a[:, 1], a[:, 0]))]
    kb = b[np.lexsort((b[:, 1], b[:, 0]))]
    return np.allclose(ka, kb, atol=tol)


def detect_grid(coords, tol=1e-2):
    """
    Nhan dien luoi tu toa do goc. Tra ve spec {'type','nx','ny','sx','sy',
    'cx','cy'} hoac None neu khong phai luoi deu / hoa mai.
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

    # sy: khoang cach hang deu
    if ny > 1:
        dys = np.diff(ys)
        if np.max(dys) - np.min(dys) > tol:
            return None
        sy = float(np.mean(dys))
    else:
        sy = 0.0

    # sx: tu hang dai nhat
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
    name = "luoi" if spec['type'] == 'A' else "hoa mai"
    return "%s %dx%d, sx=%.2f sy=%.2f" % (name, spec['nx'], spec['ny'],
                                          spec['sx'], spec['sy'])


# ============================================================================
# Rang buoc
# ============================================================================
def check_constraints(coords, res, params):
    """Kiem tra R1/R2/R3/R4 cho 1 ket qua MCOC. Tra ve (ok, [loi])."""
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

    # San khoang cach tim-tim: 3d nhung khong khat hon hien trang goc
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
    """Khoang cach tim-tim nho nhat cua luoi >= san cho phep."""
    sx, sy, t = spec['sx'], spec['sy'], spec['type']
    if spec['nx'] > 1 and sx < floor - 1e-6:
        return False
    if spec['ny'] > 1:
        if t == 'A':
            if sy < floor - 1e-6:
                return False
        else:  # hoa mai: hang ke nhau lech sx/2
            diag = np.hypot(sx / 2.0, sy)
            if diag < floor - 1e-6:
                return False
    return True


def _edge_ok(spec, params):
    coords = grid_coords(spec)
    mx = float(np.max(np.abs(coords[:, 0])))
    my = float(np.max(np.abs(coords[:, 1])))
    return mx <= params.get('_max_x_allow', float('inf')) + 1e-4 and \
        my <= params.get('_max_y_allow', float('inf')) + 1e-4


# ============================================================================
# Sinh cac BUOC TINH CHINH ung vien tu luoi hien tai
# ============================================================================
def candidate_moves(spec, params, allow_removal):
    """Tra ve list (spec_moi, mo_ta). Luon giu luoi deu/hoa mai doi xung."""
    d = params['D_PILE']
    floor = params.get('_spacing_floor', 3.0 * d)
    step = params.get('refine_step', 0.0) or max(0.25 * d, 0.10)  # nac co (m)
    s_max = 6.0 * d

    out = []
    nx, ny, sx, sy = spec['nx'], spec['ny'], spec['sx'], spec['sy']

    def add(sp, label):
        if not _spacing_ok(sp, floor):
            return
        if not _edge_ok(sp, params):
            return
        out.append((sp, label))

    # (a) co sx mot nac
    if nx > 1:
        lo = floor if spec['type'] == 'A' else max(
            floor, 2.0 * np.sqrt(max(floor ** 2 - sy ** 2, 0.0)))
        new_sx = max(sx - step, lo)
        if new_sx < sx - 1e-6:
            sp = dict(spec, sx=round(new_sx, 3))
            add(sp, "co sx %.2f->%.2f" % (sx, new_sx))

    # (b) co sy mot nac
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
        # (c) bo nguyen 1 COT: gian sx toi da de bu lai (uu tien kha thi)
        if nx > 2:
            for sx2 in ((min(s_max, 2 * params.get('_max_x_allow', 1e9) / (nx - 2)),
                         sx)):
                sx2 = round(min(max(sx2, floor), s_max), 3)
                sp = dict(spec, nx=nx - 1, sx=sx2)
                add(sp, "bo 1 cot -> %dx%d (sx=%.2f)" % (nx - 1, ny, sx2))

        # (d) bo nguyen 1 HANG
        if ny > 2:
            for sy2 in ((min(s_max, 2 * params.get('_max_y_allow', 1e9) / (ny - 2)),
                         sy)):
                sy2 = round(min(max(sy2, floor), s_max), 3)
                sp = dict(spec, ny=ny - 1, sy=sy2)
                add(sp, "bo 1 hang -> %dx%d (sy=%.2f)" % (nx, ny - 1, sy2))

        # (e) chuyen luoi A -> hoa mai B (tiet kiem floor(ny/2) coc)
        if spec['type'] == 'A' and nx >= 2 and ny >= 2:
            sy_b = max(sy, np.sqrt(max(floor ** 2 - (sx / 2.0) ** 2, 0.0)))
            sp = dict(spec, type='B', sy=round(sy_b, 3))
            add(sp, "chuyen sang hoa mai %dx%d" % (nx, ny))

    # Loai trung lap
    uniq, seen = [], set()
    for sp, lb in out:
        key = (sp['type'], sp['nx'], sp['ny'], round(sp['sx'], 3), round(sp['sy'], 3))
        if key not in seen:
            seen.add(key)
            uniq.append((sp, lb))
    return uniq


# ============================================================================
# TOI UU PARETO TOAN CUC (predict - verify - recalibrate)
# ============================================================================
def _n_piles(t, nx, ny):
    if t == 'A':
        return nx * ny
    return nx * ((ny + 1) // 2) + (nx - 1) * (ny // 2)


def enumerate_configs(params, n_max, mode, grid0, nmax_axis=14):
    """
    Liet ke TOAN BO ho luoi chuan kha thi ve hinh hoc:
    (kieu A/B) x nx x ny, voi sx_max/sy_max theo mep be va 6d.
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
    """Co deu mot cau hinh (spec luoi hoac toa do tuy bien) voi he so k."""
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
    Tim he so co k NHO NHAT sao cho du bao Kc*Pmax_be_cung(k) <= target
    va khoang cach >= san. base: spec luoi hoac toa do tuy bien.
    Tra ve (k, coords) hoac (None, None) neu ngay k=1 da vuot target.
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
        return None, None                     # khong kha thi ngay o k=1

    k_lo = min(1.0, floor / ms1)              # gioi han san khoang cach
    lo, hi = k_lo, 1.0
    for _ in range(24):                        # binary search
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
    TOI UU PARETO + HOP DEN MCOC:
      1. Goi MCOC tinh phuong an goc -> he so hieu chinh K.
      2. Liet ke toan bo ho luoi chuan; voi moi cau hinh giai he so co nho
         nhat theo DU BAO (be cung x K) -> tap ung vien tren mat Pareto
         (so coc, do gon be).
      3. Kiem chung ung vien tot nhat bang MCOC that:
           - DAT  -> thanh phuong an duong nhiem, tiep tuc tim tot hon;
           - KHONG DAT -> luu he so hieu chinh RIENG cua cau hinh do,
             tinh lai du bao (ung vien tu dong bi day lui tren mat Pareto).
      4. Lap den khi khong con ung vien nao TROI HON phuong an duong nhiem
         hoac het ngan sach goi MCOC.
    """
    log = log or (lambda m: print(m))
    coords0 = np.asarray(params['original_coords'], dtype=float)
    history = []
    n_calls = [0]
    mode = params.get('refine_mode', 'full')
    P_LIMIT = params.get('P_LIMIT', 500.0)
    P_TENSION = params.get('P_TENSION', 0.0)
    target = params.get('target_ratio', 0.99) * P_LIMIT

    # --- Noi long rang buoc theo hien trang goc -----------------------------
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

    # --- Buoc 0: MCOC phuong an goc ------------------------------------------
    log("Buoc 0: goi MCOC danh gia phuong an goc (%d coc)" % len(coords0))
    original = evaluate(coords0, "goc")
    pm_r0, _ = rigid_pmax_pmin(coords0, loads)
    K_global = original['pmax'] / pm_r0 if pm_r0 > 1e-9 else 1.0
    log("He so hieu chinh K (MCOC/be cung) = %.4f" % K_global)

    incumbent = original if original['ok'] else None
    if incumbent is None:
        log("Phuong an goc KHONG DAT -> tim phuong an DAT trong ho luoi chuan...")

    # Ho cau hinh ung vien:
    #   - mode toan cuc: TOAN BO ho luoi chuan trong be (ke ca khi goc la
    #     bo tri tuy bien) + phuong an co deu giu nguyen hinh dang goc
    #   - mode 'spacing': chi co khoang cach cua chinh cau hinh goc
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
        bases.append((coords0, "co deu cum"))  # giu nguyen hinh dang goc
    log("Ho phuong an ung vien: %d cau hinh" % len(bases))

    cfg_K = {}        # he so hieu chinh RIENG tung cau hinh (sau khi MCOC chay)
    tested = set()    # (key, k) da kiem chung

    def cfg_key(base):
        if isinstance(base, dict):
            return (base['type'], base['nx'], base['ny'])
        return ('custom',)

    while n_calls[0] < budget:
        # Mat Pareto du bao voi he so hieu chinh moi nhat
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

        # Chi giu ung vien TROI HON phuong an duong nhiem (it coc hon,
        # hoac bang coc nhung gon hon)
        if incumbent is not None:
            cands = [r for r in cands
                     if (r['n'], r['fp']) < (incumbent['n'],
                                             incumbent['footprint'] - 1e-6)]
        if not cands:
            log("Khong con ung vien nao troi hon -> DUNG.")
            break

        # Loc mat Pareto (khong bi ung vien khac troi hon ve ca n va fp)
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

        cand = front[0]    # uu tien it coc nhat
        label = "%s k=%.3f" % (cand['name'], cand['k'])
        log("Kiem chung MCOC: %s (du bao Pmax~%.1f T)" % (label, cand['pred']))
        rec = evaluate(cand['coords'], label)
        tested.add((cfg_key(cand['base']), round(cand['k'], 3)))

        # Hieu chinh he so K rieng cua cau hinh nay theo ket qua that
        pm_r = rigid_pmax_pmin(cand['coords'], loads)[0]
        if pm_r > 1e-9:
            cfg_K[cfg_key(cand['base'])] = rec['pmax'] / pm_r

        if rec['ok']:
            if incumbent is None or \
               (rec['n'], rec['footprint']) < (incumbent['n'], incumbent['footprint']):
                incumbent = rec
                log("  -> Phuong an duong nhiem MOI: %d coc, be %.1f m, Pmax=%.1f T"
                    % (rec['n'], rec['footprint'], rec['pmax']))
        # KHONG DAT: cfg_K da duoc cap nhat, vong sau du bao se tu day lui

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
# Vong lap chinh
# ============================================================================
def run_refinement(params, loads, evaluator, log=None, max_iter=60,
                   mcoc_per_iter=4):
    """
    Tinh chinh phuong an goc bang vong lap Hop Den tren LUOI DIEM.

    params phai co: D_PILE, P_LIMIT, original_coords (+ SAFE_D, P_TENSION...)
    params['refine_mode']:
        'full'    (mac dinh) - co khoang cach VA giam so coc (bo hang/cot,
                               chuyen hoa mai)
        'spacing'            - chi co khoang cach, giu nguyen so coc
    evaluator(coords) -> dict {'pmax','pmin','mxmax','mymax'} (goi MCOC)
    """
    log = log or (lambda m: print(m))
    coords0 = np.asarray(params['original_coords'], dtype=float)
    history = []
    n_calls = [0]
    allow_removal = params.get('refine_mode', 'full') != 'spacing'
    log("Che do: %s" % ("co khoang cach + giam so coc" if allow_removal
                        else "chi co khoang cach (giu nguyen so coc)"))

    # ---- Noi long rang buoc theo HIEN TRANG goc (khong khat hon goc) ------
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

    # ---- Nhan dien luoi goc -------------------------------------------------
    grid = detect_grid(coords0)
    if grid is None:
        log("CHU Y: phuong an goc la bo tri doi xung TUY BIEN (khong phai "
            "luoi deu/hoa mai chuan) -> giu nguyen HINH DANG bo tri, chi co "
            "deu toan cum tung buoc nho; khong giam so coc.")
    else:
        log("Luoi goc: " + grid_label(grid))

    def evaluate(coords, label):
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

    # ---- Buoc 0: MCOC danh gia phuong an goc -------------------------------
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

        # He so hieu chinh K cap nhat tu lan goi MCOC gan nhat
        pm_rigid, _ = rigid_pmax_pmin(cur['coords'], loads)
        K = cur['pmax'] / pm_rigid if pm_rigid > 1e-9 else 1.0

        # Sinh va du bao cac buoc ung vien
        cands = []
        if cur_grid is not None:
            moves = [(sp, lb, grid_coords(sp))
                     for sp, lb in candidate_moves(cur_grid, params, allow_removal)]
        else:
            # Bo tri tuy bien: CO DEU toan cum mot nac nho quanh trong tam,
            # giu nguyen hinh dang; khong bo coc.
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

        # Uu tien: it coc nhat -> be gon nhat -> du bao thap nhat
        cands.sort(key=lambda r: (r['n'], r['fp'], r['pred']))

        improved = False
        for cand in cands[:mcoc_per_iter]:
            # Buoc phai thuc su tot hon hien tai
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
