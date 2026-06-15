"""
test_nsga2.py - Kiem thu engine NSGA-II.

Chay:
    cd d:/Project/TEDI/OptApp
    python tests/test_nsga2.py
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.nsga2_optimizer import run_nsga2, decode, min_spacing


# ============================================================================
# Dữ liệu vào dùng chung cho các test (bệ 6.0x9.6, cọc D1.2, [Po]=500T)
# ============================================================================
PARAMS = {
    'L_X': 6.0, 'L_Y': 9.6, 'D_PILE': 1.2, 'SAFE_D': 1.2,
    'P_LIMIT': 500.0, 'P_TENSION': 0.0, 'M_LIMIT': 0.0, 'mock_mode': True,
    'original_coords': [[-1.5, -3.0], [1.5, -3.0], [-1.5, 0.0],
                        [1.5, 0.0], [-1.5, 3.0], [1.5, 3.0]],
    'orig_pmax': 519.63, 'orig_pmin': 0.0, 'orig_mxmax': 7.49, 'orig_mymax': 27.82,
}
LOADS = [
    {'Hx': 0, 'Hy': 0, 'N': 2577.0, 'Mx': 1500.0, 'My': 1500.0, 'Mz': 0},
    {'Hx': 0, 'Hy': 0, 'N': 2400.0, 'Mx': 800.0, 'My': 2000.0, 'Mz': 0},
    {'Hx': 0, 'Hy': 0, 'N': 2800.0, 'Mx': 1800.0, 'My': 1200.0, 'Mz': 0},
]


def _check(cond, msg):
    """In [PASS]/[FAIL] kèm thông điệp rồi assert điều kiện."""
    print(("  [PASS] " if cond else "  [FAIL] ") + msg)
    assert cond, msg


# ============================================================================
# Các test
# ============================================================================
def test_runs_and_recommends():
    """Engine chạy được và trả về phương án kiến nghị cùng số lần đánh giá > 0."""
    print("TEST 1: NSGA-II chay & dua ra phuong an kien nghi")
    # secondary='pmax' de cac assert ve mat Pareto (n, pmax) ben duoi nhat quan
    res = run_nsga2(PARAMS, LOADS, pop_size=30, n_gen=20, seed=1, secondary='pmax')
    _check(res['recommended'] is not None, "co phuong an kien nghi")
    _check(res['n_evals'] > 0, "co goi danh gia (%d lan)" % res['n_evals'])
    return res


def test_pareto_non_dominated(res):
    """Mọi cặp phương án trên mặt Pareto đều không thống trị lẫn nhau."""
    print("TEST 2: Mat Pareto khong co phuong an bi thong tri")
    pf = res['pareto_front']
    _check(len(pf) >= 1, "Pareto khong rong (%d phuong an)" % len(pf))
    for a in pf:
        for b in pf:
            if a is b:
                continue
            # b thống trị a nếu b không tệ hơn ở cả 2 mục tiêu và tốt hơn ở ít nhất 1
            dom = (b['n'] <= a['n'] and b['pmax'] <= a['pmax'] and
                   (b['n'] < a['n'] or b['pmax'] < a['pmax']))
            _check(not dom, "khong bi thong tri: (%d,%.1f) vs (%d,%.1f)"
                   % (a['n'], a['pmax'], b['n'], b['pmax']))


def test_feasible_respect_constraints(res):
    """Mỗi phương án hợp lệ phải thỏa: Pmax<=[Po], khoảng cách tim>=3d, nằm trong bệ."""
    print("TEST 3: Moi phuong an DAT thuc su thoa rang buoc")
    d = PARAMS['D_PILE']
    Po = PARAMS['P_LIMIT']
    for c in res['all_valid_configs']:
        _check(c['pmax'] <= Po + 1e-6,
               "Pmax=%.1f <= Po=%.1f (%dx%d)" % (c['pmax'], Po, c['nx'], c['ny']))
        s = min_spacing(np.asarray(c['coords'], float))
        # Khoảng cách tim-đến-tim nhỏ nhất phải >= 3 lần đường kính cọc
        _check(s >= 3 * d - 1e-3,
               "khoang cach %.2f >= 3d=%.2f" % (s, 3 * d))
        mx = np.max(np.abs(np.asarray(c['coords'])[:, 0]))
        my = np.max(np.abs(np.asarray(c['coords'])[:, 1]))
        # Mép cọc cộng khoảng an toàn không vượt nửa kích thước bệ theo từng phương
        _check(mx + PARAMS['SAFE_D'] <= PARAMS['L_X'] / 2 + 1e-3, "trong be X")
        _check(my + PARAMS['SAFE_D'] <= PARAMS['L_Y'] / 2 + 1e-3, "trong be Y")


def test_decode_repairs_typeB():
    """decode tự sửa genome Kiểu B nhỏ hơn 2x2 thành nx,ny>=2 và sinh được tọa độ."""
    print("TEST 4: decode sua chua genome Kieu B < 2x2")
    spec, coords = decode({'type': 'B', 'nx': 1, 'ny': 1, 'sx': 4.0, 'sy': 4.0},
                          PARAMS)
    _check(spec['nx'] >= 2 and spec['ny'] >= 2, "nx,ny duoc nang len >=2")
    _check(len(coords) >= 1, "sinh duoc toa do")


def test_reproducible():
    """Cùng một seed cho ra phương án kiến nghị giống hệt (tính tái lập được)."""
    print("TEST 5: Cung seed cho cung ket qua")
    r1 = run_nsga2(PARAMS, LOADS, pop_size=24, n_gen=12, seed=7)
    r2 = run_nsga2(PARAMS, LOADS, pop_size=24, n_gen=12, seed=7)
    a, b = r1['recommended'], r2['recommended']
    _check(a['n'] == b['n'] and abs(a['pmax'] - b['pmax']) < 1e-6,
           "tai lap: (%d,%.2f) == (%d,%.2f)" % (a['n'], a['pmax'], b['n'], b['pmax']))


if __name__ == "__main__":
    res = test_runs_and_recommends()
    test_pareto_non_dominated(res)
    test_feasible_respect_constraints(res)
    test_decode_repairs_typeB()
    test_reproducible()
    print("\n  TAT CA TEST DA PASS.")
    rec = res['recommended']
    print("  -> Kien nghi: Kieu %s %dx%d, %d coc, Pmax=%.2f T"
          % (rec['type'], rec['nx'], rec['ny'], rec['n'], rec['pmax']))
