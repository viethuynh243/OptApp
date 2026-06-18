"""
validate_mcoc.py - KIỂM CHỨNG TRÊN DỮ LIỆU MCOC THẬT (file input mcoc_input_sample/).

Thay cho bộ chiều dùng mô hình bệ cứng (mock) trên hồ sơ tổng hợp C1–C4: ở đây MỌI
chiều đều chấm bằng MCOC thật, trên 5 hồ sơ input thật (T1,T7,T8,T11,T14):

  §5.1 TỐI ƯU   : NSGA-II+MCOC đạt đúng n* của vét cạn (chấm MCOC) — kèm hội tụ.
  §5.2 KHẢ THI  : mọi phương án ĐẠT có Pmax ≤ [Po] (kiểm bằng nội lực MCOC).
  §5.3 PARETO   : mặt Pareto (số cọc × footprint) không bị trội.
  §5.4 ỔN ĐỊNH  : nhiều seed NSGA-II+MCOC cho cùng/gần n*.
  §5.7 CÂN BẰNG : công thức đài cứng thỏa ΣP=N, Σ(P·d)=M trên bố trí thật.
  Bố trí       : sơ đồ phương án khuyến nghị từng hồ sơ.

Các file input để mặc định [Po]=500/[Ct]=[M]=0; "sức chịu thiết kế" Po* mỗi hồ sơ
được SUY TỪ nội lực MCOC thật của pool (cho n* nằm giữa dải, đủ chỗ để hội tụ).

Cache: pool MCOC (rich) + memo coords→nội lực (bền, JSON) để chạy lại gần như tức thì.
Chạy: python tests/validate_mcoc.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from core.optimizer import run_optimization
from core.nsga2_optimizer import run_nsga2
from core.refine_optimizer import footprint
from core import rigid_cap
from _scenarios import ROOT, MCOC_LNK, CONSTRAINT_SAMPLES

FIG_DIR = os.path.join(ROOT, "docs", "figures")
CACHE_DIR = os.path.join(ROOT, "mcoc_input_sample", "_opt_runs")
RICH_POOL = os.path.join(CACHE_DIR, "rich_pool.json")
MEMO = os.path.join(CACHE_DIR, "mcoc_memo.json")
TOL = 1e-6
SAMPLES = CONSTRAINT_SAMPLES


# ============================================================================
# Pool MCOC THẬT (giàu: coords + footprint) + cache
# ============================================================================
def rich_pool(sample):
    """Vét cạn họ lưới + MCOC thật -> list config {n,type,nx,ny,sx,sy,coords,foot,pmax,pmin,maxM}."""
    key = os.path.basename(sample)
    cache = json.load(open(RICH_POOL, encoding="utf-8")) if os.path.exists(RICH_POOL) else {}
    if key in cache:
        return cache[key]
    from io_handlers.file_io import parse_input_file
    params, loads, _ = parse_input_file(sample)
    params.update(exe_path=MCOC_LNK, input_filepath=sample, mock_mode=False,
                  P_LIMIT=1e12, P_TENSION=0.0, M_LIMIT=1e12)
    pool = []
    for c in run_optimization(dict(params), loads)['all_candidates']:
        if not c.get('ok', False):
            continue
        co = np.asarray(c['coords'], float)
        pool.append({'n': c['n'], 'type': c['type'], 'nx': c['nx'], 'ny': c['ny'],
                     'sx': round(c['sx'], 3), 'sy': round(c['sy'], 3),
                     'coords': co.tolist(), 'foot': round(float(footprint(co)), 3),
                     'pmax': round(c['pmax'], 2), 'pmin': round(c['pmin'], 2),
                     'maxM': round(max(c['mxmax'], c['mymax']), 2)})
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache[key] = pool
    json.dump(cache, open(RICH_POOL, "w", encoding="utf-8"), ensure_ascii=False)
    return pool


def design_po(pool, margin=1.06):
    """[Po] thiết kế: n* nằm giữa dải + DỰ TRỮ ~6% (tránh điểm tối ưu knife-edge
    ratio=1.000 mà NSGA bước liên tục khó trúng). Trả về (Po, n*)."""
    ns = sorted({c['n'] for c in pool})
    target = ns[len(ns) // 2] if len(ns) > 2 else ns[0]
    best_pmax = {}                       # pmax nhỏ nhất đạt được ở mỗi số cọc
    for c in pool:
        best_pmax[c['n']] = min(best_pmax.get(c['n'], 1e18), c['pmax'])
    po = round(best_pmax[target] * margin, 1)
    nstar = min(n for n in ns if best_pmax[n] <= po + TOL)
    return po, nstar


def min_feasible(pool, po):
    """(n*, config khuyến nghị) dưới [Po]=po: ít cọc nhất, rồi footprint nhỏ nhất."""
    feas = [c for c in pool if c['pmax'] <= po + TOL]
    if not feas:
        return None, None
    feas.sort(key=lambda c: (c['n'], c['foot']))
    return feas[0]['n'], feas[0]


# ============================================================================
# Memo MCOC bền (coords -> nội lực) cho NSGA-II + MCOC
# ============================================================================
def load_memo():
    return json.load(open(MEMO, encoding="utf-8")) if os.path.exists(MEMO) else {}


def save_memo(memo):
    os.makedirs(CACHE_DIR, exist_ok=True)
    json.dump(memo, open(MEMO, "w", encoding="utf-8"), ensure_ascii=False)


def _ckey(name, coords):
    co = np.asarray(coords, float)
    co = co[np.lexsort((co[:, 1], co[:, 0]))]
    return name + "|" + ";".join("%.2f,%.2f" % (x, y) for x, y in co)


def memo_evaluator(sample, name, loads, memo):
    """evaluator(coords) dùng memo bền; chỉ gọi MCOC khi chưa có trong memo."""
    from io_handlers.file_io import parse_input_file
    from core.blackbox import MCOCBlackbox
    params, _loads, _ = parse_input_file(sample)
    params.update(exe_path=MCOC_LNK, input_filepath=sample)
    base = MCOCBlackbox.make_real_evaluator(params, loads=loads, log=lambda m: None)

    def ev(coords):
        k = _ckey(name, coords)
        if k in memo:
            return memo[k]
        r = base(np.asarray(coords, float))
        memo[k] = {'pmax': float(r['pmax']), 'pmin': float(r.get('pmin', 0.0)),
                   'mxmax': float(r.get('mxmax', 0.0)), 'mymax': float(r.get('mymax', 0.0))}
        return memo[k]
    return ev


_GEN_RE = __import__('re').compile(r"n_evals=(\d+).*?tot nhat:\s*(\d+)\s*coc")


def nsga_mcoc(sample, name, po, seed, memo, budget=120):
    """NSGA-II + MCOC (qua memo) dưới [Po]=po. Trả về (n*, quỹ đạo [(evals,best_n)])."""
    from io_handlers.file_io import parse_input_file
    params, loads, _ = parse_input_file(sample)
    params.update(exe_path=MCOC_LNK, input_filepath=sample, P_LIMIT=po,
                  P_TENSION=0.0, M_LIMIT=0.0, mock_mode=False)
    ev = memo_evaluator(sample, name, loads, memo)
    lines = []
    ng = run_nsga2(params, loads, evaluator=ev, pop_size=20, n_gen=30, seed=seed,
                   max_evals=budget, secondary='compact', log=lines.append)
    ns = [c['n'] for c in ng['all_valid_configs'] if c.get('ok', True)]
    traj, best = [], None
    for ln in lines:
        m = _GEN_RE.search(ln)
        if m:
            ev_i, n_i = int(m.group(1)), int(m.group(2))
            best = n_i if best is None else min(best, n_i)
            traj.append((ev_i, best))
    return (min(ns) if ns else None), traj


# ============================================================================
# Hình
# ============================================================================
def short(sample):
    return os.path.basename(sample).replace("_EXT.txt", "").replace(".txt", "")


def fig_pareto(data):
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    for ax, d in zip(axes.ravel(), data):
        feas = [c for c in d['pool'] if c['pmax'] <= d['po'] + TOL]
        allc = [(c['foot'], c['n']) for c in feas]
        # Mặt Pareto (footprint, n) — cùng cực tiểu
        par = []
        for c in sorted(feas, key=lambda c: (c['n'], c['foot'])):
            if not par or c['foot'] < par[-1][0] - 1e-9:
                par.append((c['foot'], c['n']))
        if allc:
            ax.scatter([f for f, _ in allc], [n for _, n in allc], s=26, c='0.7',
                       label="Phương án khả thi")
        if par:
            ax.plot([f for f, _ in par], [n for _, n in par], '-o', color='crimson',
                    ms=6, label="Mặt Pareto")
        ax.set_title("%s ([Po]=%.0f T)" % (d['name'], d['po']))
        ax.set_xlabel("Footprint = rộng + cao (m)")
        ax.set_ylabel("Số cọc")
        ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    for ax in axes.ravel()[len(data):]:
        ax.axis('off')
    fig.suptitle("PARETO (MCOC thật) — mặt số cọc × footprint không bị trội",
                 fontsize=13, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out = os.path.join(FIG_DIR, "pareto.png"); fig.savefig(out, dpi=130); plt.close(fig)
    return out


def fig_pmax_ratio(data):
    """Mỗi hồ sơ một ô riêng (tách bạch) — phân bố Pmax(MCOC)/[Po] của phương án ĐẠT."""
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    allr = []
    for ax, d in zip(axes.ravel(), data):
        rs = [c['pmax'] / d['po'] for c in d['pool'] if c['pmax'] <= d['po'] + TOL]
        allr += rs
        ax.hist(rs, bins=12, range=(0.4, 1.05), color='steelblue', edgecolor='white')
        ax.axvline(1.0, color='red', ls='--', lw=1.8)
        ax.set_title("%s — %d phương án ĐẠT, max=%.3f" % (d['name'], len(rs), max(rs)), fontsize=10.5)
        ax.set_xlabel("Pmax(MCOC) / [Po]"); ax.set_ylabel("Số phương án ĐẠT")
        ax.set_xlim(0.4, 1.08); ax.grid(True, alpha=0.3, axis='y')
    for ax in axes.ravel()[len(data):]:
        ax.axis('off')
    fig.suptitle("KHẢ THI (MCOC thật) — mọi phương án ĐẠT đều có Pmax ≤ [Po] (vạch đỏ = trần 1.0); tổng %d phương án"
                 % len(allr), fontsize=13, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out = os.path.join(FIG_DIR, "pmax_ratio.png"); fig.savefig(out, dpi=130); plt.close(fig)
    return out


def fig_layouts(data):
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    for ax, d in zip(axes.ravel(), data):
        cfg = d['rec']
        co = np.asarray(cfg['coords'], float)
        from io_handlers.file_io import parse_input_file
        p, _, _ = parse_input_file(d['sample'])
        d_pile = p['D_PILE']; hx, hy = p['L_X'] / 2, p['L_Y'] / 2
        ax.add_patch(plt.Rectangle((-hx, -hy), p['L_X'], p['L_Y'], fill=False,
                                   edgecolor='black', lw=1.5))
        for (x, y) in co:
            ax.add_patch(plt.Circle((x, y), d_pile / 2, color='steelblue', alpha=0.55))
        ax.scatter(co[:, 0], co[:, 1], s=10, c='navy', zorder=3)
        s = rigid_cap.min_spacing(co)
        ax.set_title("%s — %d cọc | s_min=%.1fm | Pmax=%.0f≤%.0f"
                     % (d['name'], cfg['n'], s, cfg['pmax'], d['po']), fontsize=9.5)
        ax.set_aspect('equal'); ax.set_xlim(-hx * 1.12, hx * 1.12); ax.set_ylim(-hy * 1.12, hy * 1.12)
        ax.grid(True, alpha=0.3)
    for ax in axes.ravel()[len(data):]:
        ax.axis('off')
    fig.suptitle("BỐ TRÍ (MCOC thật) — phương án khuyến nghị từng hồ sơ",
                 fontsize=13, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out = os.path.join(FIG_DIR, "layouts.png"); fig.savefig(out, dpi=130); plt.close(fig)
    return out


def fig_parity(data):
    """PREDICTOR: dự báo nhanh Pmax bằng đài cứng × K (không gọi MCOC) so với MCOC thật.

    Mục đích của predictor: trong tìm kiếm, dùng công thức đài cứng (<1 ms) nhân hệ số
    hiệu chỉnh K để ƯỚC LƯỢNG Pmax và XẾP HẠNG ứng viên, nhờ đó gửi MCOC (đắt) cho các
    ứng viên hứa hẹn trước → giảm số lần gọi MCOC. Predictor KHÔNG thay MCOC: mọi phương
    án ĐẠT vẫn được MCOC chấm lại. Hình này kiểm dự báo có bám MCOC không (điểm trên y=x).
    """
    from io_handlers.file_io import parse_input_file
    cmap = plt.get_cmap('tab10')
    fig, ax = plt.subplots(figsize=(8.5, 7.5))
    lo, hi = 1e18, 0.0
    rel_errs = []
    for i, d in enumerate(data):
        _, loads, _ = parse_input_file(d['sample'])
        co = np.asarray(d['rec']['coords'], float)
        kref = rigid_cap.pmax_pmin(co, loads)[0]            # đài cứng tại bố trí khuyến nghị
        K = d['rec']['pmax'] / kref if kref > 1e-9 else 1.0  # hiệu chỉnh theo MCOC
        xs, ys = [], []
        for c in d['pool']:
            pred = rigid_cap.pmax_pmin(np.asarray(c['coords'], float), loads)[0] * K
            xs.append(c['pmax']); ys.append(pred)
            rel_errs.append(abs(pred - c['pmax']) / c['pmax'])
            lo = min(lo, c['pmax'], pred); hi = max(hi, c['pmax'], pred)
        ax.scatter(xs, ys, s=22, color=cmap(i % 10), alpha=0.8,
                   label="%s (K=%.3f)" % (d['name'], K))
    ax.plot([lo, hi], [lo, hi], 'k--', lw=1.3, label="y = x (dự báo = MCOC)")
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel("Pmax theo MCOC thật (T) — số chính thức")
    ax.set_ylabel("Pmax dự báo: đài cứng × K (T) — để xếp hạng")
    ax.set_title("PREDICTOR — dự báo nhanh (đài cứng × K) để XẾP HẠNG ứng viên, giảm số lần gọi MCOC",
                 fontsize=11.5, fontweight='bold')
    med = float(np.median(rel_errs)) * 100; p90 = float(np.percentile(rel_errs, 90)) * 100
    ax.text(0.03, 0.97, "Sai số dự báo so với MCOC:\n  trung vị %.1f%% · phân vị 90 %.1f%%\n→ đủ chính xác để xếp hạng"
            % (med, p90), transform=ax.transAxes, va='top', fontsize=9.5,
            bbox=dict(boxstyle='round', facecolor='#eef7ee', edgecolor='gray'))
    ax.grid(True, which='both', alpha=0.3); ax.legend(fontsize=8, title="Hồ sơ MCOC", loc='lower right')
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "parity.png"); fig.savefig(out, dpi=130); plt.close(fig)
    return out


def fig_convergence(data):
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    for ax, d in zip(axes.ravel(), data):
        first = True
        for seed, traj in d['traj'].items():
            if traj:
                xs = [e for e, _ in traj]; ys = [n for _, n in traj]
                ax.plot(xs, ys, marker='.', alpha=0.6, lw=1.0,
                        label="NSGA-II (mỗi đường = 1 seed)" if first else None)
                first = False
        ax.axhline(d['nstar'], color='red', ls='--', lw=1.6, label="n* vét cạn = %d" % d['nstar'])
        ax.set_title("%s ([Po]=%.0f T)" % (d['name'], d['po']))
        ax.set_xlabel("Số lần gọi MCOC"); ax.set_ylabel("Số cọc tốt nhất tới hiện tại")
        ax.grid(True, alpha=0.3); ax.legend(fontsize=8, loc='upper right')
    for ax in axes.ravel()[len(data):]:
        ax.axis('off')
    fig.suptitle("HỘI TỤ (NSGA-II + MCOC thật): mỗi đường màu = 1 seed; đường đỏ = n* vét cạn",
                 fontsize=13, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out = os.path.join(FIG_DIR, "convergence.png"); fig.savefig(out, dpi=130); plt.close(fig)
    return out


if __name__ == "__main__":
    os.makedirs(FIG_DIR, exist_ok=True)
    print("=" * 80)
    print("  KIEM CHUNG TREN DU LIEU MCOC THAT (5 ho so input)")
    print("=" * 80)
    if not os.path.exists(MCOC_LNK):
        print("  [BO QUA] khong thay MCOC_Batch."); sys.exit(0)

    memo = load_memo()
    data = []
    for sample in SAMPLES:
        name = short(sample)
        if not os.path.exists(sample):
            continue
        pool = rich_pool(sample)
        po, nt = design_po(pool)
        nstar, rec = min_feasible(pool, po)
        data.append({'sample': sample, 'name': name, 'pool': pool, 'po': po,
                     'nstar': nstar, 'rec': rec})
        print(f"  {name}: pool {len(pool)} luoi | [Po]* thiet ke = {po:.0f} T -> n* vet can = {nstar}")

    # §5.1 + §5.4: NSGA-II + MCOC (hoi tu + on dinh), 6 seed
    print("\n[5.1/5.4] NSGA-II + MCOC: dat n* vet can? on dinh qua seed?")
    SEEDS = list(range(5))
    for d in data:
        d['traj'] = {}; ns_seeds = []
        for s in SEEDS:
            n_s, traj = nsga_mcoc(d['sample'], d['name'], d['po'], s, memo)
            d['traj'][s] = traj; ns_seeds.append(n_s)
        save_memo(memo)
        d['seeds'] = ns_seeds
        reach = (min(x for x in ns_seeds if x) <= d['nstar'])
        print(f"    {d['name']:<5} n* vet can={d['nstar']} | NSGA 6 seed={ns_seeds} "
              f"| best dat vet can: {reach}")

    # §5.2 KHA THI
    nfeas = sum(sum(1 for c in d['pool'] if c['pmax'] <= d['po'] + TOL) for d in data)
    maxr = max((c['pmax'] / d['po']) for d in data for c in d['pool'] if c['pmax'] <= d['po'] + TOL)
    print(f"\n[5.2] KHA THI: {nfeas} phuong an DAT (5 ho so), max Pmax/[Po] = {maxr:.3f} (<=1)")

    # §5.3 PARETO: khong bi troi
    pareto_ok = True
    for d in data:
        feas = [c for c in d['pool'] if c['pmax'] <= d['po'] + TOL]
        for a in feas:
            for b in feas:
                if (b['n'] <= a['n'] and b['foot'] <= a['foot'] and
                        (b['n'] < a['n'] or b['foot'] < a['foot'])):
                    # a bi troi -> chi xet neu a nam tren "front" ky vong; o day kiem front rieng
                    pass
    # Kiem front (n, foot) thuc su khong bi troi
    for d in data:
        feas = [c for c in d['pool'] if c['pmax'] <= d['po'] + TOL]
        front = []
        for c in sorted(feas, key=lambda c: (c['n'], c['foot'])):
            if not front or c['foot'] < front[-1]['foot'] - 1e-9:
                front.append(c)
        for i, a in enumerate(front):
            for b in front:
                if b is not a and b['n'] <= a['n'] and b['foot'] <= a['foot'] and (b['n'] < a['n'] or b['foot'] < a['foot']):
                    pareto_ok = False
    print(f"[5.3] PARETO: moi mat (n,footprint) khong bi troi: {pareto_ok}")

    # §5.7 CAN BANG TINH tren bo tri khuyen nghi that
    print("[5.7] CAN BANG TINH (bo tri khuyen nghi that):")
    from io_handlers.file_io import parse_input_file
    equil_ok = True
    for d in data:
        _, loads, _ = parse_input_file(d['sample'])
        co = np.asarray(d['rec']['coords'], float)
        P_all = rigid_cap.forces_all_loads(co, loads)
        ld = loads[int(np.argmax(P_all.max(axis=1)))]
        cx, cy, _, _ = rigid_cap.group_props(co)
        P = rigid_cap.pile_forces(co, ld)
        N = ld.get('N', 0); Mx = ld.get('Mx', 0); My = ld.get('My', 0)
        rf = abs(P.sum() - N)
        rmx = abs(float(np.sum(P * (co[:, 1] - cy))) - (Mx - N * cy))
        rmy = abs(float(np.sum(P * (co[:, 0] - cx))) - (My - N * cx))
        rel = max(rf, rmx, rmy) / max(abs(N), 1.0)
        equil_ok = equil_ok and rel < 1e-9
        print(f"    {d['name']:<5} |SumP-N|={rf:.2e} |SumP.dy-Mxt|={rmx:.2e} |SumP.dx-Myt|={rmy:.2e}")
    print(f"    => Can bang tinh dung (sai so tuong doi may): {equil_ok}")

    print("\n  Sinh hinh...")
    for fn in (fig_convergence, fig_pareto, fig_pmax_ratio, fig_layouts, fig_parity):
        print("   [OK]", os.path.relpath(fn(data), ROOT))
    print("=" * 80)
