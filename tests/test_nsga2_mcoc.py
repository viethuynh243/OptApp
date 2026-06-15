"""
test_nsga2_mcoc.py - Kiem thu NSGA-II danh gia bang MCOC THUC (qua stub subprocess).
Xac nhan duong "exact" (khong dung be cung trong quyet dinh) chay duoc.

Chay: python tests/test_nsga2_mcoc.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np
from core.blackbox import MCOCBlackbox
from core.nsga2_optimizer import run_nsga2
from io_handlers.file_io import parse_input_file
from io_handlers.mcoc_writer import self_check

WORK = os.path.join(ROOT, "tests", "_work")
os.makedirs(WORK, exist_ok=True)
INPUT_FILE = os.path.join(WORK, "DEMO_NSGA.txt")
STUB = os.path.join(ROOT, "tests", "mcoc_stub.py")


# ============================================================================
# Dựng dữ liệu vào
# ============================================================================
def build_input():
    """Tạo file input MCOC: bệ 7.2x13.2, 8 cọc D1.2 (lưới 2x4), 2 tổ hợp tải, Po=500T."""
    coords = [(-1.8, -5.4), (1.8, -5.4), (-1.8, -1.8), (1.8, -1.8),
              (-1.8, 1.8), (1.8, 1.8), (-1.8, 5.4), (1.8, 5.4)]
    L = ["DEMO NSGA MCOC", "8 2 0 0 0 0 0 0 7.2 13.2 1.8", "",
         "83.0 105.0 2025.0 -1499.0 951.0 0.0",
         "20.0 0.0 2577.0 -94.0 170.0 0.0"]
    for i, (x, y) in enumerate(coords, 1):
        L += ["0.0", str(i), "3001028 3001028 3001028 3001028 100 0 400",
              "20.0", "1.2", "1.2", "0.0", "1.131", "0.1018", "500", "33333.3",
              "16666.7", "%.3f   %.3f" % (x, y), "0", "0", "0"]
    open(INPUT_FILE, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return coords


# ============================================================================
# Kịch bản kiểm thử
# ============================================================================
def main():
    """Chạy NSGA-II với evaluator MCOC thực (stub) ở chế độ EXACT và kiểm tra:
    có phương án kiến nghị, đúng chế độ MCOC-exact, Pmax<=[Po], có file kết quả."""
    print("=" * 60)
    print(" TEST: NSGA-II + MCOC thuc (stub) — duong EXACT")
    print("=" * 60)
    build_input()
    params, loads, _ = parse_input_file(INPUT_FILE)
    assert params.get('original_coords'), "parser thieu original_coords"

    params['exe_path'] = STUB
    params['input_filepath'] = INPUT_FILE
    params['SAFE_D'] = params['D_PILE']
    params['P_LIMIT'] = params.get('P_LIMIT', 500.0)
    params['mock_mode'] = False

    ok, msg = self_check(INPUT_FILE, params['original_coords'])
    assert ok, "template self-check FAIL: " + msg
    print("[OK] template:", msg)

    evaluator = MCOCBlackbox.make_real_evaluator(params)
    res = run_nsga2(params, loads, evaluator=evaluator,
                    pop_size=10, n_gen=4, max_evals=25, seed=1,
                    log=lambda m: None)

    rec = res['recommended']
    assert rec is not None, "khong tim duoc phuong an: " + res['reason']
    assert res['n_evals'] > 0, "khong goi MCOC lan nao"
    # Phải đi đúng nhánh đánh giá bằng MCOC thực, không dùng công thức bệ cứng
    assert res['eval_mode'] == 'MCOC-exact', "phai la che do MCOC-exact, got " + res['eval_mode']
    assert rec['pmax'] <= params['P_LIMIT'] + 1e-6, "Pmax vuot [Po]"
    assert len(rec['coords']) == rec['n'] >= 2, "so coc khong hop le"  # số tọa độ khớp số cọc, >=2
    # File kết quả MCOC thực đã được sinh?
    workdir = evaluator.workdir
    nfiles = len([f for f in os.listdir(workdir) if f.endswith('_result.txt')])
    assert nfiles >= 1, "MCOC stub khong sinh file ket qua"

    print(f"[OK] NSGA-II+MCOC: {res['n_evals']} lan goi MCOC, "
          f"che do={res['eval_mode']}")
    print(f"[OK] Kien nghi: kieu {rec['type']} {rec['nx']}x{rec['ny']}, "
          f"{rec['n']} coc, Pmax={rec['pmax']:.2f} T")
    print(f"[OK] Mat Pareto: {len(res['pareto_front'])} phuong an")
    print("\n  TAT CA TEST DA PASS.")


if __name__ == "__main__":
    main()
