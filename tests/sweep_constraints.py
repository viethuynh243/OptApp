"""
sweep_constraints.py - KIỂM CHỨNG XUYÊN SUỐT: đổi ngưỡng sức chịu (nén [Po]-R5,
nhổ [Ct]-R5b, uốn [M]-R6) thì VẪN TÌM ĐƯỢC PHƯƠNG ÁN TỐI ƯU — trên NHIỀU hồ sơ
MCOC THẬT (`mcoc_input_sample/`), không tách bạch về một hồ sơ.

Với mỗi hồ sơ trong `_scenarios.CONSTRAINT_SAMPLES`:
  1. Đánh giá MỘT LẦN toàn bộ họ lưới hợp lệ bằng MCOC thật (run_optimization +
     MCOC), thu pool {n, Pmax, Pmin, Mômen đầu cọc} — nội lực thật cho mỗi số cọc.
  2. Với mỗi ngưỡng, số cọc tối ưu = phương án ít cọc nhất còn thỏa:
        n*([Po]) = min n có Pmax ≤ [Po];  n*([Ct]) = min n có Pmin ≥ −[Ct];
        n*([M])  = min n có mômen ≤ [M].
     (Đây là vét cạn họ lưới chấm MCOC — hàm mục tiêu tìm phương án ít cọc nhất.)

Các file input để mặc định [Po]=500, [Ct]=[M]=0 nên dải ngưỡng kiểm nghiệm KHÔNG
lấy mặc định mà SUY TỪ dải nội lực thật của từng pool. Lực nhổ (R5b) chỉ xuất hiện
ở hồ sơ tải lệch tâm mạnh (T7, T8) nên R5b chỉ vẽ cho các hồ sơ đó.

Pool MCOC được cache (JSON) để chạy lại nhanh; xóa cache để buộc chạy lại MCOC.
Chạy: python tests/sweep_constraints.py
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
from _scenarios import ROOT, MCOC_LNK, CONSTRAINT_SAMPLES

FIG_DIR = os.path.join(ROOT, "docs", "figures")
CACHE = os.path.join(ROOT, "mcoc_input_sample", "_opt_runs", "pool_cache.json")
TOL = 1e-6


def build_pool(sample):
    """Pool MCOC thật của một hồ sơ: list {n, pmax, pmin, maxM}. Có cache JSON."""
    key = os.path.basename(sample)
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE, encoding="utf-8"))
        except Exception:
            cache = {}
    if key in cache:
        return cache[key]
    from io_handlers.file_io import parse_input_file
    params, loads, _ = parse_input_file(sample)
    params.update(exe_path=MCOC_LNK, input_filepath=sample, mock_mode=False,
                  P_LIMIT=1e12, P_TENSION=0.0, M_LIMIT=1e12)
    cands = run_optimization(dict(params), loads)['all_candidates']
    pool = [{'n': c['n'], 'pmax': round(c['pmax'], 2), 'pmin': round(c['pmin'], 2),
             'maxM': round(max(c['mxmax'], c['mymax']), 2)} for c in cands if c.get('ok', False)]
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    cache[key] = pool
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return pool


def nstar(pool, predicate):
    """Số cọc nhỏ nhất có ít nhất một phương án trong pool thỏa predicate (None nếu không)."""
    ns = [c['n'] for c in pool if predicate(c)]
    return min(ns) if ns else None


def logspace_pts(lo, hi, n=14):
    """n điểm cách đều theo log giữa lo và hi (lo>0)."""
    return list(np.exp(np.linspace(np.log(lo), np.log(hi), n)))


def po_curve(pool):
    """(threshold [Po], n*) trên dải Pmax thật của pool."""
    vals = [c['pmax'] for c in pool]
    xs = logspace_pts(min(vals) * 1.001, max(vals) * 1.02)
    return [(x, nstar(pool, lambda c, x=x: c['pmax'] <= x + TOL)) for x in xs]


def m_curve(pool):
    """(threshold [M], n*) trên dải mômen thật của pool."""
    vals = [c['maxM'] for c in pool]
    xs = logspace_pts(min(vals) * 1.001, max(vals) * 1.02)
    return [(x, nstar(pool, lambda c, x=x: c['maxM'] <= x + TOL)) for x in xs]


def ct_curve(pool):
    """(threshold [Ct], n*) — chỉ có nghĩa khi pool có lực nhổ (Pmin<0)."""
    demand = [-c['pmin'] for c in pool if c['pmin'] < 0]   # nhu cầu sức chịu nhổ
    if not demand:
        return None
    least = min(d for d in demand if d > 0) if any(d > 0 for d in demand) else min(demand)
    xs = logspace_pts(max(least * 1.001, 1.0), max(demand) * 1.02)
    return [(x, nstar(pool, lambda c, x=x: c['pmin'] >= -x - TOL)) for x in xs]


def has_tension(pool):
    return min(c['pmin'] for c in pool) < -TOL


def monotone_noninc(curve):
    """n* không tăng khi ngưỡng tăng; vô nghiệm (None) chỉ ở đầu (ngưỡng nhỏ nhất)."""
    seen, prev = False, None
    for _, n in curve:
        if n is None:
            if seen:
                return False
            continue
        seen = True
        if prev is not None and n > prev:
            return False
        prev = n
    return True


def make_figure(data):
    """3 ô (R5/R5b/R6); mỗi hồ sơ một đường; trục ngưỡng theo log (thang lực khác nhau)."""
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.2))
    cmap = plt.get_cmap('tab10')
    titles = ['(a) R5 — nới [Po] thì n* giảm', '(b) R5b — chỉ T7, T8 có lực nhổ (tải lệch tâm mạnh)',
              '(c) R6 — siết [M] thì n* tăng']
    xlabels = ['Sức chịu nén [Po] (T)', 'Sức chịu nhổ [Ct] (T)', 'Sức chịu uốn [M] (T·m)']
    keys = ['po', 'ct', 'm']
    for ax, title, xlabel, key in zip(axes, titles, xlabels, keys):
        for i, d in enumerate(data):
            curve = d[key]
            if not curve:
                continue
            feas = [(x, n) for x, n in curve if n is not None]
            if feas:
                ax.plot([x for x, _ in feas], [n for _, n in feas], '-o', ms=4,
                        color=cmap(i % 10), label=d['name'])
        ax.set_xscale('log')
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Số cọc tối ưu n*')
        ax.set_title(title)
        ax.grid(True, which='both', alpha=0.3)
        ax.legend(fontsize=8, title='Hồ sơ MCOC')
    fig.suptitle('TÌM ĐƯỢC TỐI ƯU KHI ĐỔI NGƯỠNG RÀNG BUỘC (R5, R5b, R6) — nhiều hồ sơ MCOC thật',
                 fontsize=13, fontweight='bold')
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    out = os.path.join(FIG_DIR, "constraints.png")
    fig.savefig(out, dpi=130)
    plt.close(fig)
    return out


if __name__ == "__main__":
    os.makedirs(FIG_DIR, exist_ok=True)
    print("=" * 80)
    print("  KIEM CHUNG XUYEN SUOT: doi nguong rang buoc -> van tim duoc toi uu")
    print("  (nhieu ho so MCOC that trong mcoc_input_sample/)")
    print("=" * 80)
    if not os.path.exists(MCOC_LNK):
        print("  [BO QUA] khong thay MCOC_Batch.")
        sys.exit(0)

    data, all_mono = [], True
    for sample in CONSTRAINT_SAMPLES:
        name = os.path.basename(sample).replace("_EXT.txt", "").replace(".txt", "")
        if not os.path.exists(sample):
            print(f"  [BO QUA] khong thay {name}")
            continue
        pool = build_pool(sample)
        if not pool:
            print(f"  [BO QUA] {name}: pool rong")
            continue
        ns = sorted({c['n'] for c in pool})
        d = {'name': name, 'pool': pool,
             'po': po_curve(pool), 'm': m_curve(pool),
             'ct': ct_curve(pool) if has_tension(pool) else None}
        data.append(d)
        # Kiem don dieu tung rang buoc
        mono_po = monotone_noninc(d['po']); mono_m = monotone_noninc(d['m'])
        mono_ct = monotone_noninc(d['ct']) if d['ct'] else True
        all_mono = all_mono and mono_po and mono_m and mono_ct
        nstar_po = [n for _, n in d['po'] if n is not None]
        nstar_m = [n for _, n in d['m'] if n is not None]
        print(f"\n  {name}: pool {len(pool)} luoi, n = {min(ns)}..{max(ns)}"
              f"{' | CO luc nho' if d['ct'] else ''}")
        print(f"     R5  [Po] {min(c['pmax'] for c in pool):.0f}..{max(c['pmax'] for c in pool):.0f} T"
              f"  -> n* {max(nstar_po)}..{min(nstar_po)}  | don dieu: {mono_po}")
        if d['ct']:
            nstar_ct = [n for _, n in d['ct'] if n is not None]
            print(f"     R5b [Ct] (nho toi {-min(c['pmin'] for c in pool):.0f} T)"
                  f"  -> n* {max(nstar_ct)}..{min(nstar_ct)}  | don dieu: {mono_ct}")
        print(f"     R6  [M]  {min(c['maxM'] for c in pool):.0f}..{max(c['maxM'] for c in pool):.0f} T.m"
              f"  -> n* {max(nstar_m)}..{min(nstar_m)}  | don dieu: {mono_m}")

    print(f"\n  => Don dieu DUNG tren MOI ho so & MOI rang buoc: {all_mono}")

    # Doi chung engine: NSGA-II + MCOC tai 1 moc R6 tieu bieu (ho so T7)
    from io_handlers.file_io import parse_input_file
    from core.blackbox import MCOCBlackbox
    t7 = next((s for s in CONSTRAINT_SAMPLES if "T7" in s), None)
    if t7:
        params, loads, _ = parse_input_file(t7)
        params.update(exe_path=MCOC_LNK, input_filepath=t7, mock_mode=False,
                      P_LIMIT=1e12, P_TENSION=0.0, M_LIMIT=140.0)
        ev = MCOCBlackbox.make_real_evaluator(params, loads=loads, log=lambda m: None)
        ng = run_nsga2(params, loads, evaluator=ev, pop_size=12, n_gen=10, seed=0,
                       max_evals=60, secondary='compact', log=lambda m: None)
        ns = [c['n'] for c in ng['all_valid_configs'] if c.get('ok', True)]
        n_nsga = min(ns) if ns else None
        t7pool = next(d['pool'] for d in data if d['name'] == "T7")
        n_grid = nstar(t7pool, lambda c: c['maxM'] <= 140 + TOL)
        print(f"  Doi chung engine (T7, [M]=140 T.m): NSGA-II+MCOC n*={n_nsga} | vet can pool={n_grid}"
              f" | {'khop' if n_nsga == n_grid else 'LECH'}")

    out = make_figure(data)
    print(f"\n  [OK] {os.path.relpath(out, ROOT)}")
    print("=" * 80)
